# 1. Fix the .env file (Remove extra quotes)
try:
    with open(".env", "r") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if "=" in line:
            key, val = line.split("=", 1)
            # Extra quotes hata rahe hain
            val = val.strip().strip("'").strip('"')
            new_lines.append(f"{key}={val}\n")
        else:
            new_lines.append(line)

    with open(".env", "w") as f:
        f.writelines(new_lines)
except Exception as e:
    print(f"❌ .env fix error: {e}")

# 2. Fix main_brainV3.py to use Advanced Groq Model
try:
    with open("main_brainV3.py", "r") as f:
        code = f.read()
    
    # Fake/Old model ko Meta ke sabse smart model se replace karna
    code = code.replace('GROQ_BUILDER_MODEL = "openai/gpt-oss-120b"', 'GROQ_BUILDER_MODEL = "llama-3.3-70b-versatile"')
    
    with open("main_brainV3.py", "w") as f:
        f.write(code)
except Exception as e:
    print(f"❌ Code fix error: {e}")

print("✅ Galti theek ho gayi! Quotes hat gaye aur Super Model set ho gaya.")
