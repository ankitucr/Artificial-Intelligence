import re
from collections import Counter

def extract_word_lengths(text):
    words = re.findall(r'\b\w+\b', text.lower())
    word_lengths = [len(word) for word in words]
    return word_lengths

def calculate_word_length_statistics(word_lengths):
    total_length = sum(word_lengths)
    average_length = total_length / len(word_lengths)
    max_length = max(word_lengths)
    min_length = min(word_lengths)
    return average_length, max_length, min_length

def main():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    word_lengths = extract_word_lengths(text)
    average_length, max_length, min_length = calculate_word_length_statistics(word_lengths)
    print("Average word length:", average_length)
    print("Max word length:", max_length)
    print("Min word length:", min_length)

if __name__ == "__main__":
    main()