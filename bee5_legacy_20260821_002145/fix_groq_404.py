import re

with open("main_brainV3.py", "r") as f:
    code = f.read()

# Auto-detect logic for Groq
dynamic_groq_logic = """
# Auto-detect active Groq model so it NEVER gets 404
GROQ_PLANNER_MODEL = "mixtral-8x7b-32768" # Safe default
if groq_client:
    try:
        active_models = [m.id for m in groq_client.models.list().data]
        # Pick the best available fast model automatically
        GROQ_PLANNER_MODEL = next((m for m in active_models if "llama" in m.lower() or "gemma" in m.lower()), active_models[0])
        print(f"✅ Groq automatically selected active model: {GROQ_PLANNER_MODEL}")
    except:
        pass
"""

# Hardcoded line ko dynamic block se replace karna
code = re.sub(
    r'GROQ_PLANNER_MODEL\s*=\s*".*?"', 
    dynamic_groq_logic.strip(), 
    code
)

with open("main_brainV3.py", "w") as f:
    f.write(code)

print("✅ Groq 404 Fix Applied! Ab Groq auto-detect karega aur OpenRouter 70B code likhega.")
