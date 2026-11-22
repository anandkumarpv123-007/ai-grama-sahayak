import importlib.util
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ai_grama_sahayak.core.retrieval_client")


class RetrievalOutcome:
    """
    Encapsulates the result of calling Member 2's retrieval interface.
    Explicitly distinguishes between:
    1. Genuine empty search results (success=True, chunks=[])
    2. Successful retrieved context (success=True, chunks=[...])
    3. Retrieval failure / service exceptions (success=False, error=...)
    4. Service module absent from workspace (success=True, is_available=False, chunks=[])
    """

    def __init__(
        self,
        chunks: List[Dict[str, Any]],
        success: bool,
        is_available: bool,
        error: Optional[str] = None,
    ):
        self.chunks = chunks
        self.success = success
        self.is_available = is_available
        self.error = error

    def __repr__(self) -> str:
        return (
            f"<RetrievalOutcome success={self.success} "
            f"chunks_count={len(self.chunks)} is_available={self.is_available} "
            f"error={self.error}>"
        )


def fetch_retrieval_context(
    query: str,
    assistant: str,
    language: str,
    state: Optional[str] = None,
    district: Optional[str] = None,
    top_k: int = 5,
) -> RetrievalOutcome:
    """
    Calls the agreed internal retrieval interface owned by Member 2:
        retrieve_context(
            query: str,
            assistant: str,
            language: str,
            state: str | None,
            district: str | None,
            top_k: int = 5
        )

    Strict requirements:
    - Never creates a competing retrieval implementation.
    - Accurately distinguishes between a genuine empty result and a service failure.
    - Logs retrieval failures with clear error messages.
    """
    # 1. Check if Member 2's module is genuinely present on disk
    if importlib.util.find_spec("app.services.retrieval") is None:
        logger.debug(
            "Member 2 retrieval service (app.services.retrieval) not present in workspace; "
            "operating in zero-evidence safe fallback mode."
        )
        return RetrievalOutcome(
            chunks=[],
            success=True,
            is_available=False,
            error=None,
        )

    # 2. Module exists: import and execute agreed interface
    try:
        from app.services.retrieval import retrieve_context
    except Exception as exc:
        logger.error(
            "Failed to import Member 2 retrieve_context from app.services.retrieval: %s",
            exc,
            exc_info=True,
        )
        return RetrievalOutcome(
            chunks=[],
            success=False,
            is_available=True,
            error=f"Retrieval import error: {exc}",
        )

    try:
        results = retrieve_context(
            query=query,
            assistant=assistant,
            language=language,
            state=state,
            district=district,
            top_k=top_k,
        )

        if not isinstance(results, list):
            err_msg = f"retrieve_context returned invalid non-list type: {type(results).__name__}"
            logger.error("Member 2 retrieval service contract violation: %s", err_msg)
            return RetrievalOutcome(
                chunks=[],
                success=False,
                is_available=True,
                error=err_msg,
            )

        # Genuine retrieval result (may be empty [] if no documents matched)
        logger.info(
            "Member 2 retrieve_context executed successfully [chunks_returned=%d, query='%s']",
            len(results),
            query[:50],
        )
        return RetrievalOutcome(
            chunks=results,
            success=True,
            is_available=True,
            error=None,
        )

    except Exception as exc:
        logger.error(
            "Member 2 retrieval execution failed with exception: %s",
            exc,
            exc_info=True,
        )
        return RetrievalOutcome(
            chunks=[],
            success=False,
            is_available=True,
            error=str(exc),
        )
