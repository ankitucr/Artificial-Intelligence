import re
import sys

file_name = "main_brainV3.py"

try:
    with open(file_name, "r") as f:
        code = f.read()

    # 1. Update Models Config
    old_config = """PLANNER_MODEL = os.environ.get("PLANNER_MODEL", "openrouter/free")
BUILDER_MODEL = os.environ.get("BUILDER_MODEL", "meta-llama/llama-3.3-70b-instruct")
REVIEWER_MODEL = os.environ.get("REVIEWER_MODEL", "openrouter/free")"""

    new_config = """PLANNER_MODEL = os.environ.get("PLANNER_MODEL", "nvidia/nemotron-3-ultra:free")
PLANNER_BACKUP_MODEL = os.environ.get("PLANNER_BACKUP_MODEL", "z-ai/glm-5.2:free")
BUILDER_MODEL = os.environ.get("BUILDER_MODEL", "poolside/laguna-s-2.1:free")
BUILDER_BACKUP_MODEL = os.environ.get("BUILDER_BACKUP_MODEL", "nvidia/nemotron-3.5-lightning:free")
REVIEWER_MODEL = os.environ.get("REVIEWER_MODEL", "nvidia/nemotron-3.5-content-safety:free")
REVIEWER_BACKUP_MODEL = os.environ.get("REVIEWER_BACKUP_MODEL", "cohere/north-mini-code:free")"""

    code = code.replace(old_config, new_config)

    # 2. Update call_openrouter function
    old_call_openrouter = """def call_openrouter(model: str, system_prompt: str, user_prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=30,
    )
    if r.status_code == 429:
        raise RateLimited(f"{model} rate-limited by OpenRouter")
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]"""

    new_call_openrouter = """def call_openrouter(primary_model: str, backup_model: str, system_prompt: str, user_prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={"model": primary_model, "messages": messages},
            timeout=30,
        )
        if r.status_code == 429:
            raise RateLimited(f"{primary_model} rate-limited by OpenRouter")
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"⚠️ Primary model {primary_model} failed ({e}). Switching to Backup: {backup_model}...")
        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={"model": backup_model, "messages": messages},
                timeout=30,
            )
            if r.status_code == 429:
                raise RateLimited(f"{backup_model} rate-limited by OpenRouter")
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as backup_e:
            raise RuntimeError(f"Both Primary and Backup models failed. Error: {backup_e}")"""

    code = code.replace(old_call_openrouter, new_call_openrouter)

    # 3. Update the function calls inside ask_planner, ask_builder, ask_reviewer
    code = code.replace("call_openrouter(PLANNER_MODEL,", "call_openrouter(PLANNER_MODEL, PLANNER_BACKUP_MODEL,")
    code = code.replace("call_openrouter(BUILDER_MODEL,", "call_openrouter(BUILDER_MODEL, BUILDER_BACKUP_MODEL,")
    code = code.replace("call_openrouter(REVIEWER_MODEL,", "call_openrouter(REVIEWER_MODEL, REVIEWER_BACKUP_MODEL,")

    # Write changes back
    with open(file_name, "w") as f:
        f.write(code)
    
    print("✅ Super Brain Upgrade Complete! main_brainV3.py update ho gaya hai.")

except Exception as e:
    print(f"❌ Error aaya: {e}")
