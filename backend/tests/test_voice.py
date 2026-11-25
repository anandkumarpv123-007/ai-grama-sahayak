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
import time
import asyncio
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
    detect_container_mime,
)


def run_sync(coro):
    """Drives coroutines synchronously using asyncio event loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


def create_dummy_wav_bytes(
    duration_sec: float = 0.05,
    channels: int = 1,
    sampwidth: int = 2,
    framerate: int = 16000,
) -> bytes:
    """Helper to create a small valid WAV file with standard RIFF header."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        num_samples = int(framerate * duration_sec)
        wf.writeframes(b"\x00" * (channels * sampwidth * num_samples))
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

    def test_transcribe_normalizes_parameterized_webm_mime(self):
        """Verify audio/webm;codecs=opus is normalized to audio/webm before forwarding to Sarvam."""
        service = VoiceTranscriptionService()
        service.sarvam_key = "test_key"
        service.openai_key = None
        dummy_webm = b"\x1a\x45\xdf\xa3" + b"\x00" * 40

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "transcript": "గ్రామ పంచాయతీ సేవలు",
            "confidence": 0.92
        }
        mock_client = MockHttpxClient(mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            res = run_sync(service.transcribe("recording.webm", "audio/webm;codecs=opus", dummy_webm, "te"))
            self.assertEqual(res["transcribed_text"], "గ్రామ పంచాయతీ సేవలు")
            self.assertEqual(len(mock_client.recorded_calls), 1)
            file_tuple = mock_client.recorded_calls[0]["files"]["file"]
            self.assertEqual(file_tuple[0], "recording.webm")
            self.assertEqual(file_tuple[2], "audio/webm")

    def test_transcribe_normalizes_parameterized_ogg_mime(self):
        """Verify audio/ogg;codecs=opus is normalized to audio/ogg before forwarding to Sarvam."""
        service = VoiceTranscriptionService()
        service.sarvam_key = "test_key"
        service.openai_key = None
        dummy_ogg = b"OggS" + b"\x00" * 40

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "transcript": "hello grama sahayak",
            "confidence": 0.88
        }
        mock_client = MockHttpxClient(mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            res = run_sync(service.transcribe("recording.ogg", "audio/ogg;codecs=opus", dummy_ogg, "en"))
            self.assertEqual(res["transcribed_text"], "hello grama sahayak")
            self.assertEqual(len(mock_client.recorded_calls), 1)
            file_tuple = mock_client.recorded_calls[0]["files"]["file"]
            self.assertEqual(file_tuple[0], "recording.ogg")
            self.assertEqual(file_tuple[2], "audio/ogg")

    def test_transcribe_provider_format_error_maps_to_400(self):
        """Verify provider 400 with Invalid file type raises INVALID_AUDIO_FORMAT 400, not 503."""
        service = VoiceTranscriptionService()
        service.sarvam_key = "test_key"
        service.openai_key = None
        dummy_webm = b"\x1a\x45\xdf\xa3" + b"\x00" * 40

        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {
            "error": {"message": "Invalid file type: audio/unsupported. Only audio/webm allowed."}
        }
        mock_client = MockHttpxClient(mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with self.assertRaises(VoiceServiceException) as ctx:
                run_sync(service.transcribe("recording.webm", "audio/webm", dummy_webm, "te"))
            self.assertEqual(ctx.exception.status_code, 400)
            self.assertEqual(ctx.exception.code, "INVALID_AUDIO_FORMAT")

    def test_transcribe_provider_request_error_maps_to_400(self):
        """Verify generic provider 400 error raises INVALID_AUDIO_REQUEST 400, not 503."""
        service = VoiceTranscriptionService()
        service.sarvam_key = "test_key"
        service.openai_key = None
        dummy_webm = b"\x1a\x45\xdf\xa3" + b"\x00" * 40

        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {
            "error": {"message": "Invalid model parameter specified"}
        }
        mock_client = MockHttpxClient(mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with self.assertRaises(VoiceServiceException) as ctx:
                run_sync(service.transcribe("recording.webm", "audio/webm", dummy_webm, "te"))
            self.assertEqual(ctx.exception.status_code, 400)
            self.assertEqual(ctx.exception.code, "INVALID_AUDIO_REQUEST")

    def test_detect_container_mime_formats(self):
        """Verify detect_container_mime accurately identifies container types from magic bytes."""
        webm_data = b"\x1a\x45\xdf\xa3" + b"\x00" * 30
        wav_data = create_dummy_wav_bytes()
        ogg_data = b"OggS" + b"\x00" * 30
        mp3_data = b"ID3" + b"\x00" * 30
        flac_data = b"fLaC" + b"\x00" * 30
        mp4_data = b"\x00\x00\x00\x20ftypM4A " + b"\x00" * 20
        corrupt_data = b"NOT_AUDIO_FILE_DATA_1234567890"

        self.assertEqual(detect_container_mime(webm_data), "audio/webm")
        self.assertEqual(detect_container_mime(wav_data), "audio/wav")
        self.assertEqual(detect_container_mime(ogg_data), "audio/ogg")
        self.assertEqual(detect_container_mime(mp3_data), "audio/mpeg")
        self.assertEqual(detect_container_mime(flac_data), "audio/flac")
        self.assertEqual(detect_container_mime(mp4_data), "audio/mp4")
        self.assertIsNone(detect_container_mime(corrupt_data))
        self.assertIsNone(detect_container_mime(b""))

    def test_transcribe_detects_container_from_binary_when_mime_is_octet_stream(self):
        """Verify binary header detection prevents defaulting to WAV when octet-stream is supplied."""
        service = VoiceTranscriptionService()
        service.sarvam_key = "test_key"
        service.openai_key = None
        dummy_webm = b"\x1a\x45\xdf\xa3" + b"\x00" * 40

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "transcript": "ధృవీకరించబడిన ఆడియో",
            "confidence": 0.95
        }
        mock_client = MockHttpxClient(mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            res = run_sync(service.transcribe("audio.bin", "application/octet-stream", dummy_webm, "te"))
            self.assertEqual(res["transcribed_text"], "ధృవీకరించబడిన ఆడియో")
            self.assertEqual(len(mock_client.recorded_calls), 1)
            file_tuple = mock_client.recorded_calls[0]["files"]["file"]
            self.assertEqual(file_tuple[0], "audio.webm")
            self.assertEqual(file_tuple[2], "audio/webm")

    def test_transcribe_ambiguous_headerless_audio_rejected_400(self):
        """Verify non-audio bytes with application/octet-stream are rejected with 400 without assuming WAV."""
        service = VoiceTranscriptionService()
        service.sarvam_key = "test_key"
        service.openai_key = None
        fake_bytes = b"TEXT_NOT_AN_AUDIO_HEADER_123456789"

        with self.assertRaises(VoiceServiceException) as ctx:
            run_sync(service.transcribe("unknown.bin", "application/octet-stream", fake_bytes, "en"))
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.code, "INVALID_AUDIO_FORMAT")


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
        mock_resp.json.return_value = {"audios": [dummy_b64, dummy_b64, dummy_b64]}
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


class TestVoiceConfiguration(unittest.TestCase):
    """Verify centralized environment and settings loading."""

    def test_settings_voice_defaults(self):
        from app.core.config import Settings
        s = Settings()
        self.assertEqual(s.SARVAM_STT_MODEL, "saaras:v4")
        self.assertEqual(s.SARVAM_TTS_MODEL, "bulbul:v3")
        self.assertEqual(s.SARVAM_TTS_SPEAKER, "kavitha")

    def test_process_env_precedence(self):
        from app.core.config import Settings
        with patch.dict(os.environ, {
            "SARVAM_STT_MODEL": "test-stt-override",
            "SARVAM_TTS_MODEL": "test-tts-override",
            "SARVAM_TTS_SPEAKER": "test-speaker-override",
        }):
            s = Settings()
            self.assertEqual(s.SARVAM_STT_MODEL, "test-stt-override")
            self.assertEqual(s.SARVAM_TTS_MODEL, "test-tts-override")
            self.assertEqual(s.SARVAM_TTS_SPEAKER, "test-speaker-override")

    def test_missing_key_behavior_isolated(self):
        """Verify service raises 503 when explicitly initialized without keys."""
        wav = create_dummy_wav_bytes()
        service_stt = VoiceTranscriptionService(sarvam_key="", openai_key="")
        with self.assertRaises(VoiceServiceException) as ctx:
            run_sync(service_stt.transcribe("sample.wav", "audio/wav", wav, "en"))
        self.assertEqual(ctx.exception.status_code, 503)
        self.assertEqual(ctx.exception.code, "VOICE_PROVIDER_UNAVAILABLE")

        service_tts = VoiceSynthesisService(sarvam_key="", openai_key="")
        with self.assertRaises(VoiceServiceException) as ctx:
            run_sync(service_tts.speak("Test text", "en"))
        self.assertEqual(ctx.exception.status_code, 503)
        self.assertEqual(ctx.exception.code, "VOICE_PROVIDER_UNAVAILABLE")


class TestSarvamModelCompatibility(unittest.TestCase):
    """Verify current Sarvam model parameters and provider failure modes."""

    def test_transcribe_sarvam_uses_saaras_v4(self):
        service = VoiceTranscriptionService(sarvam_key="mock_key", openai_key=None)
        wav = create_dummy_wav_bytes()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "request_id": "test_req_123",
            "transcript": "రైతు భరోసా",
            "language_code": "te-IN"
        }
        mock_client = MockHttpxClient(mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            res = run_sync(service.transcribe("sample.wav", "audio/wav", wav, "te"))
            self.assertEqual(res["transcribed_text"], "రైతు భరోసా")
            self.assertEqual(res["language"], "te")
            self.assertIsNone(res["confidence"])
            self.assertEqual(len(mock_client.recorded_calls), 1)
            call = mock_client.recorded_calls[0]
            self.assertEqual(call["data"]["model"], "saaras:v4")
            self.assertEqual(call["data"]["language_code"], "te-IN")
            self.assertEqual(call["headers"]["api-subscription-key"], "mock_key")

    def test_speak_sarvam_uses_bulbul_v3_and_kavitha(self):
        service = VoiceSynthesisService(sarvam_key="mock_key", openai_key=None)
        dummy_wav = create_dummy_wav_bytes()
        dummy_b64 = base64.b64encode(dummy_wav).decode("utf-8")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"audios": [dummy_b64]}
        mock_client = MockHttpxClient(mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            res = run_sync(service.speak("నమస్కారం", "te"))
            self.assertEqual(res["language"], "te")
            self.assertEqual(res["mime_type"], "audio/wav")
            self.assertEqual(len(mock_client.recorded_calls), 1)
            call = mock_client.recorded_calls[0]
            self.assertEqual(call["json"]["model"], "bulbul:v3")
            self.assertEqual(call["json"]["speaker"], "kavitha")
            self.assertEqual(call["json"]["target_language_code"], "te-IN")
            self.assertEqual(call["headers"]["api-subscription-key"], "mock_key")

    def test_transcribe_sarvam_http_errors_raise_503(self):
        service = VoiceTranscriptionService(sarvam_key="mock_key", openai_key=None)
        wav = create_dummy_wav_bytes()

        for status_code in [401, 429, 500, 502, 503]:
            mock_resp = MagicMock()
            mock_resp.status_code = status_code
            mock_resp.text = f"Error {status_code}"
            mock_client = MockHttpxClient(mock_resp)

            with patch("httpx.AsyncClient", return_value=mock_client):
                with self.assertRaises(VoiceServiceException) as ctx:
                    run_sync(service.transcribe("sample.wav", "audio/wav", wav, "en"))
                self.assertEqual(ctx.exception.status_code, 503)
                self.assertEqual(ctx.exception.code, "VOICE_PROVIDER_UNAVAILABLE")

    def test_speak_sarvam_http_errors_raise_503(self):
        service = VoiceSynthesisService(sarvam_key="mock_key", openai_key=None)

        for status_code in [400, 401, 429, 500, 503]:
            mock_resp = MagicMock()
            mock_resp.status_code = status_code
            mock_resp.text = f"Error {status_code}"
            mock_client = MockHttpxClient(mock_resp)

            with patch("httpx.AsyncClient", return_value=mock_client):
                with self.assertRaises(VoiceServiceException) as ctx:
                    run_sync(service.speak("Hello citizen", "en"))
                self.assertEqual(ctx.exception.status_code, 503)
                self.assertEqual(ctx.exception.code, "VOICE_PROVIDER_UNAVAILABLE")

    def test_speak_sarvam_empty_audios_raises_503(self):
        service = VoiceSynthesisService(sarvam_key="mock_key", openai_key=None)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"audios": []}
        mock_client = MockHttpxClient(mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with self.assertRaises(VoiceServiceException) as ctx:
                run_sync(service.speak("Hello citizen", "en"))
            self.assertEqual(ctx.exception.status_code, 503)
            self.assertEqual(ctx.exception.code, "VOICE_PROVIDER_UNAVAILABLE")

    def test_multi_chunk_wav_combining(self):
        chunk1 = create_dummy_wav_bytes(duration_sec=0.05)
        chunk2 = create_dummy_wav_bytes(duration_sec=0.05)
        b64_1 = base64.b64encode(chunk1).decode("utf-8")
        b64_2 = base64.b64encode(chunk2).decode("utf-8")

        combined_b64 = combine_wav_base64_chunks([b64_1, b64_2])
        combined_bytes = base64.b64decode(combined_b64)

        with wave.open(io.BytesIO(combined_bytes), "rb") as wf:
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)
            self.assertEqual(wf.getframerate(), 16000)
            self.assertGreater(wf.getnframes(), 1000)

    def test_combine_wav_strict_all_or_nothing_validation(self):
        """Strict all-or-nothing validation rejects any malformed, inconsistent, or empty chunk."""
        valid_chunk = base64.b64encode(create_dummy_wav_bytes(duration_sec=0.05, framerate=8000)).decode("utf-8")

        # 1. Empty list
        with self.assertRaises(ValueError):
            combine_wav_base64_chunks([])

        # 2. Malformed base64
        with self.assertRaises(ValueError):
            combine_wav_base64_chunks([valid_chunk, "not-valid-base64!"])

        # 3. Truncated header
        short_b64 = base64.b64encode(b"RIFFshort").decode("utf-8")
        with self.assertRaises(ValueError):
            combine_wav_base64_chunks([valid_chunk, short_b64])

        # 4. Inconsistent framerate
        diff_rate_chunk = base64.b64encode(create_dummy_wav_bytes(duration_sec=0.05, framerate=16000)).decode("utf-8")
        with self.assertRaises(ValueError):
            combine_wav_base64_chunks([valid_chunk, diff_rate_chunk])

        # 5. Inconsistent channels (stereo vs mono)
        stereo_chunk = base64.b64encode(create_dummy_wav_bytes(channels=2, duration_sec=0.05, framerate=8000)).decode("utf-8")
        with self.assertRaises(ValueError):
            combine_wav_base64_chunks([valid_chunk, stereo_chunk])

    def test_speak_overall_synthesis_deadline_enforced(self):
        """Synthesis aborts with 504 when overall deadline is exceeded across batches."""
        service = VoiceSynthesisService(sarvam_key="mock_key", openai_key=None)
        mock_client = MagicMock()

        async def mock_post(*args, **kwargs):
            import httpx
            raise httpx.TimeoutException("Client timed out")

        mock_client.__aenter__.return_value.post = mock_post

        with patch("httpx.AsyncClient", return_value=mock_client):
            with self.assertRaises(VoiceServiceException) as ctx:
                run_sync(service.speak("Test deadline", "en"))
            self.assertEqual(ctx.exception.status_code, 504)
            self.assertEqual(ctx.exception.code, "VOICE_SYNTHESIS_TIMEOUT")

    def test_speak_sarvam_rejects_missing_audio_chunks(self):
        """Sarvam provider rejects batch response if returned audio count does not match batch count."""
        service = VoiceSynthesisService(sarvam_key="mock_key", openai_key=None)
        dummy_wav = create_dummy_wav_bytes(framerate=8000)
        dummy_b64 = base64.b64encode(dummy_wav).decode("utf-8")

        two_chunk_text = "First long sentence for testing text chunking. Second long sentence for testing text chunking."
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"audios": [dummy_b64]}  # Only 1 audio returned for 2 chunks!
        mock_client = MockHttpxClient(mock_resp)

        with patch("app.services.voice.synthesis.chunk_text", return_value=["Sentence 1", "Sentence 2"]):
            with patch("httpx.AsyncClient", return_value=mock_client):
                with self.assertRaises(VoiceServiceException) as ctx:
                    run_sync(service.speak(two_chunk_text, "en"))
                self.assertEqual(ctx.exception.status_code, 503)

    def test_speak_sarvam_multi_batch_production_chunks(self):
        """Verifies multi-batch synthesis under production settings when chunks > 3."""
        service = VoiceSynthesisService(sarvam_key="mock_key", openai_key=None)
        dummy_wav = create_dummy_wav_bytes(framerate=8000)
        dummy_b64 = base64.b64encode(dummy_wav).decode("utf-8")

        mock_client = MagicMock()
        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            payload = kwargs.get("json", {})
            batch_inputs = payload.get("inputs", [])
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"audios": [dummy_b64] * len(batch_inputs)}
            return resp

        mock_client.__aenter__.return_value.post = mock_post

        four_chunks = ["Chunk 1", "Chunk 2", "Chunk 3", "Chunk 4"]
        with patch("app.services.voice.synthesis.chunk_text", return_value=four_chunks):
            with patch("httpx.AsyncClient", return_value=mock_client):
                res = run_sync(service.speak("Multi-batch text", "te"))
                self.assertIn("audio_base64", res)
                self.assertEqual(call_count, 2)

    def test_combine_wav_rejects_truncated_pcm_data(self):
        """Strict validation rejects truncated PCM data even when the RIFF header is valid."""
        raw_valid = create_dummy_wav_bytes(duration_sec=0.1, framerate=8000)
        self.assertGreater(len(raw_valid), 44)
        valid_b64 = base64.b64encode(raw_valid).decode("utf-8")

        # 1. Complete valid WAV works
        combined = combine_wav_base64_chunks([valid_b64])
        self.assertTrue(bool(combined))

        # 2. Truncate 200 bytes of PCM from the end (valid RIFF header declaring 800 frames, but fewer bytes)
        raw_trunc = raw_valid[:-200]
        trunc_b64 = base64.b64encode(raw_trunc).decode("utf-8")
        with self.assertRaises(ValueError) as ctx:
            combine_wav_base64_chunks([trunc_b64])
        self.assertIn("PCM data length mismatch", str(ctx.exception))

        # 3. Truncated second chunk in a multi-chunk response
        with self.assertRaises(ValueError) as ctx:
            combine_wav_base64_chunks([valid_b64, trunc_b64])
        self.assertIn("PCM data length mismatch", str(ctx.exception))

        # 4. Declared frame count exceeding actual PCM bytes
        with self.assertRaises(ValueError):
            combine_wav_base64_chunks([trunc_b64, valid_b64])

    def test_speak_rejects_truncated_pcm_chunk_returns_503(self):
        """Provider returning truncated PCM chunk fails strict validation and returns 503, never partial audio."""
        service = VoiceSynthesisService(sarvam_key="mock_key", openai_key=None)
        raw_valid = create_dummy_wav_bytes(duration_sec=0.1, framerate=8000)
        raw_trunc = raw_valid[:-100]
        trunc_b64 = base64.b64encode(raw_trunc).decode("utf-8")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"audios": [trunc_b64]}
        mock_client = MockHttpxClient(mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with self.assertRaises(VoiceServiceException) as ctx:
                run_sync(service.speak("Test text", "en"))
            self.assertEqual(ctx.exception.status_code, 503)
            self.assertEqual(ctx.exception.code, "VOICE_PROVIDER_UNAVAILABLE")

    def test_speak_inflight_call_cannot_exceed_hard_overall_deadline(self):
        """In-flight provider call is cancelled and raises 504 when exceeding hard overall deadline."""
        service = VoiceSynthesisService(sarvam_key="mock_key", openai_key=None, overall_deadline_sec=0.1)
        mock_client = MagicMock()

        async def slow_post(*args, **kwargs):
            await asyncio.sleep(0.5)
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"audios": ["dummy"]}
            return resp

        mock_client.__aenter__.return_value.post = slow_post

        with patch("httpx.AsyncClient", return_value=mock_client):
            t0 = time.monotonic()
            with self.assertRaises(VoiceServiceException) as ctx:
                run_sync(service.speak("Short test", "en"))
            elapsed = time.monotonic() - t0
            self.assertEqual(ctx.exception.status_code, 504)
            self.assertEqual(ctx.exception.code, "VOICE_SYNTHESIS_TIMEOUT")
            self.assertLess(elapsed, 0.4)

    def test_speak_multiple_batches_cannot_exceed_hard_overall_deadline(self):
        """Multiple sequential batches cannot cumulatively exceed overall deadline."""
        service = VoiceSynthesisService(sarvam_key="mock_key", openai_key=None, overall_deadline_sec=0.15)
        dummy_wav = create_dummy_wav_bytes(framerate=8000)
        dummy_b64 = base64.b64encode(dummy_wav).decode("utf-8")
        mock_client = MagicMock()

        async def paced_post(*args, **kwargs):
            await asyncio.sleep(0.1)
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"audios": [dummy_b64] * 3}
            return resp

        mock_client.__aenter__.return_value.post = paced_post

        four_chunks = ["Chunk 1", "Chunk 2", "Chunk 3", "Chunk 4"]
        with patch("app.services.voice.synthesis.chunk_text", return_value=four_chunks):
            with patch("httpx.AsyncClient", return_value=mock_client):
                t0 = time.monotonic()
                with self.assertRaises(VoiceServiceException) as ctx:
                    run_sync(service.speak("Long test", "en"))
                elapsed = time.monotonic() - t0
                self.assertEqual(ctx.exception.status_code, 504)
                self.assertEqual(ctx.exception.code, "VOICE_SYNTHESIS_TIMEOUT")
                self.assertLess(elapsed, 0.3)

    def test_speak_provider_fallback_cannot_reset_hard_overall_deadline(self):
        """Provider fallback to OpenAI cannot reset the overall deadline clock."""
        service = VoiceSynthesisService(sarvam_key="mock_key", openai_key="mock_openai", overall_deadline_sec=0.15)
        mock_client = MagicMock()

        async def slow_sarvam_or_openai(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            await asyncio.sleep(0.1)
            if "sarvam" in url:
                resp = MagicMock()
                resp.status_code = 500
                return resp
            # OpenAI
            await asyncio.sleep(0.1)
            resp = MagicMock()
            resp.status_code = 200
            resp.content = b"mp3data"
            return resp

        mock_client.__aenter__.return_value.post = slow_sarvam_or_openai

        with patch("httpx.AsyncClient", return_value=mock_client):
            t0 = time.monotonic()
            with self.assertRaises(VoiceServiceException) as ctx:
                run_sync(service.speak("Fallback test", "en"))
            elapsed = time.monotonic() - t0
            self.assertEqual(ctx.exception.status_code, 504)
            self.assertEqual(ctx.exception.code, "VOICE_SYNTHESIS_TIMEOUT")
            self.assertLess(elapsed, 0.3)

    def test_speak_no_partial_audio_returned_after_timeout(self):
        """No partial audio from early batches is returned when a subsequent batch times out."""
        service = VoiceSynthesisService(sarvam_key="mock_key", openai_key=None, overall_deadline_sec=0.12)
        dummy_wav = create_dummy_wav_bytes(framerate=8000)
        dummy_b64 = base64.b64encode(dummy_wav).decode("utf-8")
        mock_client = MagicMock()
        call_num = 0

        async def post_first_fast_second_slow(*args, **kwargs):
            nonlocal call_num
            call_num += 1
            if call_num == 1:
                resp = MagicMock()
                resp.status_code = 200
                resp.json.return_value = {"audios": [dummy_b64] * 3}
                return resp
            # Batch 2 stalls
            await asyncio.sleep(0.5)
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"audios": [dummy_b64]}
            return resp

        mock_client.__aenter__.return_value.post = post_first_fast_second_slow

        four_chunks = ["Chunk 1", "Chunk 2", "Chunk 3", "Chunk 4"]
        with patch("app.services.voice.synthesis.chunk_text", return_value=four_chunks):
            with patch("httpx.AsyncClient", return_value=mock_client):
                with self.assertRaises(VoiceServiceException) as ctx:
                    run_sync(service.speak("Multi batch partial check", "en"))
                self.assertEqual(ctx.exception.status_code, 504)
                self.assertEqual(ctx.exception.code, "VOICE_SYNTHESIS_TIMEOUT")


if __name__ == "__main__":
    unittest.main()
