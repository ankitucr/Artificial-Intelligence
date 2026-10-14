#!/usr/bin/env python3
"""
BEE5 self-evolution orchestrator.

Does NOT modify evolution_engine.py. Repeatedly invokes the existing
engine (subprocess) against every discovered target/evaluator pair
under evolution/targets/, and only promotes a candidate to the live
target file when the engine itself reports MUTATION ACCEPTED (an
evaluator-verified strict score improvement).
"""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGETS_DIR = ROOT / "evolution" / "targets"
ARCHIVE = ROOT / "evolution" / "archive"
PROMOTIONS_LOG = ROOT / "evolution" / "promotions.jsonl"

DEFAULT_TASK = (
    "Fix any evaluator failures while preserving every existing "
    "passing behavior. Prefer the smallest correct semantic change."
)

DEFAULT_MAX_GENERATIONS = 5


def discover_pairs():
    pairs = []
    for path in sorted(TARGETS_DIR.glob("*.py")):
        if path.name.endswith("_eval.py"):
            continue
        evaluator = path.with_name(path.stem + "_eval.py")
        if evaluator.exists():
            pairs.append((path, evaluator))
    return pairs


def run_evaluator(target: Path, evaluator: Path):
    result = subprocess.run(
        [sys.executable, str(evaluator), str(target)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    try:
        return json.loads(result.stdout.strip())
    except Exception:
        return {"ok": False, "error": result.stdout + result.stderr}


def run_engine_cycle(target: Path, evaluator: Path, task: str):
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "evolution_engine.py"),
            str(target),
            str(evaluator),
            task,
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr.strip():
        print(result.stderr, file=sys.stderr)
    return result.returncode == 0


def find_latest_archive_dir(after_ts: float):
    if not ARCHIVE.exists():
        return None
    candidates = []
    for d in ARCHIVE.iterdir():
        if not d.is_dir():
            continue
        meta = d / "metadata.json"
        if not meta.exists():
            continue
        try:
            mtime = meta.stat().st_mtime
        except OSError:
            continue
        if mtime >= after_ts - 1:
            candidates.append((mtime, d))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def promote(target: Path, evaluator: Path, archive_dir: Path):
    candidate_path = archive_dir / "candidate.py"
    if not candidate_path.exists():
        print(f"  Warning: no candidate.py found in {archive_dir}, skipping promotion.")
        return False

    backup_path = target.with_name(f"{target.name}.bak_{int(time.time())}")
    shutil.copy2(target, backup_path)
    shutil.copy2(candidate_path, target)

    verify = run_evaluator(target, evaluator)

    if not verify.get("ok"):
        print(f"  Post-promotion verification FAILED for {target.name}; restoring backup.")
        shutil.copy2(backup_path, target)
        return False

    meta_path = archive_dir / "metadata.json"
    metadata = {}
    if meta_path.exists():
        try:
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            metadata = {}

    record = {
        "timestamp": time.time(),
        "target": str(target),
        "backup": str(backup_path),
        "archive_dir": str(archive_dir),
        "parent_hash": metadata.get("parent_hash"),
        "candidate_hash": metadata.get("candidate_hash"),
        "score_before": metadata.get("parent_evaluation", {}).get("score"),
        "score_after": verify.get("score"),
        "verified": True,
    }

    PROMOTIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with PROMOTIONS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(
        f"  Promoted {target.name}: "
        f"{record['score_before']} -> {record['score_after']} "
        f"(backup: {backup_path.name})"
    )
    return True


def main():
    max_generations = DEFAULT_MAX_GENERATIONS
    task = DEFAULT_TASK

    if len(sys.argv) > 1:
        try:
            max_generations = int(sys.argv[1])
        except ValueError:
            pass

    if len(sys.argv) > 2:
        task = " ".join(sys.argv[2:])

    pairs = discover_pairs()

    if not pairs:
        print("No target/evaluator pairs found under evolution/targets/.")
        return 1

    print("========================================")
    print("   BEE5 SELF-EVOLUTION SESSION")
    print("========================================")
    print(f"Discovered {len(pairs)} target(s):")
    for target, evaluator in pairs:
        print(f"  - {target.name}")
    print(f"Max generations per target: {max_generations}")

    active = {str(t): True for t, _ in pairs}
    summary = []

    for generation in range(1, max_generations + 1):
        if not any(active.values()):
            print("\nAll targets converged. Stopping early.")
            break

        print(f"\n########## GENERATION {generation} ##########")

        for target, evaluator in pairs:
            key = str(target)
            if not active[key]:
                continue

            print(f"\n--- {target.name} (generation {generation}) ---")

            before_eval = run_evaluator(target, evaluator)
            before_score = before_eval.get("score")
            before_total = before_eval.get("total")

            if (
                before_eval.get("ok")
                and before_score is not None
                and before_total is not None
                and before_score >= before_total
            ):
                print(f"  {target.name} already at {before_score}/{before_total}; nothing to evolve.")
                active[key] = False
                summary.append({"target": target.name, "generation": generation, "result": "already_optimal"})
                continue

            start_ts = time.time()
            accepted = run_engine_cycle(target, evaluator, task)

            if not accepted:
                print(f"  No accepted mutation this generation for {target.name}.")
                active[key] = False
                summary.append({"target": target.name, "generation": generation, "result": "no_improvement"})
                continue

            archive_dir = find_latest_archive_dir(start_ts)
            if archive_dir is None:
                print("  Warning: engine reported ACCEPTED but no matching archive found.")
                active[key] = False
                summary.append({"target": target.name, "generation": generation, "result": "archive_not_found"})
                continue

            promoted = promote(target, evaluator, archive_dir)

            summary.append({
                "target": target.name,
                "generation": generation,
                "result": "promoted" if promoted else "promotion_failed",
                "score_before": before_score,
            })

            if not promoted:
                active[key] = False

    print("\n========================================")
    print("   SELF-EVOLUTION SESSION SUMMARY")
    print("========================================")
    for entry in summary:
        print(f"  gen {entry['generation']:<2} | {entry['target']:<30} | {entry['result']}")

    print(f"\nFull promotion evidence: {PROMOTIONS_LOG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
