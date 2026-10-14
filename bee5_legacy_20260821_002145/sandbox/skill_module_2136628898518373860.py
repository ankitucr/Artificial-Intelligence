"""Analyze the frequency of words in a given text and return a dictionary of word counts and a sorted list of the most frequent words."""
import re
from collections import Counter

SAMPLE_ARGS = {
    "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
    "num_most_frequent": 10
}

def extract_words(text):
    """Extract words from the given text, converting to lowercase and removing punctuation."""
    words = re.findall(r'\b\w+\b', text.lower())
    return words

def calculate_word_frequencies(words):
    """Calculate the frequency of each word in the given list of words."""
    word_counts = Counter(words)
    return dict(word_counts)

def sort_most_frequent_words(word_counts, num_most_frequent):
    """Return a sorted list of the most frequent words in the given dictionary of word counts."""
    most_frequent_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:num_most_frequent]
    return most_frequent_words

def run(args):
    """Analyze the frequency of words in the given text and return a dictionary of word counts and a sorted list of the most frequent words."""
    text = args.get("text", "")
    num_most_frequent = args.get("num_most_frequent", 10)
    words = extract_words(text)
    word_counts = calculate_word_frequencies(words)
    most_frequent_words = sort_most_frequent_words(word_counts, num_most_frequent)
    return {
        "word_counts": word_counts,
        "most_frequent_words": most_frequent_words
    }

if __name__ == "__main__":
    result = run(SAMPLE_ARGS)
    expected_word_counts = {
        'lorem': 1, 'ipsum': 1, 'dolor': 1, 'sit': 1, 'amet': 1, 'consectetur': 1, 'adipiscing': 1, 'elit': 1, 'sed': 1, 'do': 1, 
        'eiusmod': 1, 'tempor': 1, 'incididunt': 1, 'ut': 2, 'labore': 1, 'et': 1, 'dolore': 1, 'magna': 1, 'aliqua': 1, 
        'enim': 1, 'ad': 1, 'minim': 1, 'veniam': 1, 'quis': 1, 'nostrud': 1, 'exercitation': 1, 'ullamco': 1, 'laboris': 1, 
        'nisi': 1, 'aliquip': 1, 'ex': 1, 'ea': 1, 'commodo': 1, 'consequat': 1
    }
    expected_most_frequent_words = [
        ('ut', 2), ('lorem', 1), ('ipsum', 1), ('dolor', 1), ('sit', 1), ('amet', 1), ('consectetur', 1), ('adipiscing', 1), 
        ('elit', 1), ('sed', 1)
    ]
    assert result["word_counts"] == expected_word_counts
    assert result["most_frequent_words"] == expected_most_frequent_words
    print("Test passed!")