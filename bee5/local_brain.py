#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

MODEL = Path.home() / "bee5" / "models" / "bee5-model.gguf"
LLAMA = Path.home() / "llama.cpp" / "build" / "bin" / "llama-cli"

SYSTEM_PROMPT = """You are BEE5, a private local cognitive AI system.

Your primary purpose is to understand tasks, reason about them, use the skills provided to you, learn from execution results, and gradually improve your capabilities.

Core principles:

1. You are local and private.
2. You must only claim capabilities that actually exist in your registered skill library.
3. Skills are executable tools manually provided to BEE5.
4. Before using a skill, understand its purpose, inputs, outputs, dependencies, and safety constraints.
5. Prefer existing verified skills instead of unnecessarily reinventing solutions.
6. When a task requires multiple capabilities, compose existing skills in a logical sequence.
7. Observe the result of every important skill execution.
8. Record useful successful procedures and important failures in memory.
9. Treat failures as learning information.
10. Never modify the live BEE5 core blindly.
11. Any future self-improvement must create a candidate version, test it in isolation, compare it against the current version, create a backup, and only then promote it if it is demonstrably better.
12. Never bypass safety checks, testing, or approval requirements.
13. Be precise, practical, and honest about uncertainty.
14. Do not invent tools, files, memories, results, or capabilities.

BEE5 is not merely a chatbot. It is a skill-driven cognitive system whose capabilities grow through verified skills, memory, experience, and controlled evolution.x
"""


def check():
    if not LLAMA.is_file():
        raise FileNotFoundError(f"llama-cli not found: {LLAMA}")

    if not MODEL.is_file():
        raise FileNotFoundError(f"Model not found: {MODEL}")


def ask(prompt: str) -> str:
    check()

    full_prompt = (
        SYSTEM_PROMPT
        + "\nUser:\n"
        + prompt
        + "\n\nBEE5:\n"
    )

    command = [
        str(LLAMA),
        "-m",
        str(MODEL),
        "-p",
        full_prompt,
        "-n",
        "80",
        "-st",
        "--no-display-prompt",
    ]

    result = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
    )

    if result.returncode != 0:
        error = result.stderr.strip()
        raise RuntimeError(error or "llama-cli failed")

    return result.stdout.strip()


def status():
    check()

    print("========================================")
    print("           BEE5 LOCAL BRAIN")
    print("========================================")
    print(f"Model   : {MODEL}")
    print(f"LLAMA   : {LLAMA}")
    print("Backend : llama.cpp")
    print("Network : NOT REQUIRED")
    print("Mode    : SINGLE TURN")
    print("========================================")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print('  python local_brain.py status')
        print('  python local_brain.py ask "your question"')
        return 1

    command = sys.argv[1]

    try:
        if command == "status":
            status()
            return 0

        if command == "ask":
            if len(sys.argv) < 3:
                print('Usage: python local_brain.py ask "your question"')
                return 1

            print(ask(sys.argv[2]))
            return 0

        print(f"Unknown command: {command}")
        return 1

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
