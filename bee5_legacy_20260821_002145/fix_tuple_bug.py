import re

with open("main_brainV3.py", "r") as f:
    code = f.read()

# Completely rewrite get_recent_skills to be 100% bulletproof against tuple/path mixups
old_block_start = "def get_recent_skills() -> str:"
# Let's find and replace the whole function cleanly
if old_block_start in code:
    # Find the function definition and replace it entirely
    parts = code.split(old_block_start)
    # Get everything before the function
    pre = parts[0]
    # Find where the function ends (next function definition or end of file)
    func_body_and_rest = parts[1]
    
    # Next function starts with 'def ' or we can just replace up to the next def
    next_defs = func_body_and_rest.split("\ndef ")
    new_func = """def get_recent_skills() -> str:
    sys.path.insert(0, str(DIRS["active"]))
    paths = list(DIRS["active"].glob("skill_module_*.py"))
    if not paths: return "No existing skills yet."
    
    valid_paths = []
    for p in paths:
        m = re.search(r"\\d+", p.name)
        if m:
            valid_paths.append((int(m.group()), p))
    valid_paths.sort(key=lambda x: x[0])
    
    recent_files = [p for _, p in valid_paths[-4:]]
    return "\\n\\n".join(f"# --- File: {p.name} ---\\n{p.read_text()}\\n" for p in recent_files)

"""
    # Reassemble code
    rest = "\ndef ".join(next_defs[1:]) if len(next_defs) > 1 else ""
    code = pre + new_func + ("def " + rest if rest else "")
    
    with open("main_brainV3.py", "w") as f:
        f.write(code)
    print("✅ get_recent_skills function completely rewritten and fixed!")
else:
    print("❌ Could not find get_recent_skills in main_brainV3.py")
