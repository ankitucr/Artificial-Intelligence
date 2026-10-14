import re
from collections import Counter

def extract_common_word_endings(text1: str, text2: str) -> list:
    words1 = re.findall(r'\b\w+\b', text1.lower())
    words2 = re.findall(r'\b\w+\b', text2.lower())
    common_words = set(words1) & set(words2)
    endings = []
    for word in common_words:
        for i in range(1, len(word) + 1):
            ending = word[-i:]
            if sum(1 for w in common_words if w.endswith(ending)) > 1:
                endings.append(ending)
    return list(set(endings))

def calculate_ending_frequency(text: str) -> dict:
    words = re.findall(r'\b\w+\b', text.lower())
    endings = {}
    for word in words:
        for i in range(1, len(word) + 1):
            ending = word[-i:]
            if ending in endings:
                endings[ending] += 1
            else:
                endings[ending] = 1
    return endings

def compare_ending_frequencies(text1: str, text2: str) -> dict:
    ending_freq1 = calculate_ending_frequency(text1)
    ending_freq2 = calculate_ending_frequency(text2)
    common_endings = set(ending_freq1.keys()) & set(ending_freq2.keys())
    frequency_diff = {ending: ending_freq1[ending] - ending_freq2[ending] for ending in common_endings}
    return frequency_diff

def main():
    text1 = "This is a sample text."
    text2 = "This is another sample text."
    print(extract_common_word_endings(text1, text2))
    print(calculate_ending_frequency(text1))
    print(compare_ending_frequencies(text1, text2))

if __name__ == "__main__":
    main()