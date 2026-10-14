def calculate_statistics(data):
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    standard_deviation = variance ** 0.5
    median = sorted(data)[len(data) // 2] if len(data) % 2!= 0 else (sorted(data)[len(data) // 2 - 1] + sorted(data)[len(data) // 2]) / 2
    mode = max(set(data), key=data.count)
    return mean, variance, standard_deviation, median, mode

def analyze_text(text):
    words = text.split()
    word_frequency = {word: words.count(word) for word in set(words)}
    return word_frequency

def main():
    data = [1, 2, 3, 4, 5]
    mean, variance, standard_deviation, median, mode = calculate_statistics(data)
    print(f"Mean: {mean}")
    print(f"Variance: {variance}")
    print(f"Standard Deviation: {standard_deviation}")
    print(f"Median: {median}")
    print(f"Mode: {mode}")

    text = "This is a sample text"
    word_frequency = analyze_text(text)
    print(f"Word Frequency: {word_frequency}")

if __name__ == "__main__":
    main()