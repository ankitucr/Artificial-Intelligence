import json
import os
import numpy as np


# ============================================================
# EVOLVING NEURAL SYSTEM V5
# Repeated Novelty Detection + Adaptive Neurogenesis
# ============================================================

NUM_INPUT = 8
NUM_CLUSTERS = 3

INITIAL_NEURONS = 3
MIN_NEURONS = 3
MAX_NEURONS = 30

TRAIN_SAMPLES = 900
TEST_SAMPLES = 180

LEARNING_RATE = 0.08
MIN_LEARNING_RATE = 0.015

BASE_NOISE = 0.025
MAX_NOISE = 0.16

# ------------------------------------------------------------
# Novelty system
# ------------------------------------------------------------

NOVELTY_THRESHOLD = 0.030
NOVELTY_CONFIRMATIONS = 6
NOVELTY_COOLDOWN = 8

MAX_BIRTHS_PER_GENERATION = 1

# ------------------------------------------------------------
# Evolution
# ------------------------------------------------------------

PRUNE_AFTER_AGE = 60
PRUNE_FITNESS = 0.035

CHECKPOINT_EVERY = 10

STATE_FILE = "neurons/evolution_state_v5.npz"
LINEAGE_FILE = "neurons/neuron_lineage_v5.json"


# ============================================================
# ENVIRONMENT
# ============================================================

class Environment:

    def __init__(self):

        self.base_modes = {

            0: [
                np.array(
                    [0.95, 0.95, 0.95, 0.95,
                     0.05, 0.05, 0.05, 0.05]
                ),

                np.array(
                    [0.72, 0.88, 0.68, 0.84,
                     0.28, 0.12, 0.30, 0.15]
                ),

                np.array(
                    [0.58, 0.92, 0.76, 0.67,
                     0.42, 0.08, 0.24, 0.33]
                ),
            ],

            1: [
                np.array(
                    [0.05, 0.05, 0.05, 0.05,
                     0.95, 0.95, 0.95, 0.95]
                ),

                np.array(
                    [0.28, 0.12, 0.30, 0.15,
                     0.72, 0.88, 0.68, 0.84]
                ),

                np.array(
                    [0.42, 0.08, 0.24, 0.33,
                     0.58, 0.92, 0.76, 0.67]
                ),
            ],

            2: [
                np.array(
                    [0.95, 0.05, 0.95, 0.05,
                     0.95, 0.05, 0.95, 0.05]
                ),

                np.array(
                    [0.82, 0.18, 0.76, 0.22,
                     0.70, 0.12, 0.86, 0.28]
                ),

                np.array(
                    [0.68, 0.30, 0.88, 0.16,
                     0.78, 0.24, 0.62, 0.34]
                ),
            ],
        }

    def noise(self, generation):

        phase = generation // 75

        return min(
            MAX_NOISE,
            BASE_NOISE + phase * 0.012
        )

    def modes(self, generation):

        result = {}

        for cluster in range(NUM_CLUSTERS):

            modes = [
                x.copy()
                for x in self.base_modes[cluster]
            ]

            # ------------------------------------------
            # NEW MODE 4
            # ------------------------------------------

            if generation >= 100:

                if cluster == 0:
                    modes.append(
                        np.array(
                            [0.82, 0.63, 0.91, 0.58,
                             0.18, 0.37, 0.09, 0.42]
                        )
                    )

                elif cluster == 1:
                    modes.append(
                        np.array(
                            [0.18, 0.37, 0.09, 0.42,
                             0.82, 0.63, 0.91, 0.58]
                        )
                    )

                else:
                    modes.append(
                        np.array(
                            [0.86, 0.22, 0.63, 0.38,
                             0.79, 0.17, 0.91, 0.29]
                        )
                    )

            # ------------------------------------------
            # NEW MODE 5
            # ------------------------------------------

            if generation >= 200:

                if cluster == 0:
                    modes.append(
                        np.array(
                            [0.47, 0.94, 0.61, 0.79,
                             0.53, 0.06, 0.39, 0.21]
                        )
                    )

                elif cluster == 1:
                    modes.append(
                        np.array(
                            [0.53, 0.06, 0.39, 0.21,
                             0.47, 0.94, 0.61, 0.79]
                        )
                    )

                else:
                    modes.append(
                        np.array(
                            [0.59, 0.27, 0.83, 0.18,
                             0.71, 0.36, 0.92, 0.11]
                        )
                    )

            # ------------------------------------------
            # NEW MODE 6
            # ------------------------------------------

            if generation >= 300:

                if cluster == 0:
                    modes.append(
                        np.array(
                            [0.35, 0.90, 0.48, 0.82,
                             0.65, 0.10, 0.52, 0.18]
                        )
                    )

                elif cluster == 1:
                    modes.append(
                        np.array(
                            [0.65, 0.10, 0.52, 0.18,
                             0.35, 0.90, 0.48, 0.82]
                        )
                    )

                else:
                    modes.append(
                        np.array(
                            [0.77, 0.14, 0.55, 0.31,
                             0.64, 0.19, 0.88, 0.23]
                        )
                    )

            result[cluster] = modes

        return result

    def sample(
        self,
        rng,
        cluster,
        generation
    ):

        modes = self.modes(
            generation
        )[cluster]

        # Every mode has equal probability.
        mode = modes[
            int(
                rng.integers(
                    0,
                    len(modes)
                )
            )
        ]

        x = mode.copy()

        # Gradual concept drift.
        if generation >= 150:

            drift = min(
                0.08,
                (generation - 150) * 0.00025
            )

            x += rng.normal(
                0,
                drift,
                NUM_INPUT
            )

        x += rng.normal(
            0,
            self.noise(generation),
            NUM_INPUT
        )

        return np.clip(
            x,
            0,
            1
        )


