"""
Voice Transcription Service for AI Grama Sahayak
Author: Member 3
Contract: POST /api/voice/transcribe (multipart/form-data: file, language)
Returns: { "transcribed_text": str, "language": str, "confidence": float }
"""

import os
import io
import logging
from typing import Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger("voice.transcription")

SUPPORTED_LANGUAGES = {"en", "te"}
MAX_AUDIO_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".ogg", ".webm", ".m4a", ".flac", ".aac"}
ALLOWED_MIME_TYPES = {
    "audio/wav", "audio/x-wav", "audio/wave",
    "audio/mpeg", "audio/mp3",
    "audio/ogg", "application/ogg",
    "audio/webm",
    "audio/m4a", "audio/x-m4a", "audio/mp4",
    "audio/flac", "audio/x-flac",
    "audio/aac", "application/octet-stream"
}


class VoiceServiceException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[list] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(self.message)


def detect_container_mime(data: bytes) -> Optional[str]:
    """
    Detects audio container MIME type strictly from binary magic bytes / header signatures.
    Returns canonical MIME type, or None if unrecognized.
    """
    if len(data) < 4:
        return None

    # WebM / Matroska EBML header: 0x1A 0x45 0xDF 0xA3
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        return "audio/webm"

    # WAV / RIFF: starts with 'RIFF', bytes 8..12 are 'WAVE' (or big-endian 'RIFX' ... 'WAVE')
    if len(data) >= 12 and (data.startswith(b"RIFF") or data.startswith(b"RIFX")) and data[8:12] == b"WAVE":
        return "audio/wav"

    # OGG: 'OggS'
    if data.startswith(b"OggS"):
        return "audio/ogg"

    # MP3: ID3v2 tag ('ID3') or MPEG frame sync header (0xFF, high 3 bits of next byte set, layer != 0)
    if data.startswith(b"ID3"):
        return "audio/mpeg"
    if len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0 and (data[1] & 0x06) != 0x00:
        return "audio/mpeg"

    # FLAC: 'fLaC'
    if data.startswith(b"fLaC"):
        return "audio/flac"

    # MP4 / M4A: ISO base media file with 'ftyp' box at offset 4
    if len(data) >= 8 and data[4:8] == b"ftyp":
        return "audio/mp4"

    # AAC ADTS header: 0xFF followed by 0xF0..0xF1 (syncword 12 bits set)
    if len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xF6) == 0xF0:
        return "audio/aac"

    return None


def is_valid_audio_magic(data: bytes, ext: str = "") -> bool:
    """
    Verifies actual binary magic bytes / header signatures for supported audio formats.
    Strictly validates audio bytes: arbitrary non-audio bytes are rejected even with a valid extension.
    """
    return detect_container_mime(data) is not None


