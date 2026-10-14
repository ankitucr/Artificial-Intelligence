import numpy as np
import matplotlib.pyplot as plt
import os
import time

# ---- Fixed network params (same as brain_v2.py) ----
NUM_PATTERNS = 10
NUM_NEURONS = NUM_PATTERNS * 3
INPUT_IDX = list(range(0, NUM_PATTERNS))
HIDDEN_IDX = list(range(NUM_PATTERNS, NUM_PATTERNS * 2))
OUTPUT_IDX = list(range(NUM_PATTERNS * 2, NUM_PATTERNS * 3))

THRESHOLD = 1.0
RESET_POTENTIAL = 0.0
LEAK_RATE = 0.05
BLOCK_SIZE = 40

LEARNING_RATE = 0.05
DECAY_RATE = 0.03
MAX_WEIGHT = 2.0
MIN_WEIGHT = 0.1

NOISE_LEVEL = 0.08          # fixed at your best stochastic-resonance point
TRAIN_STEPS = 4000
TEST_STEPS = 2000

INHIBITION_VALUES = np.linspace(0, 15, 8)
RUNS_PER_VALUE = 5


def run_simulation(noise_level, inhibition_strength, seed,
                    train_steps=TRAIN_STEPS, test_steps=TEST_STEPS, block_size=BLOCK_SIZE):
    rng = np.random.default_rng(seed)

    weights = np.zeros((NUM_NEURONS, NUM_NEURONS))
    for i in range(NUM_PATTERNS):
        for h in range(NUM_PATTERNS):
            weights[INPUT_IDX[i]][HIDDEN_IDX[h]] = 1.15 if i == h else 0.5
    for h in range(NUM_PATTERNS):
        for o in range(NUM_PATTERNS):
            weights[HIDDEN_IDX[h]][OUTPUT_IDX[o]] = 1.15 if h == o else 0.5

    connection_mask = weights > 0
    membrane_potential = np.zeros(NUM_NEURONS)
    last_fired = np.full(NUM_NEURONS, -100)

    def apply_lateral_inhibition(fired_idx, layer_idx, mp):
        layer_fired = [i for i in fired_idx if i in layer_idx]
        if len(layer_fired) > 0:
            for other in layer_idx:
                if other not in layer_fired:
                    mp[other] -= inhibition_strength
        return mp

    def run_step(t, pattern, learning_on):
        nonlocal membrane_potential, last_fired, weights

        external_input = np.zeros(NUM_NEURONS)
        external_input[INPUT_IDX[pattern]] = 0.08

        noise = rng.uniform(-noise_level, noise_level, NUM_NEURONS)
        membrane_potential += noise
        membrane_potential -= LEAK_RATE * membrane_potential
        membrane_potential += external_input

        fired = membrane_potential >= THRESHOLD
        fired_idx = np.where(fired)[0]

        correct_fire = False
        output_fired = False

        if len(fired_idx) > 0:
            membrane_potential[fired_idx] = RESET_POTENTIAL
            last_fired[fired_idx] = t

            membrane_potential[:] = apply_lateral_inhibition(fired_idx, HIDDEN_IDX, membrane_potential)
            membrane_potential[:] = apply_lateral_inhibition(fired_idx, OUTPUT_IDX, membrane_potential)

            for idx in fired_idx:
                if idx in OUTPUT_IDX:
                    output_fired = True
                    if idx == OUTPUT_IDX[pattern]:
                        correct_fire = True

            incoming_signal = weights[fired_idx, :].sum(axis=0)
            membrane_potential += incoming_signal

            if learning_on:
                for j in fired_idx:
                    connected_i = np.where(connection_mask[:, j])[0]
                    recently = (0 <= (t - last_fired[connected_i])) & \
                               ((t - last_fired[connected_i]) <= 5) & \
                               (last_fired[connected_i] != -100)
                    weights[connected_i[recently], j] = np.minimum(
                        MAX_WEIGHT, weights[connected_i[recently], j] + LEARNING_RATE)
                    weights[connected_i[~recently], j] = np.maximum(
                        MIN_WEIGHT, weights[connected_i[~recently], j] - DECAY_RATE)

        return output_fired, correct_fire

    for t in range(train_steps):
        pattern = (t // block_size) % NUM_PATTERNS
        run_step(t, pattern, learning_on=True)

    correct = 0
    total_output = 0
    for t in range(train_steps, train_steps + test_steps):
        pattern = (t // block_size) % NUM_PATTERNS
        output_fired, correct_fire = run_step(t, pattern, learning_on=False)
        if output_fired:
            total_output += 1
            if correct_fire:
                correct += 1

    return (correct / total_output * 100) if total_output > 0 else 0.0


def main():
    print("Averaged inhibition sweep chal raha hai...")
    means, stds = [], []

    for inh in INHIBITION_VALUES:
        accs = []
        start = time.time()
        for run in range(RUNS_PER_VALUE):
            seed = int(inh * 1000) + run
            acc = run_simulation(NOISE_LEVEL, inh, seed)
            accs.append(acc)
        means.append(np.mean(accs))
        stds.append(np.std(accs))
        print(f"inhibition={inh:5.2f} -> mean acc={np.mean(accs):5.1f}% "
              f"(std={np.std(accs):4.1f}%) [{time.time()-start:.1f}s, {RUNS_PER_VALUE} runs]")

    means = np.array(means)
    stds = np.array(stds)

    plt.figure(figsize=(8, 5))
    plt.errorbar(INHIBITION_VALUES, means, yerr=stds, marker='o', capsize=4, color='#2b6cb0')
    plt.xlabel("Inhibition strength")
    plt.ylabel("Accuracy (%)")
    plt.title(f"Inhibition sweep (averaged over {RUNS_PER_VALUE} runs, noise={NOISE_LEVEL})")
    plt.grid(alpha=0.3)
    plt.tight_layout()

    out_dir = os.path.expanduser("~/storage/pictures/brain_project/")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "inhibition_sweep_averaged.png")
    plt.savefig(out_path, dpi=150)
    print(f"\nGraph saved: {out_path}")


if __name__ == "__main__":
    main()
