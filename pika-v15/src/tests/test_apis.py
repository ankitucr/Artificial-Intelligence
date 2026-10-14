import os
import requests
from dotenv import load_dotenv

# .env file load karna (root directory se)
dotenv_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(dotenv_path=dotenv_path)

# Dummy Prompt for all models
PROMPT = "Say exactly 'OK' and nothing else."
USER_MSG = [{"role": "user", "content": PROMPT}]

def check_api(name, env_var, url, payload_type, model=None, headers=None, data=None):
    print(f"\n⚡ Testing {name}...")
    api_key = os.getenv(env_var)

    if not api_key or api_key == "your_key_here":
        print(f"❌ FAIL: API Key missing in .env ({env_var})")
        return

    # Set Default Headers
    if not headers:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    # Format Payload based on Provider Type
    if payload_type == "openai":
        data = {"model": model, "messages": USER_MSG, "max_tokens": 10}
    elif payload_type == "gemini":
        url = f"{url}?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": PROMPT}]}]}
    elif payload_type == "cohere":
        data = {
            "model": model,
            "messages": USER_MSG,
            "max_tokens": 10
        }
    elif payload_type == "hf":
        data = {
            "model": model,
            "messages": USER_MSG,
            "max_tokens": 10
        }

    try:
        res = requests.post(url, headers=headers, json=data, timeout=20)
        if res.status_code == 200:
            print(f"✅ {name} is ONLINE! (Status 200)")
        else:
            print(f"❌ Error {res.status_code}: {res.text[:300]}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    print("🚀 Initiating Pika v15 Mega Load-Balancer Diagnostics...\n")

    # 1. Google Gemini — 1.5-flash is deprecated, use 2.5-flash
    check_api("Gemini (Google AI)", "GEMINI_API_KEY",
              "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent", "gemini")

    # 2. Groq — llama3-8b-8192 was decommissioned Aug 30 2025, use llama-3.1-8b-instant
    check_api("Groq", "GROQ_API_KEY",
              "https://api.groq.com/openai/v1/chat/completions", "openai", model="llama-3.1-8b-instant")

    # 3. Mistral — mistral-small-latest is still valid
    check_api("Mistral", "MISTRAL_API_KEY",
              "https://api.mistral.ai/v1/chat/completions", "openai", model="mistral-small-latest")

    # 4. Cerebras — use llama3.1-8b (confirm exact id via /v1/models if this fails)
    check_api("Cerebras", "CEREBRAS_API_KEY",
              "https://api.cerebras.ai/v1/chat/completions", "openai", model="llama3.1-8b")

    # 5. Hugging Face — legacy api-inference.huggingface.co returns 410 now.
    #    New router is OpenAI-compatible chat endpoint.
    check_api("Hugging Face", "HUGGINGFACE_API_KEY",
              "https://router.huggingface.co/v1/chat/completions", "hf",
              model="mistralai/Mistral-7B-Instruct-v0.2")

    # 6. GitHub Models — old models.inference.ai.azure.com endpoint retired,
    #    current endpoint is models.github.ai
    check_api("GitHub Models", "GITHUB_MODELS_API_KEY",
              "https://models.github.ai/inference/chat/completions", "openai", model="openai/gpt-4o")

    # 7. Cohere — v1/chat is legacy; v2/chat is current, payload shape also changed
    check_api("Cohere", "COHERE_API_KEY",
              "https://api.cohere.com/v2/chat", "cohere", model="command-r-plus")

    # 8. Cloudflare Workers AI
    cf_account = os.getenv("CLOUDFLARE_ACCOUNT_ID", "your_account_id")
    check_api("Cloudflare", "CLOUDFLARE_API_TOKEN",
              f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/v1/chat/completions", "openai",
              model="@cf/meta/llama-3-8b-instruct")

    print("\n🏁 Diagnostics Complete! Load Balancer Map is ready.")
