import statistics

def calculate_median(numbers):
    return statistics.median(numbers)

def calculate_mode(numbers):
    frequency = {}
    for num in numbers:
        frequency[num] = frequency.get(num, 0) + 1
    max_frequency = max(frequency.values())
    modes = [num for num, freq in frequency.items() if freq == max_frequency]
    return modes

def calculate_statistics(numbers):
    mean = sum(numbers) / len(numbers)
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    std_dev = variance ** 0.5
    median = calculate_median(numbers)
    mode = calculate_mode(numbers)
    return mean, variance, std_dev, median, mode

def main():
    numbers = [1, 2, 3, 4, 5]
    mean, variance, std_dev, median, mode = calculate_statistics(numbers)
    print("Mean:", mean)
    print("Variance:", variance)
    print("Standard Deviation:", std_dev)
    print("Median:", median)
    print("Mode:", mode)

if __name__ == "__main__":
    main()