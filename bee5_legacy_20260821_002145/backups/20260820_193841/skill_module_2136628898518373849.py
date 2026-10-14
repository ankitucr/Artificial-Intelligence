import re
from collections import Counter

def extract_word_frequencies(text):
    words = re.findall(r'\b\w+\b', text.lower())
    word_counts = Counter(words)
    total_words = len(words)
    word_frequencies = {word: count / total_words for word, count in word_counts.items()}
    return word_frequencies

def calculate_median_word_length(word_frequencies):
    words = list(word_frequencies.keys())
    word_lengths = [len(word) for word in words]
    word_lengths.sort()
    n = len(word_lengths)
    if n % 2 == 1:
        median_length = word_lengths[n // 2]
    else:
        median_length = (word_lengths[n // 2 - 1] + word_lengths[n // 2]) / 2
    return median_length

def main():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    word_frequencies = extract_word_frequencies(text)
    median_length = calculate_median_word_length(word_frequencies)
    print("Word frequencies:", word_frequencies)
    print("Median word length:", median_length)

if __name__ == "__main__":
    main()