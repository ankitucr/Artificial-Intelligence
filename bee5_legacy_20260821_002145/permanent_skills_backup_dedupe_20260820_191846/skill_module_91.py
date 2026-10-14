def calculate_statistics(data):
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = variance ** 0.5
    return mean, variance, std_dev

def analyze_text(text):
    words = text.split()
    word_counts = {}
    for word in words:
        if word in word_counts:
            word_counts[word] += 1
        else:
            word_counts[word] = 1
    return word_counts

def find_mode(data):
    counts = {}
    for num in data:
        if num in counts:
            counts[num] += 1
        else:
            counts[num] = 1
    max_count = max(counts.values())
    modes = [num for num, count in counts.items() if count == max_count]
    return modes

def main():
    data = [1, 2, 2, 3, 3, 3, 4, 4, 4, 4]
    mean, variance, std_dev = calculate_statistics(data)
    print(f"Mean: {mean}, Variance: {variance}, Std Dev: {std_dev}")
    text = "this is a sample text"
    word_counts = analyze_text(text)
    print(word_counts)
    mode = find_mode(data)
    print(f"Mode: {mode}")

if __name__ == "__main__":
    main()