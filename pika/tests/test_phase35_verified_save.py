import tempfile
from pathlib import Path

from core.brain import _phase35_save_repair
from core.semantic_code_memory import SemanticCodeMemory


def run_test():
    with tempfile.TemporaryDirectory(prefix="pika_verified_save_") as tmp:
        memory = SemanticCodeMemory(Path(tmp) / "memory.json")
        candidate = "return a * b"

        good = {
            "success": True,
            "accepted_candidate": candidate,
            "test_passed": True,
            "repair": {
                "success": True,
                "stage": "healed",
                "final_candidate": candidate,
                "test_passed": True,
                "validation_passed": True,
                "commit_passed": True,
                "test": {"success": True},
                "validation": {"success": True},
                "commit": {"success": True},
                "attempts": [{
                    "success": True,
                    "stage": "committed",
                    "candidate": candidate,
                    "test": {"success": True},
                    "validation": {"success": True},
                    "commit": {"success": True},
                }],
            },
        }

        saved = _phase35_save_repair(
            memory,
            "Fix calculator multiplication",
            [candidate],
            good,
            {"root_cause": "incorrect multiplication implementation"},
        )
        assert saved is True
        hits = memory.retrieve(
            "Fix calculator multiplication",
            verified_only=True,
        )
        assert any(v["code"] == candidate for v in hits), hits

        # Missing proof must not create a trusted record.
        unsafe = {
            "success": True,
            "accepted_candidate": "return a / b",
            "test_passed": False,
            "repair": {"final_candidate": "return a / b"},
        }
        saved_unsafe = _phase35_save_repair(
            memory,
            "Fix calculator division",
            ["return a / b"],
            unsafe,
            {},
        )
        assert saved_unsafe is False
        assert not any(
            v["code"] == "return a / b"
            and v["verification"] in {"test_verified", "formally_verified"}
            for v in memory.data["variants"]
        )

        # Summary booleans without execution records are not proof.
        spoofed = {
            "success": True,
            "accepted_candidate": "return a - b",
            "test_passed": True,
            "repair": {"final_candidate": "return a - b"},
        }
        saved_spoofed = _phase35_save_repair(
            memory,
            "Fix calculator subtraction",
            ["return a - b"],
            spoofed,
            {},
        )
        assert saved_spoofed is False
        assert not any(
            v["code"] == "return a - b"
            for v in memory.data["variants"]
        )

        print("PHASE 35 VERIFIED SAVE: PASS")
        print("Verified: exact accepted candidate is persisted.")
        print("Verified: successful evidence makes it retrievable.")
        print("Verified: missing test evidence cannot create trusted memory.")


if __name__ == "__main__":
    run_test()
