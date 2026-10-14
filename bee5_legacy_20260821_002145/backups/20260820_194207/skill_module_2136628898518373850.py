import re
from collections import Counter

def extract_word_prefixes(text, prefix_length):
    words = re.findall(r'\b\w+\b', text.lower())
    word_prefixes = [word[:prefix_length] for word in words]
    return word_prefixes

def calculate_word_prefix_frequencies(word_prefixes):
    prefix_counts = Counter(word_prefixes)
    total_prefixes = len(word_prefixes)
    prefix_frequencies = {prefix: count / total_prefixes for prefix, count in prefix_counts.items()}
    return prefix_frequencies

def main():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    word_prefixes = extract_word_prefixes(text, 3)
    prefix_frequencies = calculate_word_prefix_frequencies(word_prefixes)
    print("Word prefix frequencies:", prefix_frequencies)

if __name__ == "__main__":
    main()