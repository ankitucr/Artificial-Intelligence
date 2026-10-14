import tempfile
from pathlib import Path

from core.brain import _phase35_save_repair
from core.phase33_controller import Phase33Controller
from core.semantic_code_memory import SemanticCodeMemory


def main():
    candidate = "def multiply(a, b):\n    return a * b"

    with tempfile.TemporaryDirectory(prefix="pika_phase35_flow_") as tmp:
        root = Path(tmp)
        workspace = root / "workspace"
        workspace.mkdir()

        controller = Phase33Controller(workspace_root=workspace)
        # Replace only the healer execution boundary; keep the real controller.
        controller.healer.repair_candidates = lambda **kwargs: {
            "success": True,
            "stage": "healed",
            "final_candidate": candidate,
            "validation": {"success": True},
            "test": {"success": True},
            "test_passed": True,
            "validation_passed": True,
            "commit": {"success": True},
            "commit_passed": True,
        }

        result = controller.repair(
            diagnosis={
                "error_type": "code_error",
                "root_cause": "incorrect multiplication",
            },
            relative_path="calculator.py",
            old_text="return a + b",
            candidates=[candidate],
            test_path="test_calculator.py",
            task="Implement calculator multiplication",
        )

        print("CONTROLLER RESULT:")
        print({
            "success": result.get("success"),
            "accepted_candidate": result.get("accepted_candidate"),
            "test_passed": result.get("test_passed"),
            "repair_stage": result.get("stage"),
        })

        assert result["success"] is True
        assert result["accepted_candidate"] == candidate
        assert result["test_passed"] is True

        db = root / "semantic_code_memory.json"
        memory = SemanticCodeMemory(db)

        saved = _phase35_save_repair(
            memory,
            "Implement calculator multiplication",
            [candidate],
            result,
            {"root_cause": "incorrect multiplication"},
        )
        assert saved is True

        # Verify persistence through a fresh instance.
        reloaded = SemanticCodeMemory(db)
        hits = reloaded.retrieve(
            "Implement calculator multiplication",
            verified_only=True,
        )
        assert any(v["code"] == candidate for v in hits), hits

        print("\nSAVED RECORD:")
        for item in reloaded.data["variants"]:
            print({
                "intent": item["intent"],
                "code": item["code"],
                "verification": item["verification"],
                "evidence": item["evidence"],
            })

        print("\nPHASE 35 CONTROLLER -> MEMORY: PASS")
        print("Production workspace and production memory were not modified.")


if __name__ == "__main__":
    main()
