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


class WordRegion(BaseModel):
    """A single located occurrence of an extracted value inside the PDF.

    Coordinates are in PDF points (1/72 inch), top-left origin, matching
    the page's native coordinate space (as used by PyMuPDF/pdf.js/etc).
    """

    category: str = Field(..., description="Category this value belongs to.")
    value: str = Field(..., description="The exact text found on the page.")
    page: int = Field(..., description="1-indexed page number.")
    x: float = Field(..., description="Left offset of the bounding box, in points.")
    y: float = Field(..., description="Top offset of the bounding box, in points.")
    width: float = Field(..., description="Bounding box width, in points.")
    height: float = Field(..., description="Bounding box height, in points.")


class CategoriesExtractionResponse(BaseModel):
    """Structured response for PDF extraction route.

    The categories object is the universal contract: any uploaded PDF must
    produce a fixed shape with every category represented by a list.

    ``regions`` is an additional, best-effort list of bounding boxes for
    every category value that could be located in the PDF's text layer.
    It is only populated for PDF uploads (DOCX has no fixed page geometry)
    and may be empty for scanned/image-only PDFs.
    """

    categories: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Mapping category -> extracted values from the PDF.",
    )
    regions: List[WordRegion] = Field(
        default_factory=list,
        description="Bounding boxes of extracted values found in the PDF.",
    )


class PDFExtractionRequest(BaseModel):
    """Request model for upload-based document extraction.

    Accepts an uploaded PDF or DOCX file. The free-text message is no
    longer the source of extraction instructions; the category prompt is
    stored in the service and is universal for all documents.
    """

    # intentionally no free-text instruction field
    pass
