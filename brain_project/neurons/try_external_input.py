import numpy as np
import os

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


def run_simulation(noise_level, inhibition_strength, seed,
                    train_steps, test_steps, external_input_strength):
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
        external_input[INPUT_IDX[pattern]] = external_input_strength

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
        pattern = (t // BLOCK_SIZE) % NUM_PATTERNS
        run_step(t, pattern, learning_on=True)

    correct = 0
    total_output = 0
    no_fire = 0
    for t in range(train_steps, train_steps + test_steps):
        pattern = (t // BLOCK_SIZE) % NUM_PATTERNS
        output_fired, correct_fire = run_step(t, pattern, learning_on=False)
        if output_fired:
            total_output += 1
            if correct_fire:
                correct += 1
        else:
            no_fire += 1

    acc = (correct / total_output * 100) if total_output > 0 else float('nan')
    return acc, no_fire, total_output


def main():
    NOISE = 0.083
    INHIBITION = 2.0
    RUNS = 5
    TRAIN_STEPS = 20000
    TEST_STEPS = 2000

    input_strengths = [0.08, 0.12, 0.16, 0.20, 0.25, 0.30]

    for strength in input_strengths:
        accs, no_fires, totals = [], [], []
        for run in range(RUNS):
            seed = run * 111 + int(strength * 1000)
            acc, nf, total = run_simulation(NOISE, INHIBITION, seed, TRAIN_STEPS, TEST_STEPS, strength)
            if not np.isnan(acc):
                accs.append(acc)
            no_fires.append(nf)
            totals.append(total)
        print(f"external_input={strength:.2f} -> mean acc={np.mean(accs):.1f}% "
              f"(valid runs={len(accs)}/{RUNS}), avg fires={np.mean(totals):.0f}/{TEST_STEPS}, "
              f"avg no-fire={np.mean(no_fires):.0f}")


if __name__ == "__main__":
    main()
