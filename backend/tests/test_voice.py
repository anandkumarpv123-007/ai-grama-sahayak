"""
Unit and Integration Tests for Voice Services and API Router (Member 3)
Verifies:
  - STT unavailable without API keys (assert 503)
  - No fabricated transcription or fake confidence (genuine score or None)
  - Strict audio magic bytes verification (fake audio rejected with 400)
  - TTS unavailable without providers (assert 503)
  - No fake audio chime response
  - No silent text truncation at 500/1000 characters
  - Safe chunking and concatenation of speech synthesis
  - Provider failure handling (assert 503)
  - 15 MB audio size enforcement (assert 413)
  - Audio format and header validation (assert 400)
  - Empty / corrupted audio (assert 400)
  - Empty text / text too long (assert 400)
  - Unsupported language handling (assert 422)
  - Router registration under prefix="/api" yields /api/voice/transcribe and /api/voice/speak
"""

import sys
import os
import unittest
import base64
import wave
import io
import json
from unittest.mock import patch, MagicMock

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from starlette.datastructures import UploadFile
from app.api.voice import router as voice_router, speak_voice, transcribe_voice, VoiceSpeakRequest, CHUNK_SIZE
from app.services.voice.synthesis import VoiceSynthesisService, chunk_text, combine_wav_base64_chunks
from app.services.voice.transcription import (
    VoiceTranscriptionService,
    VoiceServiceException,
    MAX_AUDIO_SIZE_BYTES,
    is_valid_audio_magic,
)


def run_sync(coro):
    """Drives coroutines synchronously without socket-bound event loops."""
    stack = [coro]
    res = None
    while stack:
        curr = stack[-1]
        try:
            val = curr.send(res)
            res = None
            if hasattr(val, "send"):
                stack.append(val)
        except StopIteration as e:
            stack.pop()
            res = e.value
    return res


