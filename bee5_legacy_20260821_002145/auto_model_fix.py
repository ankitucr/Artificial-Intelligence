import os
import re
from groq import Groq
from dotenv import load_dotenv

# API key load karo
load_dotenv(override=True)
api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    print("❌ Error: GROQ_API_KEY nahi mili!")
    exit()

client = Groq(api_key=api_key)

# 1. Groq se active models ki list maango
print("🔍 Groq server se active models dhoondh rahe hain...")
try:
    available_models = [m.id for m in client.models.list().data]
except Exception as e:
    print(f"❌ API Error: {e}")
    exit()

# 2. Sabse best available models chuno
# Builder ke liye sabse bada model (70b ya mixtral)
builder_model = next((m for m in available_models if "70b" in m), None)
if not builder_model: 
    builder_model = next((m for m in available_models if "mixtral" in m), available_models[0])

# Planner/Reviewer ke liye fast model (8b ya gemma)
planner_model = next((m for m in available_models if "8b" in m), None)
if not planner_model: 
    planner_model = next((m for m in available_models if "gemma" in m), builder_model)

print(f"✅ Builder ke liye set kiya: {builder_model}")
print(f"✅ Planner/Reviewer ke liye set kiya: {planner_model}")

# 3. main_brainV3.py ko update karo
with open("main_brainV3.py", "r") as f:
    code = f.read()

code = re.sub(r'GROQ_BUILDER_MODEL\s*=\s*".*"', f'GROQ_BUILDER_MODEL = "{builder_model}"', code)
code = re.sub(r'GROQ_PLANNER_MODEL\s*=\s*".*"', f'GROQ_PLANNER_MODEL = "{planner_model}"', code)
code = re.sub(r'GROQ_REVIEWER_MODEL\s*=\s*".*"', f'GROQ_REVIEWER_MODEL = "{planner_model}"', code)

with open("main_brainV3.py", "w") as f:
    f.write(code)

print("🚀 Jaadu poora hua! Ab code hamesha working model hi use karega.")
