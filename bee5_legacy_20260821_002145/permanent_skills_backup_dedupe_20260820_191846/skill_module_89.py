def calculate_statistics(data):
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = variance ** 0.5
    return mean, variance, std_dev

def analyze_text(text):
    words = text.split()
    word_freq = {}
    for word in words:
        if word in word_freq:
            word_freq[word] += 1
        else:
            word_freq[word] = 1
    return word_freq

def find_common_prefix(words):
    if not words:
        return ""
    prefix = words[0]
    for word in words[1:]:
        while not word.startswith(prefix):
            prefix = prefix[:-1]
    return prefix

def main():
    data = [1, 2, 3, 4, 5]
    mean, variance, std_dev = calculate_statistics(data)
    print(f"Mean: {mean}, Variance: {variance}, Std Dev: {std_dev}")

    text = "this is a sample text"
    word_freq = analyze_text(text)
    print(word_freq)

    words = ["this", "that", "those"]
    prefix = find_common_prefix(words)
    print(prefix)

if __name__ == "__main__":
    main()