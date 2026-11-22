import logging
import uuid
from fastapi import APIRouter, status
from app.schemas.chat import ChatRequest, ChatResponse
from app.agents.router import agent_router
from app.core.retrieval_client import fetch_retrieval_context
from app.core.exceptions import BadRequestException
from app.database.session import get_session_factory
from app.models.conversation import Conversation
from app.models.message import ChatMessage

logger = logging.getLogger("ai_grama_sahayak.api.chat")

router = APIRouter()


def _save_chat_interaction_safely(
    conv_id: str,
    request: ChatRequest,
    response: ChatResponse,
) -> None:
    """
    Safely records conversation and message in PostgreSQL if available.
    Never fails the user's chat request if database is unreachable.
    """
    try:
        session_factory = get_session_factory()
        with session_factory() as session:
            # Check if conversation exists
            conv = (
                session.query(Conversation)
                .filter(Conversation.conversation_id == conv_id)
                .first()
            )
            if not conv:
                conv = Conversation(
                    conversation_id=conv_id,
                    assistant=request.assistant.value,
                    language=request.language.value,
                    state=request.state,
                    district=request.district,
                )
                session.add(conv)
            else:
                conv.assistant = request.assistant.value
                conv.language = request.language.value
                if request.state:
                    conv.state = request.state
                if request.district:
                    conv.district = request.district

            # Record citizen query message
            user_msg = ChatMessage(
                conversation_id=conv_id,
                role="user",
                content=request.message,
                sources=None,
            )
            session.add(user_msg)

            # Record assistant response message
            sources_json = [s.model_dump() for s in response.sources]
            assistant_msg = ChatMessage(
                conversation_id=conv_id,
                role="assistant",
                content=response.answer,
                sources=sources_json if sources_json else None,
            )
            session.add(assistant_msg)
            session.commit()
    except Exception as exc:
        logger.debug("Database interaction persistence skipped/failed: %s", exc)


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Main Chat Endpoint",
    description="Processes citizen messages, routes to domain specialist, retrieves verified context, and returns grounded answers.",
)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    # 1. Validate message content
    clean_message = request.message.strip()
    if not clean_message:
        raise BadRequestException(
            message="Message cannot be blank or empty whitespace.",
            code="EMPTY_MESSAGE",
        )

    # 2. Generate conversation ID if omitted
    conv_id = request.conversation_id
    if not conv_id or not conv_id.strip():
        conv_id = f"conv_{uuid.uuid4().hex[:12]}"

    # 3. Call internal retrieval interface owned by Member 2
    retrieval_outcome = fetch_retrieval_context(
        query=clean_message,
        assistant=request.assistant.value,
        language=request.language.value,
        state=request.state,
        district=request.district,
        top_k=5,
    )

    # 4. Route to specialist agent
    result = agent_router.route_and_process(
        query=clean_message,
        assistant=request.assistant,
        language=request.language,
        state=request.state,
        district=request.district,
        retrieval_outcome=retrieval_outcome,
    )

    response = ChatResponse(
        conversation_id=conv_id,
        answer=result["answer"],
        assistant=request.assistant,
        language=request.language,
        sources=result["sources"],
        needs_follow_up=result["needs_follow_up"],
        follow_up_questions=result["follow_up_questions"],
        safety_notice=result["safety_notice"],
    )

    # 5. Persist interaction in database (safe, non-blocking on failure)
    _save_chat_interaction_safely(conv_id, request, response)

    return response
