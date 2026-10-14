import re
from collections import Counter

def extract_word_suffixes(text, suffix_length):
    words = re.findall(r'\b\w+\b', text.lower())
    word_suffixes = [word[-suffix_length:] for word in words if len(word) >= suffix_length]
    return word_suffixes

def calculate_word_suffix_frequencies(word_suffixes):
    suffix_counts = Counter(word_suffixes)
    total_suffixes = len(word_suffixes)
    suffix_frequencies = {suffix: count / total_suffixes for suffix, count in suffix_counts.items()}
    return suffix_frequencies

def main():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    word_suffixes = extract_word_suffixes(text, 3)
    suffix_frequencies = calculate_word_suffix_frequencies(word_suffixes)
    print("Word suffix frequencies:", suffix_frequencies)

if __name__ == "__main__":
    main()