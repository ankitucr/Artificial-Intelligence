import re
from collections import Counter

def extract_common_word_suffixes(text1: str, text2: str) -> list:
    words1 = re.findall(r'\b\w+\b', text1.lower())
    words2 = re.findall(r'\b\w+\b', text2.lower())
    common_words = set(words1) & set(words2)
    suffixes = []
    for word in common_words:
        for i in range(1, len(word) + 1):
            suffix = word[-i:]
            if sum(1 for w in common_words if w.endswith(suffix)) > 1:
                suffixes.append(suffix)
    return list(set(suffixes))

def calculate_suffix_frequency(text: str) -> dict:
    words = re.findall(r'\b\w+\b', text.lower())
    suffix_freq = {}
    for word in words:
        for i in range(1, len(word) + 1):
            suffix = word[-i:]
            if suffix in suffix_freq:
                suffix_freq[suffix] += 1
            else:
                suffix_freq[suffix] = 1
    return suffix_freq

def compare_suffix_frequencies(text1: str, text2: str) -> dict:
    suffix_freq1 = calculate_suffix_frequency(text1)
    suffix_freq2 = calculate_suffix_frequency(text2)
    common_suffixes = set(suffix_freq1.keys()) & set(suffix_freq2.keys())
    frequency_diff = {suffix: suffix_freq1[suffix] - suffix_freq2[suffix] for suffix in common_suffixes}
    return frequency_diff

def main():
    text1 = "This is a sample text."
    text2 = "This is another sample text."
    print(extract_common_word_suffixes(text1, text2))
    print(calculate_suffix_frequency(text1))
    print(compare_suffix_frequencies(text1, text2))

if __name__ == "__main__":
    main()