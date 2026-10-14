# Sandbox failed: bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

"""Utility to convert a string into a URL-friendly slug."""
import re

SAMPLE_ARGS = {
    "text": "Hello, World! This is a test: 100% awesome."
}

def slugify(text: str) -> str:
    """Convert *text* into a URL‑friendly slug.

    Steps:
    1. Lower‑case the string.
    2. Replace any sequence of non‑alphanumeric characters with a single hyphen.
    3. Strip leading and trailing hyphens.
    """
    # Lower‑case
    lowered = text.lower()
    # Replace non‑alphanumeric sequences with hyphen
    replaced = re.sub(r"[^a-z0-9]+", "-", lowered)
    # Strip hyphens from ends
    slug = replaced.strip("-")
    return slug

def run(args: dict) -> dict:
    """Entry point for the slugify skill.

    Expected *args* format:
        {"text": "<string to slugify>"}

    Returns a dict with the slug under the key ``"slug"``.
    """
    if "text" not in args:
        raise ValueError("Missing required key 'text' in args")
    result_slug = slugify(str(args["text"]))
    return {"slug": result_slug}

if __name__ == "__main__":
    expected = "hello-world-this-is-a-test-100-awesome"
    output = run(SAMPLE_ARGS)
    if output.get("slug") != expected:
        raise AssertionError(f"Expected slug '{expected}', got '{output.get('slug')}'")
    print("All tests passed.")