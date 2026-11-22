"""
Voice Synthesis Service for AI Grama Sahayak
Author: Member 3
Contract: POST /api/voice/speak (JSON: text, language)
Returns: { "audio_base64": str, "mime_type": str, "language": str }
"""

import os
import io
import re
import wave
import base64
import logging
from typing import Dict, Any, List, Optional
from .transcription import VoiceServiceException, SUPPORTED_LANGUAGES

logger = logging.getLogger("voice.synthesis")

MAX_TEXT_LENGTH = 4000


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
    """
    if not b64_chunks:
        return ""
    if len(b64_chunks) == 1:
        return b64_chunks[0]

    pcm_data = bytearray()
    params = None
    for b64 in b64_chunks:
        try:
            raw = base64.b64decode(b64)
            if len(raw) < 44:
                continue
            with wave.open(io.BytesIO(raw), "rb") as wf:
                if params is None:
                    params = wf.getparams()
                pcm_data.extend(wf.readframes(wf.getnframes()))
        except Exception:
            try:
                raw = base64.b64decode(b64)
                if len(raw) > 44:
                    pcm_data.extend(raw[44:])
            except Exception:
                pass

    if not pcm_data:
        return b64_chunks[0]

    out_buf = io.BytesIO()
    with wave.open(out_buf, "wb") as out_wf:
        if params:
            out_wf.setparams(params)
        else:
            out_wf.setnchannels(1)
            out_wf.setsampwidth(2)
            out_wf.setframerate(8000)
        out_wf.writeframes(bytes(pcm_data))

    return base64.b64encode(out_buf.getvalue()).decode("utf-8")


class VoiceSynthesisService:
    """Handles text validation and real TTS speech synthesis for Telugu and English."""

    def __init__(self):
        self.sarvam_key = os.getenv("SARVAM_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

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

        # 1. External Provider: Sarvam AI (Native support for Telugu & Indian English)
        if self.sarvam_key:
            try:
                import httpx
                target_lang_code = "te-IN" if lang == "te" else "en-IN"
                chunks = chunk_text(text, max_chars=500)
                if not chunks:
                    chunks = [text]

                async with httpx.AsyncClient(timeout=45.0) as client:
                    payload = {
                        "inputs": chunks,
                        "target_language_code": target_lang_code,
                        "speaker": "meera",
                        "pitch": 0,
                        "pace": 1.0,
                        "speech_sample_rate": 8000,
                        "enable_preprocessing": True,
                        "model": "bulbul:v1"
                    }
                    headers = {
                        "api-subscription-key": self.sarvam_key,
                        "Content-Type": "application/json"
                    }
                    response = await client.post("https://api.sarvam.ai/text-to-speech", json=payload, headers=headers)
                    if response.status_code == 200:
                        res_json = response.json()
                        audios = res_json.get("audios", [])
                        if audios and len(audios) > 0:
                            combined_audio = combine_wav_base64_chunks(audios)
                            return {
                                "audio_base64": combined_audio,
                                "mime_type": "audio/wav",
                                "language": lang
                            }
                    logger.error("Sarvam TTS returned status %d: %s", response.status_code, response.text[:200])
            except Exception as e:
                logger.error("Sarvam TTS request failed: %s", type(e).__name__)

        # 2. External Provider: OpenAI TTS
        if self.openai_key:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=45.0) as client:
                    payload = {
                        "model": "tts-1",
                        "input": text,
                        "voice": "nova"
                    }
                    headers = {
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json"
                    }
                    response = await client.post("https://api.openai.com/v1/audio/speech", json=payload, headers=headers)
                    if response.status_code == 200:
                        audio_b64 = base64.b64encode(response.content).decode("utf-8")
                        return {
                            "audio_base64": audio_b64,
                            "mime_type": "audio/mpeg",
                            "language": lang
                        }
                    logger.error("OpenAI TTS returned status %d: %s", response.status_code, response.text[:200])
            except Exception as e:
                logger.error("OpenAI TTS request failed: %s", type(e).__name__)

        # 3. No real provider configured or all providers failed
        # Explicitly return 503 Service Unavailable — NEVER return chimes or fake audio!
        logger.warning("Voice synthesis requested but no TTS provider is available or reachable.")
        raise VoiceServiceException(
            code="VOICE_PROVIDER_UNAVAILABLE",
            message="Text-to-speech service is currently unavailable. No external TTS provider is configured or reachable on the backend.",
            status_code=503,
            details=[{"issue": "Neither SARVAM_API_KEY nor OPENAI_API_KEY is configured or reachable on the server."}]
        )
