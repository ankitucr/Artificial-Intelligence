#!/usr/bin/env python3

import json
import math
import os
import signal
import subprocess
import time
from collections import deque
from datetime import datetime


# ============================================================
# LIVE SENSOR COGNITIVE BRAIN V4
# Sense -> Represent -> Predict -> Act -> Observe -> Reward
# ============================================================

STATE_FILE = "neurons/sensor_brain_v4_state.json"
MEMORY_FILE = "neurons/sensor_brain_v4_memory.json"
LINEAGE_FILE = "neurons/sensor_brain_v4_lineage.json"

INITIAL_NEURONS = 4
MAX_NEURONS = 100
MIN_NEURONS = 4

SAMPLE_DELAY = 0.40

EMA_ALPHA = 0.20

NOVELTY_THRESHOLD = 0.24
NOVELTY_CONFIRMATIONS = 4
BIRTH_COOLDOWN = 10

LEARNING_RATE = 0.08
MIN_LEARNING_RATE = 0.01

PREDICTION_MEMORY = 50
MEMORY_LIMIT = 1000

PRUNE_AFTER = 500
PRUNE_FITNESS = 0.055

CHECKPOINT_SECONDS = 30

RUNNING = True


# ============================================================
# HELPERS
# ============================================================

def timestamp():
    return datetime.now().isoformat(
        timespec="milliseconds"
    )


def safe_float(value):
    try:
        value = float(value)

        if math.isfinite(value):
            return value

    except Exception:
        pass

    return None


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def mean_squared_distance(a, b):

    if not a or not b:
        return 999.0

    n = min(len(a), len(b))

    if n == 0:
        return 999.0

    total = 0.0

    for i in range(n):

        d = (
            float(a[i])
            - float(b[i])
        )

        total += d * d

    return total / n


def euclidean_distance(a, b):

    mse = mean_squared_distance(
        a,
        b
    )

    if mse >= 999:
        return 999.0

    return math.sqrt(mse)


# ============================================================
# TERMUX SENSOR
# ============================================================

def read_sensor_snapshot():

    try:

        process = subprocess.run(
            [
                "termux-sensor",
                "-a",
                "-n",
                "1"
            ],
            capture_output=True,
            text=True,
            timeout=8
        )

        if process.returncode != 0:
            return {}

        raw = process.stdout.strip()

        if not raw:
            return {}

        return json.loads(raw)

    except Exception:
        return {}


# ============================================================
# SENSOR FINDER
# ============================================================

def find_values(
    data,
    required,
    minimum=1
):

    if not isinstance(data, dict):
        return []

    required = [
        x.lower()
        for x in required
    ]

    for name, obj in data.items():

        lname = name.lower()

        if not all(
            key in lname
            for key in required
        ):
            continue

        if not isinstance(obj, dict):
            continue

        values = obj.get(
            "values",
            []
        )

        if not isinstance(
            values,
            list
        ):
            continue

        result = []

        for value in values:

            value = safe_float(
                value
            )

            if value is not None:

                result.append(
                    value
                )

        if len(result) >= minimum:

            return result

    return []


# ============================================================
# NORMALIZATION
# ============================================================

def signed(value, scale):

    if scale <= 0:
        return 0.5

    return clamp(
        0.5
        + 0.5
        * math.tanh(
            value / scale
        )
    )


def positive(value, scale):

    if value <= 0:
        return 0.0

    return clamp(
        value / scale
    )


# ============================================================
# SENSOR ENCODER
# ============================================================

