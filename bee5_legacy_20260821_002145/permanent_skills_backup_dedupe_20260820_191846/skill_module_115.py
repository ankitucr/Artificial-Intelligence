import statistics

def calculate_statistics(data):
    mean = statistics.mean(data)
    variance = statistics.variance(data)
    standard_deviation = statistics.stdev(data)
    median = statistics.median(data)
    mode = statistics.multimode(data)
    return mean, variance, standard_deviation, median, mode

def generate_random_data(size):
    import random
    return [random.randint(1, 100) for _ in range(size)]

def main():
    data = generate_random_data(10)
    mean, variance, standard_deviation, median, mode = calculate_statistics(data)
    print(f"Mean: {mean}")
    print(f"Variance: {variance}")
    print(f"Standard Deviation: {standard_deviation}")
    print(f"Median: {median}")
    print(f"Mode: {mode}")

if __name__ == "__main__":
    main()