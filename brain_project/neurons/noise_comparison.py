import numpy as np
import matplotlib.pyplot as plt
import os

def run_network(noise_level, time_steps=4000):
    num_patterns = 10
    num_neurons = num_patterns * 3
    input_idx = list(range(0, num_patterns))
    hidden_idx = list(range(num_patterns, num_patterns*2))
    output_idx = list(range(num_patterns*2, num_patterns*3))

    threshold = 1.0
    reset_potential = 0.0
    leak_rate = 0.05
    block_size = 40
    learning_rate = 0.05
    decay_rate = 0.03
    max_weight = 2.0
    min_weight = 0.1

    weights = np.zeros((num_neurons, num_neurons))
    for i in range(num_patterns):
        for h in range(num_patterns):
            weights[input_idx[i]][hidden_idx[h]] = 1.15 if i == h else 0.5
    for h in range(num_patterns):
        for o in range(num_patterns):
            weights[hidden_idx[h]][output_idx[o]] = 1.15 if h == o else 0.5

    connection_mask = weights > 0
    membrane_potential = np.zeros(num_neurons)
    correct_output_count = 0
    total_output_spikes = 0
    last_fired = np.full(num_neurons, -100)

    for t in range(time_steps):
        pattern = (t // block_size) % num_patterns
        external_input = np.zeros(num_neurons)
        external_input[input_idx[pattern]] = 0.08

        noise = np.random.uniform(-noise_level, noise_level, num_neurons)
        membrane_potential += noise

        membrane_potential -= leak_rate * membrane_potential
        membrane_potential += external_input

        fired = membrane_potential >= threshold
        fired_idx = np.where(fired)[0]

        if len(fired_idx) > 0:
            membrane_potential[fired_idx] = reset_potential
            last_fired[fired_idx] = t

            for idx in fired_idx:
                if idx in output_idx:
                    total_output_spikes += 1
                    if idx == output_idx[pattern]:
                        correct_output_count += 1

            incoming_signal = weights[fired_idx, :].sum(axis=0)
            membrane_potential += incoming_signal

            for j in fired_idx:
                connected_i = np.where(connection_mask[:, j])[0]
                recently_fired = (0 <= (t - last_fired[connected_i])) & ((t - last_fired[connected_i]) <= 5) & (last_fired[connected_i] != -100)
                weights[connected_i[recently_fired], j] = np.minimum(max_weight, weights[connected_i[recently_fired], j] + learning_rate)
                weights[connected_i[~recently_fired], j] = np.maximum(min_weight, weights[connected_i[~recently_fired], j] - decay_rate)

    accuracy = (correct_output_count / total_output_spikes * 100) if total_output_spikes > 0 else 0
    return accuracy

# ---- Test multiple noise levels ----
noise_levels = [0.0, 0.02, 0.05, 0.08, 0.12, 0.16, 0.20, 0.25]
accuracies = []

print("Testing different noise levels...\n")
for nl in noise_levels:
    acc = run_network(nl)
    accuracies.append(acc)
    print(f"Noise = {nl:.2f}  ->  Accuracy = {acc:.1f}%")

# ---- Graph ----
plt.figure(figsize=(9, 5))
plt.plot(noise_levels, accuracies, marker='o', color='blue', linewidth=2)
plt.xlabel("Noise Level")
plt.ylabel("Accuracy (%)")
plt.title("Network Robustness: Accuracy vs Noise Level")
plt.grid(True, alpha=0.3)
plt.ylim(0, 105)

save_path = os.path.expanduser("~/storage/pictures/brain_project/noise_comparison.png")
plt.savefig(save_path)
print(f"\nGraph saved: {save_path}")