class SensorEncoder:

    def __init__(self):

        self.names = []

        self.previous = None

        self.ema = None

    def encode(self, data):

        base = []
        names = []

        # ----------------------------------------------------
        # Accelerometer
        # ----------------------------------------------------

        acc = find_values(
            data,
            [
                "accelerometer",
                "non-wakeup"
            ],
            3
        )

        if not acc:

            acc = find_values(
                data,
                ["accelerometer"],
                3
            )

        for i in range(3):

            value = (
                acc[i]
                if i < len(acc)
                else 0.0
            )

            base.append(
                signed(
                    value,
                    10.0
                )
            )

            names.append(
                f"accelerometer_{i}"
            )

        # ----------------------------------------------------
        # Gyroscope
        # ----------------------------------------------------

        gyro = find_values(
            data,
            [
                "gyroscope",
                "non-wakeup"
            ],
            3
        )

        if not gyro:

            gyro = find_values(
                data,
                ["gyroscope"],
                3
            )

        for i in range(3):

            value = (
                gyro[i]
                if i < len(gyro)
                else 0.0
            )

            base.append(
                signed(
                    value,
                    5.0
                )
            )

            names.append(
                f"gyroscope_{i}"
            )

        # ----------------------------------------------------
        # Magnetometer
        # ----------------------------------------------------

        mag = find_values(
            data,
            [
                "magnetometer",
                "non-wakeup"
            ],
            3
        )

        if not mag:

            mag = find_values(
                data,
                ["magnetometer"],
                3
            )

        for i in range(3):

            value = (
                mag[i]
                if i < len(mag)
                else 0.0
            )

            base.append(
                signed(
                    value,
                    100.0
                )
            )

            names.append(
                f"magnetometer_{i}"
            )

        # ----------------------------------------------------
        # Gravity
        # ----------------------------------------------------

        gravity = find_values(
            data,
            ["gravity"],
            3
        )

        for i in range(3):

            value = (
                gravity[i]
                if i < len(gravity)
                else 0.0
            )

            base.append(
                signed(
                    value,
                    10.0
                )
            )

            names.append(
                f"gravity_{i}"
            )

        # ----------------------------------------------------
        # Linear acceleration
        # ----------------------------------------------------

        linear = find_values(
            data,
            ["linear_acceleration"],
            3
        )

        for i in range(3):

            value = (
                linear[i]
                if i < len(linear)
                else 0.0
            )

            base.append(
                signed(
                    value,
                    10.0
                )
            )

            names.append(
                f"linear_acceleration_{i}"
            )

        # ----------------------------------------------------
        # Rotation vector
        # ----------------------------------------------------

        rotation = find_values(
            data,
            [
                "rotation vector",
                "non-wakeup"
            ],
            4
        )

        if not rotation:

            rotation = find_values(
                data,
                ["rotation vector"],
                4
            )

        for i in range(4):

            value = (
                rotation[i]
                if i < len(rotation)
                else 0.0
            )

            base.append(
                signed(
                    value,
                    1.0
                )
            )

            names.append(
                f"rotation_{i}"
            )

        # ----------------------------------------------------
        # Light
        # ----------------------------------------------------

        light = find_values(
            data,
            ["light sensor"],
            1
        )

        if not light:

            light = find_values(
                data,
                ["lux"],
                1
            )

        light_value = (
            light[0]
            if light
            else 0.0
        )

        base.append(
            positive(
                light_value,
                1000.0
            )
        )

        names.append(
            "light"
        )

        # ----------------------------------------------------
        # Proximity
        # ----------------------------------------------------

        proximity = find_values(
            data,
            ["proximity"],
            1
        )

        proximity_value = (
            proximity[0]
            if proximity
            else 0.0
        )

        base.append(
            positive(
                proximity_value,
                10.0
            )
        )

        names.append(
            "proximity"
        )

        # ----------------------------------------------------
        # Pedometer
        # ----------------------------------------------------

        pedometer = find_values(
            data,
            ["pedometer"],
            1
        )

        step_value = (
            pedometer[0]
            if pedometer
            else 0.0
        )

        base.append(
            positive(
                step_value % 1000,
                1000.0
            )
        )

        names.append(
            "pedometer_mod"
        )

        # ----------------------------------------------------
        # Activity recognition
        # ----------------------------------------------------

        activity = find_values(
            data,
            ["activity_recognition"],
            4
        )

        for i in range(4):

            value = (
                activity[i]
                if i < len(activity)
                else 0.0
            )

            base.append(
                positive(
                    value,
                    5.0
                )
            )

            names.append(
                f"activity_{i}"
            )

        # ----------------------------------------------------
        # EMA smoothing
        # ----------------------------------------------------

        if self.ema is None:

            self.ema = list(base)

        else:

            self.ema = [
                EMA_ALPHA * current
                + (
                    1.0
                    - EMA_ALPHA
                ) * old

                for current, old
                in zip(
                    base,
                    self.ema
                )
            ]

        # ----------------------------------------------------
        # Temporal derivative
        # ----------------------------------------------------

        if self.previous is None:

            delta = [
                0.0
                for _ in self.ema
            ]

        else:

            delta = [
                abs(
                    current
                    - previous
                )

                for current, previous
                in zip(
                    self.ema,
                    self.previous
                )
            ]

        self.previous = list(
            self.ema
        )

        # Current + temporal change.
        state = (
            self.ema
            + delta
        )

        self.names = (
            names
            + [
                f"delta_{name}"
                for name in names
            ]
        )

        return (
            state,
            self.names
        )


# ============================================================
# NEURON
# ============================================================

