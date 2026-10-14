#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from evolution_engine import generate_mutation

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "evolution" / "workspace" / "unsafe_experiment"


def read_eval(
    evaluator: Path,
    target: Path
):
    result = subprocess.run(
        [
            sys.executable,
            str(evaluator),
            str(target),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )

    raw = result.stdout.strip()

    if not raw:
        raise RuntimeError(
            result.stderr.strip()
            or "Evaluator returned no output."
        )

    decoder = json.JSONDecoder()

    for index, char in enumerate(raw):
        if char != "{":
            continue

        try:
            obj, _ = decoder.raw_decode(
                raw[index:]
            )
        except Exception:
            continue

        if isinstance(obj, dict) and "score" in obj:
            return obj

    raise RuntimeError(
        "Could not parse evaluator JSON.\n" + raw
    )


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: python evolution_experiment.py "
            "<target.py> <evaluator.py>"
        )
        return 1

    parent = Path(
        sys.argv[1]
    ).resolve()

    evaluator = Path(
        sys.argv[2]
    ).resolve()

    if not parent.exists():
        print(f"Parent not found: {parent}")
        return 2

    if not evaluator.exists():
        print(f"Evaluator not found: {evaluator}")
        return 2

    print("========================================")
    print(" BEE5 UNSAFE MUTATION EXPERIMENT")
    print("========================================")
    print()

    parent_eval = read_eval(
        evaluator,
        parent
    )

    print("===== PARENT =====")
    print(
        json.dumps(
            parent_eval,
            ensure_ascii=False,
            indent=2
        )
    )

    os.environ[
        "BEE5_EXPERIMENTAL_UNSAFE_MUTATION"
    ] = "1"

    print()
    print("===== GENERATING WITHOUT MUTATION GUARD =====")

    try:
        candidate_source = generate_mutation(
            parent,
            "Fix the failing punctuation-spacing case while preserving every existing passing behavior.",
            parent_eval,
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "stage": "generation",
                    "error": str(exc),
                },
                ensure_ascii=False,
                indent=2
            )
        )
        return 3

    WORK.mkdir(
        parents=True,
        exist_ok=True
    )

    candidate = (
        WORK
        / f"candidate_{time.time_ns()}.py"
    )

    candidate.write_text(
        candidate_source,
        encoding="utf-8"
    )

    print()
    print("===== CANDIDATE SOURCE CREATED =====")
    print(candidate)

    print()
    print("===== CANDIDATE EVALUATION =====")

    candidate_eval = read_eval(
        evaluator,
        candidate
    )

    print(
        json.dumps(
            candidate_eval,
            ensure_ascii=False,
            indent=2
        )
    )

    print()
    print("===== EXPERIMENT RESULT =====")

    parent_score = parent_eval.get(
        "score"
    )
    candidate_score = candidate_eval.get(
        "score"
    )

    print(
        json.dumps(
            {
                "parent_score": parent_score,
                "candidate_score": candidate_score,
                "improved": (
                    candidate_score is not None
                    and parent_score is not None
                    and candidate_score > parent_score
                ),
                "candidate_path": str(candidate),
                "live_parent_modified": False,
            },
            ensure_ascii=False,
            indent=2
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
