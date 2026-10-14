import re
from collections import Counter

def extract_common_prefixes(text1: str, text2: str) -> list:
    words1 = re.findall(r'\b\w+\b', text1.lower())
    words2 = re.findall(r'\b\w+\b', text2.lower())
    common_words = set(words1) & set(words2)
    prefixes = []
    for word in common_words:
        for i in range(1, len(word)):
            prefix = word[:i]
            if sum(1 for w in common_words if w.startswith(prefix)) > 1:
                prefixes.append(prefix)
    return list(set(prefixes))

def calculate_prefix_frequency(text: str) -> dict:
    words = re.findall(r'\b\w+\b', text.lower())
    prefixes = {}
    for word in words:
        for i in range(1, len(word)):
            prefix = word[:i]
            if prefix in prefixes:
                prefixes[prefix] += 1
            else:
                prefixes[prefix] = 1
    return prefixes

def compare_prefix_frequencies(text1: str, text2: str) -> dict:
    prefix_freq1 = calculate_prefix_frequency(text1)
    prefix_freq2 = calculate_prefix_frequency(text2)
    common_prefixes = set(prefix_freq1.keys()) & set(prefix_freq2.keys())
    frequency_diff = {prefix: prefix_freq1[prefix] - prefix_freq2[prefix] for prefix in common_prefixes}
    return frequency_diff