class Neuron:

    def __init__(
        self,
        neuron_id,
        prototype,
        cluster="unknown",
        parent=None,
        born=0
    ):

        self.id = neuron_id

        self.prototype = list(
            prototype
        )

        self.cluster = cluster

        self.confidence = 0.20

        self.fitness = 0.20

        self.age = 0

        self.parent = parent

        self.children = []

        self.activation_count = 0

        self.associated_memories = deque(
            maxlen=100
        )

        self.previous_states = deque(
            maxlen=PREDICTION_MEMORY
        )

        self.next_states = deque(
            maxlen=PREDICTION_MEMORY
        )

        self.actions = deque(
            maxlen=PREDICTION_MEMORY
        )

        self.reward = 0.0

        self.prediction_error = 0.0

        self.stability = 0.0

        self.last_distance = 1.0

        self.last_activation = 0

        self.birth_generation = born

    def distance(self, state):

        return euclidean_distance(
            self.prototype,
            state
        )

    def learn(
        self,
        state,
        generation
    ):

        d = self.distance(
            state
        )

        self.last_distance = d

        lr = max(
            MIN_LEARNING_RATE,
            LEARNING_RATE
            / math.sqrt(
                1.0
                + self.activation_count
                / 30.0
            )
        )

        # Learn strongly only when state is
        # already in the neuron's neighborhood.
        if d <= NOVELTY_THRESHOLD:

            for i in range(
                min(
                    len(self.prototype),
                    len(state)
                )
            ):

                self.prototype[i] += (
                    lr
                    * (
                        state[i]
                        - self.prototype[i]
                    )
                )

        self.age += 1
        self.activation_count += 1
        self.last_activation = generation

        self.prediction_error = (
            0.90
            * self.prediction_error
            + 0.10
            * min(
                d,
                1.0
            )
        )

        stability = (
            1.0
            - clamp(
                d
            )
        )

        self.stability = (
            0.95
            * self.stability
            + 0.05
            * stability
        )

        confidence_now = math.exp(
            -3.0 * d
        )

        self.confidence = clamp(
            0.94
            * self.confidence
            + 0.06
            * confidence_now
        )

        prediction_quality = (
            1.0
            - clamp(
                self.prediction_error
            )
        )

        usage = min(
            1.0,
            self.activation_count / 250.0
        )

        self.fitness = clamp(
            0.45 * self.confidence
            + 0.25 * self.stability
            + 0.20 * usage
            + 0.10 * prediction_quality
        )

        return d

    def remember(
        self,
        state_id,
        d
    ):

        self.associated_memories.append(
            {
                "state_id": state_id,
                "distance": round(
                    d,
                    6
                ),
                "time": timestamp()
            }
        )

    def add_previous(
        self,
        neuron_id
    ):

        if neuron_id is None:
            return

        if neuron_id not in self.previous_states:

            self.previous_states.append(
                neuron_id
            )

    def add_next(
        self,
        neuron_id
    ):

        if neuron_id is None:
            return

        if neuron_id not in self.next_states:

            self.next_states.append(
                neuron_id
            )

    def add_action(
        self,
        action
    ):

        self.actions.append(
            {
                "time": timestamp(),
                "action": action
            }
        )

    def update_reward(
        self,
        value
    ):

        self.reward = (
            0.95
            * self.reward
            + 0.05
            * clamp(
                value
            )
        )


# ============================================================
# BRAIN
# ============================================================

