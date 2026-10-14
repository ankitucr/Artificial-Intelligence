import ast
import os
import sys
import time
import traceback
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parent
SKILLS_DIR = ROOT / "permanent_skills"
LOG_DIR = ROOT / "skill_execution_logs"

# Maximum time allowed for one skill.
TIMEOUT = 8

# Number of skills executed simultaneously.
# Keep this low on a phone.
WORKERS = 4

LOG_DIR.mkdir(exist_ok=True)


def analyse_source(path: Path):
    """Extract useful information without executing the file."""

    result = {
        "functions": [],
        "classes": [],
        "imports": [],
        "syntax": "UNKNOWN",
    }

    try:
        source = path.read_text(
            encoding="utf-8",
            errors="replace"
        )

        tree = ast.parse(source, filename=str(path))

        result["syntax"] = "OK"

        for node in tree.body:

            if isinstance(node, ast.FunctionDef):
                result["functions"].append(node.name)

            elif isinstance(node, ast.AsyncFunctionDef):
                result["functions"].append(
                    f"async:{node.name}"
                )

            elif isinstance(node, ast.ClassDef):
                result["classes"].append(node.name)

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    result["imports"].append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                result["imports"].append(
                    node.module or ""
                )

    except SyntaxError as e:
        result["syntax"] = (
            f"FAIL line={e.lineno}: {e.msg}"
        )

    except Exception as e:
        result["syntax"] = (
            f"ERROR: {type(e).__name__}: {e}"
        )

    return result


def run_skill(path: Path):
    """Execute one skill as an isolated child process."""

    name = path.name
    start = time.monotonic()

    static = analyse_source(path)

    log_file = LOG_DIR / f"{name}.log"

    header = f"""
============================================================
SKILL EXECUTION REPORT
============================================================
File       : {name}
Path       : {path}
Started    : {time.strftime("%Y-%m-%d %H:%M:%S")}
Timeout    : {TIMEOUT}s
============================================================

STATIC ANALYSIS
---------------
Syntax     : {static["syntax"]}
Functions  : {static["functions"]}
Classes    : {static["classes"]}
Imports    : {static["imports"]}

EXECUTION
---------
"""

    try:
        env = os.environ.copy()

        # Tell the skill that it is being inspected.
        env["SKILL_AUDIT_MODE"] = "1"
        env["PYTHONUNBUFFERED"] = "1"

        process = subprocess.run(
            [
                sys.executable,
                "-u",
                str(path),
            ],
            cwd=str(SKILLS_DIR),
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            env=env,
        )

        elapsed = time.monotonic() - start

        stdout = process.stdout or ""
        stderr = process.stderr or ""

        if process.returncode == 0:
            status = "COMPLETED"

        else:
            status = f"FAILED_EXIT_{process.returncode}"

        report = (
            header
            + f"Status     : {status}\n"
            + f"Runtime    : {elapsed:.3f}s\n\n"
            + "----- STDOUT -----\n"
            + stdout
            + "\n----- STDERR -----\n"
            + stderr
            + "\n----- END EXECUTION -----\n"
        )

    except subprocess.TimeoutExpired as e:

        elapsed = time.monotonic() - start

        stdout = e.stdout or ""
        stderr = e.stderr or ""

        report = (
            header
            + "Status     : TIMEOUT\n"
            + f"Runtime    : {elapsed:.3f}s\n\n"
            + "----- STDOUT BEFORE TIMEOUT -----\n"
            + str(stdout)
            + "\n----- STDERR BEFORE TIMEOUT -----\n"
            + str(stderr)
            + "\n----- END EXECUTION -----\n"
        )

        status = "TIMEOUT"

    except Exception:

        elapsed = time.monotonic() - start

        report = (
            header
            + "Status     : RUNNER_ERROR\n"
            + f"Runtime    : {elapsed:.3f}s\n\n"
            + traceback.format_exc()
        )

        status = "RUNNER_ERROR"

    log_file.write_text(
        report,
        encoding="utf-8"
    )

    # Compact live console output.
    output_preview = ""

    try:
        if stdout:
            output_preview = stdout.strip().replace(
                "\n",
                " | "
            )[:220]
    except Exception:
        pass

    print(
        f"[{status:<18}] "
        f"{name:<45} "
        f"{elapsed:6.2f}s"
    )

    if output_preview:
        print(
            f"    └─ {output_preview}"
        )

    return {
        "name": name,
        "status": status,
        "runtime": elapsed,
        "log": str(log_file),
        "functions": len(static["functions"]),
        "classes": len(static["classes"]),
    }


def main():

    if not SKILLS_DIR.exists():
        print(
            f"ERROR: {SKILLS_DIR} does not exist."
        )
        sys.exit(1)

    skills = sorted(
        SKILLS_DIR.glob("*.py")
    )

    # Don't execute the runner itself if copied there.
    skills = [
        p for p in skills
        if p.name != Path(__file__).name
    ]

    print()
    print("=" * 72)
    print("        BEE5 PERMANENT SKILL EXECUTION AUDITOR")
    print("=" * 72)
    print()
    print(f"Skills found : {len(skills)}")
    print(f"Workers      : {WORKERS}")
    print(f"Timeout      : {TIMEOUT}s / skill")
    print(f"Logs         : {LOG_DIR}")
    print()
    print(
        "IMPORTANT: No permanent skill files will be modified."
    )
    print()
    print("-" * 72)

    start = time.monotonic()

    results = []

    # Execute several skills simultaneously.
    with ThreadPoolExecutor(
        max_workers=WORKERS
    ) as executor:

        futures = {
            executor.submit(
                run_skill,
                path
            ): path
            for path in skills
        }

        for future in as_completed(futures):

            path = futures[future]

            try:
                results.append(
                    future.result()
                )

            except Exception as e:
                print(
                    f"[RUNNER_ERROR] {path.name}: {e}"
                )

    elapsed = time.monotonic() - start

    completed = sum(
        r["status"] == "COMPLETED"
        for r in results
    )

    failed = sum(
        r["status"].startswith("FAILED")
        for r in results
    )

    timeout = sum(
        r["status"] == "TIMEOUT"
        for r in results
    )

    runner_errors = sum(
        r["status"] == "RUNNER_ERROR"
        for r in results
    )

    print()
    print("=" * 72)
    print("                 AUDIT COMPLETE")
    print("=" * 72)

    print(f"Total skills : {len(skills)}")
    print(f"Completed    : {completed}")
    print(f"Failed       : {failed}")
    print(f"Timeout      : {timeout}")
    print(f"Runner error : {runner_errors}")
    print(f"Total time   : {elapsed:.2f}s")

    print()
    print(f"Individual logs:")
    print(f"    {LOG_DIR}/")

    print()
    print("Useful commands:")
    print()
    print("  List logs:")
    print("    ls skill_execution_logs/")
    print()
    print("  Read one:")
    print("    cat skill_execution_logs/skill_module_75.py.log")
    print()
    print("  Find failures:")
    print("    grep -l 'Status     : FAILED\\|Status     : TIMEOUT' skill_execution_logs/*.log")
    print()
    print("  Find completed:")
    print("    grep -l 'Status     : COMPLETED' skill_execution_logs/*.log")
    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