class VoiceTranscriptionService:
    """Handles audio validation and real STT transcription for Telugu and English."""

    def __init__(self, sarvam_key: Optional[str] = None, openai_key: Optional[str] = None):
        self.sarvam_key = sarvam_key or os.getenv("SARVAM_API_KEY") or settings.SARVAM_API_KEY
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY
        self.sarvam_model = os.getenv("SARVAM_STT_MODEL") or settings.SARVAM_STT_MODEL

    def validate_input(self, filename: Optional[str], content_type: Optional[str], file_bytes: bytes, language: str) -> None:
        # Validate language
        if not language or language.lower().strip() not in SUPPORTED_LANGUAGES:
            raise VoiceServiceException(
                code="UNSUPPORTED_LANGUAGE",
                message=f"Unsupported language code '{language}'. Supported languages are: 'te' (Telugu) and 'en' (English).",
                status_code=422,
                details=[{"field": "language", "issue": "Must be 'en' or 'te'"}]
            )

        # Validate file presence and non-empty
        if not file_bytes or len(file_bytes) == 0:
            raise VoiceServiceException(
                code="EMPTY_AUDIO_FILE",
                message="The uploaded audio file is empty. Please provide recorded audio.",
                status_code=400,
                details=[{"field": "file", "issue": "File size is 0 bytes"}]
            )

        # Enforce 15 MB limit
        if len(file_bytes) > MAX_AUDIO_SIZE_BYTES:
            raise VoiceServiceException(
                code="PAYLOAD_TOO_LARGE",
                message=f"Audio file size ({len(file_bytes)} bytes) exceeds the maximum allowed limit of {MAX_AUDIO_SIZE_BYTES // (1024 * 1024)} MB.",
                status_code=413,
                details=[{"field": "file", "issue": "Exceeds 15MB"}]
            )

        # Validate extension or MIME type
        ext = os.path.splitext(filename or "")[1].lower()
        content_type_clean = (content_type or "").split(";")[0].strip().lower()

        is_valid_ext = ext in ALLOWED_EXTENSIONS
        is_valid_mime = content_type_clean in ALLOWED_MIME_TYPES

        if not is_valid_ext and not is_valid_mime:
            raise VoiceServiceException(
                code="INVALID_AUDIO_FORMAT",
                message=f"Unsupported audio format '{ext or content_type_clean}'. Supported formats: wav, mp3, ogg, webm, m4a, flac.",
                status_code=400,
                details=[{"field": "file", "issue": f"Invalid format '{ext or content_type}'"}]
            )

        # Verify minimal audio length
        if len(file_bytes) < 32:
            raise VoiceServiceException(
                code="CORRUPTED_AUDIO_FILE",
                message="Audio file appears corrupted or too brief to contain valid speech data.",
                status_code=400,
                details=[{"field": "file", "issue": "Audio header too small"}]
            )

        # Check binary format header / magic
        if not is_valid_audio_magic(file_bytes, ext):
            raise VoiceServiceException(
                code="INVALID_AUDIO_FORMAT",
                message=f"File content does not match a valid audio format header for '{ext}'.",
                status_code=400,
                details=[{"field": "file", "issue": "Corrupt or invalid audio magic header"}]
            )

    async def transcribe(self, filename: Optional[str], content_type: Optional[str], file_bytes: bytes, language: str = "en") -> Dict[str, Any]:
        """
        Transcribes audio bytes to text in Telugu or English.
        Requires configured real external STT provider (Sarvam AI or OpenAI).
        Never fabricates user speech or confidence scores.
        """
        lang = language.lower().strip()
        self.validate_input(filename, content_type, file_bytes, lang)

        # Determine container format strictly from binary magic header
        detected_mime = detect_container_mime(file_bytes)
        clean_mime = (content_type or "").split(";")[0].strip().lower()

        # If MIME is missing, ambiguous, or generic binary, prefer detected container
        if not clean_mime or clean_mime in {"application/octet-stream", "binary/octet-stream"}:
            clean_mime = detected_mime or ""

        if not clean_mime or not detected_mime:
            raise VoiceServiceException(
                code="INVALID_AUDIO_FORMAT",
                message="Cannot determine valid audio format from binary header. Please provide a supported audio recording (WAV, WebM, MP3, OGG).",
                status_code=400,
                details=[{"field": "file", "issue": "Unrecognized or missing audio header"}]
            )

        # Map clean MIME to proper extension for forwarding to external STT provider
        mime_to_ext = {
            "audio/webm": ".webm",
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
            "audio/wave": ".wav",
            "audio/ogg": ".ogg",
            "application/ogg": ".ogg",
            "audio/mpeg": ".mp3",
            "audio/mp3": ".mp3",
            "audio/mp4": ".m4a",
            "audio/m4a": ".m4a",
            "audio/x-m4a": ".m4a",
            "audio/flac": ".flac",
            "audio/x-flac": ".flac",
            "audio/aac": ".aac",
        }
        send_ext = mime_to_ext.get(detected_mime, os.path.splitext(filename or "")[1].lower() or ".wav")
        send_filename = filename if (filename and filename.endswith(send_ext)) else f"audio{send_ext}"

        # 1. External Provider: Sarvam AI
        if self.sarvam_key:
            try:
                import httpx
                target_lang_code = "te-IN" if lang == "te" else "en-IN"
                async with httpx.AsyncClient(timeout=30.0) as client:
                    files = {"file": (send_filename, file_bytes, clean_mime)}
                    data = {"model": self.sarvam_model, "language_code": target_lang_code}
                    headers = {"api-subscription-key": self.sarvam_key}
                    response = await client.post("https://api.sarvam.ai/speech-to-text", files=files, data=data, headers=headers)
                    if response.status_code == 200:
                        res_json = response.json()
                        transcript = res_json.get("transcript", "")
                        if transcript:
                            raw_conf = res_json.get("confidence")
                            confidence = None
                            if raw_conf is not None:
                                try:
                                    confidence = round(float(raw_conf), 2)
                                except (ValueError, TypeError):
                                    confidence = None
                            elif "words" in res_json and isinstance(res_json["words"], list):
                                word_confs = [w.get("confidence") for w in res_json["words"] if isinstance(w, dict) and w.get("confidence") is not None]
                                if word_confs:
                                    try:
                                        confidence = round(float(sum(word_confs) / len(word_confs)), 2)
                                    except (ValueError, TypeError, ZeroDivisionError):
                                        confidence = None

                            return {
                                "transcribed_text": transcript,
                                "language": lang,
                                "confidence": confidence
                            }
                    elif response.status_code == 400:
                        err_msg = ""
                        try:
                            err_data = response.json()
                            if isinstance(err_data, dict):
                                err_msg = err_data.get("error", {}).get("message", "") or err_data.get("message", "")
                        except Exception:
                            err_msg = response.text[:200]
                        logger.error("Sarvam STT returned status 400: %s", err_msg or response.text[:200])
                        if "invalid file type" in err_msg.lower() or "not allowed" in err_msg.lower():
                            raise VoiceServiceException(
                                code="INVALID_AUDIO_FORMAT",
                                message=f"Speech provider rejected audio format: {err_msg}",
                                status_code=400,
                                details=[{"field": "file", "issue": err_msg}]
                            )
                        raise VoiceServiceException(
                            code="INVALID_AUDIO_REQUEST",
                            message=f"Speech transcription request was rejected: {err_msg or 'Bad Request'}",
                            status_code=400,
                            details=[{"field": "file", "issue": err_msg or "Provider rejected request format"}]
                        )
                    logger.error("Sarvam STT returned status %d: %s", response.status_code, response.text[:200])
            except VoiceServiceException:
                raise
            except Exception as e:
                logger.error("Sarvam STT request failed: %s", type(e).__name__)

        # 2. External Provider: OpenAI Whisper
        if self.openai_key:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=30.0) as client:
                    files = {"file": (filename or "audio.wav", file_bytes, clean_mime)}
                    data = {"model": "whisper-1", "language": lang}
                    headers = {"Authorization": f"Bearer {self.openai_key}"}
                    response = await client.post("https://api.openai.com/v1/audio/transcriptions", files=files, data=data, headers=headers)
                    if response.status_code == 200:
                        res_json = response.json()
                        transcript = res_json.get("text", "")
                        if transcript:
                            raw_conf = res_json.get("confidence")
                            confidence = None
                            if raw_conf is not None:
                                try:
                                    confidence = round(float(raw_conf), 2)
                                except (ValueError, TypeError):
                                    confidence = None

                            return {
                                "transcribed_text": transcript,
                                "language": lang,
                                "confidence": confidence
                            }
                    elif response.status_code == 400:
                        err_msg = ""
                        try:
                            err_data = response.json()
                            if isinstance(err_data, dict):
                                err_msg = err_data.get("error", {}).get("message", "") or err_data.get("message", "")
                        except Exception:
                            err_msg = response.text[:200]
                        logger.error("OpenAI Whisper STT returned status 400: %s", err_msg or response.text[:200])
                        raise VoiceServiceException(
                            code="INVALID_AUDIO_REQUEST",
                            message=f"Speech transcription request was rejected: {err_msg or 'Bad Request'}",
                            status_code=400,
                            details=[{"field": "file", "issue": err_msg or "Provider rejected request format"}]
                        )
                    logger.error("OpenAI Whisper STT returned status %d: %s", response.status_code, response.text[:200])
            except VoiceServiceException:
                raise
            except Exception as e:
                logger.error("OpenAI Whisper request failed: %s", type(e).__name__)

        # 3. No real provider configured or all providers failed
        # Explicitly return 503 Service Unavailable — NEVER invent user speech or fake confidence!
        logger.warning("Voice transcription requested but no STT provider is available or reachable.")
        raise VoiceServiceException(
            code="VOICE_PROVIDER_UNAVAILABLE",
            message="Speech transcription service is currently unavailable. No external STT provider is configured or reachable on the backend.",
            status_code=503,
            details=[{"issue": "Neither SARVAM_API_KEY nor OPENAI_API_KEY is configured or reachable on the server."}]
        )
