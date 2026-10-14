import re

with open("main_brainV3.py", "r") as f:
    code = f.read()

# Safe regex replacement for sorting files without crashing on NoneType
target_line = 'files = sorted(DIRS["active"].glob("skill_module_*.py"), key=lambda p: int(re.search(r"\\d+", p.name).group()))'

safe_replacement = """files = []
    for p in DIRS["active"].glob("skill_module_*.py"):
        m = re.search(r"\\d+", p.name)
        if m:
            files.append((int(m.group()), p))
    files.sort(key=lambda x: x[0])"""

if target_line in code:
    code = code.replace(target_line, safe_replacement)
    with open("main_brainV3.py", "w") as f:
        f.write(code)
    print("✅ Successfully patched main_brainV3.py!")
else:
    print("⚠️ Target line already modified or not found. Let's check manually.")
