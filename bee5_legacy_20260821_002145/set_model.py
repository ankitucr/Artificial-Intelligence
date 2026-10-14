with open("main_brainV3.py", "r") as f:
    code = f.read()

# Set OpenRouter model strictly to meta-llama/llama-3.3-70b-instruct as requested
code = code.replace(
    'OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")',
    'OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")'
)

with open("main_brainV3.py", "w") as f:
    f.write(code)

print("✅ OpenRouter model set to meta-llama/llama-3.3-70b-instruct!")
