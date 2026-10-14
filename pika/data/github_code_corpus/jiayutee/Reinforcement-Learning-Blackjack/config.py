# Blackjack RL Configuration

# Game Settings
DECK_COUNT = 6 # Standard casino usually uses 6-8 decks
MIN_BET = 1
MAX_BET = 100
BLACKJACK_PAYOUT = 1.5

# RL Hyperparameters
LEARNING_RATE = 0.001
GAMMA = 0.99  # Discount factor
EPSILON_START = 1.0
EPSILON_END = 0.01
EPSILON_DECAY = 0.995
BATCH_SIZE = 64
MEMORY_SIZE = 10000
TARGET_UPDATE = 10  # Number of episodes before updating target network
HIDDEN_SIZE = 128

# Training Settings
NUM_EPISODES = 5000
EVAL_INTERVAL = 100
MODEL_SAVE_DIR = "models"
LOG_DIR = "logs"

# Display Settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 30
