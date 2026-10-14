import re
from collections import Counter

def extract_sentence_lengths(text):
    sentences = re.split(r'[.!?]', text)
    sentence_lengths = [len(sentence.split()) for sentence in sentences if sentence]
    return sentence_lengths

def calculate_sentence_length_statistics(sentence_lengths):
    if not sentence_lengths:
        return 0, 0, 0
    total_length = sum(sentence_lengths)
    average_length = total_length / len(sentence_lengths)
    max_length = max(sentence_lengths)
    min_length = min(sentence_lengths)
    return average_length, max_length, min_length

def main():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    sentence_lengths = extract_sentence_lengths(text)
    average_length, max_length, min_length = calculate_sentence_length_statistics(sentence_lengths)
    print("Average sentence length:", average_length)
    print("Max sentence length:", max_length)
    print("Min sentence length:", min_length)

if __name__ == "__main__":
    main()