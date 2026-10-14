import re
from collections import Counter

def extract_most_common_words(text: str, num_words: int = 10) -> list:
    """
    Extract the most common words from the input text.

    Args:
    text (str): The input text.
    num_words (int): The number of most common words to return. Defaults to 10.

    Returns:
    list: A list of tuples containing the most common words and their frequencies.
    """
    words = re.findall(r'\b\w+\b', text.lower())
    word_counts = Counter(words)
    return word_counts.most_common(num_words)

def calculate_word_frequency(text: str) -> dict:
    """
    Calculate the frequency of each word in the input text.

    Args:
    text (str): The input text.

    Returns:
    dict: A dictionary where the keys are the unique words and the values are their frequencies.
    """
    words = re.findall(r'\b\w+\b', text.lower())
    word_counts = Counter(words)
    return dict(word_counts)

def compare_word_frequencies(text1: str, text2: str) -> dict:
    """
    Compare the word frequencies of two input texts.

    Args:
    text1 (str): The first input text.
    text2 (str): The second input text.

    Returns:
    dict: A dictionary where the keys are the unique words and the values are their frequency differences.
    """
    word_counts1 = calculate_word_frequency(text1)
    word_counts2 = calculate_word_frequency(text2)
    common_words = set(word_counts1.keys()) & set(word_counts2.keys())
    frequency_diff = {word: word_counts1[word] - word_counts2[word] for word in common_words}
    return frequency_diff