import re
from collections import Counter

def extract_common_word_pairs(text1: str, text2: str) -> list:
    words1 = re.findall(r'\b\w+\b', text1.lower())
    words2 = re.findall(r'\b\w+\b', text2.lower())
    common_words = set(words1) & set(words2)
    pairs = []
    for word in common_words:
        for other_word in common_words:
            if word != other_word:
                pair = tuple(sorted([word, other_word]))
                pairs.append(pair)
    return list(set(pairs))

def calculate_pair_frequency(text: str) -> dict:
    words = re.findall(r'\b\w+\b', text.lower())
    pairs = []
    for i in range(len(words) - 1):
        pair = tuple(sorted([words[i], words[i + 1]]))
        pairs.append(pair)
    pair_freq = Counter(pairs)
    return dict(pair_freq)

def compare_pair_frequencies(text1: str, text2: str) -> dict:
    pair_freq1 = calculate_pair_frequency(text1)
    pair_freq2 = calculate_pair_frequency(text2)
    common_pairs = set(pair_freq1.keys()) & set(pair_freq2.keys())
    frequency_diff = {pair: pair_freq1[pair] - pair_freq2[pair] for pair in common_pairs}
    return frequency_diff

def main():
    text1 = "This is a sample text."
    text2 = "This is another sample text."
    print(extract_common_word_pairs(text1, text2))
    print(calculate_pair_frequency(text1))
    print(compare_pair_frequencies(text1, text2))

if __name__ == "__main__":
    main()