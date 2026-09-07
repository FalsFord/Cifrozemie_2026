"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    """Incoming question payload."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="Question or message to send to GigaChat",
    )


class QuestionResponse(BaseModel):
    """Outgoing answer payload."""

    message: str = Field(
        ...,
        description="Answer from GigaChat",
    )
