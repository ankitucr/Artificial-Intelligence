# Calculates word frequencies in a given text and returns a dictionary with word frequencies and a sorted list of the top-N most common words.
import re
from collections import Counter

SAMPLE_ARGS = {
    "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
    "n": 10
}

def extract_words(text):
    """Extracts words from the given text, stripping punctuation and converting to lower case."""
    return re.findall(r'\b\w+\b', text.lower())

def calculate_word_frequencies(words):
    """Calculates word frequencies in the given list of words."""
    word_counts = Counter(words)
    total_words = len(words)
    word_frequencies = {word: count / total_words for word, count in word_counts.items()}
    return word_frequencies

def get_top_n_words(word_frequencies, n):
    """Returns the top-N most common words and their frequencies."""
    top_n_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)[:n]
    return top_n_words

def run(args: dict) -> dict:
    """Calculates word frequencies in the given text and returns a dictionary with word frequencies and a sorted list of the top-N most common words."""
    words = extract_words(args["text"])
    word_frequencies = calculate_word_frequencies(words)
    top_n_words = get_top_n_words(word_frequencies, args["n"])
    return {
        "word_frequencies": word_frequencies,
        "top_n_words": top_n_words
    }

if __name__ == "__main__":
    result = run(SAMPLE_ARGS)
    expected_result = {
        "word_frequencies": {
            'lorem': 1/49, 
            'ipsum': 1/49, 
            'dolor': 1/49, 
            'sit': 1/49, 
            'amet': 2/49, 
            'consectetur': 1/49, 
            'adipiscing': 1/49, 
            'elit': 1/49, 
            'sed': 1/49, 
            'do': 1/49, 
            'eiusmod': 1/49, 
            'tempor': 1/49, 
            'incididunt': 1/49, 
            'ut': 2/49, 
            'labore': 1/49, 
            'et': 2/49, 
            'dolore': 1/49, 
            'magna': 1/49, 
            'aliqua': 1/49, 
            'enim': 1/49, 
            'ad': 1/49, 
            'minim': 1/49, 
            'veniam': 1/49, 
            'quis': 1/49, 
            'nostrud': 1/49, 
            'exercitation': 1/49, 
            'ullamco': 1/49, 
            'laboris': 1/49, 
            'nisi': 1/49, 
            'aliquip': 1/49, 
            'ex': 1/49, 
            'ea': 1/49, 
            'commodo': 1/49, 
            'consequat': 1/49
        },
        "top_n_words": [('ut', 2/49), ('et', 2/49), ('amet', 2/49), ('lorem', 1/49), ('ipsum', 1/49), ('dolor', 1/49), ('sit', 1/49), ('consectetur', 1/49), ('adipiscing', 1/49), ('elit', 1/49)]
    }
    if result!= expected_result:
        raise AssertionError(f"Expected {expected_result} but got {result}")