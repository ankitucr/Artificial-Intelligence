def calculate_median(numbers):
    numbers.sort()
    length = len(numbers)
    if length % 2 == 0:
        median = (numbers[length // 2 - 1] + numbers[length // 2]) / 2
    else:
        median = numbers[length // 2]
    return median

def calculate_mode(numbers):
    frequency = {}
    for number in numbers:
        if number in frequency:
            frequency[number] += 1
        else:
            frequency[number] = 1
    max_frequency = max(frequency.values())
    modes = [number for number, freq in frequency.items() if freq == max_frequency]
    return modes

def calculate_statistics(numbers):
    mean = sum(numbers) / len(numbers)
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    standard_deviation = variance ** 0.5
    median = calculate_median(numbers)
    mode = calculate_mode(numbers)
    return {
        'mean': mean,
        'variance': variance,
        'standard_deviation': standard_deviation,
        'median': median,
        'mode': mode
    }

def main():
    numbers = [1, 2, 3, 4, 4, 5, 5, 5]
    stats = calculate_statistics(numbers)
    print("Mean:", stats['mean'])
    print("Variance:", stats['variance'])
    print("Standard Deviation:", stats['standard_deviation'])
    print("Median:", stats['median'])
    print("Mode:", stats['mode'])

if __name__ == "__main__":
    main()