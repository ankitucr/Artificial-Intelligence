from __future__ import annotations

from pathlib import Path
from typing import Any

from core.controlled_editor import ControlledEditor
from tools.workspace import WorkspaceTools


class SelfHealingEngine:

    def __init__(
        self,
        workspace_root: str | Path,
        max_retries: int = 2,
    ):
        self.root = Path(
            workspace_root
        ).expanduser().resolve()

        self.max_retries = max_retries

        self.workspace = WorkspaceTools(
            self.root
        )

        self.editor = ControlledEditor(
            self.root
        )


    def repair_candidates(
        self,
        relative_path: str,
        old_text: str,
        candidates: list[str],
        test_path: str,
    ) -> dict[str, Any]:
        """
        Try multiple candidate fixes.

        Every failed candidate is rolled back before
        the next candidate is attempted.
        """

        attempts: list[dict[str, Any]] = []

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):

            print(
                f"[PIKA] Candidate attempt "
                f"{index}/{len(candidates)}"
            )

            edit = self.editor.replace_text(
                relative_path,
                old_text,
                candidate,
            )

            if not edit["success"]:
                attempts.append({
                    "attempt": index,
                    "stage": "edit",
                    "success": False,
                    "error": edit.get("error"),
                })
                continue

            backup = edit["backup"]

            validation = (
                self.workspace.validate_python(
                    relative_path
                )
            )

            if not validation["success"]:

                rollback = self.editor.rollback(
                    backup,
                    relative_path,
                )

                attempts.append({
                    "attempt": index,
                    "stage": "syntax",
                    "success": False,
                    "candidate": candidate,
                    "validation": validation,
                    "rollback": rollback,
                })

                continue

            test = self.workspace.run_python_test(
                test_path
            )

            if test["success"]:

                attempts.append({
                    "attempt": index,
                    "stage": "test",
                    "success": True,
                    "candidate": candidate,
                    "validation": validation,
                    "test": test,
                })

                return {
                    "success": True,
                    "attempts": attempts,
                    "final_attempt": index,
                    "final_candidate": candidate,
                    "backup": backup,
                    "validation": validation,
                    "test": test,
                }

            # Failed test → capture evidence → rollback.
            rollback = self.editor.rollback(
                backup,
                relative_path,
            )

            attempts.append({
                "attempt": index,
                "stage": "test",
                "success": False,
                "candidate": candidate,
                "validation": validation,
                "test": test,
                "rollback": rollback,
                "feedback": {
                    "reason": (
                        "Candidate failed validation test."
                    ),
                    "stderr": test.get("stderr", ""),
                    "stdout": test.get("stdout", ""),
                    "exit_code": test.get("returncode"),
                },
            })

        return {
            "success": False,
            "attempts": attempts,
            "error": (
                "All repair candidates failed."
            ),
        }

    def repair(
        self,
        relative_path: str,
        old_text: str,
        new_text: str,
        test_path: str,
    ) -> dict[str, Any]:

        attempts: list[dict[str, Any]] = []

        for attempt in range(
            1,
            self.max_retries + 2,
        ):

            print(
                f"[PIKA] Repair attempt "
                f"{attempt}/{self.max_retries + 1}"
            )

            edit = self.editor.replace_text(
                relative_path,
                old_text,
                new_text,
            )

            if not edit["success"]:

                attempts.append({
                    "attempt": attempt,
                    "stage": "edit",
                    "success": False,
                    "error": edit.get("error"),
                })

                return {
                    "success": False,
                    "attempts": attempts,
                    "error": edit.get("error"),
                }

            backup = edit["backup"]

            validation = (
                self.workspace.validate_python(
                    relative_path
                )
            )

            if not validation["success"]:

                rollback = self.editor.rollback(
                    backup,
                    relative_path,
                )

                attempts.append({
                    "attempt": attempt,
                    "stage": "syntax",
                    "success": False,
                    "validation": validation,
                    "rollback": rollback,
                })

                continue

            test = self.workspace.run_python_test(
                test_path
            )

            if test["success"]:

                attempts.append({
                    "attempt": attempt,
                    "stage": "test",
                    "success": True,
                    "validation": validation,
                    "test": test,
                })

                return {
                    "success": True,
                    "attempts": attempts,
                    "final_attempt": attempt,
                    "backup": backup,
                    "validation": validation,
                    "test": test,
                }

            rollback = self.editor.rollback(
                backup,
                relative_path,
            )

            attempts.append({
                "attempt": attempt,
                "stage": "test",
                "success": False,
                "validation": validation,
                "test": test,
                "rollback": rollback,
            })

        return {
            "success": False,
            "attempts": attempts,
            "error": (
                "Repair failed after all "
                "allowed attempts."
            ),
        }
