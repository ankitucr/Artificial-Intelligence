import json
import tempfile
from pathlib import Path

from core.brain import _phase35_save_repair
from core.semantic_code_memory import SemanticCodeMemory


def main():
    print("\n========== ISOLATED SAVE TEST ==========")

    with tempfile.TemporaryDirectory(prefix="pika_memory_audit_") as tmp:
        db = Path(tmp) / "semantic_code_memory.json"
        memory = SemanticCodeMemory(db)

        candidate = "def multiply(a, b):\n    return a * b"

        outcome = {
            "success": True,
            "accepted_candidate": candidate,
            "test_passed": True,
            "repair": {
                "final_candidate": candidate,
                "test_passed": True,
                "validation_passed": True,
                "commit_passed": True,
                "test": {"success": True},
                "validation": {"success": True},
                "commit": {"success": True},
            },
        }

        saved = _phase35_save_repair(
            memory,
            "Implement a calculator multiplication function",
            [candidate],
            outcome,
            {"root_cause": "multiplication implementation needed"},
        )
        assert saved is True, "Expected verified save to succeed"

        print("\n--- SAVED JSON RECORD ---")
        print(json.dumps(memory.data["variants"], indent=2))

        # Simulate restart: construct a new instance from the same file.
        restarted = SemanticCodeMemory(db)
        hits = restarted.retrieve(
            "calculator multiplication function",
            verified_only=True,
            limit=5,
        )
        assert any(v["code"] == candidate for v in hits), hits

        print("\n--- AFTER RELOAD ---")
        print("Database path:", db)
        print("Stats:", json.dumps(restarted.stats(), indent=2))
        print("Retrieved variants:", len(hits))
        for item in hits:
            print(json.dumps({
                "id": item["id"],
                "intent": item["intent"],
                "verification": item["verification"],
                "code": item["code"],
                "evidence": item["evidence"],
                "uses": item["uses"],
            }, indent=2))

        print("\nISOLATED SAVE + RELOAD: PASS")

    print("\n========== EXISTING PRODUCTION MEMORY (READ ONLY) ==========")
    production = Path("data/semantic_code_memory.json")

    if not production.exists():
        print("Production semantic memory file does not exist yet.")
        print("No production data was created or modified by this audit.")
        return

    try:
        data = json.loads(production.read_text(encoding="utf-8"))
        variants = data.get("variants", [])
        print("File:", production)
        print("Total variants:", len(variants))

        counts = {}
        for item in variants:
            status = item.get("verification", "missing")
            counts[status] = counts.get(status, 0) + 1
        print("Verification counts:", json.dumps(counts, indent=2))

        for index, item in enumerate(variants, 1):
            print(f"\n--- PRODUCTION VARIANT {index} ---")
            print(json.dumps({
                "id": item.get("id"),
                "intent": item.get("intent"),
                "description": item.get("description"),
                "language": item.get("language"),
                "verification": item.get("verification"),
                "tags": item.get("tags"),
                "code": item.get("code"),
                "evidence": item.get("evidence"),
                "uses": item.get("uses"),
            }, ensure_ascii=False, indent=2))
    except Exception as exc:
        print("Could not safely read production memory:", repr(exc))

    print("\nPRODUCTION MEMORY WAS NOT MODIFIED.")


if __name__ == "__main__":
    main()
