from core.workspace_runtime import WorkspaceRuntime


def main():

    print("=" * 60)
    print("PIKA PHASE 11")
    print("REAL ENGINEERING WORKSPACE TEST")
    print("=" * 60)

    runtime = WorkspaceRuntime(
        "/data/data/com.termux/files/home/pika"
    )

    # ---------------------------------------------------------
    # LIST
    # ---------------------------------------------------------

    listing = runtime.execute(
        "workspace_list"
    )

    print()
    print("PROJECT FILES:")
    print(
        f"Found {listing['count']} files"
    )

    for path in listing["files"][:20]:
        print(" -", path)

    # ---------------------------------------------------------
    # READ
    # ---------------------------------------------------------

    brain = runtime.execute(
        "workspace_read",
        relative_path="core/brain.py",
    )

    print()
    print("BRAIN READ:")
    print(
        "success =",
        brain["success"],
    )

    print(
        "bytes =",
        brain.get("bytes"),
    )

    # ---------------------------------------------------------
    # SEARCH
    # ---------------------------------------------------------

    search = runtime.execute(
        "workspace_search",
        query="class PIKABrain",
        relative_dir="core",
    )

    print()
    print("CODE SEARCH:")
    print(
        "matches =",
        search["count"],
    )

    for match in search["matches"]:
        print(
            f"{match['file']}:"
            f"{match['line']}: "
            f"{match['text']}"
        )

    # ---------------------------------------------------------
    # PYTHON VALIDATION
    # ---------------------------------------------------------

    validation = runtime.execute(
        "workspace_validate_python",
        relative_path="core/brain.py",
    )

    print()
    print("PYTHON VALIDATION:")
    print(
        "success =",
        validation["success"],
    )

    # ---------------------------------------------------------
    # FINAL CHECK
    # ---------------------------------------------------------

    passed = (
        listing["success"]
        and listing["count"] > 0

        and brain["success"]
        and "PIKABrain"
        in brain["content"]

        and search["success"]
        and search["count"] >= 1

        and validation["success"]
    )

    print()

    if passed:
        print(
            "PIKA PHASE 11 WORKSPACE TEST: PASSED"
        )
    else:
        print(
            "PIKA PHASE 11 WORKSPACE TEST: FAILED"
        )


if __name__ == "__main__":
    main()
