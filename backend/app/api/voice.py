"""
Voice API Router for AI Grama Sahayak
Author: Member 3
Prefix: /voice (so when registered by Member 1's main.py under /api, final paths are /api/voice/*)
Endpoints:
  POST /api/voice/transcribe
  POST /api/voice/speak
Adheres strictly to docs/api_contracts.md
"""

import logging
from fastapi import APIRouter, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

from app.services.voice.transcription import VoiceTranscriptionService, VoiceServiceException, MAX_AUDIO_SIZE_BYTES
from app.services.voice.synthesis import VoiceSynthesisService

logger = logging.getLogger("voice.api")

# Router prefix is /voice so Member 1's main.py can supply prefix="/api"
router = APIRouter(prefix="/voice", tags=["voice"])

transcription_service = VoiceTranscriptionService()
synthesis_service = VoiceSynthesisService()

CHUNK_SIZE = 64 * 1024  # 64 KB chunks for safe streaming read


class VoiceSpeakRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize into speech")
    language: str = Field("en", description="Language code: 'en' or 'te'")


def error_response(code: str, message: str, status_code: int, details: Optional[list] = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or []
            }
        }
    )


@router.post("/transcribe")
async def transcribe_voice(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = Form("en", description="Target language ('te' or 'en')")
):
    """
    POST /api/voice/transcribe
    Transcribes uploaded audio file to text in Telugu or English.
    """
    try:
        # Enforce 15 MB limit incrementally while reading
        file_bytes = bytearray()
        while True:
            chunk = file.file.read(CHUNK_SIZE) if hasattr(file, "file") else await file.read(CHUNK_SIZE)
            if not chunk:
                break
            file_bytes.extend(chunk)
            if len(file_bytes) > MAX_AUDIO_SIZE_BYTES:
                return error_response(
                    code="PAYLOAD_TOO_LARGE",
                    message=f"Audio file size exceeds the maximum allowed limit of {MAX_AUDIO_SIZE_BYTES // (1024 * 1024)} MB.",
                    status_code=413,
                    details=[{"field": "file", "issue": "Exceeds 15MB limit"}]
                )

        result = await transcription_service.transcribe(
            filename=file.filename,
            content_type=file.content_type,
            file_bytes=bytes(file_bytes),
            language=language
        )
        return result
    except VoiceServiceException as ve:
        return error_response(
            code=ve.code,
            message=ve.message,
            status_code=ve.status_code,
            details=ve.details
        )
    except Exception:
        logger.exception("Unexpected server error in transcribe_voice")
        return error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An internal server error occurred while processing the audio transcription.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/speak")
async def speak_voice(request: VoiceSpeakRequest):
    """
    POST /api/voice/speak
    Synthesizes given text into base64 encoded audio in Telugu or English.
    """
    try:
        result = await synthesis_service.speak(
            text=request.text,
            language=request.language
        )
        return result
    except VoiceServiceException as ve:
        return error_response(
            code=ve.code,
            message=ve.message,
            status_code=ve.status_code,
            details=ve.details
        )
    except Exception:
        logger.exception("Unexpected server error in speak_voice")
        return error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An internal server error occurred while synthesizing speech audio.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
