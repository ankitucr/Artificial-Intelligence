import re
from collections import Counter

def extract_word_pattern(text, pattern):
    words = re.findall(pattern, text.lower())
    return words

def calculate_word_pattern_frequency(text, pattern):
    words = extract_word_pattern(text, pattern)
    word_counts = Counter(words)
    total_words = len(words)
    word_frequencies = {word: count / total_words for word, count in word_counts.items()}
    return word_frequencies

def main():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    pattern = r'\b\w{3,}\b'  # words with 3 or more characters
    word_frequencies = calculate_word_pattern_frequency(text, pattern)
    print("Word frequencies:", word_frequencies)

if __name__ == "__main__":
    main()