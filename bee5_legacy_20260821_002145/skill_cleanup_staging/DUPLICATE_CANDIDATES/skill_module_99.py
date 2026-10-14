import statistics

def calculate_statistics(data):
    mean = statistics.mean(data)
    variance = statistics.variance(data)
    std_dev = statistics.stdev(data)
    mode = statistics.mode(data)
    return mean, variance, std_dev, mode

def analyze_text(text):
    words = text.split()
    word_freq = {}
    for word in words:
        if word in word_freq:
            word_freq[word] += 1
        else:
            word_freq[word] = 1
    return word_freq

def main():
    data = [1, 2, 3, 4, 5]
    mean, variance, std_dev, mode = calculate_statistics(data)
    print(f"Mean: {mean}, Variance: {variance}, Std Dev: {std_dev}, Mode: {mode}")
    
    text = "This is a sample text"
    word_freq = analyze_text(text)
    print(word_freq)

if __name__ == "__main__":
    main()