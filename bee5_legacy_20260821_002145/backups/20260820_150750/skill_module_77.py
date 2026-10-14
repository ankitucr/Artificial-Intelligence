import re
from collections import defaultdict

def extract_sentence_structure(text: str) -> dict:
    """
    Extract the sentence structure from the input text.

    Args:
    text (str): The input text.

    Returns:
    dict: A dictionary where the keys are the sentence lengths and the values are the frequencies.
    """
    sentences = re.split(r'[.!?]\s*', text)
    sentence_lengths = [len(sentence.split()) for sentence in sentences if sentence]
    sentence_structure = defaultdict(int)
    for length in sentence_lengths:
        sentence_structure[length] += 1
    return dict(sentence_structure)

def calculate_average_sentence_length(text: str) -> float:
    """
    Calculate the average sentence length in the input text.

    Args:
    text (str): The input text.

    Returns:
    float: The average sentence length.
    """
    sentences = re.split(r'[.!?]\s*', text)
    sentence_lengths = [len(sentence.split()) for sentence in sentences if sentence]
    return sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0

def compare_sentence_structures(text1: str, text2: str) -> dict:
    """
    Compare the sentence structures of two input texts.

    Args:
    text1 (str): The first input text.
    text2 (str): The second input text.

    Returns:
    dict: A dictionary where the keys are the sentence lengths and the values are the frequency differences.
    """
    sentence_structure1 = extract_sentence_structure(text1)
    sentence_structure2 = extract_sentence_structure(text2)
    common_lengths = set(sentence_structure1.keys()) & set(sentence_structure2.keys())
    frequency_diff = {length: sentence_structure1[length] - sentence_structure2[length] for length in common_lengths}
    return frequency_diff