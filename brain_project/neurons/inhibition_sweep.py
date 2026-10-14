import numpy as np
import matplotlib.pyplot as plt
import os

def run_network(inhibition_strength, noise_level=0.08, train_steps=4000, test_steps=2000):
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
    last_fired = np.full(num_neurons, -100)

    def inhibit(fired_idx, layer_idx, mp):
        layer_fired = [i for i in fired_idx if i in layer_idx]
        if len(layer_fired) > 0:
            for other in layer_idx:
                if other not in layer_fired:
                    mp[other] -= inhibition_strength
        return mp

    correct = 0
    total_output = 0

    for t in range(train_steps + test_steps):
        learning_on = t < train_steps
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

            membrane_potential[:] = inhibit(fired_idx, hidden_idx, membrane_potential)
            membrane_potential[:] = inhibit(fired_idx, output_idx, membrane_potential)

            if not learning_on:
                for idx in fired_idx:
                    if idx in output_idx:
                        total_output += 1
                        if idx == output_idx[pattern]:
                            correct += 1

            incoming_signal = weights[fired_idx, :].sum(axis=0)
            membrane_potential += incoming_signal

            if learning_on:
                for j in fired_idx:
                    connected_i = np.where(connection_mask[:, j])[0]
                    recently = (0 <= (t - last_fired[connected_i])) & ((t - last_fired[connected_i]) <= 5) & (last_fired[connected_i] != -100)
                    weights[connected_i[recently], j] = np.minimum(max_weight, weights[connected_i[recently], j] + learning_rate)
                    weights[connected_i[~recently], j] = np.maximum(min_weight, weights[connected_i[~recently], j] - decay_rate)

    accuracy = (correct / total_output * 100) if total_output > 0 else 0
    return accuracy

# ---- Sweep test ----
inhibition_values = [0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 15.0]
accuracies = []

print("Testing different inhibition strengths (noise=0.08)...\n")
for inh in inhibition_values:
    acc = run_network(inh)
    accuracies.append(acc)
    print(f"Inhibition = {inh:5.1f}  ->  Accuracy = {acc:.1f}%")

best_idx = np.argmax(accuracies)
print(f"\nBest inhibition: {inhibition_values[best_idx]} with {accuracies[best_idx]:.1f}% accuracy")

# ---- Graph ----
plt.figure(figsize=(9, 5))
plt.plot(inhibition_values, accuracies, marker='o', color='purple', linewidth=2)
plt.scatter([inhibition_values[best_idx]], [accuracies[best_idx]], color='gold', s=150, zorder=5, label="Best")
plt.xlabel("Inhibition Strength")
plt.ylabel("Accuracy (%)")
plt.title("Effect of Lateral Inhibition on Accuracy (noise=0.08)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.ylim(0, 105)

save_path = os.path.expanduser("~/storage/pictures/brain_project/inhibition_sweep.png")
plt.savefig(save_path)
print(f"\nGraph saved: {save_path}")
