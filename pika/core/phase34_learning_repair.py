from __future__ import annotations

from pathlib import Path
from typing import Any

from core.learning_repair_bridge import LearningRepairBridge


class Phase34LearningRepair:
    """
    Lightweight integration layer.

    It does NOT replace Phase 33.

    Phase 33 remains responsible for:
      - transaction
      - controlled editing
      - syntax validation
      - independent testing
      - rollback

    This layer only decides whether PIKA already knows a solution.
    """

    def __init__(
        self,
        workspace_root: str | Path,
        memory_path: str | Path | None = None,
    ):
        self.root = (
            Path(workspace_root)
            .expanduser()
            .resolve()
        )

        self.bridge = LearningRepairBridge(
            self.root,
            memory_path=memory_path,
        )

    def lookup_candidates(
        self,
        *,
        task: str = "",
        error_type: str = "",
        root_cause: str = "",
        error_message: str = "",
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Return ranked verified memory candidates."""
        return self.bridge.learner.best_solutions(
            task=task,
            error_type=error_type,
            root_cause=root_cause,
            error_message=error_message,
            limit=limit,
        )

    def lookup(
        self,
        *,
        task: str = "",
        error_type: str = "",
        root_cause: str = "",
        error_message: str = "",
    ) -> dict[str, Any] | None:

        solution = self.bridge.find(
            task=task,
            error_type=error_type,
            root_cause=root_cause,
            error_message=error_message,
        )

        if solution is None:
            print(
                "[PHASE34] MEMORY MISS -> "
                "Cohere may be required."
            )
            return None

        print(
            "[PHASE34] MEMORY HIT -> "
            "learned solution available."
        )

        return solution
