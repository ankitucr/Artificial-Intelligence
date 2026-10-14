from core.workspace_runtime import WorkspaceRuntime


def main():

    print("=" * 60)
    print("PIKA PHASE 12")
    print("REAL TEST EXECUTION + EVIDENCE")
    print("=" * 60)

    runtime = WorkspaceRuntime(
        "/data/data/com.termux/files/home/pika"
    )

    test_path = "test_phase11_workspace.py"

    print()
    print("TEST TARGET:")
    print(test_path)

    print()
    print("EXECUTING...")

    result = runtime.execute(
        "workspace_run_python_test",
        relative_path=test_path,
        timeout=120,
    )

    print()
    print("=" * 60)
    print("EXECUTION EVIDENCE")
    print("=" * 60)

    print()
    print("SUCCESS:")
    print(result["success"])

    print()
    print("EXIT CODE:")
    print(result["returncode"])

    print()
    print("DURATION:")
    print(
        f"{result['duration_seconds']} seconds"
    )

    print()
    print("STDOUT:")
    print(result["stdout"])

    print()
    print("STDERR:")
    print(result["stderr"])

    print()
    print("EVIDENCE:")
    print(result["evidence"])

    passed = (
        result["success"]
        and result["returncode"] == 0
        and not result["timed_out"]
        and "PIKA PHASE 11 WORKSPACE TEST: PASSED"
        in result["stdout"]
    )

    print()

    if passed:
        print(
            "PIKA PHASE 12 EXECUTION TEST: PASSED"
        )
    else:
        print(
            "PIKA PHASE 12 EXECUTION TEST: FAILED"
        )


if __name__ == "__main__":
    main()
