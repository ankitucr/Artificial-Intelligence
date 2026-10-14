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
# LIVE SENSOR BRAIN V3
# Real Android Sensors -> Temporal Learning -> Neurogenesis
# ============================================================

STATE_FILE = "neurons/sensor_brain_v3_state.json"
MEMORY_FILE = "neurons/sensor_brain_v3_memory.json"
LINEAGE_FILE = "neurons/sensor_brain_v3_lineage.json"

MAX_NEURONS = 100
INITIAL_NEURONS = 4

SAMPLE_DELAY = 0.40

EMA_ALPHA = 0.20

NOVELTY_THRESHOLD = 0.22
NOVELTY_CONFIRMATIONS = 5
BIRTH_COOLDOWN = 10

LEARNING_RATE = 0.08
MIN_LEARNING_RATE = 0.012

MEMORY_LIMIT = 1000
TRANSITION_LIMIT = 500

PRUNE_AFTER = 500
PRUNE_FITNESS = 0.06

FEATURE_DECIMALS = 4

RUNNING = True


# ============================================================
# TIME
# ============================================================

def timestamp():
    return datetime.now().isoformat(timespec="milliseconds")


# ============================================================
# SAFE NUMERIC
# ============================================================

def number(value):
    try:
        value = float(value)

        if math.isfinite(value):
            return value

    except Exception:
        pass

    return None


# ============================================================
# CLAMP
# ============================================================

def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


# ============================================================
# VECTOR DISTANCE
# ============================================================

def distance(a, b):

    if not a or not b:
        return 999.0

    n = min(len(a), len(b))

    if n == 0:
        return 999.0

    total = 0.0

    for i in range(n):

        d = float(a[i]) - float(b[i])

        total += d * d

    return math.sqrt(total / n)


# ============================================================
# TERMUX SENSOR API
# ============================================================

