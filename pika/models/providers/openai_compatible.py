import os
import httpx

from models.base import ModelProvider


class OpenAICompatibleProvider(ModelProvider):

    name = "openai-compatible"

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout: float = 180.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key or os.getenv("PIKA_API_KEY")
        self.timeout = timeout

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        context=None,
    ) -> dict:

        messages = []

        if system:
            messages.append({
                "role": "system",
                "content": system,
            })

        if context:
            messages.extend(context)

        messages.append({
            "role": "user",
            "content": prompt,
        })

        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 128,
            "stream": False,
        }

        url = f"{self.base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:

                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )

                response.raise_for_status()
                data = response.json()

        except Exception as exc:
            return {
                "success": False,
                "provider": self.name,
                "model": self.model,
                "text": "",
                "error": str(exc),
            }

        text = ""

        try:
            text = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            text = str(data)

        return {
            "success": True,
            "provider": self.name,
            "model": self.model,
            "text": text,
            "raw": data,
        }

    async def health(self) -> bool:

        try:
            async with httpx.AsyncClient(
                timeout=5
            ) as client:

                response = await client.get(
                    f"{self.base_url}/models"
                )

                return response.status_code == 200

        except Exception:
            return False
