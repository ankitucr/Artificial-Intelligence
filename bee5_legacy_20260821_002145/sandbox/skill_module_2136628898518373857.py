Computes normalized frequencies of overlapping character trigrams in a given text, returning a dictionary mapping each trigram to its probability.
```python
SAMPLE_ARGS = {"text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit."}

def extract_character_trigrams(text, trigram_length=3):
    trigrams = [text[i:i+trigram_length] for i in range(len(text)-trigram_length+1)]
    return trigrams

def calculate_trigram_frequencies(trigrams):
    trigram_counts = {}
    for trigram in trigrams:
        if trigram in trigram_counts:
            trigram_counts[trigram] += 1
        else:
            trigram_counts[trigram] = 1
    total_trigrams = len(trigrams)
    trigram_frequencies = {trigram: count / total_trigrams for trigram, count in trigram_counts.items()}
    return trigram_frequencies

def validate_input(text):
    return len(text) >= 3

def run(args: dict) -> dict:
    text = args["text"]
    if not validate_input(text):
        return {}
    trigrams = extract_character_trigrams(text)
    trigram_frequencies = calculate_trigram_frequencies(trigrams)
    return trigram_frequencies

if __name__ == "__main__":
    result = run(SAMPLE_ARGS)
    expected_result = {}
    trigrams = extract_character_trigrams(SAMPLE_ARGS["text"])
    for trigram in set(trigrams):
        count = trigrams.count(trigram)
        expected_result[trigram] = count / len(trigrams)
    assert result == expected_result, "Result does not match expected result"
    print("Test passed.")