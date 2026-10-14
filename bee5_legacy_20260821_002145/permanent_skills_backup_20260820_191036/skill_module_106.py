def calculate_statistics(data):
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = variance ** 0.5
    median = sorted(data)[len(data) // 2]
    mode = max(set(data), key=data.count)
    return mean, variance, std_dev, median, mode

def analyze_text(text):
    words = text.split()
    word_freq = {word: words.count(word) for word in set(words)}
    return word_freq

def main():
    data = [1, 2, 3, 4, 5]
    text = "This is a sample text"
    mean, variance, std_dev, median, mode = calculate_statistics(data)
    word_freq = analyze_text(text)
    print("Mean:", mean)
    print("Variance:", variance)
    print("Standard Deviation:", std_dev)
    print("Median:", median)
    print("Mode:", mode)
    print("Word Frequency:", word_freq)

if __name__ == "__main__":
    main()