# Sandbox failed: bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

"""Slugify a string to a URL-friendly slug."""
import re

SAMPLE_ARGS = {
    "text": "Hello, World! This is a test: 100% awesome."
}

def _slugify(text: str) -> str:
    lowered = text.lower()
    replaced = re.sub(r"[^a-z0-9]+", "-", lowered)
    return replaced.strip("-")

def run(args: dict) -> dict:
    if "text" not in args:
        raise ValueError("Missing required key 'text'")
    slug = _slugify(str(args["text"]))
    return {"slug": slug}

if __name__ == "__main__":
    expected = "hello-world-this-is-a-test-100-awesome"
    output = run(SAMPLE_ARGS)
    if output.get("slug") != expected:
        raise AssertionError(f"Expected slug '{expected}', got '{output.get('slug')}'")
    print("All tests passed.")