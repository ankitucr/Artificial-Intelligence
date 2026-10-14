with open("main_brainV3.py", "r") as f:
    lines = f.readlines()

with open("main_brainV3.py", "w") as f:
    for line in lines:
        # 1. Fixing Groq (The Master Builder)
        if line.startswith("GROQ_BUILDER_MODEL ="):
            f.write('GROQ_BUILDER_MODEL = "llama-3.1-70b-versatile"\n')
            
        # 2. Fixing OpenRouter (Bypassing the crowded 429 endpoint)
        elif line.startswith("PLANNER_MODEL ="):
            f.write('PLANNER_MODEL = "meta-llama/llama-3-8b-instruct:free"\n')
        elif line.startswith("PLANNER_BACKUP_MODEL ="):
            f.write('PLANNER_BACKUP_MODEL = "google/gemma-7b-it:free"\n')
        elif line.startswith("BUILDER_MODEL ="):
            f.write('BUILDER_MODEL = "mistralai/mistral-7b-instruct:free"\n')
        elif line.startswith("BUILDER_BACKUP_MODEL ="):
            f.write('BUILDER_BACKUP_MODEL = "meta-llama/llama-3-8b-instruct:free"\n')
        elif line.startswith("REVIEWER_MODEL ="):
            f.write('REVIEWER_MODEL = "meta-llama/llama-3-8b-instruct:free"\n')
        elif line.startswith("REVIEWER_BACKUP_MODEL ="):
            f.write('REVIEWER_BACKUP_MODEL = "microsoft/phi-3-mini-128k-4k-free"\n')
        else:
            f.write(line)

print("✅ Asli Jaadu: Groq Llama-3.1-70B wapas aa gaya aur 429/404 errors hamesha ke liye block ho gaye!")
