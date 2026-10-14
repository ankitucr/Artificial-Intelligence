from models.base import ModelProvider


class MockProvider(ModelProvider):

    name = "bootstrap-model"

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        context=None,
    ) -> dict:

        return {
            "success": True,
            "provider": self.name,
            "text": (
                "MODEL_BOOTSTRAP_OK\n\n"
                "PIKA successfully reached the model-provider layer.\n"
                "A real local inference backend can now be attached."
            ),
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
            },
        }
