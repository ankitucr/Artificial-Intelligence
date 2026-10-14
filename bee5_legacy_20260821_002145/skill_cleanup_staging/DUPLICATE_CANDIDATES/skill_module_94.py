def calculate_statistics(data):
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = variance ** 0.5
    return mean, variance, std_dev

def find_mode(data):
    frequency = {}
    for num in data:
        frequency[num] = frequency.get(num, 0) + 1
    max_frequency = max(frequency.values())
    modes = [num for num, freq in frequency.items() if freq == max_frequency]
    return modes

def analyze_data(data):
    mean, variance, std_dev = calculate_statistics(data)
    mode = find_mode(data)
    return mean, variance, std_dev, mode

def main():
    data = [1, 2, 3, 4, 5, 5, 5]
    mean, variance, std_dev, mode = analyze_data(data)
    print(f"Mean: {mean}, Variance: {variance}, Std Dev: {std_dev}, Mode: {mode}")

if __name__ == "__main__":
    main()