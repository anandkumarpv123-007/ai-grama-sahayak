"""
Voice Test Runner for Member 3
Executes voice service and API endpoint tests without requiring socket-bound event loops.
"""

import sys
import os
import base64
import wave
import io
import json
from unittest.mock import patch

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from starlette.datastructures import UploadFile
from app.api.voice import router as voice_router, speak_voice, transcribe_voice, VoiceSpeakRequest
from app.services.voice.synthesis import VoiceSynthesisService
from app.services.voice.transcription import VoiceTranscriptionService, VoiceServiceException, MAX_AUDIO_SIZE_BYTES


def run_sync(coro):
    """Drives a coroutine synchronously to completion without event loop socket binding."""
    try:
        coro.send(None)
    except StopIteration as e:
        return e.value


def make_dummy_wav() -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(b"\x00\x00" * 800)
    return buf.getvalue()


def run_all_tests():
    print("=== Running Member 3 Voice Tests ===", flush=True)

    # 1. Router Registration Test
    test_app = FastAPI()
    test_app.include_router(voice_router, prefix="/api")
    paths = list(test_app.openapi()["paths"].keys())
    assert "/api/voice/transcribe" in paths, "Expected /api/voice/transcribe route"
    assert "/api/voice/speak" in paths, "Expected /api/voice/speak route"
    print("PASS: Router registration with prefix='/api'", flush=True)

    # 2. VoiceSynthesisService Tests
    synth = VoiceSynthesisService()
    synth.sarvam_key = None
    synth.openai_key = None

    # 2.1 Empty text error
    try:
        run_sync(synth.speak("   ", "en"))
        assert False, "Should have raised exception for empty text"
    except VoiceServiceException as e:
        assert e.code == "EMPTY_TEXT"
        assert e.status_code == 400
        print("PASS: VoiceSynthesisService empty text validation", flush=True)

    # 2.2 Unsupported language error
    try:
        run_sync(synth.speak("Hello", "fr"))
        assert False, "Should have raised exception for unsupported language"
    except VoiceServiceException as e:
        assert e.code == "UNSUPPORTED_LANGUAGE"
        assert e.status_code == 422
        print("PASS: VoiceSynthesisService unsupported language validation", flush=True)

    # 2.3 Text too long error
    try:
        run_sync(synth.speak("A" * 5000, "en"))
        assert False, "Should have raised exception for text too long"
    except VoiceServiceException as e:
        assert e.code == "TEXT_TOO_LONG"
        assert e.status_code == 400
        print("PASS: VoiceSynthesisService text too long validation", flush=True)

    # 2.4 No fake chime without providers (must return 503)
    try:
        run_sync(synth.speak("Valid text", "en"))
        assert False, "Should have raised 503 VOICE_PROVIDER_UNAVAILABLE"
    except VoiceServiceException as e:
        assert e.code == "VOICE_PROVIDER_UNAVAILABLE"
        assert e.status_code == 503
        print("PASS: VoiceSynthesisService raises 503 without providers (no fake audio)", flush=True)

    # 3. VoiceTranscriptionService Tests
    trans = VoiceTranscriptionService()
    trans.sarvam_key = None
    trans.openai_key = None
    wav_bytes = make_dummy_wav()

    # 3.1 Empty audio
    try:
        run_sync(trans.transcribe("audio.wav", "audio/wav", b"", "en"))
        assert False, "Should have raised exception for empty audio"
    except VoiceServiceException as e:
        assert e.code == "EMPTY_AUDIO_FILE"
        assert e.status_code == 400
        print("PASS: VoiceTranscriptionService empty audio validation", flush=True)

    # 3.2 Corrupted audio (< 32 bytes)
    try:
        run_sync(trans.transcribe("audio.wav", "audio/wav", b"too small", "en"))
        assert False, "Should have raised exception for corrupted audio"
    except VoiceServiceException as e:
        assert e.code == "CORRUPTED_AUDIO_FILE"
        assert e.status_code == 400
        print("PASS: VoiceTranscriptionService corrupted audio validation", flush=True)

    # 3.3 Invalid format
    try:
        run_sync(trans.transcribe("audio.txt", "text/plain", b"this is not audio at all 1234567890", "en"))
        assert False, "Should have raised exception for invalid format"
    except VoiceServiceException as e:
        assert e.code == "INVALID_AUDIO_FORMAT"
        assert e.status_code == 400
        print("PASS: VoiceTranscriptionService invalid format validation", flush=True)

    # 3.4 Unsupported language
    try:
        run_sync(trans.transcribe("audio.wav", "audio/wav", wav_bytes, "ja"))
        assert False, "Should have raised exception for unsupported language"
    except VoiceServiceException as e:
        assert e.code == "UNSUPPORTED_LANGUAGE"
        assert e.status_code == 422
        print("PASS: VoiceTranscriptionService unsupported language validation", flush=True)

    # 3.5 No fake transcript without providers (must return 503)
    try:
        run_sync(trans.transcribe("audio.wav", "audio/wav", wav_bytes, "en"))
        assert False, "Should have raised 503 VOICE_PROVIDER_UNAVAILABLE"
    except VoiceServiceException as e:
        assert e.code == "VOICE_PROVIDER_UNAVAILABLE"
        assert e.status_code == 503
        print("PASS: VoiceTranscriptionService raises 503 without providers (no fake words)", flush=True)

    # 4. Router Endpoints Tests
    # 4.1 POST /api/voice/speak error 503 without providers
    req = VoiceSpeakRequest(text="Welfare scheme guidance", language="en")
    with patch.object(VoiceSynthesisService, "speak", side_effect=VoiceServiceException(
        code="VOICE_PROVIDER_UNAVAILABLE",
        message="No external TTS provider configured",
        status_code=503
    )):
        res = run_sync(speak_voice(req))
        assert res.status_code == 503
        err_body = json.loads(res.body.decode())
        assert err_body["error"]["code"] == "VOICE_PROVIDER_UNAVAILABLE"
        print("PASS: speak_voice router endpoint returns 503 when provider unavailable", flush=True)

    # 4.2 POST /api/voice/speak with mock provider success
    dummy_b64 = base64.b64encode(b"REAL_AUDIO_BYTES").decode("utf-8")
    with patch.object(VoiceSynthesisService, "speak", return_value={"audio_base64": dummy_b64, "mime_type": "audio/wav", "language": "en"}):
        res = run_sync(speak_voice(req))
        assert res["language"] == "en"
        assert res["audio_base64"] == dummy_b64
        print("PASS: speak_voice router endpoint returns real audio from provider", flush=True)

    # 4.3 POST /api/voice/speak error response schema
    req_err = VoiceSpeakRequest(text="", language="en")
    res_err = run_sync(speak_voice(req_err))
    assert res_err.status_code == 400
    err_body = json.loads(res_err.body.decode())
    assert err_body["error"]["code"] == "EMPTY_TEXT"
    assert "message" in err_body["error"]
    print("PASS: speak_voice router error response schema", flush=True)

    # 4.4 POST /api/voice/transcribe with mock provider success
    up = UploadFile(io.BytesIO(wav_bytes), filename="voice.wav", headers={"content-type": "audio/wav"})
    mock_stt = {"transcribed_text": "What schemes are available?", "language": "en", "confidence": 0.94}
    with patch.object(VoiceTranscriptionService, "transcribe", return_value=mock_stt):
        res_t = run_sync(transcribe_voice(file=up, language="en"))
        assert res_t["language"] == "en"
        assert res_t["transcribed_text"] == "What schemes are available?"
        print("PASS: transcribe_voice router endpoint returns real transcription from provider", flush=True)

    # 4.5 POST /api/voice/transcribe error 503 without providers
    up2 = UploadFile(io.BytesIO(wav_bytes), filename="voice.wav", headers={"content-type": "audio/wav"})
    with patch.object(VoiceTranscriptionService, "transcribe", side_effect=VoiceServiceException(
        code="VOICE_PROVIDER_UNAVAILABLE",
        message="No external STT provider configured",
        status_code=503
    )):
        res_t_err = run_sync(transcribe_voice(file=up2, language="en"))
        assert res_t_err.status_code == 503
        err_t_body = json.loads(res_t_err.body.decode())
        assert err_t_body["error"]["code"] == "VOICE_PROVIDER_UNAVAILABLE"
        print("PASS: transcribe_voice router returns 503 when provider unavailable", flush=True)

    # 4.6 POST /api/voice/transcribe oversized file 413
    oversized_stream = io.BytesIO(b"\x00" * (MAX_AUDIO_SIZE_BYTES + 1024))
    up_large = UploadFile(oversized_stream, filename="large.wav", headers={"content-type": "audio/wav"})
    res_large = run_sync(transcribe_voice(file=up_large, language="en"))
    assert res_large.status_code == 413
    err_large = json.loads(res_large.body.decode())
    assert err_large["error"]["code"] == "PAYLOAD_TOO_LARGE"
    print("PASS: transcribe_voice enforces 15 MB audio streaming limit with 413", flush=True)

    # 4.7 POST /api/voice/transcribe error response format (empty audio)
    up_empty = UploadFile(io.BytesIO(b""), filename="empty.wav", headers={"content-type": "audio/wav"})
    res_empty = run_sync(transcribe_voice(file=up_empty, language="en"))
    assert res_empty.status_code == 400
    err_empty = json.loads(res_empty.body.decode())
    assert err_empty["error"]["code"] == "EMPTY_AUDIO_FILE"
    print("PASS: transcribe_voice router error response schema", flush=True)

    print("\n=== ALL VOICE TESTS PASSED SUCCESSFULLY! ===", flush=True)


if __name__ == "__main__":
    run_all_tests()