# ============================================================
# NEURON
# ============================================================

class Neuron:

    def __init__(
        self,
        neuron_id,
        weights,
        parent,
        born,
        cluster
    ):

        self.id = int(neuron_id)

        self.weights = np.array(
            weights,
            dtype=float
        )

        self.parent = (
            None
            if parent is None
            else int(parent)
        )

        self.born = int(born)

        self.age = 0

        self.wins = 0

        self.correct = 0

        self.wrong = 0

        self.fitness = 0.5

        self.seed_cluster = (
            int(cluster)
            if cluster is not None
            else None
        )

        self.cluster_votes = np.zeros(
            NUM_CLUSTERS,
            dtype=float
        )

    def distance(self, x):

        return float(
            np.mean(
                (self.weights - x) ** 2
            )
        )

    def specialization(self):

        total = self.cluster_votes.sum()

        if total <= 0:

            return self.seed_cluster

        return int(
            np.argmax(
                self.cluster_votes
            )
        )

    def confidence(self):

        total = self.cluster_votes.sum()

        if total <= 0:

            return 0.0

        return float(
            self.cluster_votes.max()
            / total
        )

    def learn(
        self,
        x,
        rate
    ):

        self.weights += (
            rate
            * (x - self.weights)
        )

        self.weights = np.clip(
            self.weights,
            0,
            1
        )


# ============================================================
# POPULATION
# ============================================================

