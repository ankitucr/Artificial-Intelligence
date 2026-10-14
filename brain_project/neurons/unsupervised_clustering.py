import numpy as np

NUM_INPUT = 8
NUM_HIDDEN = 5
NUM_CLUSTERS = 3

THRESHOLD = 1.0
RESET_POTENTIAL = 0.0
LEAK_RATE = 0.05
BLOCK_SIZE = 20

NOISE_LEVEL = 0.08
EXTERNAL_SCALE = 0.20
INHIBITION_STRENGTH = 2.0

LEARNING_RATE = 0.05
DECAY_RATE = 0.03
MAX_WEIGHT = 2.0
MIN_WEIGHT = 0.1

HOMEOSTASIS_LR = 0.02
CONSCIENCE_WEIGHT = 0.3
TARGET_RATE = 1.0 / NUM_HIDDEN

TRAIN_BLOCKS = 3000
TEST_BLOCKS_PER_CLUSTER = 30


def run_experiment(seed):
    rng = np.random.default_rng(seed)

    cluster_centers = rng.integers(0, 2, (NUM_CLUSTERS, NUM_INPUT)) * 0.7 + 0.15

    weights = rng.uniform(0.3, 0.7, (NUM_INPUT, NUM_HIDDEN))

    membrane_potential = np.zeros(NUM_INPUT + NUM_HIDDEN)
    last_fired = np.full(NUM_INPUT + NUM_HIDDEN, -100)
    hidden_slice = slice(NUM_INPUT, NUM_INPUT + NUM_HIDDEN)

    threshold_adj = np.zeros(NUM_HIDDEN)
    running_rate = np.full(NUM_HIDDEN, TARGET_RATE)
    block_fired_any = np.zeros(NUM_HIDDEN, dtype=bool)

    def run_step(t, cluster, learning_on, homeostasis_on):
        nonlocal membrane_potential, last_fired, weights, threshold_adj, running_rate, block_fired_any

        if t % BLOCK_SIZE == 0:
            if homeostasis_on and t > 0:
                running_rate[:] = 0.95 * running_rate + 0.05 * block_fired_any
                threshold_adj[:] += HOMEOSTASIS_LR * (running_rate - TARGET_RATE)
                threshold_adj[:] = np.clip(threshold_adj, -0.5, 0.5)
            block_fired_any[:] = False
            membrane_potential[:] = 0.0

        external_input = np.zeros(NUM_INPUT + NUM_HIDDEN)
        external_input[:NUM_INPUT] = cluster_centers[cluster] * EXTERNAL_SCALE

        noise = rng.uniform(-NOISE_LEVEL, NOISE_LEVEL, NUM_INPUT + NUM_HIDDEN)
        membrane_potential += noise
        membrane_potential -= LEAK_RATE * membrane_potential
        membrane_potential += external_input

        eff_threshold = np.full(NUM_INPUT + NUM_HIDDEN, THRESHOLD)
        eff_threshold[hidden_slice] += threshold_adj

        fired = membrane_potential >= eff_threshold
        fired_idx = np.where(fired)[0]

        winner_out = None

        if len(fired_idx) > 0:
            # ---- FIX: winner ko decide karne ke liye reset se PEHLE potential snapshot lo ----
            potential_snapshot = membrane_potential.copy()

            membrane_potential[fired_idx] = RESET_POTENTIAL
            last_fired[fired_idx] = t

            input_fired = fired_idx[fired_idx < NUM_INPUT]
            if len(input_fired) > 0:
                incoming_signal = weights[input_fired, :].sum(axis=0)
                membrane_potential[hidden_slice] += incoming_signal

            hidden_fired_idx = [i for i in fired_idx if i >= NUM_INPUT]
            if len(hidden_fired_idx) > 0:
                # ---- FIX: sabse zyada potential wala jeetega, index order se nahi ----
                winner = max(hidden_fired_idx, key=lambda i: potential_snapshot[i] - CONSCIENCE_WEIGHT * threshold_adj[i - NUM_INPUT])

                for h in range(NUM_INPUT, NUM_INPUT + NUM_HIDDEN):
                    if h != winner:
                        membrane_potential[h] -= INHIBITION_STRENGTH
                block_fired_any[winner - NUM_INPUT] = True

                if learning_on:
                    j = winner - NUM_INPUT
                    recently = (0 <= (t - last_fired[:NUM_INPUT])) & \
                               ((t - last_fired[:NUM_INPUT]) <= 5) & \
                               (last_fired[:NUM_INPUT] != -100)
                    weights[recently, j] = np.minimum(MAX_WEIGHT, weights[recently, j] + LEARNING_RATE)
                    weights[~recently, j] = np.maximum(MIN_WEIGHT, weights[~recently, j] - DECAY_RATE)

                winner_out = winner - NUM_INPUT

        return winner_out

    for block in range(TRAIN_BLOCKS):
        cluster = rng.integers(0, NUM_CLUSTERS)
        for step in range(BLOCK_SIZE):
            t = block * BLOCK_SIZE + step
            run_step(t, cluster, learning_on=True, homeostasis_on=True)

    win_matrix = np.zeros((NUM_CLUSTERS, NUM_HIDDEN), dtype=int)
    t_offset = TRAIN_BLOCKS * BLOCK_SIZE

    for cluster in range(NUM_CLUSTERS):
        for rep in range(TEST_BLOCKS_PER_CLUSTER):
            winners_this_block = []
            for step in range(BLOCK_SIZE):
                t = t_offset + step
                w = run_step(t, cluster, learning_on=False, homeostasis_on=False)
                if w is not None:
                    winners_this_block.append(w)
            t_offset += BLOCK_SIZE
            if winners_this_block:
                vals, counts = np.unique(winners_this_block, return_counts=True)
                win_matrix[cluster, vals[np.argmax(counts)]] += 1

    return win_matrix, threshold_adj


def main():
    win_matrix, threshold_adj = run_experiment(seed=42)

    print("Training khatam. Ab dekhte hain network ne khud kya seekha:\n")
    print("Winner matrix (rows=asli cluster [network ko pata nahi], cols=hidden neuron):")
    header = "        " + "".join(f"N{h:<5}" for h in range(NUM_HIDDEN))
    print(header)
    for c in range(NUM_CLUSTERS):
        row = f"Cluster{c}: " + "".join(f"{win_matrix[c,h]:<6}" for h in range(NUM_HIDDEN))
        print(row)

    print(f"\nFinal homeostatic threshold adjustments per neuron: {np.round(threshold_adj, 3)}")

    print("\nInterpretation:")
    for c in range(NUM_CLUSTERS):
        best_neuron = np.argmax(win_matrix[c])
        total = win_matrix[c].sum()
        purity = win_matrix[c, best_neuron] / total * 100 if total > 0 else 0
        print(f"  Cluster {c} -> mostly activates Neuron {best_neuron} ({purity:.0f}% of test blocks)")


if __name__ == "__main__":
    main()
