"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the GigaChat API service."""

    GIGACHAT_CLIENT_ID: str = "019feafc-c8d0-7b1c-bff7-cbca476a8b89"
    GIGACHAT_CLIENT_SECRET: str = "1639ca01-738d-4368-b6f5-e8bae8f62ef0"
    GIGACHAT_SCOPE: str = "GIGACHAT_API_PERS"

    GIGACHAT_AUTH_URL: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    GIGACHAT_CHAT_URL: str = "https://api.giga.chat/v1/chat/completions"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
