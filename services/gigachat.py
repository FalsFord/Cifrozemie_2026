"""GigaChat API client with token-based authentication."""

import httpx
import uuid
from fastapi import HTTPException


class GigaChatService:
    """Handles authentication and chat requests to GigaChat API."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scope: str = "GIGACHAT_API_PERS",
        auth_url: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        chat_url: str = "https://api.giga.chat/v1/chat/completions",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.auth_url = auth_url
        self.chat_url = chat_url
        self._access_token: str | None = None
        self._token_expires_at: float = 0

    @property
    def access_token(self) -> str:
        """Return cached token if still valid, otherwise refresh."""
        import time
        if self._access_token and time.time() < self._token_expires_at - 30:
            return self._access_token
        self._refresh_token()
        return self._access_token  # type: ignore[return-value]

    def _refresh_token(self) -> None:
        """Obtain a new OAuth token from GigaChat."""
        try:
            with httpx.Client(timeout=30.0, verify=False) as client:
                import base64
                credentials = "MDE5ZmVhZmMtYzhkMC03YjFjLWJmZjctY2JjYTQ3NmE4Yjg5OjE2MzljYTAxLTczOGQtNDM2OC1iNmY1LWU4YmFlOGY2MmVmMA=="
                response = client.post(
                        self.auth_url,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Authorization": f"Basic {credentials}",
                        "Accept": "application/json",
                        "RqUID": str(uuid.uuid4()),
                    },
                    data={
                        "grant_type": "client_credentials",
                        "scope": self.scope,
                    },
                )
                response.raise_for_status()
                data = response.json()
                self._access_token = data["access_token"]
                self._token_expires_at = data.get(
                    "expires_at",
                    data.get("expires_in", 1800),
                )
                # If expires_in is provided, compute expires_at
                if "expires_in" in data and "expires_at" not in data:
                    import time
                    self._token_expires_at = time.time() + data["expires_in"]
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Token refresh failed: {e.response.status_code} {e.response.text}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Token refresh error: {e}",
            )

    async def chat(self, message: str) -> str:
        """Send a message to GigaChat and return the assistant's reply."""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Request-Id": "gigachat-fastapi",
        }
        payload = {
            "model": "GigaChat-2-Max",
            "messages": [
                {"role": "user", "content": message},
            ],
            "stream": False,
            "max_tokens": 2048,
        }
        try:
            async with httpx.AsyncClient(timeout=120.0, verify="certs/russian_trusted_root_ca.cer") as client:
                response = await client.post(
                    self.chat_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=502,
                detail=f"GigaChat API error: {e.response.status_code} {e.response.text}",
            )
        except (KeyError, IndexError) as e:
            raise HTTPException(
                status_code=502,
                detail=f"Unexpected response format: {e}",
            )
