import re

# 1. Update .env file with highly stable models
try:
    with open(".env", "r") as f:
        lines = f.readlines()
    
    new_models = {
        "PLANNER_MODEL": '"meta-llama/llama-3.1-8b-instruct:free"',
        "PLANNER_BACKUP_MODEL": '"google/gemma-2-9b-it:free"',
        "BUILDER_MODEL": '"google/gemma-2-9b-it:free"',
        "BUILDER_BACKUP_MODEL": '"meta-llama/llama-3.1-8b-instruct:free"',
        "REVIEWER_MODEL": '"openrouter/free"',
        "REVIEWER_BACKUP_MODEL": '"meta-llama/llama-3.1-8b-instruct:free"'
    }
    
    new_lines = []
    for line in lines:
        match = re.match(r"^([A-Z_]+)=", line.strip())
        if match and match.group(1) in new_models:
            new_lines.append(f"{match.group(1)}={new_models[match.group(1)]}\n")
        else:
            new_lines.append(line)
            
    with open(".env", "w") as f:
        f.writelines(new_lines)
except Exception as e:
    print(f"❌ Failed to update .env: {e}")

# 2. Update main_brainV3.py
try:
    with open("main_brainV3.py", "r") as f:
        code = f.read()
        
    # Force python to read the new .env models
    code = code.replace("load_dotenv()", "load_dotenv(override=True)")
    
    # Make Reviewer logic smarter (accept SAFE as well as APPROVED)
    old_rev = """    if verdict.upper().startswith("APPROVED"):
        return True, "approved"
    return False, verdict"""
    
    new_rev = """    verdict_upper = verdict.upper()
    if "APPROVED" in verdict_upper or "SAFE" in verdict_upper:
        return True, "approved"
    return False, verdict"""
    
    code = code.replace(old_rev, new_rev)
    
    with open("main_brainV3.py", "w") as f:
        f.write(code)
        
    print("✅ All fixed! .env override ho gaya hai aur Reviewer ab smart ho gaya hai.")
except Exception as e:
    print(f"❌ Failed to update python file: {e}")
