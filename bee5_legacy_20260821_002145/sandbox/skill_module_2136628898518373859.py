Computes word frequencies in a given text and returns a dictionary of counts alongside a sorted list of the most frequent words, establishing a foundational text analysis tool.
```python
import re
from collections import Counter

SAMPLE_ARGS = {
    "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
}

def extract_words(text):
    words = re.findall(r'\b\w+\b', text.lower())
    return words

def calculate_word_frequencies(words):
    word_counts = Counter(words)
    return word_counts

def get_most_frequent_words(word_counts, n=10):
    most_frequent_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:n]
    return most_frequent_words

def run(args: dict) -> dict:
    text = args["text"]
    words = extract_words(text)
    word_counts = calculate_word_frequencies(words)
    most_frequent_words = get_most_frequent_words(word_counts)
    return {"word_counts": dict(word_counts), "most_frequent_words": most_frequent_words}

if __name__ == "__main__":
    result = run(SAMPLE_ARGS)
    expected_result = {
        "word_counts": {
            'lorem': 1, 'ipsum': 1, 'dolor': 1, 'sit': 1, 'amet': 1, 'consectetur': 1, 'adipiscing': 1, 'elit': 1, 'sed': 1, 
            'do': 1, 'eiusmod': 1, 'tempor': 1, 'incididunt': 1, 'ut': 2, 'labore': 1, 'et': 1, 'dolore': 1, 'magna': 1, 
            'aliqua': 1, 'enim': 1, 'ad': 1, 'minim': 1, 'veniam': 1, 'quis': 1, 'nostrud': 1, 'exercitation': 1, 'ullamco': 1, 
            'laboris': 1, 'nisi': 1, 'aliquip': 1, 'ex': 1, 'ea': 1, 'commodo': 1, 'consequat': 1
        }, 
        "most_frequent_words": [
            ('ut', 2), ('lorem', 1), ('ipsum', 1), ('dolor', 1), ('sit', 1), ('amet', 1), ('consectetur', 1), ('adipiscing', 1), 
            ('elit', 1), ('sed', 1)
        ]
    }
    if result!= expected_result:
        raise AssertionError(f"Expected {expected_result}, got {result}")