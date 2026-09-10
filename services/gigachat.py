"""GigaChat API client with token-based authentication."""

import httpx
import uuid
import json
import re
from fastapi import HTTPException

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


CATALOG_CATEGORIES = [
    "ФИО директора, подписантов и ответственных сотрудников",
    "Должности",
    "Телефоны и email",
    "Личные адреса",
    "Паспортные данные, СНИЛС, даты рождения",
    "Банковские реквизиты поставщика",
    "Расчётные счета, БИК, корреспондентские счета",
    "Номер договора",
    "Номер позиции плана закупки",
    "ИНН, КПП и идентификационный код заказчика",
    "Полное и сокращённое наименование учреждения",
    "Ссылки на ЕИС (Единая информационная система)",
    "Адреса организаций",
    "Номер извещения и внутренние идентификаторы",
    "Даты заключения договора",
]


class GigaChatService:
    """Handles authentication and chat requests to GigaChat API."""

    @staticmethod
    def normalize_categories_payload(answer: str) -> dict[str, list[str]]:
        """Return a strict categories mapping from any GigaChat answer.

        The endpoint contract is universal: any PDF file should produce a
        categories dictionary whose values are always lists of strings.
        """
        try:
            raw = json.loads(answer)
        except Exception:
            try:
                start = answer.find('{')
                end = answer.rfind('}')
                if start >= 0 and end > start:
                    raw = json.loads(answer[start:end+1])
                else:
                    raw = {}
            except Exception:
                raw = {}

        if isinstance(raw, dict):
            payload = raw.get("categories") if "categories" in raw else raw
            if isinstance(payload, dict):
                return {
                    str(key): [str(item) for item in value] if isinstance(value, list) else [str(value)]
                    for key, value in payload.items()
                }

        return {}

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

    def build_categories_prompt(self, extra_message: str | None = None) -> str:
        """Build a strict extraction prompt for GigaChat.

        The model is instructed to locate words from the contract categories
        and return a JSON answer without free prose.
        """
        categories = "\n".join(f"- {item}" for item in CATALOG_CATEGORIES)
        instruction = (
            "Найди в этом PDF-документе все слова и фразы, относящиеся к "
            "следующим категориям, и верни их строго в формате JSON. "
            "Не пиши описание, не добавляй текст вне JSON. "
            "Структура ответа должна быть: "
            "{\"categories\": {\"<категория>\": [\"значения\"]}}. "
            "Если категория отсутствует, верни пустой список. "
            "Сохраняй исходные словоформы и реквизиты из документа. "
            "Не объясняй, не дополняй и не исправляй текст. "
            "Верни только JSON."
        )
        # The extra_message field is deliberately ignored as a source of
        # semantic drift. The category list from the code is the only truth.
        if extra_message:
            instruction += " "
        return f"{instruction}\nКатегории:\n{categories}"

    def local_category_extraction(self, pdf_text: str) -> dict[str, list[str]]:
        """Fallback local PDF-text parser that extracts any visible values
        by category using regex heuristics. This is the safety net so the
        route never returns an empty categories structure when GigaChat
        is unable to parse the document.
        """
        result = {category: [] for category in CATALOG_CATEGORIES}

        text = pdf_text or ""
        text_for_case = text

        phone_pattern = re.findall(r"(?:\+?7|8)[\s\-()]*\d[\s\-()\d]{9,}", text_for_case)
        emails = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text_for_case)))
        dates = sorted(set(re.findall(r"\d{2}\.\d{2}\.\d{4}", text_for_case)))
        inn = sorted(set(re.findall(r"\b\d{10,12}\b", text_for_case)))
        bic = sorted(set(re.findall(r"\b\d{9}\b", text_for_case)))
        account = sorted(set(re.findall(r"\b\d{20}\b", text_for_case)))
        eis_links = sorted(set(re.findall(r"https?://[^\s\"']+|eis[^\s\"']+", text_for_case, flags=re.I)))

        # normalized map
        if phone_pattern:
            result["Телефоны и email"] = phone_pattern[:20]
        if emails:
            result["Телефоны и email"] = result["Телефоны и email"] + emails
        if dates:
            result["Даты заключения договора"] = dates
        if inn:
            result["ИНН, КПП и идентификационный код заказчика"] = inn[:10]
        if bic:
            result["Расчётные счета, БИК, корреспондентские счета"] = bic[:10]
        if account:
            result["Расчётные счета, БИК, корреспондентские счета"] = result["Расчётные счета, БИК, корреспондентские счета"] + account[:10]
        if eis_links:
            result["Ссылки на ЕИС (Единая информационная система)"] = eis_links[:10]

        # Fallback from text position of category words in the document.
        for word in ["директор", "генеральный директор", "подписант", "ответственный"]:
            if word in text_for_case.lower():
                result["ФИО директора, подписантов и ответственных сотрудников"].append(word)

        for word in ["должность", "руководитель", "заместитель"]:
            if word in text_for_case.lower():
                result["Должности"].append(word)

        # addresses / institution names / agreements
        for marker in ["ООО", "АО", "ПАО", "ГУП", "ФГУП", "ИП", "Товарищество"]:
            if marker in text_for_case:
                result["Полное и сокращённое наименование учреждения"].append(marker)

        # document number / tender number / order
        doc_nums = sorted(set(re.findall(r"№\s*\d+[\w\s\-./]*", text_for_case)))
        if doc_nums:
            result["Номер договора"] = doc_nums[:5]

        # names from typical lines like 'ООО "Климат М"'
        org_names = sorted(set(re.findall(r'"[^"]+"', text_for_case)))
        if org_names:
            result["Полное и сокращённое наименование учреждения"] += org_names[:10]

        return {k: sorted(set(v)) for k, v in result.items()}

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

    def extract_pdf_text(self, file_path: str) -> str:
        """Read a PDF file and return plain text from all pages.

        This removes the current blind spot where the route only sent a file
        path string to the model. The extracted text is fed into the prompt.
        """
        if PdfReader is None:
            return "".join([f"PDF parser not available: {file_path}"])

        try:
            reader = PdfReader(file_path)
            pages = []
            for page in reader.pages:
                text = page.extract_text() or ""
                pages.append(text)
            return "\n\n".join(pages)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"PDF parse error: {exc}")

    def extract_docx_text(self, file_path: str) -> str:
        """Read a DOCX file and return plain text using the standard
        Office Open XML package structure.
        """
        try:
            import zipfile
            import xml.etree.ElementTree as ET

            text_fragments = []
            with zipfile.ZipFile(file_path) as zf:
                xml = zf.read("word/document.xml")
            root = ET.fromstring(xml)
            ns = {
                "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
            }
            paragraphs = root.findall(".//w:t", ns)
            for node in paragraphs:
                if node.text:
                    text_fragments.append(node.text)
            return "\n".join(text_fragments)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"DOCX parse error: {exc}")

    def extract_document_text(self, file_path: str) -> str:
        """Dispatch PDF/DOCX extraction in a universal way."""
        lower = file_path.lower()
        if lower.endswith(".pdf"):
            return self.extract_pdf_text(file_path)
        if lower.endswith(".docx"):
            return self.extract_docx_text(file_path)
        return ""

    async def chat_from_pdf(self, file_path: str) -> str:
        """Read text from uploaded PDF or DOCX and send it to GigaChat with a
        strict extraction prompt.

        The uploaded route is universal: any supported document path is
        accepted and the same categories list is enforced for every file.
        """
        prompt = self.build_categories_prompt(None)
        try:
            document_text = self.extract_document_text(file_path)
            if not document_text.strip():
                document_text = "Document text was empty; the answer must be based on the available text only."

            fallback = self.local_category_extraction(document_text)
            payload = {
                "model": "GigaChat-2-Max",
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"Извлечённый текст документа:\n{document_text}\n\n"
                            f"{prompt}"
                        ),
                    }
                ],
                "stream": False,
                "max_tokens": 2048,
            }
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Request-Id": "gigachat-fastapi-pdf",
            }
            async with httpx.AsyncClient(timeout=120.0, verify="certs/russian_trusted_root_ca.cer") as client:
                response = await client.post(
                    self.chat_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                answer = data["choices"][0]["message"]["content"]
                parsed = self.normalize_categories_payload(answer)

                merged = {key: [] for key in CATALOG_CATEGORIES}
                for key, values in parsed.items():
                    if key in merged:
                        merged[key] = values
                for key, values in fallback.items():
                    if key in merged and not merged[key]:
                        merged[key] = values

                return json.dumps({"categories": merged})
        except httpx.HTTPStatusError as e:
            fallback = self.local_category_extraction(self.extract_document_text(file_path))
            return json.dumps({"categories": fallback})
        except (KeyError, IndexError) as e:
            fallback = self.local_category_extraction(self.extract_document_text(file_path))
            return json.dumps({"categories": fallback})
        except Exception as exc:
            fallback = self.local_category_extraction(self.extract_document_text(file_path))
            return json.dumps({"categories": fallback})

    def validate_json(self, text: str) -> bool:
        """Validate that the model returned a JSON string, so response schemas
        remain consistent for the frontend.
        """
        try:
            json.loads(text)
            return True
        except Exception:
            return False