class Population:

    def __init__(self):

        self.neurons = []

        self.next_id = 0

        self.generation = 0

        self.last_birth = -999999

        self.births_this_generation = 0

        self.total_created = 0

        self.total_pruned = 0

        self.lineage = {}

        # Repeated novelty counters.
        self.novelty_count = np.zeros(
            NUM_CLUSTERS,
            dtype=int
        )

        # Store recent novel patterns.
        self.novelty_buffer = {
            c: []
            for c in range(NUM_CLUSTERS)
        }

    # --------------------------------------------------------
    # INITIALIZATION
    # --------------------------------------------------------

    def initialize(
        self,
        environment
    ):

        modes = environment.modes(0)

        for cluster in range(
            NUM_CLUSTERS
        ):

            weights = modes[
                cluster
            ][0].copy()

            neuron = Neuron(
                self.next_id,
                weights,
                None,
                0,
                cluster
            )

            neuron.cluster_votes[
                cluster
            ] = 1

            self.neurons.append(
                neuron
            )

            self.lineage[
                str(self.next_id)
            ] = {
                "id": self.next_id,
                "parent": None,
                "born": 0,
                "event": "initial",
                "cluster": cluster
            }

            self.next_id += 1

    # --------------------------------------------------------
    # NEW GENERATION
    # --------------------------------------------------------

    def begin_generation(self):

        self.births_this_generation = 0

    # --------------------------------------------------------
    # WINNER
    # --------------------------------------------------------

    def winner(self, x):

        distances = [
            n.distance(x)
            for n in self.neurons
        ]

        index = int(
            np.argmin(distances)
        )

        return (
            self.neurons[index],
            distances[index]
        )

    # --------------------------------------------------------
    # NOVELTY BUFFER
    # --------------------------------------------------------

    def add_novel_pattern(
        self,
        cluster,
        x
    ):

        buffer = self.novelty_buffer[
            cluster
        ]

        buffer.append(
            x.copy()
        )

        if len(buffer) > 20:

            buffer.pop(0)

        self.novelty_count[
            cluster
        ] += 1

    # --------------------------------------------------------
    # BIRTH FROM NOVEL PATTERN
    # --------------------------------------------------------

    def create_neuron(
        self,
        cluster,
        parent
    ):

        if len(
            self.neurons
        ) >= MAX_NEURONS:

            return None

        if (
            self.births_this_generation
            >= MAX_BIRTHS_PER_GENERATION
        ):

            return None

        buffer = self.novelty_buffer[
            cluster
        ]

        if buffer:

            prototype = np.mean(
                np.array(buffer),
                axis=0
            )

        else:

            prototype = parent.weights.copy()

        rng = np.random.default_rng(
            self.next_id * 7919 + 17
        )

        mutation = rng.normal(
            0,
            0.025,
            NUM_INPUT
        )

        weights = np.clip(
            prototype + mutation,
            0,
            1
        )

        child = Neuron(
            self.next_id,
            weights,
            parent.id,
            self.generation,
            cluster
        )

        child.cluster_votes[
            cluster
        ] = 3

        self.neurons.append(
            child
        )

        self.lineage[
            str(self.next_id)
        ] = {
            "id": self.next_id,
            "parent": parent.id,
            "born": self.generation,
            "event": "repeated_novelty",
            "cluster": cluster
        }

        created_id = self.next_id

        self.next_id += 1

        self.total_created += 1

        self.births_this_generation += 1

        self.last_birth = (
            self.generation
        )

        # Reset novelty evidence after birth.
        self.novelty_count[
            cluster
        ] = 0

        self.novelty_buffer[
            cluster
        ].clear()

        return child

    # --------------------------------------------------------
    # PRUNING
    # --------------------------------------------------------

    def prune(self):

        if len(
            self.neurons
        ) <= MIN_NEURONS:

            return []

        protected = set()

        # Keep strongest specialist for every cluster.
        for cluster in range(
            NUM_CLUSTERS
        ):

            candidates = [
                n
                for n in self.neurons
                if n.specialization() == cluster
            ]

            if candidates:

                best = max(
                    candidates,
                    key=lambda n: n.fitness
                )

                protected.add(
                    best.id
                )

        removed = []

        for neuron in list(
            self.neurons
        ):

            if len(
                self.neurons
            ) <= MIN_NEURONS:

                break

            if neuron.id in protected:

                continue

            if neuron.age < PRUNE_AFTER_AGE:

                continue

            if neuron.fitness < PRUNE_FITNESS:

                removed.append(
                    neuron.id
                )

                self.lineage[
                    str(neuron.id)
                ]["event"] = "pruned"

                self.lineage[
                    str(neuron.id)
                ]["pruned_generation"] = (
                    self.generation
                )

                self.neurons.remove(
                    neuron
                )

                self.total_pruned += 1

        return removed


# ============================================================
# TRAIN
# ============================================================

