#!/usr/bin/env python3

from collections import Counter

SKILL_VERSION = "1.0.0"

SKILL_DESCRIPTION = (
    "Analyzes cleaned text and returns word count, unique word count, "
    "longest word, and the most frequent words."
)

SAMPLE_ARGS = {
    "text": "hello bee5 hello world"
}


def run(args: dict) -> dict:
    if not isinstance(args, dict):
        raise TypeError("args must be a dictionary")

    text = str(args.get("text", "")).strip()

    words = text.split()

    normalized = [
        word.strip(".,!?;:\"'()[]{}").lower()
        for word in words
    ]

    normalized = [
        word
        for word in normalized
        if word
    ]

    counts = Counter(normalized)

    top_words = [
        {
            "word": word,
            "count": count
        }
        for word, count in counts.most_common(5)
    ]

    longest = max(
        normalized,
        key=len,
        default=""
    )

    return {
        "ok": True,
        "skill": "text_analyzer",
        "text": text,
        "word_count": len(normalized),
        "unique_word_count": len(set(normalized)),
        "longest_word": longest,
        "top_words": top_words,
    }


if __name__ == "__main__":
    print(run(SAMPLE_ARGS))
