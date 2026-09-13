"""Fallback local LLM stub used when the GigaChat API is unavailable."""


async def call_local_llm(message: str) -> str:
    """Return a placeholder answer for the given message.

    This is a stand-in for a real local model. It always returns the
    literal string ``"local_llm"`` and is only used as a fallback when
    the GigaChat API call fails.

    Args:
        message: The user's message (currently unused by the stub).

    Returns:
        The fixed placeholder response ``"local_llm"``.
    """
    response = "local_llm"
    return response