def train(
    rng,
    population,
    environment
):

    generation = (
        population.generation
    )

    population.begin_generation()

    lr = max(
        MIN_LEARNING_RATE,
        LEARNING_RATE
        * (0.996 ** generation)
    )

    for _ in range(
        TRAIN_SAMPLES
    ):

        cluster = int(
            rng.integers(
                0,
                NUM_CLUSTERS
            )
        )

        x = environment.sample(
            rng,
            cluster,
            generation
        )

        winner, distance = (
            population.winner(x)
        )

        # ----------------------------------------------------
        # REPEATED NOVELTY DETECTION
        # ----------------------------------------------------

        if distance > NOVELTY_THRESHOLD:

            population.add_novel_pattern(
                cluster,
                x
            )

            # Do NOT immediately create a neuron.
            # Require repeated evidence.
            if (
                population.novelty_count[
                    cluster
                ] >= NOVELTY_CONFIRMATIONS
                and
                generation
                - population.last_birth
                >= NOVELTY_COOLDOWN
            ):

                child = population.create_neuron(
                    cluster,
                    winner
                )

                if child is not None:

                    print(
                        f"    NEUROGENESIS: "
                        f"N{child.id:03d} "
                        f"<- N{winner.id:03d} "
                        f"| target=Cluster{cluster} "
                        f"| novelty="
                        f"{population.novelty_count[cluster]}"
                    )

                    winner = child

        # ----------------------------------------------------
        # LEARNING
        # ----------------------------------------------------

        winner.wins += 1

        winner.cluster_votes[
            cluster
        ] += 1

        predicted = (
            winner.specialization()
        )

        if predicted == cluster:

            winner.correct += 1

        else:

            winner.wrong += 1

        winner.learn(
            x,
            lr
        )

    # --------------------------------------------------------
    # FITNESS
    # --------------------------------------------------------

    for neuron in population.neurons:

        neuron.age += 1

        total = (
            neuron.cluster_votes.sum()
        )

        if total <= 0:

            neuron.fitness *= 0.92

            continue

        confidence = (
            neuron.confidence()
        )

        performance = (
            neuron.correct
            / max(
                neuron.correct
                + neuron.wrong,
                1
            )
        )

        usage = min(
            1.0,
            neuron.wins
            / TRAIN_SAMPLES
        )

        neuron.fitness = (
            0.50 * confidence
            + 0.35 * performance
            + 0.15 * usage
        )


# ============================================================
# EVALUATION
# ============================================================

def evaluate(
    rng,
    population,
    environment
):

    confusion = np.zeros(
        (
            NUM_CLUSTERS,
            NUM_CLUSTERS
        ),
        dtype=int
    )

    correct = np.zeros(
        NUM_CLUSTERS,
        dtype=int
    )

    total = np.zeros(
        NUM_CLUSTERS,
        dtype=int
    )

    for cluster in range(
        NUM_CLUSTERS
    ):

        for _ in range(
            TEST_SAMPLES
        ):

            x = environment.sample(
                rng,
                cluster,
                population.generation
            )

            winner, _ = (
                population.winner(x)
            )

            predicted = (
                winner.specialization()
            )

            if predicted is None:

                continue

            predicted = int(
                predicted
            )

            confusion[
                cluster,
                predicted
            ] += 1

            total[
                cluster
            ] += 1

            if predicted == cluster:

                correct[
                    cluster
                ] += 1

    accuracy = (
        correct
        / np.maximum(
            total,
            1
        )
    )

    overall = (
        correct.sum()
        / max(
            total.sum(),
            1
        )
    )

    return (
        accuracy,
        overall,
        confusion
    )


# ============================================================
# SAVE
# ============================================================

def save_state(
    population
):

    os.makedirs(
        "neurons",
        exist_ok=True
    )

    ids = np.array(
        [
            n.id
            for n in population.neurons
        ],
        dtype=int
    )

    weights = np.array(
        [
            n.weights
            for n in population.neurons
        ],
        dtype=float
    )

    fitness = np.array(
        [
            n.fitness
            for n in population.neurons
        ],
        dtype=float
    )

    np.savez(
        STATE_FILE,
        generation=population.generation,
        ids=ids,
        weights=weights,
        fitness=fitness,
        next_id=population.next_id
    )

    with open(
        LINEAGE_FILE,
        "w"
    ) as f:

        json.dump(
            population.lineage,
            f,
            indent=2
        )


# ============================================================
# CHECKPOINT
# ============================================================

