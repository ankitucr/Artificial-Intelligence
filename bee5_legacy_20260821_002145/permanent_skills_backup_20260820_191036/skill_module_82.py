import re
from collections import Counter

def extract_word_chains(text: str) -> list:
    words = re.findall(r'\b\w+\b', text.lower())
    word_chains = []
    for i in range(len(words) - 1):
        if words[i][-1] == words[i + 1][0]:
            word_chains.append((words[i], words[i + 1]))
    return word_chains

def calculate_chain_frequency(text: str) -> dict:
    word_chains = extract_word_chains(text)
    chain_freq = Counter(word_chains)
    return dict(chain_freq)

def compare_chain_frequencies(text1: str, text2: str) -> dict:
    chain_freq1 = calculate_chain_frequency(text1)
    chain_freq2 = calculate_chain_frequency(text2)
    common_chains = set(chain_freq1.keys()) & set(chain_freq2.keys())
    frequency_diff = {chain: chain_freq1[chain] - chain_freq2[chain] for chain in common_chains}
    return frequency_diff

def main():
    text1 = "This is a sample text."
    text2 = "This is another sample text."
    print(extract_word_chains(text1))
    print(calculate_chain_frequency(text2))
    print(compare_chain_frequencies(text1, text2))

if __name__ == "__main__":
    main()