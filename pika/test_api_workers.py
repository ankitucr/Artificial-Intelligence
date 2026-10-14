import asyncio
import os

from dotenv import load_dotenv

from models.providers.api import APIProvider

load_dotenv()


PROVIDERS = [

    {
        "name": "groq",
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.1-8b-instant",
        "key": "GROQ_API_KEY",
    },

    {
        "name": "cerebras",
        "base_url": "https://api.cerebras.ai/v1",
        "model": "llama-3.1-8b",
        "key": "CEREBRAS_API_KEY",
    },

    {
        "name": "mistral",
        "base_url": "https://api.mistral.ai/v1",
        "model": "mistral-small-latest",
        "key": "MISTRAL_API_KEY",
    },

    {
        "name": "github-models",
        "base_url": "https://models.github.ai/inference",
        "model": "openai/gpt-4o-mini",
        "key": "GITHUB_MODELS_API_KEY",
    },
]


async def test_provider(cfg):

    provider = APIProvider(
        name=cfg["name"],
        base_url=cfg["base_url"],
        model=cfg["model"],
        api_key_env=cfg["key"],
        timeout=30,
    )

    if not os.getenv(cfg["key"]):
        print(
            f"[SKIP] {cfg['name']}: "
            f"{cfg['key']} not configured"
        )
        return

    print(f"[TEST] {cfg['name']} ...")

    result = await provider.generate(
        prompt=(
            "Reply with exactly: "
            "PIKA_API_WORKER_OK"
        ),
        system=(
            "You are testing the PIKA API worker. "
            "Follow the requested output exactly."
        ),
    )

    if result["success"]:
        print(
            f"[PASS] {cfg['name']} -> "
            f"{result['text']}"
        )
    else:
        print(
            f"[FAIL] {cfg['name']} -> "
            f"{result.get('error')}"
        )

    print()


async def main():

    print("=" * 60)
    print("PIKA API WORKER TEST")
    print("=" * 60)

    for provider in PROVIDERS:
        await test_provider(provider)

    print("=" * 60)
    print("API TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
