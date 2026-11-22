from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Service health status")
    service: str = Field(default="ai-grama-sahayak", description="Service identifier")
    version: str = Field(default="1.0.0", description="API version")
