def calculate_median(numbers):
    numbers.sort()
    n = len(numbers)
    if n % 2 == 0:
        median = (numbers[n // 2 - 1] + numbers[n // 2]) / 2
    else:
        median = numbers[n // 2]
    return median

def calculate_mode(numbers):
    frequency = {}
    for num in numbers:
        if num in frequency:
            frequency[num] += 1
        else:
            frequency[num] = 1
    max_frequency = max(frequency.values())
    modes = [num for num, freq in frequency.items() if freq == max_frequency]
    return modes

def calculate_statistics(numbers):
    mean = sum(numbers) / len(numbers)
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    std_dev = variance ** 0.5
    median = calculate_median(numbers)
    mode = calculate_mode(numbers)
    return {
        'mean': mean,
        'variance': variance,
        'std_dev': std_dev,
        'median': median,
        'mode': mode
    }

def main():
    numbers = [1, 2, 3, 4, 4, 5, 5, 5]
    stats = calculate_statistics(numbers)
    print("Mean:", stats['mean'])
    print("Variance:", stats['variance'])
    print("Standard Deviation:", stats['std_dev'])
    print("Median:", stats['median'])
    print("Mode:", stats['mode'])

if __name__ == "__main__":
    main()