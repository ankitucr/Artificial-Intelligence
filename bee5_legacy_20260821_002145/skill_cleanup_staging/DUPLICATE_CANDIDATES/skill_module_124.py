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
    return mean, variance, standard_deviation, median, mode

def main():
    numbers = [1, 2, 3, 4, 5]
    mean, variance, standard_deviation, median, mode = calculate_statistics(numbers)
    print("Mean:", mean)
    print("Variance:", variance)
    print("Standard Deviation:", standard_deviation)
    print("Median:", median)
    print("Mode:", mode)

if __name__ == "__main__":
    main()