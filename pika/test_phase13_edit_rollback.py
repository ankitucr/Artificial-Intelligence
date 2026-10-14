from pathlib import Path
import tempfile

from core.controlled_editor import ControlledEditor


def main():

    print("=" * 60)
    print("PIKA PHASE 13")
    print("CONTROLLED EDIT + BACKUP + ROLLBACK TEST")
    print("=" * 60)

    with tempfile.TemporaryDirectory(
        prefix="pika_phase13_"
    ) as temp:

        root = Path(temp)

        target = root / "demo.py"

        original = (
            "def hello():\n"
            "    return 'original'\n"
        )

        target.write_text(
            original,
            encoding="utf-8",
        )

        editor = ControlledEditor(
            root
        )

        print()
        print("ORIGINAL:")
        print(
            target.read_text(
                encoding="utf-8"
            )
        )

        print("EDITING...")

        edit = editor.replace_text(
            "demo.py",
            "return 'original'",
            "return 'modified'",
        )

        print()
        print("EDIT RESULT:")
        print(edit)

        modified = target.read_text(
            encoding="utf-8"
        )

        print()
        print("AFTER EDIT:")
        print(modified)

        print("ROLLING BACK...")

        rollback = editor.rollback(
            edit["backup"],
            "demo.py",
        )

        print()
        print("ROLLBACK RESULT:")
        print(rollback)

        restored = target.read_text(
            encoding="utf-8"
        )

        print()
        print("AFTER ROLLBACK:")
        print(restored)

        passed = (
            edit["success"]
            and "modified" in modified
            and rollback["success"]
            and restored == original
        )

        print()

        if passed:
            print(
                "PIKA PHASE 13 EDIT/ROLLBACK TEST: PASSED"
            )
        else:
            print(
                "PIKA PHASE 13 EDIT/ROLLBACK TEST: FAILED"
            )


if __name__ == "__main__":
    main()
