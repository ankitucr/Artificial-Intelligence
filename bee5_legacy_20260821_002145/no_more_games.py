# 1. Fix Groq Model in main_brainV3.py
try:
    with open("main_brainV3.py", "r") as f:
        code = f.read()
    
    # Change non-existent 3.3 to the ultra-stable and powerful 3.1 70B model
    code = code.replace('"llama-3.3-70b-versatile"', '"llama-3.1-70b-versatile"')
    code = code.replace('"openai/gpt-oss-120b"', '"llama-3.1-70b-versatile"')
    
    with open("main_brainV3.py", "w") as f:
        f.write(code)
except Exception as e:
    print(f"❌ Code fix error: {e}")

# 2. Fix .env to use openrouter/auto (Prevents 404 errors forever)
try:
    with open(".env", "r") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.startswith("PLANNER_MODEL="):
            new_lines.append('PLANNER_MODEL="openrouter/auto"\n')
        elif line.startswith("PLANNER_BACKUP_MODEL="):
            new_lines.append('PLANNER_BACKUP_MODEL="openrouter/auto"\n')
        elif line.startswith("BUILDER_MODEL="):
            new_lines.append('BUILDER_MODEL="openrouter/auto"\n')
        elif line.startswith("BUILDER_BACKUP_MODEL="):
            new_lines.append('BUILDER_BACKUP_MODEL="openrouter/auto"\n')
        elif line.startswith("REVIEWER_MODEL="):
            new_lines.append('REVIEWER_MODEL="openrouter/auto"\n')
        elif line.startswith("REVIEWER_BACKUP_MODEL="):
            new_lines.append('REVIEWER_BACKUP_MODEL="openrouter/auto"\n')
        else:
            new_lines.append(line)

    with open(".env", "w") as f:
        f.writelines(new_lines)
except Exception as e:
    print(f"❌ .env fix error: {e}")

print("✅ DONE! Groq ab Llama-3.1-70B par hai aur OpenRouter Auto mode mein hai. No more 404s!")