def create_dummy_wav_bytes(duration_sec: float = 0.05) -> bytes:
    """Helper to create a small valid WAV file with standard RIFF header."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        num_samples = int(16000 * duration_sec)
        wf.writeframes(b"\x00\x00" * num_samples)
    return buf.getvalue()


class MockHttpxClient:
    """Mock for httpx.AsyncClient that drives async with and post without sockets."""

    def __init__(self, response_mock):
        self.response_mock = response_mock
        self.recorded_calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def post(self, url, **kwargs):
        self.recorded_calls.append({"url": url, **kwargs})
        return self.response_mock


class TestVoiceRegistration(unittest.TestCase):
    """Verify router registration matching Member 1 prefix="/api" convention."""

    def test_router_endpoints_with_api_prefix(self):
        test_app = FastAPI()
        test_app.include_router(voice_router, prefix="/api")

        registered_paths = list(test_app.openapi()["paths"].keys())
        self.assertIn("/api/voice/transcribe", registered_paths)
        self.assertIn("/api/voice/speak", registered_paths)


class TestVoiceTranscriptionValidation(unittest.TestCase):
    """Test validation and confidence handling in VoiceTranscriptionService."""

    def setUp(self):
        self.service = VoiceTranscriptionService()

    def test_transcribe_empty_file_error(self):
        with self.assertRaises(VoiceServiceException) as ctx:
            run_sync(self.service.transcribe("sample.wav", "audio/wav", b"", "en"))
        self.assertEqual(ctx.exception.code, "EMPTY_AUDIO_FILE")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_transcribe_corrupted_audio_error(self):
        with self.assertRaises(VoiceServiceException) as ctx:
            run_sync(self.service.transcribe("sample.wav", "audio/wav", b"too small", "en"))
        self.assertEqual(ctx.exception.code, "CORRUPTED_AUDIO_FILE")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_transcribe_invalid_audio_format_error(self):
        with self.assertRaises(VoiceServiceException) as ctx:
            run_sync(self.service.transcribe("document.txt", "text/plain", b"this is not audio data at all 1234567890", "en"))
        self.assertEqual(ctx.exception.code, "INVALID_AUDIO_FORMAT")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_transcribe_fake_audio_content_rejected(self):
        """Regression test: arbitrary text bytes with .wav or .mp3 extension MUST fail magic byte check."""
        fake_audio = b"THIS_IS_PLAIN_TEXT_NOT_A_VALID_AUDIO_HEADER_1234567890_FAKE_AUDIO_SAMPLE"
        with self.assertRaises(VoiceServiceException) as ctx:
            run_sync(self.service.transcribe("fake.wav", "audio/wav", fake_audio, "en"))
        self.assertEqual(ctx.exception.code, "INVALID_AUDIO_FORMAT")
        self.assertEqual(ctx.exception.status_code, 400)

        # Direct check on is_valid_audio_magic helper
        self.assertFalse(is_valid_audio_magic(fake_audio, ".wav"))
        self.assertFalse(is_valid_audio_magic(fake_audio, ".mp3"))
        self.assertFalse(is_valid_audio_magic(fake_audio, ".ogg"))

    def test_transcribe_unsupported_language_error(self):
        wav = create_dummy_wav_bytes()
        with self.assertRaises(VoiceServiceException) as ctx:
            run_sync(self.service.transcribe("sample.wav", "audio/wav", wav, "fr"))
        self.assertEqual(ctx.exception.code, "UNSUPPORTED_LANGUAGE")
        self.assertEqual(ctx.exception.status_code, 422)

    def test_transcribe_oversized_audio_error(self):
        oversized = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * (MAX_AUDIO_SIZE_BYTES + 100)
        with self.assertRaises(VoiceServiceException) as ctx:
            run_sync(self.service.transcribe("sample.wav", "audio/wav", oversized, "en"))
        self.assertEqual(ctx.exception.code, "PAYLOAD_TOO_LARGE")
        self.assertEqual(ctx.exception.status_code, 413)

    def test_transcribe_no_fake_transcript_without_keys(self):
        """CRITICAL: Without provider keys, service MUST raise 503, never invent words."""
        service = VoiceTranscriptionService()
        service.sarvam_key = None
        service.openai_key = None
        wav = create_dummy_wav_bytes()

        with self.assertRaises(VoiceServiceException) as ctx:
            run_sync(service.transcribe("sample.wav", "audio/wav", wav, "en"))

        self.assertEqual(ctx.exception.status_code, 503)
        self.assertEqual(ctx.exception.code, "VOICE_PROVIDER_UNAVAILABLE")

    def test_transcribe_genuine_confidence_extracted(self):
        """Verify genuine provider confidence is passed through and not hardcoded."""
        service = VoiceTranscriptionService()
        service.sarvam_key = "test_key"
        service.openai_key = None
        wav = create_dummy_wav_bytes()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "transcript": "రైతు భరోసా పథకం ఎప్పుడు అందుబాటులోకి వస్తుంది?",
            "confidence": 0.87
        }
        mock_client = MockHttpxClient(mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            res = run_sync(service.transcribe("audio.wav", "audio/wav", wav, "te"))
            self.assertEqual(res["transcribed_text"], "రైతు భరోసా పథకం ఎప్పుడు అందుబాటులోకి వస్తుంది?")
            self.assertEqual(res["language"], "te")
            self.assertEqual(res["confidence"], 0.87)

    def test_transcribe_provider_without_confidence_returns_none(self):
        """Verify that when provider does not report confidence, it is None, never fabricated."""
        service = VoiceTranscriptionService()
        service.sarvam_key = None
        service.openai_key = "test_key"
        wav = create_dummy_wav_bytes()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "text": "How do I apply for Rythu Bharosa?"
        }
        mock_client = MockHttpxClient(mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            res = run_sync(service.transcribe("audio.wav", "audio/wav", wav, "en"))
            self.assertEqual(res["transcribed_text"], "How do I apply for Rythu Bharosa?")
            self.assertIsNone(res["confidence"])


class TestVoiceSynthesisValidation(unittest.TestCase):
    """Test validation and chunking in VoiceSynthesisService."""

    def setUp(self):
        self.service = VoiceSynthesisService()

    def test_speak_empty_text_error(self):
        with self.assertRaises(VoiceServiceException) as ctx:
            run_sync(self.service.speak("   ", "en"))
        self.assertEqual(ctx.exception.code, "EMPTY_TEXT")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_speak_unsupported_language_error(self):
        with self.assertRaises(VoiceServiceException) as ctx:
            run_sync(self.service.speak("Hello", "es"))
        self.assertEqual(ctx.exception.code, "UNSUPPORTED_LANGUAGE")
        self.assertEqual(ctx.exception.status_code, 422)

    def test_speak_text_too_long_error(self):
        huge_text = "A" * 4500
        with self.assertRaises(VoiceServiceException) as ctx:
            run_sync(self.service.speak(huge_text, "en"))
        self.assertEqual(ctx.exception.code, "TEXT_TOO_LONG")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_speak_no_fake_audio_without_keys(self):
        """CRITICAL: Without provider keys, service MUST raise 503, never return a chime."""
        service = VoiceSynthesisService()
        service.sarvam_key = None
        service.openai_key = None

        with self.assertRaises(VoiceServiceException) as ctx:
            run_sync(service.speak("Government guidance text", "en"))

        self.assertEqual(ctx.exception.status_code, 503)
        self.assertEqual(ctx.exception.code, "VOICE_PROVIDER_UNAVAILABLE")

    def test_chunk_text_preserves_all_content(self):
        """Verify chunk_text cleanly segments long sentences without omitting any words."""
        long_text = (
            "The Government of Andhra Pradesh has implemented the YSR Rythu Bharosa scheme to provide financial "
            "assistance to farmer families. Eligible farmers receive financial assistance of 13,500 rupees per year "
            "for cultivation and input requirements. In addition, free crop insurance and borewell drilling assistance "
            "are provided through Rythu Bharosa Kendras (RBKs) established in each village. For grievances or queries, "
            "citizens can contact the local Grama Sachivalayam Agriculture Assistant or visit the official portal."
        )
        chunks = chunk_text(long_text, max_chars=120)
        self.assertTrue(len(chunks) > 1)
        for c in chunks:
            self.assertLessEqual(len(c), 120)
        # Verify all original words are preserved in exact sequence
        original_words = long_text.split()
        chunked_words = " ".join(chunks).split()
        self.assertEqual(original_words, chunked_words)

    def test_speak_does_not_silently_truncate_text(self):
        """Verify that OpenAI TTS receives the full text (> 1000 chars) without silent slicing."""
        service = VoiceSynthesisService()
        service.sarvam_key = None
        service.openai_key = "test_key"
        long_text = "This is a detailed explanation of village welfare services. " * 25  # ~1500 chars

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"RIFF" + b"\x00" * 100
        mock_client = MockHttpxClient(mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            res = run_sync(service.speak(long_text, "en"))
            self.assertEqual(len(mock_client.recorded_calls), 1)
            sent_payload = mock_client.recorded_calls[0].get("json", {})
            self.assertEqual(sent_payload.get("input"), long_text)
            self.assertEqual(len(sent_payload.get("input")), len(long_text))

    def test_speak_sarvam_chunks_long_text_without_omission(self):
        """Verify that Sarvam TTS chunks text safely without dropping any words."""
        service = VoiceSynthesisService()
        service.sarvam_key = "test_key"
        service.openai_key = None
        long_text = "ఆంధ్రప్రదేశ్ ప్రభుత్వం అమలు చేస్తున్న సంక్షేమ పథకాలు చాలా ఉన్నాయి. " * 15  # ~1000 chars

        dummy_wav = create_dummy_wav_bytes()
        dummy_b64 = base64.b64encode(dummy_wav).decode("utf-8")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"audios": [dummy_b64, dummy_b64]}
        mock_client = MockHttpxClient(mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            res = run_sync(service.speak(long_text, "te"))
            self.assertEqual(len(mock_client.recorded_calls), 1)
            sent_payload = mock_client.recorded_calls[0].get("json", {})
            inputs = sent_payload.get("inputs", [])
            self.assertTrue(len(inputs) > 1)
            for chunk in inputs:
                self.assertLessEqual(len(chunk), 500)
            # Verify Telugu words preserved
            self.assertEqual(long_text.split(), " ".join(inputs).split())


class TestVoiceRouterEndpoints(unittest.TestCase):
    """Test router endpoints directly."""

    def test_speak_endpoint_without_providers_returns_503(self):
        req = VoiceSpeakRequest(text="Welfare scheme guidance", language="en")
        with patch.object(VoiceSynthesisService, "speak", side_effect=VoiceServiceException(
            code="VOICE_PROVIDER_UNAVAILABLE",
            message="No external TTS provider configured",
            status_code=503
        )):
            res = run_sync(speak_voice(req))
            self.assertEqual(res.status_code, 503)
            body = json.loads(res.body.decode())
            self.assertEqual(body["error"]["code"], "VOICE_PROVIDER_UNAVAILABLE")

    def test_speak_endpoint_empty_text_returns_400(self):
        req = VoiceSpeakRequest(text="   ", language="en")
        res = run_sync(speak_voice(req))
        self.assertEqual(res.status_code, 400)
        body = json.loads(res.body.decode())
        self.assertEqual(body["error"]["code"], "EMPTY_TEXT")

    def test_speak_endpoint_unsupported_lang_returns_422(self):
        req = VoiceSpeakRequest(text="Bonjour", language="fr")
        res = run_sync(speak_voice(req))
        self.assertEqual(res.status_code, 422)
        body = json.loads(res.body.decode())
        self.assertEqual(body["error"]["code"], "UNSUPPORTED_LANGUAGE")

    def test_speak_endpoint_success_format_with_mock_provider(self):
        req = VoiceSpeakRequest(text="Hello citizen", language="en")
        dummy_audio = base64.b64encode(b"RIFF_AUDIO_DATA").decode("utf-8")
        mock_result = {
            "audio_base64": dummy_audio,
            "mime_type": "audio/wav",
            "language": "en"
        }
        with patch.object(VoiceSynthesisService, "speak", return_value=mock_result):
            res = run_sync(speak_voice(req))
            self.assertEqual(res["language"], "en")
            self.assertEqual(res["mime_type"], "audio/wav")
            self.assertEqual(res["audio_base64"], dummy_audio)

    def test_transcribe_endpoint_without_providers_returns_503(self):
        wav = create_dummy_wav_bytes()
        upload = UploadFile(io.BytesIO(wav), filename="test.wav", headers={"content-type": "audio/wav"})
        with patch.object(VoiceTranscriptionService, "transcribe", side_effect=VoiceServiceException(
            code="VOICE_PROVIDER_UNAVAILABLE",
            message="No external STT provider configured",
            status_code=503
        )):
            res = run_sync(transcribe_voice(file=upload, language="en"))
            self.assertEqual(res.status_code, 503)
            body = json.loads(res.body.decode())
            self.assertEqual(body["error"]["code"], "VOICE_PROVIDER_UNAVAILABLE")

    def test_transcribe_endpoint_empty_file_returns_400(self):
        upload = UploadFile(io.BytesIO(b""), filename="test.wav", headers={"content-type": "audio/wav"})
        res = run_sync(transcribe_voice(file=upload, language="en"))
        self.assertEqual(res.status_code, 400)
        body = json.loads(res.body.decode())
        self.assertEqual(body["error"]["code"], "EMPTY_AUDIO_FILE")

    def test_transcribe_endpoint_invalid_format_returns_400(self):
        upload = UploadFile(io.BytesIO(b"this is plain text not audio"), filename="test.txt", headers={"content-type": "text/plain"})
        res = run_sync(transcribe_voice(file=upload, language="en"))
        self.assertEqual(res.status_code, 400)
        body = json.loads(res.body.decode())
        self.assertEqual(body["error"]["code"], "INVALID_AUDIO_FORMAT")

    def test_transcribe_endpoint_unsupported_lang_returns_422(self):
        wav = create_dummy_wav_bytes()
        upload = UploadFile(io.BytesIO(wav), filename="test.wav", headers={"content-type": "audio/wav"})
        res = run_sync(transcribe_voice(file=upload, language="de"))
        self.assertEqual(res.status_code, 422)
        body = json.loads(res.body.decode())
        self.assertEqual(body["error"]["code"], "UNSUPPORTED_LANGUAGE")

    def test_transcribe_endpoint_success_format_with_mock_provider(self):
        wav = create_dummy_wav_bytes()
        upload = UploadFile(io.BytesIO(wav), filename="test.wav", headers={"content-type": "audio/wav"})
        mock_result = {
            "transcribed_text": "What schemes are available for farmers?",
            "language": "en",
            "confidence": 0.94
        }
        with patch.object(VoiceTranscriptionService, "transcribe", return_value=mock_result):
            res = run_sync(transcribe_voice(file=upload, language="en"))
            self.assertEqual(res["transcribed_text"], "What schemes are available for farmers?")
            self.assertEqual(res["language"], "en")
            self.assertEqual(res["confidence"], 0.94)

    def test_transcribe_endpoint_success_with_null_confidence(self):
        """Verify endpoint correctly returns confidence: None when provider does not report it."""
        wav = create_dummy_wav_bytes()
        upload = UploadFile(io.BytesIO(wav), filename="test.wav", headers={"content-type": "audio/wav"})
        mock_result = {
            "transcribed_text": "What schemes are available for farmers?",
            "language": "en",
            "confidence": None
        }
        with patch.object(VoiceTranscriptionService, "transcribe", return_value=mock_result):
            res = run_sync(transcribe_voice(file=upload, language="en"))
            self.assertEqual(res["transcribed_text"], "What schemes are available for farmers?")
            self.assertEqual(res["language"], "en")
            self.assertIsNone(res["confidence"])

    def test_transcribe_endpoint_oversized_audio_returns_413(self):
        """Verify incremental streaming read rejects > 15 MB audio with 413."""
        oversized_stream = io.BytesIO(b"\x00" * (MAX_AUDIO_SIZE_BYTES + 1024))
        upload = UploadFile(oversized_stream, filename="large.wav", headers={"content-type": "audio/wav"})
        res = run_sync(transcribe_voice(file=upload, language="en"))
        self.assertEqual(res.status_code, 413)
        body = json.loads(res.body.decode())
        self.assertEqual(body["error"]["code"], "PAYLOAD_TOO_LARGE")


if __name__ == "__main__":
    unittest.main()
