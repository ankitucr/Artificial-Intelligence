import re

try:
    with open("main_brainV3.py", "r") as f:
        code = f.read()

    # Sabhi guess kiye hue models ko hatakar universal 'openrouter/free' set karna
    code = re.sub(r'PLANNER_MODEL\s*=\s*.*', 'PLANNER_MODEL = "openrouter/free"', code)
    code = re.sub(r'PLANNER_BACKUP_MODEL\s*=\s*.*', 'PLANNER_BACKUP_MODEL = "openrouter/free"', code)
    code = re.sub(r'BUILDER_MODEL\s*=\s*.*', 'BUILDER_MODEL = "openrouter/free"', code)
    code = re.sub(r'BUILDER_BACKUP_MODEL\s*=\s*.*', 'BUILDER_BACKUP_MODEL = "openrouter/free"', code)
    code = re.sub(r'REVIEWER_MODEL\s*=\s*.*', 'REVIEWER_MODEL = "openrouter/free"', code)
    code = re.sub(r'REVIEWER_BACKUP_MODEL\s*=\s*.*', 'REVIEWER_BACKUP_MODEL = "openrouter/free"', code)

    with open("main_brainV3.py", "w") as f:
        f.write(code)
        
    print("✅ Jadu theek ho gaya! Universal Free Models set ho gaye hain.")
except Exception as e:
    print(f"❌ Error: {e}")
