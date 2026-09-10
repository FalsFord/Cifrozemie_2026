"""Pydantic schemas for request/response validation."""

from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    """Incoming question payload for plain text chat request."""

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


class CategoriesExtractionResponse(BaseModel):
    """Structured response for PDF extraction route.

    The categories object is the universal contract: any uploaded PDF must
    produce a fixed shape with every category represented by a list.
    """

    categories: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Mapping category -> extracted values from the PDF.",
    )


class PDFExtractionRequest(BaseModel):
    """Request model for upload-based document extraction.

    Accepts an uploaded PDF or DOCX file. The free-text message is no
    longer the source of extraction instructions; the category prompt is
    stored in the service and is universal for all documents.
    """

    # intentionally no free-text instruction field
    pass
