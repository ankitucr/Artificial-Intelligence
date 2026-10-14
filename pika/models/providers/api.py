import os
from typing import Any

import httpx
from dotenv import load_dotenv

from models.base import ModelProvider

load_dotenv()


class APIProvider(ModelProvider):

    def __init__(
        self,
        name: str,
        base_url: str,
        model: str,
        api_key_env: str,
        timeout: float = 60.0,
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key_env = api_key_env
        self.timeout = timeout

    def api_key(self) -> str | None:
        return os.getenv(self.api_key_env)

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        context=None,
    ) -> dict[str, Any]:

        key = self.api_key()

        if not key:
            return {
                "success": False,
                "provider": self.name,
                "model": self.model,
                "text": "",
                "error": f"Missing {self.api_key_env}",
            }

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

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 512,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:

                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )

                if response.status_code >= 400:
                    return {
                        "success": False,
                        "provider": self.name,
                        "model": self.model,
                        "text": "",
                        "error": (
                            f"HTTP {response.status_code}: "
                            f"{response.text[:500]}"
                        ),
                    }

                data = response.json()

            text = ""

            try:
                text = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                text = str(data)

            return {
                "success": True,
                "provider": self.name,
                "model": self.model,
                "text": text,
                "raw": data,
            }

        except Exception as exc:
            return {
                "success": False,
                "provider": self.name,
                "model": self.model,
                "text": "",
                "error": str(exc),
            }

    async def health(self) -> bool:

        key = self.api_key()

        if not key:
            return False

        try:
            async with httpx.AsyncClient(
                timeout=10
            ) as client:

                response = await client.get(
                    f"{self.base_url}/models",
                    headers={
                        "Authorization": f"Bearer {key}"
                    },
                )

                return response.status_code == 200

        except Exception:
            return False
