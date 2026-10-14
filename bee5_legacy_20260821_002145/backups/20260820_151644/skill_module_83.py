import re
from collections import Counter

def extract_common_word_lengths(text1: str, text2: str) -> list:
    words1 = re.findall(r'\b\w+\b', text1.lower())
    words2 = re.findall(r'\b\w+\b', text2.lower())
    common_words = set(words1) & set(words2)
    lengths = []
    for word in common_words:
        length = len(word)
        if sum(1 for w in common_words if len(w) == length) > 1:
            lengths.append(length)
    return list(set(lengths))

def calculate_length_frequency(text: str) -> dict:
    words = re.findall(r'\b\w+\b', text.lower())
    length_freq = {}
    for word in words:
        length = len(word)
        if length in length_freq:
            length_freq[length] += 1
        else:
            length_freq[length] = 1
    return length_freq

def compare_length_frequencies(text1: str, text2: str) -> dict:
    length_freq1 = calculate_length_frequency(text1)
    length_freq2 = calculate_length_frequency(text2)
    common_lengths = set(length_freq1.keys()) & set(length_freq2.keys())
    frequency_diff = {length: length_freq1[length] - length_freq2[length] for length in common_lengths}
    return frequency_diff

def main():
    text1 = "This is a sample text."
    text2 = "This is another sample text."
    print(extract_common_word_lengths(text1, text2))
    print(calculate_length_frequency(text1))
    print(compare_length_frequencies(text1, text2))

if __name__ == "__main__":
    main()