class Brain:

    def __init__(self):

        self.neurons = {}

        self.next_id = 0

        self.generation = 0

        self.states_learned = 0

        self.created_total = 0

        self.pruned_total = 0

        self.last_birth = -999999

        self.novel_count = 0

        self.novel_candidate = None

        self.previous_winner = None

        self.previous_state = None

        self.previous_prediction = None

        self.memory = deque(
            maxlen=MEMORY_LIMIT
        )

        self.transitions = deque(
            maxlen=500
        )

        self.encoder = SensorEncoder()

        self.raw_sensor_count = 0

        self.last_result = None

        self.load()

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def initialize(
        self,
        state
    ):

        if self.neurons:
            return

        # Different initial representations,
        # but ALL are based on real sensor state.
        offsets = [
            -0.12,
            -0.04,
            0.04,
            0.12
        ]

        for offset in offsets:

            prototype = [
                clamp(
                    value + offset,
                    0.0,
                    1.0
                )
                for value in state
            ]

            neuron_id = (
                f"N{self.next_id:04d}"
            )

            self.next_id += 1

            neuron = Neuron(
                neuron_id,
                prototype,
                cluster="sensor_state",
                parent=None,
                born=self.generation
            )

            self.neurons[
                neuron_id
            ] = neuron

            self.created_total += 1

        print(
            f"INITIALIZED {len(self.neurons)} "
            "NEURONS FROM REAL SENSOR STATE"
        )

    # ========================================================
    # WINNER
    # ========================================================

    def find_winner(
        self,
        state
    ):

        winner = None
        winner_distance = 999.0

        for neuron in (
            self.neurons.values()
        ):

            d = neuron.distance(
                state
            )

            # Small usage penalty.
            usage_penalty = min(
                0.03,
                neuron.activation_count
                / 50000.0
            )

            score = (
                d
                + usage_penalty
            )

            if score < winner_distance:

                winner_distance = score
                winner = neuron

        return (
            winner,
            winner_distance
        )

    # ========================================================
    # NOVELTY
    # ========================================================

    def confirm_novelty(
        self,
        state,
        distance_value
    ):

        if distance_value < (
            NOVELTY_THRESHOLD
        ):

            self.novel_count = 0
            self.novel_candidate = None

            return False

        if self.novel_candidate is None:

            self.novel_candidate = list(
                state
            )

            self.novel_count = 1

            return False

        candidate_distance = (
            euclidean_distance(
                state,
                self.novel_candidate
            )
        )

        # Require the NEW state itself to remain stable.
        if candidate_distance < (
            NOVELTY_THRESHOLD * 0.60
        ):

            self.novel_count += 1

            self.novel_candidate = [
                0.20 * current
                + 0.80 * old

                for current, old
                in zip(
                    state,
                    self.novel_candidate
                )
            ]

        else:

            self.novel_count = 1

            self.novel_candidate = list(
                state
            )

        return (
            self.novel_count
            >= NOVELTY_CONFIRMATIONS
        )

    # ========================================================
    # CREATE NEW NEURON
    # ========================================================

    def create_neuron(
        self,
        state,
        parent
    ):

        if len(
            self.neurons
        ) >= MAX_NEURONS:

            return None

        if (
            self.generation
            - self.last_birth
            < BIRTH_COOLDOWN
        ):

            return None

        neuron_id = (
            f"N{self.next_id:04d}"
        )

        self.next_id += 1

        child = Neuron(
            neuron_id,
            list(state),
            cluster=(
                parent.cluster
                if parent
                else "novel"
            ),
            parent=(
                parent.id
                if parent
                else None
            ),
            born=self.generation
        )

        child.confidence = 0.30
        child.fitness = 0.30

        self.neurons[
            neuron_id
        ] = child

        if parent:

            parent.children.append(
                neuron_id
            )

        self.created_total += 1

        self.last_birth = (
            self.generation
        )

        self.novel_count = 0
        self.novel_candidate = None

        print()
        print(
            "============================================================"
        )
        print(
            "NEUROGENESIS"
        )
        print(
            f"NEW NEURON : {neuron_id}"
        )
        print(
            f"PARENT      : "
            f"{parent.id if parent else 'ROOT'}"
        )
        print(
            f"GENERATION  : "
            f"{self.generation}"
        )
        print(
            "REASON      : CONFIRMED NOVEL SENSOR STATE"
        )
        print(
            f"POPULATION  : "
            f"{len(self.neurons)}"
        )
        print(
            "============================================================"
        )
        print()

        return child

    # ========================================================
    # PREDICTION
    # ========================================================

    def predict_next(self, neuron):

        if neuron is None:
            return None

        candidates = []

        for next_id in (
            neuron.next_states
        ):

            target = self.neurons.get(
                next_id
            )

            if target is None:
                continue

            candidates.append(
                target
            )

        if not candidates:
            return None

        return max(
            candidates,
            key=lambda x: x.fitness
        )

    # ========================================================
    # ACTION POLICY
    # ========================================================

    def choose_action(
        self,
        neuron,
        distance_value,
        state_change
    ):

        if neuron is None:
            return "observe"

        if distance_value > (
            NOVELTY_THRESHOLD
        ):

            return "investigate_novel_state"

        if neuron.prediction_error > 0.20:

            return "observe_uncertain_state"

        if state_change > 0.20:

            return "track_state_change"

        if neuron.reward > 0.70:

            return "repeat_stable_pattern"

        return "observe"

    # ========================================================
    # INTERNAL REWARD
    # ========================================================

    def calculate_internal_reward(
        self,
        distance_value,
        state_change,
        prediction_correct
    ):

        recognition = math.exp(
            -3.0 * distance_value
        )

        stability = (
            1.0
            - clamp(
                state_change
            )
        )

        prediction = (
            1.0
            if prediction_correct
            else 0.35
        )

        reward = (
            0.50 * recognition
            + 0.20 * stability
            + 0.30 * prediction
        )

        return clamp(
            reward
        )

    # ========================================================
    # PROCESS
    # ========================================================

    def process(
        self,
        sensor_data
    ):

        state, feature_names = (
            self.encoder.encode(
                sensor_data
            )
        )

        self.raw_sensor_count = len(
            flatten_numbers(
                sensor_data
            )
        )

        if not state:
            return None

        self.states_learned += 1
        self.generation += 1

        # ----------------------------------------------------
        # Initial population
        # ----------------------------------------------------

        self.initialize(
            state
        )

        # ----------------------------------------------------
        # Current winner
        # ----------------------------------------------------

        winner, d = (
            self.find_winner(
                state
            )
        )

        if winner is None:
            return None

        # ----------------------------------------------------
        # State change
        # ----------------------------------------------------

        if self.previous_state is None:

            state_change = 0.0

        else:

            state_change = (
                euclidean_distance(
                    state,
                    self.previous_state
                )
            )

        # ----------------------------------------------------
        # Prediction
        # ----------------------------------------------------

        predicted_next_id = None

        if self.previous_prediction is not None:

            predicted_next_id = (
                self.previous_prediction.id
            )

        prediction_correct = (
            predicted_next_id
            == winner.id
        )

        # ----------------------------------------------------
        # Learn winner
        # ----------------------------------------------------

        winner.learn(
            state,
            self.generation
        )

        # ----------------------------------------------------
        # Novelty
        # ----------------------------------------------------

        new_neuron = None

        novelty_confirmed = (
            self.confirm_novelty(
                state,
                d
            )
        )

        if novelty_confirmed:

            new_neuron = (
                self.create_neuron(
                    self.novel_candidate,
                    winner
                )
            )

            if new_neuron is not None:

                winner = new_neuron

                d = winner.distance(
                    state
                )

        # ----------------------------------------------------
        # Transition learning
        # ----------------------------------------------------

        if self.previous_winner is not None:

            self.previous_winner.add_next(
                winner.id
            )

            winner.add_previous(
                self.previous_winner.id
            )

            self.transitions.append(
                {
                    "time": timestamp(),
                    "from":
                        self.previous_winner.id,
                    "to":
                        winner.id
                }
            )

        # ----------------------------------------------------
        # Action
        # ----------------------------------------------------

        action = self.choose_action(
            winner,
            d,
            state_change
        )

        winner.add_action(
            action
        )

        # ----------------------------------------------------
        # Reward
        # ----------------------------------------------------

        reward = (
            self.calculate_internal_reward(
                d,
                state_change,
                prediction_correct
            )
        )

        winner.update_reward(
            reward
        )

        # ----------------------------------------------------
        # Memory
        # ----------------------------------------------------

        state_id = (
            self.states_learned
        )

        winner.remember(
            state_id,
            d
        )

        self.memory.append(
            {
                "state_id":
                    state_id,

                "time":
                    timestamp(),

                "neuron":
                    winner.id,

                "distance":
                    round(
                        d,
                        6
                    ),

                "state_change":
                    round(
                        state_change,
                        6
                    ),

                "prediction":
                    predicted_next_id,

                "prediction_correct":
                    prediction_correct,

                "action":
                    action,

                "reward":
                    round(
                        reward,
                        6
                    )
            }
        )

        # ----------------------------------------------------
        # Next prediction
        # ----------------------------------------------------

        predicted_next = (
            self.predict_next(
                winner
            )
        )

        self.previous_prediction = (
            predicted_next
        )

        self.previous_winner = (
            winner
        )

        self.previous_state = list(
            state
        )

        result = {

            "winner":
                winner.id,

            "distance":
                d,

            "state_change":
                state_change,

            "novelty":
                self.novel_count,

            "action":
                action,

            "reward":
                reward,

            "confidence":
                winner.confidence,

            "fitness":
                winner.fitness,

            "prediction":
                (
                    predicted_next.id
                    if predicted_next
                    else None
                ),

            "prediction_correct":
                prediction_correct,

            "created":
                (
                    new_neuron is not None
                ),

            "sensor_values":
                self.raw_sensor_count,

            "features":
                len(feature_names),

            "population":
                len(self.neurons)
        }

        self.last_result = result

        return result

    # ========================================================
    # PRUNE
    # ========================================================

    def prune(self):

        if len(
            self.neurons
        ) <= MIN_NEURONS:

            return 0

        protected = set()

        # Strongest neurons are protected.
        ranked = sorted(
            self.neurons.values(),
            key=lambda x: x.fitness,
            reverse=True
        )

        for neuron in ranked[
            :MIN_NEURONS
        ]:

            protected.add(
                neuron.id
            )

        # Parents with live children are protected.
        for neuron in self.neurons.values():

            if any(
                child in self.neurons
                for child in neuron.children
            ):

                protected.add(
                    neuron.id
                )

        removed = 0

        for neuron in list(
            self.neurons.values()
        ):

            if len(
                self.neurons
            ) <= MIN_NEURONS:

                break

            if neuron.id in protected:

                continue

            if neuron.age < PRUNE_AFTER:

                continue

            if neuron.fitness >= (
                PRUNE_FITNESS
            ):

                continue

            del self.neurons[
                neuron.id
            ]

            removed += 1

            self.pruned_total += 1

            print(
                f"PRUNED WEAK NEURON: "
                f"{neuron.id}"
            )

        return removed

    # ========================================================
    # SAVE
    # ========================================================

    def save(self):

        os.makedirs(
            "neurons",
            exist_ok=True
        )

        state = {

            "version": 4,

            "saved_at":
                timestamp(),

            "generation":
                self.generation,

            "next_id":
                self.next_id,

            "states_learned":
                self.states_learned,

            "created_total":
                self.created_total,

            "pruned_total":
                self.pruned_total,

            "neurons": {}
        }

        for neuron_id, neuron in (
            self.neurons.items()
        ):

            state[
                "neurons"
            ][
                neuron_id
            ] = {

                "id":
                    neuron.id,

                "prototype":
                    neuron.prototype,

                "cluster":
                    neuron.cluster,

                "confidence":
                    neuron.confidence,

                "fitness":
                    neuron.fitness,

                "age":
                    neuron.age,

                "parent":
                    neuron.parent,

                "children":
                    list(
                        neuron.children
                    ),

                "activation_count":
                    neuron.activation_count,

                "associated_memories":
                    list(
                        neuron.associated_memories
                    ),

                "previous_states":
                    list(
                        neuron.previous_states
                    ),

                "next_states":
                    list(
                        neuron.next_states
                    ),

                "actions":
                    list(
                        neuron.actions
                    ),

                "reward":
                    neuron.reward,

                "prediction_error":
                    neuron.prediction_error,

                "stability":
                    neuron.stability,

                "last_distance":
                    neuron.last_distance,

                "last_activation":
                    neuron.last_activation,

                "birth_generation":
                    neuron.birth_generation
            }

        tmp = (
            STATE_FILE
            + ".tmp"
        )

        with open(
            tmp,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                state,
                file,
                indent=2
            )

        os.replace(
            tmp,
            STATE_FILE
        )

        with open(
            MEMORY_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                list(
                    self.memory
                ),
                file,
                indent=2
            )

        lineage = {}

        for neuron_id, neuron in (
            self.neurons.items()
        ):

            lineage[
                neuron_id
            ] = {

                "id":
                    neuron.id,

                "parent":
                    neuron.parent,

                "children":
                    list(
                        neuron.children
                    ),

                "born":
                    neuron.birth_generation,

                "cluster":
                    neuron.cluster,

                "fitness":
                    neuron.fitness
            }

        with open(
            LINEAGE_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                lineage,
                file,
                indent=2
            )

    # ========================================================
    # LOAD
    # ========================================================

    def load(self):

        if not os.path.exists(
            STATE_FILE
        ):

            return

        try:

            with open(
                STATE_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(
                    file
                )

            self.generation = int(
                data.get(
                    "generation",
                    0
                )
            )

            self.next_id = int(
                data.get(
                    "next_id",
                    0
                )
            )

            self.states_learned = int(
                data.get(
                    "states_learned",
                    0
                )
            )

            self.created_total = int(
                data.get(
                    "created_total",
                    0
                )
            )

            self.pruned_total = int(
                data.get(
                    "pruned_total",
                    0
                )
            )

            loaded = data.get(
                "neurons",
                {}
            )

            if not isinstance(
                loaded,
                dict
            ):

                loaded = {}

            for neuron_id, d in (
                loaded.items()
            ):

                neuron = Neuron(
                    neuron_id,
                    d.get(
                        "prototype",
                        []
                    ),
                    d.get(
                        "cluster",
                        "unknown"
                    ),
                    d.get(
                        "parent"
                    ),
                    d.get(
                        "birth_generation",
                        0
                    )
                )

                neuron.confidence = float(
                    d.get(
                        "confidence",
                        0.20
                    )
                )

                neuron.fitness = float(
                    d.get(
                        "fitness",
                        0.20
                    )
                )

                neuron.age = int(
                    d.get(
                        "age",
                        0
                    )
                )

                neuron.children = list(
                    d.get(
                        "children",
                        []
                    )
                )

                neuron.activation_count = int(
                    d.get(
                        "activation_count",
                        0
                    )
                )

                neuron.associated_memories = deque(
                    d.get(
                        "associated_memories",
                        []
                    ),
                    maxlen=100
                )

                neuron.previous_states = deque(
                    d.get(
                        "previous_states",
                        []
                    ),
                    maxlen=PREDICTION_MEMORY
                )

                neuron.next_states = deque(
                    d.get(
                        "next_states",
                        []
                    ),
                    maxlen=PREDICTION_MEMORY
                )

                neuron.actions = deque(
                    d.get(
                        "actions",
                        []
                    ),
                    maxlen=PREDICTION_MEMORY
                )

                neuron.reward = float(
                    d.get(
                        "reward",
                        0.0
                    )
                )

                neuron.prediction_error = float(
                    d.get(
                        "prediction_error",
                        0.0
                    )
                )

                neuron.stability = float(
                    d.get(
                        "stability",
                        0.0
                    )
                )

                neuron.last_distance = float(
                    d.get(
                        "last_distance",
                        1.0
                    )
                )

                neuron.last_activation = int(
                    d.get(
                        "last_activation",
                        0
                    )
                )

                self.neurons[
                    neuron_id
                ] = neuron

            if os.path.exists(
                MEMORY_FILE
            ):

                with open(
                    MEMORY_FILE,
                    "r",
                    encoding="utf-8"
                ) as file:

                    memories = json.load(
                        file
                    )

                if isinstance(
                    memories,
                    list
                ):

                    self.memory = deque(
                        memories,
                        maxlen=MEMORY_LIMIT
                    )

            print(
                f"[V4 STATE] Loaded "
                f"{len(self.neurons)} neurons | "
                f"generation={self.generation}"
            )

        except Exception as error:

            print(
                f"[V4 STATE] Load failed: "
                f"{error}"
            )

            self.neurons = {}

    # ========================================================
    # CHECKPOINT
    # ========================================================

    def checkpoint(self):

        self.save()

        print()
        print(
            "============================================================"
        )
        print(
            "COGNITIVE SENSOR BRAIN CHECKPOINT"
        )
        print(
            "============================================================"
        )

        print(
            f"Generation       : "
            f"{self.generation}"
        )

        print(
            f"Live neurons     : "
            f"{len(self.neurons)}"
        )

        print(
            f"Next neuron ID   : "
            f"N{self.next_id:04d}"
        )

        print(
            f"Created total    : "
            f"{self.created_total}"
        )

        print(
            f"Pruned total     : "
            f"{self.pruned_total}"
        )

        print(
            f"States learned   : "
            f"{self.states_learned}"
        )

        print(
            f"Memory entries   : "
            f"{len(self.memory)}"
        )

        print(
            f"Transitions      : "
            f"{len(self.transitions)}"
        )

        print(
            f"Raw sensor nums  : "
            f"{self.raw_sensor_count}"
        )

        if self.last_result:

            print(
                f"Winner           : "
                f"{self.last_result['winner']}"
            )

            print(
                f"Prediction       : "
                f"{self.last_result['prediction']}"
            )

            print(
                f"Action           : "
                f"{self.last_result['action']}"
            )

            print(
                f"Reward           : "
                f"{self.last_result['reward']:.3f}"
            )

            print(
                f"Confidence       : "
                f"{self.last_result['confidence']:.3f}"
            )

            print(
                f"Fitness          : "
                f"{self.last_result['fitness']:.3f}"
            )

        print(
            "============================================================"
        )

        print()

        ranked = sorted(
            self.neurons.values(),
            key=lambda x: x.fitness,
            reverse=True
        )

        print(
            "TOP LEARNED NEURONS:"
        )

        for neuron in ranked[:10]:

            predicted = (
                self.predict_next(
                    neuron
                )
            )

            prediction_id = (
                predicted.id
                if predicted
                else "None"
            )

            print(
                f"  {neuron.id} | "
                f"fitness={neuron.fitness:.3f} | "
                f"confidence={neuron.confidence:.3f} | "
                f"activations={neuron.activation_count} | "
                f"parent={neuron.parent} | "
                f"children={len(neuron.children)} | "
                f"next={prediction_id}"
            )

        print()


# ============================================================
# FLATTEN RAW SENSOR VALUES
# ============================================================

def flatten_numbers(
    value
):

    result = []

    if isinstance(
        value,
        dict
    ):

        for child in value.values():

            result.extend(
                flatten_numbers(
                    child
                )
            )

    elif isinstance(
        value,
        list
    ):

        for child in value:

            result.extend(
                flatten_numbers(
                    child
                )
            )

    else:

        number = safe_float(
            value
        )

        if number is not None:

            result.append(
                number
            )

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    global RUNNING

    def stop(
        signum,
        frame
    ):

        global RUNNING

        RUNNING = False

        print()
        print(
            "STOP REQUESTED..."
        )

    signal.signal(
        signal.SIGINT,
        stop
    )

    signal.signal(
        signal.SIGTERM,
        stop
    )

    print(
        "============================================================"
    )

    print(
        "LIVE ANDROID SENSOR COGNITIVE BRAIN V4"
    )

    print(
        "============================================================"
    )

    print(
        "REAL TERMUX SENSOR DATA     : ON"
    )

    print(
        "SENSOR-SPECIFIC ENCODING    : ON"
    )

    print(
        "EMA NOISE FILTER             : ON"
    )

    print(
        "TEMPORAL STATE               : ON"
    )

    print(
        "COMPETITIVE NEURONS          : ON"
    )

    print(
        "NEXT-STATE PREDICTION        : ON"
    )

    print(
        "ACTION SUGGESTION            : ON"
    )

    print(
        "REWARD                       : ON"
    )

    print(
        "FITNESS                      : ON"
    )

    print(
        "NOVELTY DETECTION            : ON"
    )

    print(
        "NEUROGENESIS                 : ON"
    )

    print(
        "PERSISTENT MEMORY            : ON"
    )

    print(
        "LINEAGE                      : ON"
    )

    print(
        "PRUNING                      : ON"
    )

    print(
        f"MAX NEURONS                  : "
        f"{MAX_NEURONS}"
    )

    print(
        "============================================================"
    )

    print()

    brain = Brain()

    last_checkpoint = time.monotonic()

    try:

        while RUNNING:

            sensor_data = (
                read_sensor_snapshot()
            )

            if not sensor_data:

                print(
                    "WAITING FOR TERMUX SENSOR DATA..."
                )

                time.sleep(
                    1.0
                )

                continue

            result = (
                brain.process(
                    sensor_data
                )
            )

            if result is None:

                continue

            print(
                f"Gen {brain.generation:6d} | "
                f"neurons={len(brain.neurons):3d} | "
                f"winner={result['winner']} | "
                f"distance={result['distance']:.5f} | "
                f"change={result['state_change']:.5f} | "
                f"novelty={result['novelty']}/"
                f"{NOVELTY_CONFIRMATIONS} | "
                f"prediction={result['prediction']} | "
                f"action={result['action']} | "
                f"reward={result['reward']:.3f} | "
                f"confidence={result['confidence']:.3f} | "
                f"fitness={result['fitness']:.3f}"
            )

            if result["created"]:

                print(
                    "    >>> NEW SENSOR REPRESENTATION LEARNED"
                )

            if result[
                "prediction_correct"
            ]:

                print(
                    "    >>> PREDICTION CORRECT"
                )

            if (
                time.monotonic()
                - last_checkpoint
                >= CHECKPOINT_SECONDS
            ):

                brain.checkpoint()

                last_checkpoint = (
                    time.monotonic()
                )

            time.sleep(
                SAMPLE_DELAY
            )

    finally:

        print()
        print(
            "============================================================"
        )

        print(
            "SAVING V4 BRAIN..."
        )

        brain.save()

        print(
            f"Generation       : "
            f"{brain.generation}"
        )

        print(
            f"Live neurons     : "
            f"{len(brain.neurons)}"
        )

        print(
            f"Created total    : "
            f"{brain.created_total}"
        )

        print(
            f"Pruned total     : "
            f"{brain.pruned_total}"
        )

        print(
            f"States learned   : "
            f"{brain.states_learned}"
        )

        print(
            "FILES SAVED:"
        )

        print(
            f"  {STATE_FILE}"
        )

        print(
            f"  {MEMORY_FILE}"
        )

        print(
            f"  {LINEAGE_FILE}"
        )

        print(
            "============================================================"
        )


if __name__ == "__main__":
    main()

