import re
from collections import Counter

def extract_longest_word(text):
    words = re.findall(r'\b\w+\b', text.lower())
    longest_word = max(words, key=len)
    return longest_word

def calculate_average_word_length(text):
    words = re.findall(r'\b\w+\b', text.lower())
    total_length = sum(len(word) for word in words)
    average_length = total_length / len(words)
    return average_length

def main():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    longest_word = extract_longest_word(text)
    average_length = calculate_average_word_length(text)
    print("Longest word:", longest_word)
    print("Average word length:", average_length)

if __name__ == "__main__":
    main()