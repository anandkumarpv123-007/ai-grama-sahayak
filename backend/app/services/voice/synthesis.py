"""
Voice Synthesis Service for AI Grama Sahayak
Author: Member 3
Contract: POST /api/voice/speak (JSON: text, language)
Returns: { "audio_base64": str, "mime_type": str, "language": str }
"""

import os
import io
import re
import time
import wave
import base64
import logging
from typing import Dict, Any, List, Optional
from app.core.config import settings
from .transcription import VoiceServiceException, SUPPORTED_LANGUAGES

logger = logging.getLogger("voice.synthesis")

MAX_TEXT_LENGTH = 4000
OVERALL_SYNTHESIS_DEADLINE_SEC = 45.0


def chunk_text(text: str, max_chars: int = 500) -> List[str]:
    """
    Safely splits text into chunks of at most max_chars without dropping any words or characters.
    Splits on sentence boundaries (. ? ! । \n) or whitespace.
    Guarantees 100% of the input text is preserved without silent omission.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []
    # Split on sentence boundaries while keeping the terminator
    sentences = re.split(r'(?<=[.?!।\n])\s+', text)
    current_chunk = ""

    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(s) > max_chars:
            # Long sentence: split on words
            words = s.split()
            for w in words:
                if len(w) > max_chars:
                    # Long unbroken token: slice without losing any characters
                    if current_chunk:
                        chunks.append(current_chunk)
                        current_chunk = ""
                    for i in range(0, len(w), max_chars):
                        sub = w[i:i + max_chars]
                        if len(sub) == max_chars:
                            chunks.append(sub)
                        else:
                            current_chunk = sub
                elif not current_chunk:
                    current_chunk = w
                elif len(current_chunk) + len(w) + 1 <= max_chars:
                    current_chunk += " " + w
                else:
                    chunks.append(current_chunk)
                    current_chunk = w
        else:
            if not current_chunk:
                current_chunk = s
            elif len(current_chunk) + len(s) + 1 <= max_chars:
                current_chunk += " " + s
            else:
                chunks.append(current_chunk)
                current_chunk = s

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def combine_wav_base64_chunks(b64_chunks: List[str]) -> str:
    """
    Combines multiple base64-encoded WAV audio buffers into a single valid WAV base64 string.
    Strict all-or-nothing validation:
    - Rejects malformed base64.
    - Rejects invalid WAV structure.
    - Rejects mismatched audio parameters (channels, sample width, framerate).
    - Rejects 0-frame / empty audio.
    - Never silently omits or skips any chunk.
    Raises ValueError on any integrity violation.
    """
    if not b64_chunks:
        raise ValueError("No audio chunks provided for combination")

    pcm_data = bytearray()
    first_params = None

    for idx, b64 in enumerate(b64_chunks):
        if not b64 or not isinstance(b64, str):
            raise ValueError(f"Chunk {idx} is empty or not a valid string")

        try:
            raw = base64.b64decode(b64, validate=True)
        except Exception as e:
            raise ValueError(f"Chunk {idx} contains malformed base64 data: {e}")

        if len(raw) < 44 or not raw.startswith(b"RIFF"):
            raise ValueError(f"Chunk {idx} does not have a valid RIFF/WAVE header")

        try:
            with wave.open(io.BytesIO(raw), "rb") as wf:
                params = wf.getparams()
                nframes = wf.getnframes()
                if nframes <= 0:
                    raise ValueError(f"Chunk {idx} contains 0 audio frames")

                if first_params is None:
                    first_params = params
                else:
                    if (params.nchannels != first_params.nchannels or
                        params.sampwidth != first_params.sampwidth or
                        params.framerate != first_params.framerate):
                        raise ValueError(
                            f"Chunk {idx} audio parameters (channels={params.nchannels}, "
                            f"width={params.sampwidth}, rate={params.framerate}) do not match "
                            f"first chunk (channels={first_params.nchannels}, "
                            f"width={first_params.sampwidth}, rate={first_params.framerate})"
                        )

                frames = wf.readframes(nframes)
                if len(frames) == 0:
                    raise ValueError(f"Chunk {idx} returned 0 PCM bytes")
                pcm_data.extend(frames)
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Chunk {idx} is not a valid WAV file: {e}")

    out_buf = io.BytesIO()
    with wave.open(out_buf, "wb") as out_wf:
        out_wf.setparams(first_params)
        out_wf.writeframes(bytes(pcm_data))

    return base64.b64encode(out_buf.getvalue()).decode("utf-8")


class VoiceSynthesisService:
    """Handles text validation and real TTS speech synthesis for Telugu and English."""

    def __init__(self, sarvam_key: Optional[str] = None, openai_key: Optional[str] = None):
        self.sarvam_key = sarvam_key or os.getenv("SARVAM_API_KEY") or settings.SARVAM_API_KEY
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY
        self.sarvam_model = os.getenv("SARVAM_TTS_MODEL") or settings.SARVAM_TTS_MODEL
        self.sarvam_speaker = os.getenv("SARVAM_TTS_SPEAKER") or settings.SARVAM_TTS_SPEAKER

    def validate_input(self, text: str, language: str) -> None:
        if not language or language.lower().strip() not in SUPPORTED_LANGUAGES:
            raise VoiceServiceException(
                code="UNSUPPORTED_LANGUAGE",
                message=f"Unsupported language code '{language}'. Supported languages are: 'te' (Telugu) and 'en' (English).",
                status_code=422,
                details=[{"field": "language", "issue": "Must be 'en' or 'te'"}]
            )

        if not text or not text.strip():
            raise VoiceServiceException(
                code="EMPTY_TEXT",
                message="Text to synthesize cannot be empty. Please provide text for speech generation.",
                status_code=400,
                details=[{"field": "text", "issue": "Text must not be empty or whitespace"}]
            )

        if len(text) > MAX_TEXT_LENGTH:
            raise VoiceServiceException(
                code="TEXT_TOO_LONG",
                message=f"Text length ({len(text)} characters) exceeds maximum limit of {MAX_TEXT_LENGTH} characters.",
                status_code=400,
                details=[{"field": "text", "issue": f"Exceeds {MAX_TEXT_LENGTH} characters"}]
            )

    async def speak(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Synthesizes text to speech in Telugu or English.
        Requires configured real external TTS provider (Sarvam AI Bulbul or OpenAI TTS).
        Never returns fake audio chimes or synthetic filler as spoken output.
        Never silently truncates or omits text.
        """
        lang = language.lower().strip()
        self.validate_input(text, lang)

        start_time = time.monotonic()
        deadline = start_time + OVERALL_SYNTHESIS_DEADLINE_SEC
        deadline_exceeded = False

        # 1. External Provider: Sarvam AI (Native support for Telugu & Indian English)
        if self.sarvam_key:
            try:
                import httpx
                target_lang_code = "te-IN" if lang == "te" else "en-IN"
                chunks = chunk_text(text, max_chars=500)
                if not chunks:
                    chunks = [text]

                # Sarvam AI Bulbul:v3 API enforces at most 3 items in the 'inputs' list per request.
                # Batch chunks in groups of at most 3 and combine returned audio segments.
                SARVAM_MAX_BATCH_SIZE = 3
                all_audios = []
                batch_failed = False

                async with httpx.AsyncClient() as client:
                    headers = {
                        "api-subscription-key": self.sarvam_key,
                        "Content-Type": "application/json"
                    }
                    for i in range(0, len(chunks), SARVAM_MAX_BATCH_SIZE):
                        remaining_time = deadline - time.monotonic()
                        if remaining_time <= 1.0:
                            logger.error("Overall synthesis deadline exceeded before batch (remaining: %.2fs)", remaining_time)
                            deadline_exceeded = True
                            batch_failed = True
                            break

                        batch = chunks[i : i + SARVAM_MAX_BATCH_SIZE]
                        payload = {
                            "inputs": batch,
                            "target_language_code": target_lang_code,
                            "speaker": self.sarvam_speaker,
                            "pitch": 0,
                            "pace": 1.0,
                            "speech_sample_rate": 8000,
                            "enable_preprocessing": True,
                            "model": self.sarvam_model
                        }
                        req_timeout = min(remaining_time, 30.0)
                        try:
                            response = await client.post(
                                "https://api.sarvam.ai/text-to-speech",
                                json=payload,
                                headers=headers,
                                timeout=req_timeout
                            )
                        except httpx.TimeoutException:
                            logger.error("Sarvam TTS request timed out after %.2fs", req_timeout)
                            deadline_exceeded = True
                            batch_failed = True
                            break

                        if response.status_code == 200:
                            res_json = response.json()
                            audios = res_json.get("audios", [])
                            # Strict count validation: exact audio count matching requested batch size
                            if audios and len(audios) == len(batch) and all(bool(a) for a in audios):
                                all_audios.extend(audios)
                            else:
                                logger.error(
                                    "Sarvam TTS audio count mismatch: requested %d, received %d",
                                    len(batch), len(audios) if audios else 0
                                )
                                batch_failed = True
                                break
                        else:
                            logger.error("Sarvam TTS returned status %d: %s", response.status_code, response.text[:200])
                            batch_failed = True
                            break

                # Strict all-or-nothing check: total audios must match total chunks exactly
                if not batch_failed and len(all_audios) == len(chunks):
                    try:
                        combined_audio = combine_wav_base64_chunks(all_audios)
                        if combined_audio:
                            return {
                                "audio_base64": combined_audio,
                                "mime_type": "audio/wav",
                                "language": lang
                            }
                    except ValueError as ve:
                        logger.error("Strict audio integrity validation failed: %s", ve)
                        batch_failed = True
            except Exception as e:
                logger.error("Sarvam TTS request failed: %s", type(e).__name__)

        # 2. External Provider: OpenAI TTS
        if self.openai_key:
            remaining_time = deadline - time.monotonic()
            if remaining_time <= 2.0:
                deadline_exceeded = True
            else:
                try:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        payload = {
                            "model": "tts-1",
                            "input": text,
                            "voice": "nova"
                        }
                        headers = {
                            "Authorization": f"Bearer {self.openai_key}",
                            "Content-Type": "application/json"
                        }
                        req_timeout = min(remaining_time, 30.0)
                        try:
                            response = await client.post(
                                "https://api.openai.com/v1/audio/speech",
                                json=payload,
                                headers=headers,
                                timeout=req_timeout
                            )
                        except httpx.TimeoutException:
                            logger.error("OpenAI TTS timed out within remaining deadline")
                            deadline_exceeded = True
                            response = None

                        if response and response.status_code == 200:
                            audio_b64 = base64.b64encode(response.content).decode("utf-8")
                            return {
                                "audio_base64": audio_b64,
                                "mime_type": "audio/mpeg",
                                "language": lang
                            }
                        if response:
                            logger.error("OpenAI TTS returned status %d: %s", response.status_code, response.text[:200])
                except Exception as e:
                    logger.error("OpenAI TTS request failed: %s", type(e).__name__)

        # 3. Check if overall deadline was exceeded
        elapsed = time.monotonic() - start_time
        if deadline_exceeded or elapsed >= OVERALL_SYNTHESIS_DEADLINE_SEC:
            logger.error("Voice synthesis exceeded overall deadline of %.1fs (elapsed: %.1fs)", OVERALL_SYNTHESIS_DEADLINE_SEC, elapsed)
            raise VoiceServiceException(
                code="VOICE_SYNTHESIS_TIMEOUT",
                message=f"Voice synthesis exceeded the overall deadline of {OVERALL_SYNTHESIS_DEADLINE_SEC} seconds.",
                status_code=504,
                details=[{"issue": f"Synthesis timed out after {elapsed:.1f}s"}]
            )

        # 4. No real provider configured or all providers failed
        # Explicitly return 503 Service Unavailable — NEVER return chimes or fake audio!
        logger.warning("Voice synthesis requested but no TTS provider is available or reachable.")
        raise VoiceServiceException(
            code="VOICE_PROVIDER_UNAVAILABLE",
            message="Text-to-speech service is currently unavailable. No external TTS provider is configured or reachable on the backend.",
            status_code=503,
            details=[{"issue": "Neither SARVAM_API_KEY nor OPENAI_API_KEY is configured or reachable on the server."}]
        )
