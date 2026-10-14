import re
from collections import Counter

def extract_word_pairs(text):
    words = re.findall(r'\b\w+\b', text.lower())
    word_pairs = [(words[i], words[i+1]) for i in range(len(words)-1)]
    return word_pairs

def calculate_word_pair_frequencies(word_pairs):
    pair_counts = Counter(word_pairs)
    total_pairs = len(word_pairs)
    pair_frequencies = {pair: count / total_pairs for pair, count in pair_counts.items()}
    return pair_frequencies

def main():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    word_pairs = extract_word_pairs(text)
    pair_frequencies = calculate_word_pair_frequencies(word_pairs)
    print("Word pair frequencies:", pair_frequencies)

if __name__ == "__main__":
    main()