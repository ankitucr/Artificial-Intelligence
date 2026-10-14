from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

WORKSPACE_DIR = BASE_DIR / "workspace"
STORAGE_DIR = BASE_DIR / "storage"
LOG_DIR = BASE_DIR / "logs"

APP_NAME = "PIKA"
VERSION = "0.1.0"

DEFAULT_AGENT = "local"

MAX_TASK_STEPS = 20
MAX_MEMORY_RESULTS = 10

WORKSPACE_DIR.mkdir(exist_ok=True)
STORAGE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
