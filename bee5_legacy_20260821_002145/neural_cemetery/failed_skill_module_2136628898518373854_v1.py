# Sandbox failed: bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

"""Slugify a string to a URL‑friendly slug."""
import re

SAMPLE_ARGS = {
    "text": "Hello, World! This is a test: 100% awesome."
}

def slugify(text: str) -> str:
    """Return a URL‑friendly slug for *text*.

    The algorithm lower‑cases the input, replaces any run of non‑alphanumeric
    characters with a single hyphen, and strips leading/trailing hyphens.
    """
    lowered = text.lower()
    replaced = re.sub(r"[^a-z0-9]+", "-", lowered)
    return replaced.strip("-")

def run(args: dict) -> dict:
    """Entry point for the slugify skill.

    Expects ``args`` to contain a ``"text"`` key and returns ``{"slug": ...}``.
    """
    if "text" not in args:
        raise ValueError("Missing required key 'text' in args")
    slug = slugify(str(args["text"]))
    return {"slug": slug}

if __name__ == "__main__":
    expected = "hello-world-this-is-a-test-100-awesome"
    output = run(SAMPLE_ARGS)
    if output.get("slug") != expected:
        raise AssertionError(f"Expected slug '{expected}', got '{output.get('slug')}'")
    print("All tests passed.")