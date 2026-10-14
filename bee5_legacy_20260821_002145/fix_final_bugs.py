import re

file_name = "main_brainV3.py"

try:
    with open(file_name, "r") as f:
        code = f.read()

    # Fix 1: Correct the URL typo (openrouter_ai -> openrouter.ai)
    if "openrouter_ai" in code:
        code = code.replace("openrouter_ai/api", "openrouter.ai/api")
        code = code.replace("openrouter_ai", "openrouter.ai")

    # Fix 2: Disable Memory Limit for Termux (to fix MapShadow CHECK crash)
    old_mem = "resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))"
    new_mem = "# resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))  # Disabled for Termux"
    code = code.replace(old_mem, new_mem)

    # Write the changes back to the file
    with open(file_name, "w") as f:
        f.write(code)

    print("✅ Bimari khatam! URL theek ho gaya aur Termux Sandbox Crash fix ho gaya.")

except Exception as e:
    print(f"❌ Error aaya: {e}")