def checkpoint(
    population,
    environment,
    accuracy,
    overall,
    confusion
):

    generation = (
        population.generation
    )

    noise = environment.noise(
        generation
    )

    mode_count = max(
        len(x)
        for x in environment.modes(
            generation
        ).values()
    )

    acc_text = [
        round(
            float(x) * 100,
            1
        )
        for x in accuracy
    ]

    print()
    print("=" * 78)
    print("EVOLUTION CHECKPOINT")
    print("=" * 78)

    print(
        f"Generation        : {generation}"
    )

    print(
        f"Live neurons      : "
        f"{len(population.neurons)}"
    )

    print(
        f"Next neuron ID    : "
        f"N{population.next_id}"
    )

    print(
        f"Created total     : "
        f"{population.total_created}"
    )

    print(
        f"Pruned total      : "
        f"{population.total_pruned}"
    )

    print(
        f"Modes / cluster   : "
        f"{mode_count}"
    )

    print(
        f"Environment noise : "
        f"{noise:.3f}"
    )

    print(
        f"Cluster accuracy  : "
        f"{acc_text}"
    )

    print(
        f"Overall accuracy  : "
        f"{overall * 100:.2f}%"
    )

    print(
        "Confusion matrix:"
    )

    print(
        confusion
    )

    print(
        "Neuron population:"
    )

    for neuron in sorted(
        population.neurons,
        key=lambda n: n.id
    ):

        spec = neuron.specialization()

        if spec is None:

            spec_text = "None"

        else:

            spec_text = (
                f"Cluster{spec}"
            )

        print(
            f"    N{neuron.id:03d} | "
            f"spec={spec_text:<9} | "
            f"fitness={neuron.fitness:.3f} | "
            f"confidence={neuron.confidence():.3f} | "
            f"age={neuron.age:4d} | "
            f"wins={neuron.wins}"
        )

    print("=" * 78)
    print()


# ============================================================
# MAIN
# ============================================================

def main():

    rng = np.random.default_rng(
        42
    )

    environment = Environment()

    population = Population()

    population.initialize(
        environment
    )

    print("=" * 78)
    print("EVOLVING NEURAL SYSTEM V5")
    print("=" * 78)
    print(
        "MULTI-MODAL CLUSTERS       : ON"
    )
    print(
        "REPEATED NOVELTY           : ON"
    )
    print(
        "PATTERN MEMORY             : ON"
    )
    print(
        "NEUROGENESIS               : ON"
    )
    print(
        "MUTATION                   : ON"
    )
    print(
        "FITNESS                    : ON"
    )
    print(
        "PRUNING                    : ON"
    )
    print(
        "CONCEPT DRIFT              : ON"
    )
    print(
        "PERMANENT EVOLUTION LOOP  : ON"
    )
    print(
        f"INITIAL NEURONS            : "
        f"{INITIAL_NEURONS}"
    )
    print(
        f"MAX NEURONS                : "
        f"{MAX_NEURONS}"
    )
    print("=" * 78)
    print()

    try:

        while True:

            population.generation += 1

            # ------------------------------------------
            # TRAIN
            # ------------------------------------------

            train(
                rng,
                population,
                environment
            )

            # ------------------------------------------
            # EVALUATE
            # ------------------------------------------

            (
                accuracy,
                overall,
                confusion
            ) = evaluate(
                rng,
                population,
                environment
            )

            # ------------------------------------------
            # PRUNE
            # ------------------------------------------

            removed = population.prune()

            for neuron_id in removed:

                print(
                    f"    PRUNED DEAD NEURON: "
                    f"N{neuron_id:03d}"
                )

            # ------------------------------------------
            # NORMAL OUTPUT
            # ------------------------------------------

            acc_text = [
                round(
                    float(x) * 100,
                    1
                )
                for x in accuracy
            ]

            print(
                f"Gen {population.generation:5d} | "
                f"neurons={len(population.neurons):2d} | "
                f"acc={acc_text} | "
                f"overall={overall * 100:6.2f}% | "
                f"created={population.total_created:2d} | "
                f"pruned={population.total_pruned:2d}"
            )

            # ------------------------------------------
            # CHECKPOINT
            # ------------------------------------------

            if (
                population.generation
                % CHECKPOINT_EVERY
                == 0
            ):

                save_state(
                    population
                )

                checkpoint(
                    population,
                    environment,
                    accuracy,
                    overall,
                    confusion
                )

    except KeyboardInterrupt:

        print()
        print("=" * 78)
        print("EVOLUTION STOPPED")
        print("=" * 78)

        print(
            f"Generation       : "
            f"{population.generation}"
        )

        print(
            f"Live neurons     : "
            f"{len(population.neurons)}"
        )

        print(
            f"Next neuron ID   : "
            f"N{population.next_id}"
        )

        print(
            f"Created total    : "
            f"{population.total_created}"
        )

        print(
            f"Pruned total     : "
            f"{population.total_pruned}"
        )

        save_state(
            population
        )

        print(
            "STATE SAVED"
        )

        print(
            f"  {STATE_FILE}"
        )

        print(
            f"  {LINEAGE_FILE}"
        )

        print("=" * 78)


if __name__ == "__main__":
    main()
