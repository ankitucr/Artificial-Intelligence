def calculate_statistics(data):
    if not data:
        return None
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = variance ** 0.5
    return {
        'mean': mean,
        'variance': variance,
        'std_dev': std_dev
    }

def parse_text(text):
    words = text.split()
    word_freq = {}
    for word in words:
        if word in word_freq:
            word_freq[word] += 1
        else:
            word_freq[word] = 1
    return word_freq

def detect_pattern(sequence):
    if len(sequence) < 2:
        return None
    pattern = []
    for i in range(len(sequence) - 1):
        if sequence[i] == sequence[i + 1]:
            pattern.append('equal')
        elif sequence[i] < sequence[i + 1]:
            pattern.append('increasing')
        else:
            pattern.append('decreasing')
    return pattern

def validate_input(data):
    if not isinstance(data, list):
        return False
    for item in data:
        if not isinstance(item, (int, float)):
            return False
    return True

def main():
    data = [1, 2, 3, 4, 5]
    stats = calculate_statistics(data)
    print(stats)
    text = "this is a sample text"
    word_freq = parse_text(text)
    print(word_freq)
    sequence = [1, 2, 3, 4, 5]
    pattern = detect_pattern(sequence)
    print(pattern)
    valid = validate_input(data)
    print(valid)

if __name__ == "__main__":
    main()