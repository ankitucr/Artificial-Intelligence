# Reviewer rejected: User Safety: safe

"""Compute readability metrics and lexical diversity for English text."""

import re
from collections import Counter

_SAMPLE_TEXT = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco "
    "laboris nisi ut aliquip ex ea commodo consequat. Duis aute "
    "irure dolor in reprehenderit in voluptate velit esse cillum."
)


def count_syllables(word):
    word = word.lower().strip()
    word = re.sub(r'[^a-z]', '', word)
    if not word:
        return 1
    vowels = "aeiouy"
    count = 0
    prev_was_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_was_wowel:
            count += 1
        prev_was_vowel = is_vowel
    if word.endswith('e') and count > 1:
        count -= 1
    if count < 1:
        count = 1
    return count


def tokenize_sentences(text):
    raw = re.split(r'[.!?]+', text)
    return [s for s in raw if s.strip()]


def tokenize_words(sentence):
    return re.findall(r'[A-Za-z]+', sentence.lower())


def compute_readability(text):
    sentences = tokenize_sentences(text)
    sentence_count = len(sentences)

    words = []
    for sentence in sentences:
        words.extend(tokenize_words(sentence))

    word_count = len(words)
    syllable_count = sum(count_syllables(w) for w in words)

    if sentence_count == 0:
        avg_sentence_length = 0.0
    else:
        avg_sentence_length = word_count / sentence_count

    if word_count == 0:
        avg_syllables_per_word = 0.0
    else:
        avg_syllables_per_word = syllable_count / word_count

    flesch_ease = 206.835 - 1.015 * avg_sentence_length - 846.296 * avg_syllables_per_word
    flesch_grade = 0.39 * avg_sentence_length + 11.8 * avg_syllables_per_word - 15.59

    if word_count > 0:
        complex_words = sum(1 for w in words if count_syllables(w) >= 3)
        gunning_fog = 0.4 * (avg_sentence_length + 100 * (complex_words / word_count))
    else:
        gunning_fog = 0.0

    word_counts = Counter(words)
    types = len(word_counts)
    type_token_ratio = (types / word_count) if word_count else 0.0
    hapax = sum(1 for c in word_counts.values() if c == 1)
    hapax_legomena_ratio = (hapax / word_count) if word_count else 0.0

    return {
        "sentence_count": sentence_count,
        "word_count": word_count,
        "syllable_count": syllable_count,
        "avg_sentence_length": avg_sentence_length,
        "avg_syllables_per_word": avg_syllables_per_word,
        "flesch_reading_ease": flesch_ease,
        "flesch_kincaid_grade": flesch_grade,
        "gunning_fog": gunning_fog,
        "type_token_ratio": type_token_ratio,
        "hapax_legomena_ratio": hapax_legomena_ratio,
    }


def run(args: dict) -> dict:
    text = args.get("text", "")
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    text = text.strip()
    return compute_readability(text)


SAMPLE_ARGS = {"text": _SAMPLE_TEXT}

if __name__ == "__main__":
    _result = run(SAMPLE_ARGS)
    assert isinstance(_result, dict)
    assert _result["word_count"] == len(
        [w for s in tokenize_sentences(SAMPLE_ARGS["text"]) for w in tokenize_words(s)]
    )
    assert _result["sentence_count"] == len(tokenize_sentences(SAMPLE_ARGS["text"]))
    assert _result["syllable_count"] > 0
    assert 0.0 <= _result["type_token_ratio"] <= 1.0
    print("Readability result:", _result)
    print("OK")