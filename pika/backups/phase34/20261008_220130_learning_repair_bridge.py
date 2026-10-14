from __future__ import annotations

from pathlib import Path
from typing import Any

from core.learning_engine import LearningEngine


class LearningRepairBridge:
    """
    Phase 34 bridge between PIKA memory and Phase 33 self-healing.

    Order:

        learned memory
              ↓
        verified solution
              ↓
        Phase 33 verification
              ↓
        success -> reinforce
        failure -> record failure
              ↓
        only then Cohere may be used
    """

    def __init__(
        self,
        workspace_root: str | Path,
        memory_path: str | Path | None = None,
    ):
        self.workspace_root = (
            Path(workspace_root)
            .expanduser()
            .resolve()
        )

        if memory_path is None:
            memory_path = (
                Path(__file__).resolve().parents[1]
                / "data"
                / "learning_engine.json"
            )

        self.learner = LearningEngine(memory_path)

    # ---------------------------------------------------------
    # MEMORY SEARCH
    # ---------------------------------------------------------

    def find(
        self,
        *,
        task: str = "",
        error_type: str = "",
        root_cause: str = "",
        error_message: str = "",
    ) -> dict[str, Any] | None:

        return self.learner.best_solution(
            task=task,
            error_type=error_type,
            root_cause=root_cause,
            error_message=error_message,
        )

    # ---------------------------------------------------------
    # CANDIDATE
    # ---------------------------------------------------------

    def build_candidate(
        self,
        solution: dict[str, Any],
        *,
        target_path: str,
        old_text: str,
        test_path: str,
    ) -> dict[str, Any]:

        replay = solution.get(
            "replay_context",
            {},
        )

        return {
            "candidate": solution.get(
                "solution",
                "",
            ),
            "method": solution.get(
                "method",
                "learned-memory",
            ),
            "old_text": (
                old_text
                or replay.get("old_text", "")
            ),
            "target_path": (
                target_path
                or replay.get("target_path", "")
            ),
            "test_path": (
                test_path
                or replay.get("test_path", "")
            ),
            "source": "learned_memory",
            "learning_similarity": solution.get(
                "similarity",
                0.0,
            ),
        }

    # ---------------------------------------------------------
    # LEARN SUCCESS / FAILURE
    # ---------------------------------------------------------

    def record(
        self,
        *,
        task: str,
        error_type: str,
        root_cause: str,
        error_message: str,
        method: str,
        solution: str,
        verification: dict[str, Any],
        success: bool,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        return self.learner.learn(
            task=task,
            error_type=error_type,
            root_cause=root_cause,
            error_message=error_message,
            method=method,
            solution=solution,
            verification=verification,
            success=success,
            source=source,
            metadata=metadata or {},
        )

    def stats(self) -> dict[str, Any]:
        return self.learner.stats()
