from __future__ import annotations

import re
from typing import Any


class Planner:
    """
    Phase 30 Adaptive Planner.

    Converts a high-level task into:
        goal
        task_type
        subtasks
        dependencies
        execution_order
        validation
        strategy

    The planner is deterministic and lightweight.
    The actual intelligent execution remains with the worker.
    """

    def plan(
        self,
        task: str,
        memories: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        memories = memories or {}

        task = str(task).strip()

        task_type = self._detect_type(task)
        complexity = self._estimate_complexity(task)

        subtasks = self._build_subtasks(
            task=task,
            task_type=task_type,
            complexity=complexity,
        )

        dependencies = self._build_dependencies(subtasks)

        execution_order = [
            step["id"]
            for step in subtasks
        ]

        validation = self._build_validation(
            task=task,
            task_type=task_type,
            subtasks=subtasks,
        )

        strategy = self._build_strategy(
            task_type=task_type,
            complexity=complexity,
            subtasks=subtasks,
        )

        memory_hints = self._extract_memory_hints(
            memories
        )

        return {
            "goal": task,
            "task_type": task_type,
            "complexity": complexity,
            "subtask_count": len(subtasks),
            "subtasks": subtasks,
            "dependencies": dependencies,
            "execution_order": execution_order,
            "validation": validation,
            "strategy": strategy,
            "memory_hints": memory_hints,
        }

    # ============================================================
    # TASK TYPE
    # ============================================================

    @staticmethod
    def _detect_type(task: str) -> str:

        text = task.lower()

        # Engineering intent must be checked before generic words
        # such as "error", because phrases like "error handling"
        # describe a feature rather than a debugging request.
        if any(
            marker in text
            for marker in [
                "build",
                "create",
                "develop",
                "implement",
                "application",
                "app",
                "api",
                "server",
                "project",
                "website",
                "rest api",
                "backend",
                "frontend",
            ]
        ):
            return "engineering"

        # Debugging markers are evaluated only when the task is
        # actually asking to diagnose or repair an existing problem.
        if any(
            marker in text
            for marker in [
                "debug",
                "debugging",
                "fix this",
                "fix the bug",
                "fix the error",
                "bug",
                "traceback",
                "not working",
                "broken",
                "fails",
                "failure",
            ]
        ):
            return "debugging"

        if any(
            marker in text
            for marker in [
                "write",
                "generate",
                "function",
                "class",
                "script",
                "code",
            ]
        ):
            return "coding"

        if any(
            marker in text
            for marker in [
                "plan",
                "roadmap",
                "architecture",
                "design",
            ]
        ):
            return "planning"

        if any(
            marker in text
            for marker in [
                "analyze",
                "analyse",
                "compare",
                "inspect",
            ]
        ):
            return "analysis"

        return "general"

    # ============================================================
    # COMPLEXITY
    # ============================================================

    @staticmethod
    def _estimate_complexity(task: str) -> str:

        text = task.lower()

        indicators = 0

        indicators += len(
            re.findall(
                r"\b(and|with|including|plus|also|then)\b",
                text,
            )
        )

        indicators += len(
            re.findall(
                r"\b(api|database|auth|authentication|"
                r"login|server|frontend|backend|"
                r"test|tests|deployment|socket|"
                r"sqlite|mongodb|postgres|redis)\b",
                text,
            )
        )

        words = len(text.split())

        if indicators >= 6 or words >= 45:
            return "high"

        if indicators >= 3 or words >= 20:
            return "medium"

        return "low"

    # ============================================================
    # SUBTASK GENERATION
    # ============================================================

    def _build_subtasks(
        self,
        task: str,
        task_type: str,
        complexity: str,
    ) -> list[dict[str, Any]]:

        if task_type == "debugging":
            return [
                self._step(
                    1,
                    "Inspect the existing project and reproduce the problem.",
                    [],
                ),
                self._step(
                    2,
                    "Identify the root cause from the observed failure.",
                    [1],
                ),
                self._step(
                    3,
                    "Implement the smallest safe fix.",
                    [2],
                ),
                self._step(
                    4,
                    "Run the relevant tests or reproduction case.",
                    [3],
                ),
                self._step(
                    5,
                    "Verify that the fix does not introduce regressions.",
                    [4],
                ),
            ]

        if task_type == "engineering":
            steps = [
                self._step(
                    1,
                    "Understand the requested system and define its required behavior.",
                    [],
                ),
                self._step(
                    2,
                    "Inspect the workspace and determine the required project structure.",
                    [1],
                ),
                self._step(
                    3,
                    "Implement the core application structure.",
                    [2],
                ),
                self._step(
                    4,
                    "Implement the requested features and integrations.",
                    [3],
                ),
                self._step(
                    5,
                    "Add validation, error handling, and edge-case handling.",
                    [4],
                ),
                self._step(
                    6,
                    "Create or update automated tests.",
                    [4],
                ),
                self._step(
                    7,
                    "Run the test suite and inspect failures.",
                    [5, 6],
                ),
                self._step(
                    8,
                    "Fix failures and retest until the requested behavior passes.",
                    [7],
                ),
                self._step(
                    9,
                    "Perform final verification against the original requirements.",
                    [8],
                ),
            ]

            if complexity == "low":
                return steps[:7]

            return steps

        if task_type == "coding":
            return [
                self._step(
                    1,
                    "Understand the requested behavior and constraints.",
                    [],
                ),
                self._step(
                    2,
                    "Design the implementation.",
                    [1],
                ),
                self._step(
                    3,
                    "Implement the requested code.",
                    [2],
                ),
                self._step(
                    4,
                    "Validate syntax and behavior.",
                    [3],
                ),
                self._step(
                    5,
                    "Review the implementation against the original request.",
                    [4],
                ),
            ]

        if task_type == "analysis":
            return [
                self._step(
                    1,
                    "Collect and inspect the relevant information.",
                    [],
                ),
                self._step(
                    2,
                    "Identify important patterns, constraints, and problems.",
                    [1],
                ),
                self._step(
                    3,
                    "Develop the analysis and conclusions.",
                    [2],
                ),
                self._step(
                    4,
                    "Validate the conclusions against the available evidence.",
                    [3],
                ),
            ]

        if task_type == "planning":
            return [
                self._step(
                    1,
                    "Define the objective and success criteria.",
                    [],
                ),
                self._step(
                    2,
                    "Identify requirements, constraints, and dependencies.",
                    [1],
                ),
                self._step(
                    3,
                    "Break the objective into executable milestones.",
                    [2],
                ),
                self._step(
                    4,
                    "Order the milestones by dependency.",
                    [3],
                ),
                self._step(
                    5,
                    "Define validation criteria for each milestone.",
                    [4],
                ),
            ]

        return [
            self._step(
                1,
                "Understand the requested objective.",
                [],
            ),
            self._step(
                2,
                "Determine the required actions.",
                [1],
            ),
            self._step(
                3,
                "Execute the solution.",
                [2],
            ),
            self._step(
                4,
                "Validate the result.",
                [3],
            ),
        ]

    # ============================================================
    # DEPENDENCIES
    # ============================================================

    @staticmethod
    def _build_dependencies(
        subtasks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        dependencies = []

        for step in subtasks:
            dependencies.append(
                {
                    "step": step["id"],
                    "depends_on": step["depends_on"],
                }
            )

        return dependencies

    # ============================================================
    # VALIDATION
    # ============================================================

    @staticmethod
    def _build_validation(
        task: str,
        task_type: str,
        subtasks: list[dict[str, Any]],
    ) -> dict[str, Any]:

        checks = [
            "The implementation addresses the original request.",
            "The result is internally consistent.",
            "Known errors are resolved.",
            "The final output is independently validated.",
        ]

        if task_type in {"coding", "engineering"}:
            checks.extend(
                [
                    "Syntax validation passes.",
                    "Relevant tests pass.",
                    "No obvious regression is introduced.",
                ]
            )

        if task_type == "debugging":
            checks.extend(
                [
                    "The original failure is reproduced before the fix.",
                    "The original failure no longer occurs after the fix.",
                ]
            )

        return {
            "required": True,
            "checks": checks,
            "success_condition": (
                "All applicable validation checks pass."
            ),
        }

    # ============================================================
    # STRATEGY
    # ============================================================

    @staticmethod
    def _build_strategy(
        task_type: str,
        complexity: str,
        subtasks: list[dict[str, Any]],
    ) -> dict[str, Any]:

        if task_type == "engineering":
            return {
                "mode": "structured_execution",
                "priority": [
                    "workspace_understanding",
                    "implementation",
                    "testing",
                    "verification",
                ],
                "allow_retry": True,
                "allow_replanning": True,
            }

        if task_type == "debugging":
            return {
                "mode": "diagnose_then_fix",
                "priority": [
                    "reproduce",
                    "diagnose",
                    "fix",
                    "test",
                ],
                "allow_retry": True,
                "allow_replanning": True,
            }

        return {
            "mode": "goal_then_validate",
            "priority": [
                "understand",
                "execute",
                "validate",
            ],
            "allow_retry": True,
            "allow_replanning": complexity != "low",
        }

    # ============================================================
    # MEMORY HINTS
    # ============================================================

    @staticmethod
    def _extract_memory_hints(
        memories: dict[str, Any],
    ) -> list[dict[str, Any]]:

        hints: list[dict[str, Any]] = []

        failures = memories.get("failures", []) or []
        lessons = memories.get("lessons", []) or []

        for failure in failures[-5:]:
            hints.append(
                {
                    "type": "failure",
                    "task": failure.get("task"),
                    "feedback": failure.get("feedback"),
                }
            )

        for lesson in lessons[-5:]:
            hints.append(
                {
                    "type": lesson.get("type", "lesson"),
                    "rule": lesson.get("rule"),
                }
            )

        return hints[-10:]

    # ============================================================
    # STEP FACTORY
    # ============================================================

    @staticmethod
    def _step(
        step_id: int,
        action: str,
        depends_on: list[int],
    ) -> dict[str, Any]:

        return {
            "id": step_id,
            "action": action,
            "depends_on": depends_on,
            "status": "pending",
        }
