import re
from collections import Counter

def extract_most_common_words(text, num_words):
    words = re.findall(r'\b\w+\b', text.lower())
    word_counts = Counter(words)
    most_common_words = word_counts.most_common(num_words)
    return most_common_words

def calculate_word_frequency(text):
    words = re.findall(r'\b\w+\b', text.lower())
    word_counts = Counter(words)
    total_words = len(words)
    word_frequencies = {word: count / total_words for word, count in word_counts.items()}
    return word_frequencies

def main():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    most_common_words = extract_most_common_words(text, 5)
    word_frequencies = calculate_word_frequency(text)
    print("Most common words:", most_common_words)
    print("Word frequencies:", word_frequencies)

if __name__ == "__main__":
    main()