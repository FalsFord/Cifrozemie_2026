import json
from fastapi import APIRouter, HTTPException, UploadFile, File
from config import settings
from services.gigachat import GigaChatService
from schemas.request import QuestionRequest, QuestionResponse, CategoriesExtractionResponse
from local_llm.example_llm import call_local_llm as call_llm


router = APIRouter()

# Initialize GigaChat service
gigachat_service = GigaChatService(
    client_id=settings.GIGACHAT_CLIENT_ID,
    client_secret=settings.GIGACHAT_CLIENT_SECRET,
    scope=settings.GIGACHAT_SCOPE,
)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.post("/question", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Send a question to GigaChat and receive an answer.

    Args:
        request: Question payload with 'message' field.

    Returns:
        Answer from GigaChat.
    """
    try:
        answer = await gigachat_service.chat(request.message)

    except HTTPException as e:
        if e.status_code >= 500:
            answer = await call_llm(request.message)
        else:
            raise
    except Exception:
        answer = await call_llm(request.message)
    return QuestionResponse(message=answer)


@router.post("/extract-pdf", response_model=CategoriesExtractionResponse)
async def extract_pdf_from_file(
    file: UploadFile = File(...),
):
    """Accept a PDF or Word (.docx) file, parse the text locally, send a
    category prompt to GigaChat, and return a structured JSON object mapping
    each category to an array of extracted values.

    The contract is intentionally universal: any supported document should
    produce the same category vocabulary and schema.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required.")

    filename = file.filename.lower()
    if filename.endswith(".pdf"):
        suffix = ".pdf"
    elif filename.endswith(".docx"):
        suffix = ".docx"
    else:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported.",
        )

    import tempfile
    import os

    tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path.close()
    file_path = tmp_path.name

    try:
        content = await file.read()
        with open(file_path, "wb") as tmp:
            tmp.write(content)

        answer = await gigachat_service.chat_from_pdf(file_path)

        # Normalize route response to a real structured categories object.
        try:
            parsed = gigachat_service.normalize_categories_payload(answer)
        except Exception:
            parsed = {}

        return CategoriesExtractionResponse(categories=parsed)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        try:
            os.unlink(file_path)
        except Exception:
            pass
