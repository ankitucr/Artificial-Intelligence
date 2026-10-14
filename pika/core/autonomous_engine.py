from __future__ import annotations

from typing import Any, Callable

from core.multi_candidate_engine import MultiCandidateEngine


class AutonomousEngineeringEngine:
    """
    Phase 24:
    End-to-end autonomous engineering orchestration.

    Actor generates candidates.
    MultiCandidateEngine performs Critic ranking,
    real validation, execution and rollback.
    """

    def __init__(
        self,
        workspace_root: str,
        actor: Callable[[str], list[str]],
        max_candidates: int = 5,
    ):
        self.actor = actor

        self.engine = MultiCandidateEngine(
            workspace_root=workspace_root,
            max_candidates=max_candidates,
        )

    def run(
        self,
        task: str,
        relative_path: str,
        old_text: str,
        test_path: str,
    ) -> dict[str, Any]:

        print("[PIKA] Actor generating candidates...")

        candidates = self.actor(task)

        if not candidates:
            return {
                "success": False,
                "stage": "generation",
                "error": "Actor generated no candidates.",
            }

        print(
            f"[PIKA] Actor generated "
            f"{len(candidates)} candidate(s)."
        )

        result = self.engine.repair(
            task=task,
            relative_path=relative_path,
            old_text=old_text,
            candidates=candidates,
            test_path=test_path,
        )

        return {
            "success": bool(
                result.get("success")
            ),
            "stage": "completed",
            "task": task,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "ranking": result.get(
                "ranking",
                [],
            ),
            "attempts": result.get(
                "attempts",
                [],
            ),
            "final_candidate": result.get(
                "final_candidate"
            ),
            "final_attempt": result.get(
                "final_attempt"
            ),
            "validation": result.get(
                "validation"
            ),
            "test": result.get(
                "test"
            ),
        }
