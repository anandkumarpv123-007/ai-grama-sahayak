from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import LanguageCode


class VoiceTranscribeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    transcribed_text: str = Field(..., description="Recognized speech text")
    language: LanguageCode = Field(..., description="Language identified or requested (en or te)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Transcription confidence score (0.0 to 1.0)")


class VoiceSpeakRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    text: str = Field(..., min_length=1, description="Text string to synthesize into speech")
    language: LanguageCode = Field(
        default=LanguageCode.EN,
        description="Speech language code (en or te)",
    )


class VoiceSpeakResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    audio_base64: str = Field(..., description="Base64-encoded audio bytes")
    mime_type: str = Field(default="audio/mpeg", description="MIME type of the audio stream")
    language: LanguageCode = Field(..., description="Language code of synthesized speech")
