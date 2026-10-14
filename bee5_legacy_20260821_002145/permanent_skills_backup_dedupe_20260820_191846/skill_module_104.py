def calculate_statistics(data):
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = variance ** 0.5
    median = sorted(data)[len(data) // 2]
    mode = max(set(data), key=data.count)
    return mean, variance, std_dev, median, mode

def process_text(text):
    words = text.split()
    word_freq = {word: words.count(word) for word in set(words)}
    return word_freq

def main():
    data = [1, 2, 3, 4, 5]
    mean, variance, std_dev, median, mode = calculate_statistics(data)
    print(f"Mean: {mean}, Variance: {variance}, Std Dev: {std_dev}, Median: {median}, Mode: {mode}")

    text = "This is a sample text"
    word_freq = process_text(text)
    print(word_freq)

if __name__ == "__main__":
    main()