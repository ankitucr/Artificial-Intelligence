import tempfile
from pathlib import Path

from core.brain import _phase35_save_repair
from core.semantic_code_memory import SemanticCodeMemory


def main():
    with tempfile.TemporaryDirectory(prefix="pika_phase35_persist_") as tmp:
        db = Path(tmp) / "memory.json"
        memory = SemanticCodeMemory(db)

        code = "return price * (1 - percent / 100)"
        context = {
            "target_path": "discount.py",
            "old_text": "return price - percent",
            "test_path": "test_discount.py",
        }
        outcome = {
            "success": True,
            "test_passed": True,
            "accepted_candidate": code,
            "repair": {"final_candidate": code},
        }

        saved = _phase35_save_repair(
            memory,
            "Fix percentage discount calculation",
            [code],
            outcome,
            {"root_cause": "incorrect percentage formula"},
            replay_context=context,
        )
        assert saved is True, "Verified repair was not saved"

        reloaded = SemanticCodeMemory(db)
        matches = [
            item for item in reloaded.data["variants"]
            if item["code"] == code
        ]
        assert len(matches) == 1, matches
        assert matches[0]["verification"] == "test_verified"
        assert matches[0]["replay_context"] == context, matches[0]

        print("PHASE 35 CONTEXT PERSISTENCE: PASS")
        print("Verified: accepted repair saved with test evidence.")
        print("Verified: replay context survived database reload.")
        print("Verified: temporary database only; production memory untouched.")


if __name__ == "__main__":
    main()
