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

    if not headers:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    if payload_type == "openai":
        data = {"model": model, "messages": USER_MSG, "max_tokens": 10}
    elif payload_type == "gemini":
        url = f"{url}?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": PROMPT}]}]}
    elif payload_type == "cohere":
        data = {"model": model, "messages": USER_MSG, "max_tokens": 10}
    elif payload_type == "hf":
        data = {"model": model, "messages": USER_MSG, "max_tokens": 10}

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

    # 1. Google Gemini — 2.5-flash retired too, API error itself pointed to 3.6-flash
    check_api("Gemini (Google AI)", "GEMINI_API_KEY",
              "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent", "gemini")

    # 2. Groq — llama-3.1-8b-instant is now Enterprise-tier gated.
    #    openai/gpt-oss-120b is currently listed with real per-token pricing (free/dev tier friendly)
    check_api("Groq", "GROQ_API_KEY",
              "https://api.groq.com/openai/v1/chat/completions", "openai", model="openai/gpt-oss-120b")

    # 3. Mistral — confirmed working, unchanged
    check_api("Mistral", "MISTRAL_API_KEY",
              "https://api.mistral.ai/v1/chat/completions", "openai", model="mistral-small-latest")

    # 4. Cerebras — model ID is correct per official docs (llama3.1-8b);
    #    404 here usually means the model isn't enabled for this specific account.
    #    Verify with: curl https://api.cerebras.ai/v1/models -H "Authorization: Bearer $CEREBRAS_API_KEY"
    check_api("Cerebras", "CEREBRAS_API_KEY",
              "https://api.cerebras.ai/v1/chat/completions", "openai", model="llama3.1-8b")

    # 5. Hugging Face — router needs "model:provider" format since multiple
    #    providers can serve the same model. novita is a commonly-available provider.
    check_api("Hugging Face", "HUGGINGFACE_API_KEY",
              "https://router.huggingface.co/v1/chat/completions", "hf",
              model="meta-llama/Llama-3.1-8B-Instruct:novita")

    # 6. GitHub Models — this was a temporary outage ("retirement brownout"),
    #    not a wrong model name. Retry later; endpoint/model below are correct.
    check_api("GitHub Models", "GITHUB_MODELS_API_KEY",
              "https://models.github.ai/inference/chat/completions", "openai", model="openai/gpt-4o")

    # 7. Cohere — command-r-plus retired 15 Sep 2025, use command-a-03-2025
    check_api("Cohere", "COHERE_API_KEY",
              "https://api.cohere.com/v2/chat", "cohere", model="command-a-03-2025")

    # 8. Cloudflare Workers AI — llama-3-8b-instruct deprecated 30 May 2026,
    #    -fast variant of 3.3-70b remains active
    cf_account = os.getenv("CLOUDFLARE_ACCOUNT_ID", "your_account_id")
    check_api("Cloudflare", "CLOUDFLARE_API_TOKEN",
              f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/v1/chat/completions", "openai",
              model="@cf/meta/llama-3.3-70b-instruct-fp8-fast")

    print("\n🏁 Diagnostics Complete! Load Balancer Map is ready.")
