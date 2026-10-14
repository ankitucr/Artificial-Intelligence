import re
from collections import Counter

def extract_ngrams(text, n):
    words = re.findall(r'\b\w+\b', text.lower())
    ngrams = [tuple(words[i:i+n]) for i in range(len(words)-n+1)]
    return ngrams

def calculate_ngram_frequencies(ngrams):
    ngram_counts = Counter(ngrams)
    total_ngrams = len(ngrams)
    ngram_frequencies = {ngram: count / total_ngrams for ngram, count in ngram_counts.items()}
    return ngram_frequencies

def main():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    ngrams = extract_ngrams(text, 3)
    ngram_frequencies = calculate_ngram_frequencies(ngrams)
    print("Ngram frequencies:", ngram_frequencies)

if __name__ == "__main__":
    main()