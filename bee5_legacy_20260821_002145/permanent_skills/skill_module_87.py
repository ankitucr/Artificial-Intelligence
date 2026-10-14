import re
from collections import Counter

def extract_word_ngrams(text: str, n: int) -> list:
    words = re.findall(r'\b\w+\b', text.lower())
    ngrams = []
    for i in range(len(words) - n + 1):
        ngram = tuple(words[i:i+n])
        ngrams.append(ngram)
    return ngrams

def calculate_ngram_frequency(text: str, n: int) -> dict:
    ngrams = extract_word_ngrams(text, n)
    ngram_freq = Counter(ngrams)
    return dict(ngram_freq)

def compare_ngram_frequencies(text1: str, text2: str, n: int) -> dict:
    ngram_freq1 = calculate_ngram_frequency(text1, n)
    ngram_freq2 = calculate_ngram_frequency(text2, n)
    common_ngrams = set(ngram_freq1.keys()) & set(ngram_freq2.keys())
    frequency_diff = {ngram: ngram_freq1[ngram] - ngram_freq2[ngram] for ngram in common_ngrams}
    return frequency_diff

def main():
    text1 = "This is a sample text."
    text2 = "This is another sample text."
    print(extract_word_ngrams(text1, 2))
    print(calculate_ngram_frequency(text1, 2))
    print(compare_ngram_frequencies(text1, text2, 2))

if __name__ == "__main__":
    main()