def read_sensor_snapshot():

    try:

        result = subprocess.run(
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

        if result.returncode != 0:
            return {}

        output = result.stdout.strip()

        if not output:
            return {}

        return json.loads(output)

    except Exception:
        return {}


# ============================================================
# GET SENSOR VALUES
# ============================================================

def get_sensor(
    data,
    keywords,
    minimum_values=1
):

    if not isinstance(data, dict):
        return []

    for name, obj in data.items():

        lname = name.lower()

        matched = True

        for keyword in keywords:

            if keyword.lower() not in lname:
                matched = False
                break

        if not matched:
            continue

        if not isinstance(obj, dict):
            continue

        values = obj.get("values", [])

        if not isinstance(values, list):
            continue

        clean = []

        for value in values:

            value = number(value)

            if value is not None:
                clean.append(value)

        if len(clean) >= minimum_values:
            return clean

    return []


# ============================================================
# FEATURE NORMALIZATION
# ============================================================

def normalize_signed(value, scale):

    if scale <= 0:
        return 0.5

    x = value / scale

    return clamp(
        0.5 + 0.5 * math.tanh(x)
    )


def normalize_positive(value, scale):

    if value < 0:
        return 0.0

    if scale <= 0:
        return 0.0

    return clamp(
        value / scale
    )


# ============================================================
# SENSOR ENCODER
# ============================================================

class SensorEncoder:

    def __init__(self):

        self.feature_names = []

        self.last_vector = None

        self.ema_vector = None

    def encode(self, data):

        features = []
        names = []

        # ----------------------------------------------------
        # ACCELEROMETER
        # ----------------------------------------------------

        acc = get_sensor(
            data,
            ["accelerometer", "non-wakeup"],
            3
        )

        if not acc:

            acc = get_sensor(
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

            features.append(
                normalize_signed(
                    value,
                    10.0
                )
            )

            names.append(
                f"accelerometer_{i}"
            )

        # ----------------------------------------------------
        # GYROSCOPE
        # ----------------------------------------------------

        gyro = get_sensor(
            data,
            ["gyroscope", "non-wakeup"],
            3
        )

        if not gyro:

            gyro = get_sensor(
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

            features.append(
                normalize_signed(
                    value,
                    5.0
                )
            )

            names.append(
                f"gyroscope_{i}"
            )

        # ----------------------------------------------------
        # MAGNETOMETER
        # ----------------------------------------------------

        mag = get_sensor(
            data,
            ["magnetometer", "non-wakeup"],
            3
        )

        if not mag:

            mag = get_sensor(
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

            features.append(
                normalize_signed(
                    value,
                    100.0
                )
            )

            names.append(
                f"magnetometer_{i}"
            )

        # ----------------------------------------------------
        # GRAVITY
        # ----------------------------------------------------

        gravity = get_sensor(
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

            features.append(
                normalize_signed(
                    value,
                    10.0
                )
            )

            names.append(
                f"gravity_{i}"
            )

        # ----------------------------------------------------
        # LINEAR ACCELERATION
        # ----------------------------------------------------

        linear = get_sensor(
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

            features.append(
                normalize_signed(
                    value,
                    10.0
                )
            )

            names.append(
                f"linear_acceleration_{i}"
            )

        # ----------------------------------------------------
        # ROTATION VECTOR
        # ----------------------------------------------------

        rotation = get_sensor(
            data,
            ["rotation vector", "non-wakeup"],
            4
        )

        if not rotation:

            rotation = get_sensor(
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

            features.append(
                normalize_signed(
                    value,
                    1.0
                )
            )

            names.append(
                f"rotation_{i}"
            )

        # ----------------------------------------------------
        # LIGHT
        # ----------------------------------------------------

        light = get_sensor(
            data,
            ["light sensor"],
            1
        )

        if not light:

            light = get_sensor(
                data,
                ["lux"],
                1
            )

        value = (
            light[0]
            if light
            else 0.0
        )

        features.append(
            normalize_positive(
                value,
                1000.0
            )
        )

        names.append(
            "light"
        )

        # ----------------------------------------------------
        # PROXIMITY
        # ----------------------------------------------------

        proximity = get_sensor(
            data,
            ["proximity"],
            1
        )

        value = (
            proximity[0]
            if proximity
            else 0.0
        )

        features.append(
            normalize_positive(
                value,
                10.0
            )
        )

        names.append(
            "proximity"
        )

        # ----------------------------------------------------
        # PEDOMETER
        # ----------------------------------------------------

        pedometer = get_sensor(
            data,
            ["pedometer"],
            1
        )

        value = (
            pedometer[0]
            if pedometer
            else 0.0
        )

        # Compress large absolute step counter.
        features.append(
            normalize_positive(
                value % 1000,
                1000.0
            )
        )

        names.append(
            "pedometer_mod"
        )

        # ----------------------------------------------------
        # ACTIVITY RECOGNITION
        # ----------------------------------------------------

        activity = get_sensor(
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

            features.append(
                normalize_positive(
                    value,
                    5.0
                )
            )

            names.append(
                f"activity_{i}"
            )

        # ----------------------------------------------------
        # FINAL VECTOR
        # ----------------------------------------------------

        # Keep names stable.
        self.feature_names = names

        # Round microscopic sensor noise.
        features = [
            round(
                clamp(value),
                FEATURE_DECIMALS
            )
            for value in features
        ]

        vector = features

        # ----------------------------------------------------
        # EMA FILTER
        # ----------------------------------------------------

        if self.ema_vector is None:

            self.ema_vector = list(
                vector
            )

        else:

            self.ema_vector = [
                (
                    EMA_ALPHA * value
                    + (1.0 - EMA_ALPHA) * old
                )

                for value, old
                in zip(
                    vector,
                    self.ema_vector
                )
            ]

        # ----------------------------------------------------
        # CHANGE VECTOR
        # ----------------------------------------------------

        if self.last_vector is None:

            change = [
                0.0
                for _ in self.ema_vector
            ]

        else:

            change = [
                abs(
                    current - previous
                )

                for current, previous
                in zip(
                    self.ema_vector,
                    self.last_vector
                )
            ]

        # Add temporal change features.
        combined = (
            self.ema_vector
            + change
        )

        self.last_vector = list(
            self.ema_vector
        )

        return (
            combined,
            names
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

        # Requested fields
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
            maxlen=50
        )

        self.next_states = deque(
            maxlen=50
        )

        self.actions = deque(
            maxlen=50
        )

        self.reward = 0.0

        # Additional learning state
        self.prediction_error = 0.0

        self.stability = 0.0

        self.last_distance = 1.0

        self.last_activation = 0

        self.correct_predictions = 0

        self.total_predictions = 0

        self.birth_generation = born

    # --------------------------------------------------------
    # DISTANCE
    # --------------------------------------------------------

    def distance(
        self,
        state
    ):

        return distance(
            self.prototype,
            state
        )

    # --------------------------------------------------------
    # LEARN
    # --------------------------------------------------------

    def learn(
        self,
        state,
        generation
    ):

        d = self.distance(
            state
        )

        self.last_distance = d

        # Learning rate decreases slowly.
        lr = max(
            MIN_LEARNING_RATE,
            LEARNING_RATE
            / math.sqrt(
                1.0
                + self.activation_count / 50.0
            )
        )

        if d < NOVELTY_THRESHOLD:

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

        self.prototype = [
            clamp(x, -1.0, 1.0)
            for x in self.prototype
        ]

        self.age += 1

        self.activation_count += 1

        self.last_activation = generation

        # ----------------------------------------------------
        # Confidence
        # ----------------------------------------------------

        confidence_now = math.exp(
            -4.0 * d
        )

        self.confidence = (
            0.94
            * self.confidence
            + 0.06
            * confidence_now
        )

        # ----------------------------------------------------
        # Prediction error
        # ----------------------------------------------------

        self.prediction_error = (
            0.90
            * self.prediction_error
            + 0.10
            * d
        )

        # ----------------------------------------------------
        # Stability
        # ----------------------------------------------------

        stability_now = (
            1.0
            - clamp(d)
        )

        self.stability = (
            0.95
            * self.stability
            + 0.05
            * stability_now
        )

        # ----------------------------------------------------
        # Fitness
        # ----------------------------------------------------

        usage = min(
            1.0,
            self.activation_count / 200.0
        )

        prediction_quality = (
            1.0
            - clamp(
                self.prediction_error
            )
        )

        self.fitness = clamp(
            0.45
            * self.confidence

            + 0.25
            * self.stability

            + 0.20
            * usage

            + 0.10
            * prediction_quality
        )

        return d

    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    def remember(
        self,
        state_id,
        distance_value
    ):

        self.associated_memories.append(
            {
                "state_id": state_id,
                "distance": round(
                    float(distance_value),
                    6
                ),
                "time": timestamp()
            }
        )

    # --------------------------------------------------------
    # ACTION
    # --------------------------------------------------------

    def register_action(
        self,
        action
    ):

        self.actions.append(
            {
                "time": timestamp(),
                "action": action
            }
        )

    # --------------------------------------------------------
    # REWARD
    # --------------------------------------------------------

    def update_reward(
        self,
        reward
    ):

        reward = clamp(
            reward
        )

        self.reward = (
            0.95
            * self.reward
            + 0.05
            * reward
        )


# ============================================================
# BRAIN
# ============================================================

class SensorBrain:

    def __init__(self):

        self.neurons = {}

        self.next_id = 0

        self.generation = 0

        self.total_states = 0

        self.created_total = 0

        self.pruned_total = 0

        self.last_birth_generation = (
            -BIRTH_COOLDOWN
        )

        self.novelty_count = 0

        self.novel_candidate = None

        self.previous_winner = None

        self.previous_state = None

        self.state_history = deque(
            maxlen=20
        )

        self.memory = deque(
            maxlen=MEMORY_LIMIT
        )

        self.transitions = deque(
            maxlen=TRANSITION_LIMIT
        )

        self.encoder = SensorEncoder()

        self.sensor_count = 0

    # ========================================================
    # INITIAL NEURONS
    # ========================================================

    def initialize(self):

        # Deliberately distinct seed prototypes.
        seeds = [
            0.10,
            0.30,
            0.60,
            0.90
        ]

        for seed in seeds:

            prototype = [
                seed
                for _ in range(54)
            ]

            neuron = self._new_neuron(
                prototype,
                cluster="state"
            )

            neuron.confidence = 0.30

    # ========================================================
    # CREATE RAW NEURON
    # ========================================================

    def _new_neuron(
        self,
        prototype,
        cluster="unknown",
        parent=None
    ):

        neuron_id = (
            f"N{self.next_id:04d}"
        )

        self.next_id += 1

        neuron = Neuron(
            neuron_id,
            prototype,
            cluster,
            parent,
            self.generation
        )

        self.neurons[
            neuron_id
        ] = neuron

        self.created_total += 1

        if parent is not None:

            parent_neuron = self.neurons.get(
                parent
            )

            if parent_neuron is not None:

                parent_neuron.children.append(
                    neuron_id
                )

        return neuron

    # ========================================================
    # WINNER
    # ========================================================

    def find_winner(
        self,
        state
    ):

        best = None
        best_distance = 999.0

        for neuron in self.neurons.values():

            d = neuron.distance(
                state
            )

            # Mild anti-monopoly penalty.
            usage = min(
                0.08,
                neuron.activation_count
                / 50000.0
            )

            score = d + usage

            if score < best_distance:

                best_distance = score

                best = neuron

        return (
            best,
            best_distance
        )

    # ========================================================
    # STABLE NOVELTY
    # ========================================================

    def novelty_confirmed(
        self,
        state,
        distance_value
    ):

        if distance_value < NOVELTY_THRESHOLD:

            self.novelty_count = 0
            self.novel_candidate = None

            return False

        if self.novel_candidate is None:

            self.novel_candidate = list(
                state
            )

            self.novelty_count = 1

            return False

        candidate_distance = distance(
            state,
            self.novel_candidate
        )

        if candidate_distance < (
            NOVELTY_THRESHOLD * 0.75
        ):

            self.novelty_count += 1

            self.novel_candidate = [
                0.30 * current
                + 0.70 * old

                for current, old
                in zip(
                    state,
                    self.novel_candidate
                )
            ]

        else:

            self.novelty_count = 1

            self.novel_candidate = list(
                state
            )

        if self.novelty_count >= (
            NOVELTY_CONFIRMATIONS
        ):

            return True

        return False

    # ========================================================
    # NEUROGENESIS
    # ========================================================

    def maybe_create(
        self,
        state,
        winner,
        distance_value
    ):

        if len(
            self.neurons
        ) >= MAX_NEURONS:

            return None

        if (
            self.generation
            - self.last_birth_generation
            < BIRTH_COOLDOWN
        ):

            return None

        confirmed = (
            self.novelty_confirmed(
                state,
                distance_value
            )
        )

        if not confirmed:

            return None

        if self.novel_candidate is None:

            return None

        parent_id = (
            winner.id
            if winner is not None
            else None
        )

        child = self._new_neuron(
            list(
                self.novel_candidate
            ),
            cluster=(
                winner.cluster
                if winner is not None
                else "novel"
            ),
            parent=parent_id
        )

        child.confidence = 0.30

        child.fitness = 0.30

        self.last_birth_generation = (
            self.generation
        )

        self.novelty_count = 0

        self.novel_candidate = None

        print()
        print(
            "##################################################"
        )
        print(
            "NEUROGENESIS"
        )
        print(
            f"NEW NEURON : {child.id}"
        )
        print(
            f"PARENT      : "
            f"{parent_id or 'ROOT'}"
        )
        print(
            f"GENERATION  : "
            f"{self.generation}"
        )
        print(
            f"DISTANCE    : "
            f"{distance_value:.5f}"
        )
        print(
            "REASON      : REPEATED NOVEL SENSOR STATE"
        )
        print(
            f"POPULATION  : "
            f"{len(self.neurons)}"
        )
        print(
            "##################################################"
        )
        print()

        return child

    # ========================================================
    # STATE TRANSITION
    # ========================================================

    def record_transition(
        self,
        previous,
        current
    ):

        if previous is None:
            return

        if current is None:
            return

        if previous.id == current.id:
            return

        current.add_previous(
            previous.id
        )

        previous.add_next(
            current.id
        )

        transition = {
            "time": timestamp(),
            "from": previous.id,
            "to": current.id
        }

        self.transitions.append(
            transition
        )

    # ========================================================
    # ACTION POLICY
    # ========================================================

    def suggest_action(
        self,
        winner,
        state_change
    ):

        if winner is None:
            return "observe"

        # This is only an internal policy suggestion.
        # No physical device action is executed.

        if state_change > 0.30:
            return "investigate_change"

        if winner.prediction_error > 0.20:
            return "observe_uncertain_state"

        if winner.reward > 0.70:
            return "repeat_stable_behavior"

        return "observe"

    # ========================================================
    # PROCESS
    # ========================================================

    def process_sensor_data(
        self,
        data
    ):

        state, feature_names = (
            self.encoder.encode(
                data
            )
        )

        self.sensor_count = len(
            flatten_sensor_numbers(
                data
            )
        )

        self.total_states += 1

        self.generation += 1

        self.state_history.append(
            list(state)
        )

        winner, d = (
            self.find_winner(
                state
            )
        )

        state_change = 0.0

        if self.previous_state is not None:

            state_change = distance(
                state,
                self.previous_state
            )

        # ----------------------------------------------------
        # Learning
        # ----------------------------------------------------

        if winner is not None:

            winner.learn(
                state,
                self.generation
            )

        # ----------------------------------------------------
        # Neurogenesis
        # ----------------------------------------------------

        child = self.maybe_create(
            state,
            winner,
            d
        )

        active = (
            child
            if child is not None
            else winner
        )

        if active is None:
            return None

        # ----------------------------------------------------
        # Transition
        # ----------------------------------------------------

        self.record_transition(
            self.previous_winner,
            active
        )

        # ----------------------------------------------------
        # Action
        # ----------------------------------------------------

        action = self.suggest_action(
            active,
            state_change
        )

        active.register_action(
            action
        )

        # ----------------------------------------------------
        # Reward
        # ----------------------------------------------------

        recognition_reward = (
            math.exp(
                -3.5 * d
            )
        )

        transition_reward = (
            1.0
            - clamp(
                state_change
            )
        )

        reward = clamp(
            0.70
            * recognition_reward

            + 0.30
            * transition_reward
        )

        active.update_reward(
            reward
        )

        # ----------------------------------------------------
        # Memory
        # ----------------------------------------------------

        active.remember(
            self.total_states,
            d
        )

        self.memory.append(
            {
                "state_id":
                    self.total_states,

                "time":
                    timestamp(),

                "neuron":
                    active.id,

                "distance":
                    round(
                        float(d),
                        6
                    ),

                "state_change":
                    round(
                        float(state_change),
                        6
                    ),

                "action":
                    action,

                "reward":
                    round(
                        float(reward),
                        6
                    ),

                "sensor_features":
                    len(feature_names)
            }
        )

        # ----------------------------------------------------
        # Previous state
        # ----------------------------------------------------

        self.previous_state = list(
            state
        )

        self.previous_winner = active

        # ----------------------------------------------------
        # Pruning
        # ----------------------------------------------------

        pruned = 0

        if (
            self.generation > 0
            and self.generation % 100 == 0
        ):

            pruned = (
                self.prune()
            )

        return {
            "winner":
                active.id,

            "distance":
                d,

            "state_change":
                state_change,

            "action":
                action,

            "reward":
                reward,

            "confidence":
                active.confidence,

            "fitness":
                active.fitness,

            "novelty":
                self.novelty_count,

            "created":
                child is not None,

            "pruned":
                pruned,

            "sensor_features":
                len(feature_names),

            "raw_sensor_values":
                self.sensor_count,

            "population":
                len(self.neurons)
        }

    # ========================================================
    # PRUNING
    # ========================================================

    def prune(self):

        if len(
            self.neurons
        ) <= INITIAL_NEURONS:

            return 0

        # Keep top neurons and all neurons
        # that have children.
        ranked = sorted(
            self.neurons.values(),
            key=lambda n: n.fitness,
            reverse=True
        )

        protected = {
            n.id
            for n in ranked[:INITIAL_NEURONS]
        }

        for neuron in self.neurons.values():

            live_children = [
                child
                for child
                in neuron.children
                if child in self.neurons
            ]

            if live_children:

                protected.add(
                    neuron.id
                )

        removed = []

        for neuron in list(
            self.neurons.values()
        ):

            if len(
                self.neurons
            ) <= INITIAL_NEURONS:

                break

            if neuron.id in protected:

                continue

            if neuron.age < PRUNE_AFTER:

                continue

            if neuron.fitness >= PRUNE_FITNESS:

                continue

            removed.append(
                neuron.id
            )

            del self.neurons[
                neuron.id
            ]

        self.pruned_total += len(
            removed
        )

        for neuron_id in removed:

            print(
                f"PRUNED WEAK NEURON: "
                f"{neuron_id}"
            )

        return len(
            removed
        )

    # ========================================================
    # SAVE
    # ========================================================

    def save(self):

        os.makedirs(
            "neurons",
            exist_ok=True
        )

        state = {
            "version": 3,

            "saved_at":
                timestamp(),

            "generation":
                self.generation,

            "next_id":
                self.next_id,

            "total_states":
                self.total_states,

            "created_total":
                self.created_total,

            "pruned_total":
                self.pruned_total,

            "sensor_count":
                self.sensor_count,

            "feature_names":
                self.encoder.feature_names,

            "neurons": {}
        }

        for neuron_id, neuron in (
            self.neurons.items()
        ):

            state["neurons"][
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

        temp_file = (
            STATE_FILE
            + ".tmp"
        )

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                state,
                file,
                indent=2
            )

        os.replace(
            temp_file,
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

                state = json.load(file)

            self.generation = int(
                state.get(
                    "generation",
                    0
                )
            )

            self.next_id = int(
                state.get(
                    "next_id",
                    0
                )
            )

            self.total_states = int(
                state.get(
                    "total_states",
                    0
                )
            )

            self.created_total = int(
                state.get(
                    "created_total",
                    0
                )
            )

            self.pruned_total = int(
                state.get(
                    "pruned_total",
                    0
                )
            )

            self.sensor_count = int(
                state.get(
                    "sensor_count",
                    0
                )
            )

            feature_names = state.get(
                "feature_names",
                []
            )

            self.encoder.feature_names = (
                feature_names
            )

            loaded = state.get(
                "neurons",
                {}
            )

            # V3 owns its state format.
            if not isinstance(
                loaded,
                dict
            ):
                loaded = {}

            for neuron_id, data in loaded.items():

                neuron = Neuron(
                    neuron_id,
                    data.get(
                        "prototype",
                        []
                    ),
                    data.get(
                        "cluster",
                        "unknown"
                    ),
                    data.get(
                        "parent"
                    ),
                    data.get(
                        "birth_generation",
                        0
                    )
                )

                neuron.confidence = float(
                    data.get(
                        "confidence",
                        0.20
                    )
                )

                neuron.fitness = float(
                    data.get(
                        "fitness",
                        0.20
                    )
                )

                neuron.age = int(
                    data.get(
                        "age",
                        0
                    )
                )

                neuron.children = list(
                    data.get(
                        "children",
                        []
                    )
                )

                neuron.activation_count = int(
                    data.get(
                        "activation_count",
                        0
                    )
                )

                neuron.associated_memories = deque(
                    data.get(
                        "associated_memories",
                        []
                    ),
                    maxlen=100
                )

                neuron.previous_states = deque(
                    data.get(
                        "previous_states",
                        []
                    ),
                    maxlen=50
                )

                neuron.next_states = deque(
                    data.get(
                        "next_states",
                        []
                    ),
                    maxlen=50
                )

                neuron.actions = deque(
                    data.get(
                        "actions",
                        []
                    ),
                    maxlen=50
                )

                neuron.reward = float(
                    data.get(
                        "reward",
                        0.0
                    )
                )

                neuron.prediction_error = float(
                    data.get(
                        "prediction_error",
                        0.0
                    )
                )

                neuron.stability = float(
                    data.get(
                        "stability",
                        0.0
                    )
                )

                neuron.last_distance = float(
                    data.get(
                        "last_distance",
                        1.0
                    )
                )

                neuron.last_activation = int(
                    data.get(
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
                f"[STATE] Loaded "
                f"{len(self.neurons)} neurons "
                f"| generation={self.generation}"
            )

        except Exception as error:

            print(
                f"[WARN] Could not load V3 state: "
                f"{error}"
            )

            self.neurons = {}

            self.next_id = 0

            self.generation = 0

            self.total_states = 0

            self.created_total = 0

            self.pruned_total = 0

            self.memory.clear()

    # ========================================================
    # CHECKPOINT
    # ========================================================

    def checkpoint(
        self,
        result
    ):

        self.save()

        print()
        print(
            "=============================================================="
        )

        print(
            "SENSOR BRAIN V3 CHECKPOINT"
        )

        print(
            "=============================================================="
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
            f"{self.total_states}"
        )

        print(
            f"Raw sensor nums  : "
            f"{self.sensor_count}"
        )

        print(
            f"Features         : "
            f"{len(self.encoder.feature_names)}"
        )

        if result:

            print(
                f"Winner           : "
                f"{result['winner']}"
            )

            print(
                f"Distance         : "
                f"{result['distance']:.5f}"
            )

            print(
                f"State change     : "
                f"{result['state_change']:.5f}"
            )

            print(
                f"Action suggestion: "
                f"{result['action']}"
            )

            print(
                f"Reward           : "
                f"{result['reward']:.3f}"
            )

            print(
                f"Confidence       : "
                f"{result['confidence']:.3f}"
            )

            print(
                f"Fitness          : "
                f"{result['fitness']:.3f}"
            )

        print(
            "=============================================================="
        )

        print()

    # ========================================================
    # STATUS
    # ========================================================

    def print_neurons(self):

        ranked = sorted(
            self.neurons.values(),
            key=lambda n: n.fitness,
            reverse=True
        )

        print(
            "TOP LEARNED NEURONS:"
        )

        for neuron in ranked[:10]:

            print(
                f"  {neuron.id} | "
                f"fitness={neuron.fitness:.3f} | "
                f"confidence={neuron.confidence:.3f} | "
                f"age={neuron.age} | "
                f"activations={neuron.activation_count} | "
                f"parent={neuron.parent} | "
                f"children={len(neuron.children)}"
            )

        print()


# ============================================================
# FLATTEN SENSOR NUMBERS
# ============================================================

def flatten_sensor_numbers(data):

    values = []

    if isinstance(data, dict):

        for value in data.values():

            values.extend(
                flatten_sensor_numbers(
                    value
                )
            )

    elif isinstance(data, list):

        for value in data:

            values.extend(
                flatten_sensor_numbers(
                    value
                )
            )

    else:

        value = number(data)

        if value is not None:
            values.append(value)

    return values


# ============================================================
# SIGNAL
# ============================================================

def stop_signal(
    signum,
    frame
):

    global RUNNING

    RUNNING = False

    print()
    print(
        "STOP REQUESTED..."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    global RUNNING

    signal.signal(
        signal.SIGINT,
        stop_signal
    )

    signal.signal(
        signal.SIGTERM,
        stop_signal
    )

    print(
        "=============================================================="
    )

    print(
        "LIVE ANDROID SENSOR EVOLVING BRAIN V3"
    )

    print(
        "=============================================================="
    )

    print(
        "REAL TERMUX SENSOR DATA     : ON"
    )

    print(
        "SENSOR NORMALIZATION        : ON"
    )

    print(
        "EMA NOISE FILTER            : ON"
    )

    print(
        "TEMPORAL STATE              : ON"
    )

    print(
        "COMPETITIVE NEURONS         : ON"
    )

    print(
        "NOVELTY DETECTION           : ON"
    )

    print(
        "NEUROGENESIS                : ON"
    )

    print(
        "MEMORY                      : ON"
    )

    print(
        "STATE TRANSITIONS           : ON"
    )

    print(
        "ACTION SUGGESTION           : ON"
    )

    print(
        "REWARD                      : ON"
    )

    print(
        "FITNESS                     : ON"
    )

    print(
        "LINEAGE                     : ON"
    )

    print(
        "PRUNING                     : ON"
    )

    print(
        "PERSISTENT STATE            : ON"
    )

    print(
        f"INITIAL NEURONS             : "
        f"{INITIAL_NEURONS}"
    )

    print(
        f"MAX NEURONS                 : "
        f"{MAX_NEURONS}"
    )

    print(
        "=============================================================="
    )

    print()

    brain = SensorBrain()

    brain.load()

    if not brain.neurons:

        # Need a first live state to establish dimensionality.
        print(
            "Waiting for first real sensor snapshot..."
        )

        while RUNNING:

            data = read_sensor_snapshot()

            if data:

                encoder = SensorEncoder()

                state, _ = encoder.encode(
                    data
                )

                brain.encoder = encoder

                # Seed neurons from the real first state.
                brain.initialize()

                # Replace initial random-style seeds
                # with variations around actual sensor state.
                for index, neuron in enumerate(
                    brain.neurons.values()
                ):

                    offset = (
                        index - 1.5
                    ) * 0.08

                    neuron.prototype = [
                        clamp(
                            value + offset,
                            -1.0,
                            1.0
                        )
                        for value in state
                    ]

                print(
                    f"REAL SENSOR STATE INITIALIZED | "
                    f"features={len(state)}"
                )

                break

            print(
                "Waiting for sensor data..."
            )

            time.sleep(1.0)

    last_checkpoint = time.monotonic()

    try:

        while RUNNING:

            data = read_sensor_snapshot()

            if not data:

                print(
                    "WAITING FOR TERMUX SENSOR DATA..."
                )

                time.sleep(1.0)

                continue

            result = (
                brain.process_sensor_data(
                    data
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
                f"reward={result['reward']:.3f} | "
                f"confidence={result['confidence']:.3f} | "
                f"fitness={result['fitness']:.3f} | "
                f"sensors={result['raw_sensor_values']} | "
                f"features={result['sensor_features']}"
            )

            if result["created"]:

                print(
                    "    NEW NEURON CREATED "
                    "FROM NOVEL SENSOR STATE"
                )

            if result["pruned"]:

                print(
                    f"    PRUNED: "
                    f"{result['pruned']}"
                )

            if (
                time.monotonic()
                - last_checkpoint
                >= 30
            ):

                brain.checkpoint(
                    result
                )

                brain.print_neurons()

                last_checkpoint = (
                    time.monotonic()
                )

            time.sleep(
                SAMPLE_DELAY
            )

    except KeyboardInterrupt:

        RUNNING = False

    finally:

        print()
        print(
            "=============================================================="
        )

        print(
            "SAVING SENSOR BRAIN V3..."
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
            f"{brain.total_states}"
        )

        print(
            f"Memory entries   : "
            f"{len(brain.memory)}"
        )

        print(
            f"State file       : "
            f"{STATE_FILE}"
        )

        print(
            f"Memory file      : "
            f"{MEMORY_FILE}"
        )

        print(
            f"Lineage file     : "
            f"{LINEAGE_FILE}"
        )

        print(
            "SENSOR BRAIN V3 SAVED."
        )

        print(
            "=============================================================="
        )


if __name__ == "__main__":
    main()

