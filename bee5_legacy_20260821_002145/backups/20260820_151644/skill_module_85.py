import re
from collections import Counter

def extract_word_prefixes(text: str) -> list:
    words = re.findall(r'\b\w+\b', text.lower())
    prefixes = []
    for word in words:
        for i in range(1, len(word) + 1):
            prefix = word[:i]
            prefixes.append(prefix)
    return prefixes

def calculate_prefix_frequency(text: str) -> dict:
    prefixes = extract_word_prefixes(text)
    prefix_freq = Counter(prefixes)
    return dict(prefix_freq)

def compare_prefix_frequencies(text1: str, text2: str) -> dict:
    prefix_freq1 = calculate_prefix_frequency(text1)
    prefix_freq2 = calculate_prefix_frequency(text2)
    common_prefixes = set(prefix_freq1.keys()) & set(prefix_freq2.keys())
    frequency_diff = {prefix: prefix_freq1[prefix] - prefix_freq2[prefix] for prefix in common_prefixes}
    return frequency_diff

def main():
    text1 = "This is a sample text."
    text2 = "This is another sample text."
    print(extract_word_prefixes(text1))
    print(calculate_prefix_frequency(text2))
    print(compare_prefix_frequencies(text1, text2))

if __name__ == "__main__":
    main()