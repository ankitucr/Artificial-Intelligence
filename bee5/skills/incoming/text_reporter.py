#!/usr/bin/env python3

SKILL_VERSION = "1.0.0"

SKILL_DESCRIPTION = (
    "Builds a concise structured report from cleaned text analysis."
)

SAMPLE_ARGS = {
    "text": "Hello BEE5 world",
    "word_count": 3,
    "unique_word_count": 3,
    "longest_word": "Hello",
}


def run(args: dict) -> dict:
    if not isinstance(args, dict):
        raise TypeError("args must be a dictionary")

    text = str(args.get("text", ""))

    word_count = int(
        args.get("word_count", 0)
    )

    unique_word_count = int(
        args.get("unique_word_count", 0)
    )

    longest_word = str(
        args.get("longest_word", "")
    )

    report = (
        f"Text contains {word_count} words and "
        f"{unique_word_count} unique words. "
        f"Longest word: {longest_word or 'none'}."
    )

    return {
        "ok": True,
        "skill": "text_reporter",
        "text": text,
        "word_count": word_count,
        "unique_word_count": unique_word_count,
        "longest_word": longest_word,
        "report": report,
    }


if __name__ == "__main__":
    print(run(SAMPLE_ARGS))
