import re
from collections import Counter

def extract_top_n_grams(text: str, n: int, num_grams: int = 10) -> list:
    words = re.findall(r'\b\w+\b', text.lower())
    n_grams = [' '.join(words[i:i+n]) for i in range(len(words)-n+1)]
    n_gram_counts = Counter(n_grams)
    return n_gram_counts.most_common(num_grams)

def calculate_n_gram_frequency(text: str, n: int) -> dict:
    words = re.findall(r'\b\w+\b', text.lower())
    n_grams = [' '.join(words[i:i+n]) for i in range(len(words)-n+1)]
    n_gram_counts = Counter(n_grams)
    return dict(n_gram_counts)

def compare_n_gram_frequencies(text1: str, text2: str, n: int) -> dict:
    n_gram_counts1 = calculate_n_gram_frequency(text1, n)
    n_gram_counts2 = calculate_n_gram_frequency(text2, n)
    common_n_grams = set(n_gram_counts1.keys()) & set(n_gram_counts2.keys())
    frequency_diff = {n_gram: n_gram_counts1[n_gram] - n_gram_counts2[n_gram] for n_gram in common_n_grams}
    return frequency_diff