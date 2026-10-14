def calculate_statistics(data):
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    standard_deviation = variance ** 0.5
    median = sorted(data)[len(data) // 2] if len(data) % 2 else (sorted(data)[len(data) // 2 - 1] + sorted(data)[len(data) // 2]) / 2
    mode = max(set(data), key=data.count)
    return mean, variance, standard_deviation, median, mode

def process_text(text):
    words = text.split()
    word_counts = {word: words.count(word) for word in set(words)}
    return word_counts

def main():
    data = [1, 2, 3, 4, 5]
    mean, variance, standard_deviation, median, mode = calculate_statistics(data)
    print(f"Mean: {mean}, Variance: {variance}, Standard Deviation: {standard_deviation}, Median: {median}, Mode: {mode}")
    text = "This is a test sentence with multiple words"
    word_counts = process_text(text)
    print(word_counts)

if __name__ == "__main__":
    main()