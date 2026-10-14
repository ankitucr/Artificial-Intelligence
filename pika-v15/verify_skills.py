"""
verify_skills.py — sanity-checks that Pika's grown skills are REAL working
code, not just placeholder text that happens to import without crashing.

Run:
    python verify_skills.py
"""

import importlib.util
import inspect
import os

SKILLS_FILE = "src/skills/pika_skills.py"


def load_skills_module():
    spec = importlib.util.spec_from_file_location("pika_skills", SKILLS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    if not os.path.exists(SKILLS_FILE):
        print(f"❌ {SKILLS_FILE} not found.")
        return

    module = load_skills_module()
    functions = [
        (name, obj) for name, obj in inspect.getmembers(module, inspect.isfunction)
    ]

    print(f"📦 Loaded {SKILLS_FILE} — {len(functions)} functions found.\n")

    # Real functional tests for a few commonly-generated skill names, using
    # ACTUAL inputs and checking the ACTUAL output — not just "did it crash".
    manual_tests = {
        "slugify": (("Hello World! 123",), lambda r: isinstance(r, str) and " " not in r),
        "flatten_dict": (({"a": {"b": 1, "c": 2}},), lambda r: isinstance(r, dict) and len(r) >= 2),
        "deep_merge": (({"a": 1}, {"b": 2}), lambda r: isinstance(r, dict) and "a" in r and "b" in r),
        "clamp": ((15, 0, 10), lambda r: r == 10),
        "is_valid_email": (("test@example.com",), lambda r: r is True),
        "safe_json_load": (('{"x": 1}',), lambda r: r == {"x": 1} or (isinstance(r, dict) and r.get("x") == 1)),
        "chunked": ((list(range(10)), 3), lambda r: len(list(r)) == 4),
        "unique_everseen": (([1, 1, 2, 2, 3],), lambda r: list(r) == [1, 2, 3]),
    }

    ran = 0
    for name, (args, check) in manual_tests.items():
        fn = dict(functions).get(name)
        if fn is None:
            continue
        ran += 1
        try:
            result = fn(*args)
            ok = check(result)
            icon = "✅" if ok else "⚠️ "
            print(f"{icon} {name}{args} -> {result!r}  {'(correct)' if ok else '(UNEXPECTED — check manually)'}")
        except Exception as e:
            print(f"❌ {name}{args} raised {type(e).__name__}: {e}")

    if ran == 0:
        print("ℹ️  None of the pre-written test cases matched function names in your file — "
              "that's fine, it just means this script doesn't know how to test THESE particular "
              "skills automatically. Use the sed/grep commands to read them manually instead.")

    print(f"\n📋 Full function list:")
    for name, fn in functions:
        sig = inspect.signature(fn)
        doc = (inspect.getdoc(fn) or "no docstring").split("\n")[0]
        print(f"   - {name}{sig}  — {doc}")


if __name__ == "__main__":
    main()
