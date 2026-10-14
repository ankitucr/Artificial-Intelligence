#!/usr/bin/env python3

SKILL_VERSION = "1.0.0"

SKILL_DESCRIPTION = (
    "Cleans and normalizes text by removing extra whitespace "
    "and returns the cleaned text with basic counts."
)

SAMPLE_ARGS = {
    "text": "  Hello   BEE5   world  "
}


def run(args: dict) -> dict:
    if not isinstance(args, dict):
        raise TypeError("args must be a dictionary")

    raw = str(args.get("text", ""))

    cleaned = " ".join(raw.split())

    words = cleaned.split() if cleaned else []

    return {
        "ok": True,
        "skill": "text_cleaner",
        "cleaned_text": cleaned,
        "word_count": len(words),
        "char_count": len(cleaned),
    }


if __name__ == "__main__":
    print(run(SAMPLE_ARGS))
