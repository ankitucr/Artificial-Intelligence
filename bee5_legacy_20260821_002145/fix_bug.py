import sys

file_name = "main_brainV3.py"
try:
    with open(file_name, "r") as f:
        code = f.read()

    old_block = r"""def get_recent_skills_source(n=CONTEXT_SKILLS) -> str:
    files = sorted(
        DIRS["active_skills"].glob("skill_module_*.py"),
        key=lambda p: int(re.search(r"\d+", p.name).group()),
    )[-n:]
    if not files:"""

    new_block = r"""def get_recent_skills_source(n=CONTEXT_SKILLS) -> str:
    valid_files = []
    for p in DIRS["active_skills"].glob("skill_module_*.py"):
        match = re.search(r"\d+", p.name)
        if match:
            valid_files.append((int(match.group()), p))
    
    valid_files.sort(key=lambda x: x[0])
    files = [p for _, p in valid_files][-n:]

    if not files:"""

    if old_block in code:
        code = code.replace(old_block, new_block)
        with open(file_name, "w") as f:
            f.write(code)
        print("✅ main_brainV3.py successfully update ho gaya hai!")
    else:
        print("⚠️ Exact purana code nahi mila. Ya toh ye pehle hi fix ho chuka hai, ya formatting alag hai.")

except Exception as e:
    print(f"❌ Error aaya: {e}")
