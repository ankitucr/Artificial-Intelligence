from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from core.controlled_editor import ControlledEditor
from core.critic import Critic
from core.candidate_ranker import CandidateRanker
from core.experience_learner import ExperienceLearner
from core.transaction_engine import TransactionEngine
from core.verification_engine import VerificationEngine


from core.learning_repair_bridge import LearningRepairBridge
class SelfHealingEngine:
    """
    Phase 33 controlled self-healing engine.

    Responsibilities:

    1. Receive a diagnosed repair problem.
    2. Rank repair candidates independently.
    3. Snapshot the affected workspace files.
    4. Apply one candidate.
    5. Run independent syntax verification.
    6. Run the supplied verification/test command.
    7. Commit only a verified repair.
    8. Roll back every failed candidate.
    9. Stop after a bounded number of candidates.

    Candidate generation is deliberately external.
    This keeps the healing engine independent from
    any particular LLM/provider.
    """

    def __init__(
        self,
        workspace_root: str | Path,
        max_retries: int = 2,
        max_candidates: int = 3,
    ):
        self.root = (
            Path(workspace_root)
            .expanduser()
            .resolve()
        )

        self.max_retries = max(
            0,
            int(max_retries),
        )

        self.max_candidates = max(
            1,
            int(max_candidates),
        )

        self.editor = ControlledEditor(
            self.root
        )

        self.critic = Critic()

        self.learner = ExperienceLearner(
            self.root
            / "data"
            / "experience.json"
        )
        self.phase34_learning = LearningRepairBridge(
            self.root,
        )

        self.ranker = CandidateRanker(
            self.critic,
            learner=self.learner,
        )

        self.transaction = TransactionEngine(
            self.root
        )

        self.verification = None

    # ------------------------------------------------------------
    # PATH SAFETY
    # ------------------------------------------------------------

    def _safe_path(
        self,
        relative_path: str,
    ) -> Path:

        path = (
            self.root
            / relative_path
        ).resolve()

        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(
                "Repair path escapes workspace."
            ) from exc

        return path

    # ------------------------------------------------------------
    # READ CURRENT SOURCE
    # ------------------------------------------------------------

    def read_source(
        self,
        relative_path: str,
    ) -> dict[str, Any]:

        try:
            path = self._safe_path(
                relative_path
            )

            if not path.is_file():
                return {
                    "success": False,
                    "error": (
                        f"File not found: "
                        f"{relative_path}"
                    ),
                }

            content = path.read_text(
                encoding="utf-8"
            )

            return {
                "success": True,
                "path": relative_path,
                "content": content,
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
            }

    # ------------------------------------------------------------
    # CANDIDATE RANKING
    # ------------------------------------------------------------

    def rank_candidates(
        self,
        task: str,
        candidates: list[str],
    ) -> list[dict[str, Any]]:

        if not candidates:
            return []

        limited = candidates[
            : self.max_candidates
        ]

        ranked = self.ranker.rank(
            task,
            limited,
        )

        return ranked[
            : self.max_candidates
        ]

    # ------------------------------------------------------------
    # TRANSACTION
    # ------------------------------------------------------------

    def _begin_transaction(
        self,
        relative_path: str,
    ) -> dict[str, Any]:

        try:
            return self.transaction.begin(
                [relative_path]
            )

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
            }

    def _rollback(
        self,
        transaction_id: str | None,
    ) -> dict[str, Any] | None:

        if not transaction_id:
            return None

        try:
            return self.transaction.rollback(
                transaction_id
            )

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
            }

    def _commit(
        self,
        transaction_id: str | None,
    ) -> dict[str, Any] | None:

        if not transaction_id:
            return None

        try:
            return self.transaction.commit(
                transaction_id
            )

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
            }

    # ------------------------------------------------------------
    # CANDIDATE APPLICATION
    # ------------------------------------------------------------

    def _apply_candidate(
        self,
        relative_path: str,
        old_text: str,
        candidate: str,
    ) -> dict[str, Any]:

        return self.editor.replace_text(
            relative_path,
            old_text,
            candidate,
        )

    # ------------------------------------------------------------
    # PYTHON VERIFICATION
    # ------------------------------------------------------------

    def _verify_python(self, relative_path: str):
        """
        Verify Python syntax against the SAME workspace root used
        by this SelfHealingEngine instance.
        """
        from workspace.manager import WorkspaceManager

        manager = WorkspaceManager(self.root)

        return manager.check_python(relative_path)
    def _run_test(self, test_path: str):
        """
        Run the test against the SAME workspace root used
        by this SelfHealingEngine instance.
        """
        from workspace.manager import WorkspaceManager

        manager = WorkspaceManager(self.root)

        return manager.run_command(
            ["python", test_path]
        )
    def repair_candidates(
        self,
        relative_path: str,
        old_text: str,
        candidates: list[str],
        test_path: str,
        task: str = "",
    ) -> dict[str, Any]:
        """
        Attempt bounded autonomous repairs.

        Each candidate receives its own transaction.

        Failed candidate:
            rollback

        Successful candidate:
            verification
            commit

        No candidate:
            no workspace modification remains.
        """

        if not candidates:
            return {
                "success": False,
                "stage": "generation",
                "error": (
                    "No repair candidates were supplied."
                ),
                "attempts": [],
            }

        if not old_text:
            return {
                "success": False,
                "stage": "input",
                "error": (
                    "Repair target text cannot be empty."
                ),
                "attempts": [],
            }

        source = self.read_source(
            relative_path
        )

        if not source.get("success"):
            return {
                "success": False,
                "stage": "read",
                "error": source.get(
                    "error",
                    "Unable to read repair target.",
                ),
                "attempts": [],
            }

        ranked = self.rank_candidates(
            task,
            candidates,
        )

        attempts: list[dict[str, Any]] = []

        print()
        print(
            "[PIKA SELF-HEALING] "
            f"{len(ranked)} candidate(s) selected."
        )

        for index, item in enumerate(
            ranked,
            start=1,
        ):

            candidate = item[
                "candidate"
            ]

            print(
                "[PIKA SELF-HEALING] "
                f"Candidate {index}/{len(ranked)}"
            )

            transaction = (
                self._begin_transaction(
                    relative_path
                )
            )

            if not transaction.get(
                "success",
                False,
            ):

                attempts.append(
                    {
                        "attempt": index,
                        "success": False,
                        "stage": (
                            "transaction_begin"
                        ),
                        "candidate": candidate,
                        "error": transaction.get(
                            "error",
                            "Transaction creation failed.",
                        ),
                    }
                )

                continue

            transaction_id = (
                transaction.get(
                    "transaction_id"
                )
            )

            edit = self._apply_candidate(
                relative_path,
                old_text,
                candidate,
            )

            if not edit.get(
                "success",
                False,
            ):

                rollback = self._rollback(
                    transaction_id
                )

                attempts.append(
                    {
                        "attempt": index,
                        "success": False,
                        "stage": "edit",
                        "candidate": candidate,
                        "edit": edit,
                        "rollback": rollback,
                    }
                )

                continue

            validation = self._verify_python(
                relative_path
            )

            if not validation.get(
                "success",
                False,
            ):

                rollback = self._rollback(
                    transaction_id
                )

                attempts.append(
                    {
                        "attempt": index,
                        "success": False,
                        "stage": "syntax",
                        "candidate": candidate,
                        "validation": validation,
                        "rollback": rollback,
                    }
                )

                continue

            test = self._run_test(
                test_path
            )

            if not test.get(
                "success",
                False,
            ):

                rollback = self._rollback(
                    transaction_id
                )

                attempts.append(
                    {
                        "attempt": index,
                        "success": False,
                        "stage": "test",
                        "candidate": candidate,
                        "validation": validation,
                        "test": test,
                        "rollback": rollback,
                        "feedback": {
                            "stdout": test.get(
                                "stdout",
                                "",
                            ),
                            "stderr": test.get(
                                "stderr",
                                "",
                            ),
                            "error": test.get(
                                "error",
                                "",
                            ),
                        },
                    }
                )

                continue

            commit = self._commit(
                transaction_id
            )

            if not commit or not commit.get(
                "success",
                False,
            ):

                rollback = self._rollback(
                    transaction_id
                )

                attempts.append(
                    {
                        "attempt": index,
                        "success": False,
                        "stage": "commit",
                        "candidate": candidate,
                        "commit": commit,
                        "rollback": rollback,
                    }
                )

                continue

            attempts.append(
                {
                    "attempt": index,
                    "success": True,
                    "stage": "committed",
                    "candidate": candidate,
                    "validation": validation,
                    "test": test,
                    "commit": commit,
                }
            )

            return {
                "success": True,
                "stage": "healed",
                "attempts": attempts,
                "final_attempt": index,
                "final_candidate": candidate,
                "validation": validation,
                "test": test,
                "commit": commit,
            }

        return {
            "success": False,
            "stage": "exhausted",
            "attempts": attempts,
            "error": (
                "All bounded self-healing "
                "candidates failed."
            ),
        }

    # ------------------------------------------------------------
    # SINGLE REPAIR COMPATIBILITY API
    # ------------------------------------------------------------

    def repair(
        self,
        relative_path: str,
        old_text: str,
        new_text: str,
        test_path: str,
    ) -> dict[str, Any]:

        return self.repair_candidates(
            relative_path=relative_path,
            old_text=old_text,
            candidates=[new_text],
            test_path=test_path,
            task=(
                "Repair the implementation while "
                "preserving existing behavior."
            ),
        )
