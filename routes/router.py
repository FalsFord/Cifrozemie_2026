from fastapi import APIRouter, HTTPException
from config import settings
from services.gigachat import GigaChatService
from schemas.request import QuestionRequest, QuestionResponse
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
    except Exception as e:
        answer = await call_llm(request.message)
        #raise HTTPException(status_code=500, detail=f"GigaChat error: {e}")
    return QuestionResponse(message=answer)