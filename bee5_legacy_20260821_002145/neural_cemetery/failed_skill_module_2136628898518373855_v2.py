# Reviewer rejected: REJECTED: The self-ॕine does not閎-test for correctness (the assertion `len(result["trigram_frequencies"]) > 0` is too weak to catch logic errors in frequency calculation).

Computes the frequencies of three-character sequences in a given text.
```python
def extract_character_trigrams(text):
    """
    Extracts all three-character sequences from the given text.
    
    Args:
        text (str): The input text.
    
    Returns:
        list: A list of three-character sequences.
    """
    cleaned_text = ''.join(filter(str.isalnum, text)).lower()
    trigrams = [cleaned_text[i:i+3] for i in range(max(0, len(cleaned_text)-2))]
    return trigrams

def calculate_trigram_frequencies(trigrams):
    """
    Calculates the frequencies of the given three-character sequences.
    
    Args:
        trigrams (list): A list of three-character sequences.
    
    Returns:
        dict: A dictionary with trigrams as keys and their frequencies as values.
    """
    trigram_counts = {}
    for trigram in trigrams:
        if trigram in trigram_counts:
            trigram_counts[trigram] += 1
        else:
            trigram_counts[trigram] = 1
    total_trigrams = len(trigrams)
    if total_trigrams == 0:
        return {}
    trigram_frequencies = {trigram: count / total_trigrams for trigram, count in trigram_counts.items()}
    return trigram_frequencies

SAMPLE_ARGS = {
    "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
}

def run(args: dict) -> dict:
    """
    Computes the frequencies of three-character sequences in the given text.
    
    Args:
        args (dict): A dictionary with the input text.
    
    Returns:
        dict: A dictionary with the trigram frequencies.
    """
    text = args.get("text", "")
    trigrams = extract_character_trigrams(text)
    trigram_frequencies = calculate_trigram_frequencies(trigrams)
    return {"trigram_frequencies": trigram_frequencies}

if __name__ == "__main__":
    result = run(SAMPLE_ARGS)
    if len(''.join(filter(str.isalnum, SAMPLE_ARGS["text"]))) <= 2:
        assert len(result["trigram_frequencies"]) == 0
    else:
        assert len(result["trigram_frequencies"]) > 0