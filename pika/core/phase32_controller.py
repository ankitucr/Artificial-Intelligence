from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .transaction_engine import TransactionEngine
from .verification_engine import VerificationEngine
from .error_analyzer import ErrorAnalyzer
from .recovery_engine import RecoveryEngine
from .workspace_executor import WorkspaceExecutor
from .package_manager import PackageManager


class Phase32Controller:
    """
    Controlled transactional execution and recovery layer.

    Flow:

        worker
          -> transaction
          -> execute
          -> diagnose
          -> controlled recovery
          -> retry
          -> verify
          -> commit

    Recovery is bounded and dependency installation is generic.
    """

    MAX_INTERNAL_RECOVERY = 2

    def __init__(self, tool_runtime):
        self.tool_runtime = tool_runtime

        workspace_root = (
            Path(__file__).resolve().parents[1]
            / "workspace"
        )

        self.workspace_root = workspace_root
        self.transaction = TransactionEngine(
            workspace_root
        )
        self.verification = VerificationEngine(
            tool_runtime
        )
        self.error_analyzer = ErrorAnalyzer()
        self.recovery = RecoveryEngine()
        self.package_manager = PackageManager()

    def _diagnose(
        self,
        error: str,
        attempt: int = 1,
        *,
        worker_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        diagnosis = self.error_analyzer.analyze(
            {
                "error": error,
                "worker_result": worker_result,
            }
        )

        recovery = self.recovery.decide(
            diagnosis,
            attempt,
        )

        return {
            "diagnosis": diagnosis,
            "recovery": recovery,
            "recovery_feedback": self._feedback(
                diagnosis,
                recovery,
                error,
            ),
            "worker_error": error,
        }

    @staticmethod
    def _feedback(
        diagnosis: dict[str, Any],
        recovery: dict[str, Any],
        error: str,
    ) -> str:

        return (
            "PHASE 32 RECOVERY DIAGNOSIS\n"
            f"Error type: "
            f"{diagnosis.get('error_type')}\n"
            f"Root cause: "
            f"{diagnosis.get('root_cause')}\n"
            f"Detected dependency: "
            f"{diagnosis.get('package')}\n"
            f"Recommended recovery: "
            f"{recovery.get('action')}\n"
            f"Original error: {error}\n\n"
            "No failed transaction was committed."
        )

    def _install_dependency(
        self,
        diagnosis: dict[str, Any],
    ) -> dict[str, Any]:

        package = diagnosis.get("package")

        if not package:
            return {
                "success": False,
                "action": "install_dependency",
                "error": (
                    "Dependency was detected but "
                    "package identity could not be determined."
                ),
            }

        installation = self.package_manager.install(
            package
        )

        return {
            "success": bool(
                installation.get("success")
            ),
            "action": "install_dependency",
            "package": package,
            "installation": installation,
            "verified": bool(
                installation.get("available_after")
                or installation.get("already_available")
            ),
        }

    @staticmethod
    def _parse_actions(
        output: str,
    ) -> dict[str, Any]:

        if not output or not output.strip():
            raise ValueError(
                "Worker returned empty output."
            )

        text = output.strip()

        if text.startswith("```"):
            lines = text.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines).strip()

        try:
            data = json.loads(text)

        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")

            if start == -1 or end == -1 or end <= start:
                raise ValueError(
                    "Worker output is not valid JSON."
                )

            try:
                data = json.loads(
                    text[start:end + 1]
                )

            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Worker output contains invalid JSON: {exc}"
                ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "Worker JSON root must be an object."
            )

        if not isinstance(
            data.get("files"),
            list,
        ):
            raise ValueError(
                "Worker JSON field 'files' must be a list."
            )

        if not isinstance(
            data.get("commands"),
            list,
        ):
            raise ValueError(
                "Worker JSON field 'commands' must be a list."
            )

        return data

    @staticmethod
    def _file_paths(
        actions: dict[str, Any],
    ) -> list[str]:

        paths = []

        for item in actions.get("files", []):
            if not isinstance(item, dict):
                continue

            path = item.get("path")

            if (
                isinstance(path, str)
                and path.strip()
            ):
                paths.append(path)

        return paths

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

    def _execute_once(
        self,
        executor: WorkspaceExecutor,
        worker_output: str,
    ) -> dict[str, Any]:

        return executor.execute_worker_output(
            worker_output
        )

    def execute(
        self,
        worker_output: str,
        attempt: int = 1,
        worker_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        # --------------------------------------------------------
        # WORKER/API FAILURE
        # --------------------------------------------------------

        if worker_result is not None:
            if worker_result.get(
                "success",
                True,
            ) is False:

                error = str(
                    worker_result.get(
                        "error",
                        "Worker execution failed.",
                    )
                )

                recovery_data = self._diagnose(
                    error,
                    attempt,
                    worker_result=worker_result,
                )

                return {
                    "success": False,
                    "stage": "worker",
                    "error": error,
                    **recovery_data,
                }

        # --------------------------------------------------------
        # PARSE
        # --------------------------------------------------------

        try:
            actions = self._parse_actions(
                worker_output
            )

        except Exception as exc:
            error = str(exc)

            return {
                "success": False,
                "stage": "parse",
                "error": error,
                **self._diagnose(
                    error,
                    attempt,
                ),
            }

        paths = self._file_paths(actions)

        # --------------------------------------------------------
        # TRANSACTION
        # --------------------------------------------------------

        transaction_id = None

        if paths:
            try:
                transaction = self.transaction.begin(
                    paths
                )

                if not transaction.get(
                    "success",
                    False,
                ):
                    error = (
                        "Failed to create workspace "
                        "transaction snapshot."
                    )

                    return {
                        "success": False,
                        "stage": "transaction_begin",
                        "error": error,
                        **self._diagnose(
                            error,
                            attempt,
                        ),
                    }

                transaction_id = transaction.get(
                    "transaction_id"
                )

            except Exception as exc:
                error = (
                    f"Transaction begin failed: {exc}"
                )

                return {
                    "success": False,
                    "stage": "transaction_begin",
                    "error": error,
                    **self._diagnose(
                        error,
                        attempt,
                    ),
                }

        executor = WorkspaceExecutor(
            self.tool_runtime
        )

        execution = None
        dependency_recovery = None
        recovery_history = []

        # --------------------------------------------------------
        # EXECUTE + CONTROLLED INTERNAL RECOVERY
        # --------------------------------------------------------

        for recovery_attempt in range(
            self.MAX_INTERNAL_RECOVERY + 1
        ):

            execution = self._execute_once(
                executor,
                worker_output,
            )

            if execution.get(
                "success",
                False,
            ):
                break

            error = str(
                execution.get(
                    "error",
                    "Workspace execution failed.",
                )
            )

            diagnosis_data = self._diagnose(
                error,
                attempt + recovery_attempt,
            )

            diagnosis = diagnosis_data.get(
                "diagnosis",
                {},
            )

            recovery = diagnosis_data.get(
                "recovery",
                {},
            )

            action = recovery.get(
                "action"
            )

            recovery_history.append(
                {
                    "attempt": recovery_attempt + 1,
                    "error": error,
                    "diagnosis": diagnosis,
                    "recovery": recovery,
                }
            )

            # Only dependency installation is performed
            # automatically inside this controller.
            if (
                action == "install_dependency"
                and recovery_attempt
                < self.MAX_INTERNAL_RECOVERY
            ):

                dependency_recovery = (
                    self._install_dependency(
                        diagnosis
                    )
                )

                recovery_history[
                    -1
                ]["dependency_recovery"] = (
                    dependency_recovery
                )

                if dependency_recovery.get(
                    "success"
                ):
                    continue

            # No safe automatic action available.
            break

        # --------------------------------------------------------
        # EXECUTION FAILED
        # --------------------------------------------------------

        if not execution or not execution.get(
            "success",
            False,
        ):

            error = str(
                execution.get(
                    "error",
                    "Workspace execution failed.",
                )
                if execution
                else "Workspace execution failed."
            )

            diagnosis_data = self._diagnose(
                error,
                attempt,
            )

            rollback = self._rollback(
                transaction_id
            )

            return {
                "success": False,
                "stage": "execution",
                "error": error,
                "execution": execution,
                "transaction": {
                    "transaction_id": transaction_id,
                    "rollback": rollback,
                },
                "recovery_history": recovery_history,
                "dependency_recovery": (
                    dependency_recovery
                ),
                **diagnosis_data,
            }

        # --------------------------------------------------------
        # INDEPENDENT VERIFICATION
        # --------------------------------------------------------

        verification = (
            self.verification.verify_files(
                paths
            )
        )

        if not verification.get(
            "success",
            False,
        ):

            error = (
                "Independent verification failed."
            )

            rollback = self._rollback(
                transaction_id
            )

            return {
                "success": False,
                "stage": "verification",
                "error": error,
                "execution": execution,
                "verification": verification,
                "transaction": {
                    "transaction_id": transaction_id,
                    "rollback": rollback,
                },
                "recovery_history": recovery_history,
                **self._diagnose(
                    error,
                    attempt,
                ),
            }

        # --------------------------------------------------------
        # COMMIT
        # --------------------------------------------------------

        if transaction_id:

            try:
                commit_result = (
                    self.transaction.commit(
                        transaction_id
                    )
                )

            except Exception as exc:
                commit_result = {
                    "success": False,
                    "error": str(exc),
                }

            if not commit_result.get(
                "success",
                False,
            ):

                error = (
                    "Transaction commit failed."
                )

                rollback = self._rollback(
                    transaction_id
                )

                return {
                    "success": False,
                    "stage": "commit",
                    "error": error,
                    "execution": execution,
                    "verification": verification,
                    "transaction": {
                        "transaction_id": transaction_id,
                        "commit": commit_result,
                        "rollback": rollback,
                    },
                    **self._diagnose(
                        error,
                        attempt,
                    ),
                }

        else:
            commit_result = None

        return {
            "success": True,
            "stage": "committed",
            "execution": execution,
            "verification": verification,
            "transaction": {
                "transaction_id": transaction_id,
                "commit": commit_result,
            },
            "recovery_history": recovery_history,
            "dependency_recovery": (
                dependency_recovery
            ),
        }
