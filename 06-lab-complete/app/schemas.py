"""Request/response models for the agent API."""
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    user_id: str = Field(..., min_length=1, max_length=128)


class AskMetadata(BaseModel):
    environment: str
    model: str
    cost_usd: float


class AskResponse(BaseModel):
    answer: str
    user_id: str
    conversation_length: int
    metadata: AskMetadata
