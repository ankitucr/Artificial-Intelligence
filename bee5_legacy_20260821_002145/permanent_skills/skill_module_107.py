def calculate_statistics(data):
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = variance ** 0.5
    median = sorted(data)[len(data) // 2]
    mode = max(set(data), key=data.count)
    return mean, variance, std_dev, median, mode

def word_frequency(text):
    words = text.split()
    frequency = {}
    for word in words:
        if word in frequency:
            frequency[word] += 1
        else:
            frequency[word] = 1
    return frequency

def process_text(text, data):
    mean, variance, std_dev, median, mode = calculate_statistics(data)
    frequency = word_frequency(text)
    return mean, variance, std_dev, median, mode, frequency

def main():
    text = "This is a sample text"
    data = [1, 2, 3, 4, 5]
    mean, variance, std_dev, median, mode, frequency = process_text(text, data)
    print("Mean:", mean)
    print("Variance:", variance)
    print("Standard Deviation:", std_dev)
    print("Median:", median)
    print("Mode:", mode)
    print("Word Frequency:", frequency)

if __name__ == "__main__":
    main()