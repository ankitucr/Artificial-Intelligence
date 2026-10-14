from __future__ import annotations

import re
from typing import Any


class DecisionEngine:
    """
    Memory-guided strategy selector.

    The engine does not blindly trust memory.
    It uses historical evidence to influence the next routing decision.
    """

    def decide(
        self,
        task_analysis: dict[str, Any],
        memories: dict[str, Any] | None = None,
        tool_runtime: Any = None,
        attempt: int = 1,
        previous_feedback: str = "",
    ) -> dict[str, Any]:

        memories = memories or {}

        task = str(task_analysis.get("task", "") or "")
        task_type = str(task_analysis.get("task_type", "unknown"))
        tool_required = bool(task_analysis.get("tool_required"))
        tool_capabilities = task_analysis.get("tool_capabilities", []) or []

        task_signature = self._task_signature(task, task_analysis)

        available_tools: list[str] = []

        if tool_runtime and tool_capabilities:
            discovery = tool_runtime.discover(tool_capabilities)
            available_tools = discovery.get("tools", []) or []

        evidence = self._historical_evidence(
            task=task,
            task_type=task_type,
            task_signature=task_signature,
            memories=memories,
        )

        # ---------------------------------------------------------
        # Retry after evaluator feedback
        # ---------------------------------------------------------
        if previous_feedback:
            return {
                "mode": "agent",
                "confidence": 0.97,
                "reason": "retry requires general worker reasoning using evaluator feedback.",
                "task_signature": task_signature,
                "attempt": attempt,
                "available_tools": available_tools,
                "history": evidence,
            }

        # ---------------------------------------------------------
        # Exact historical tool success
        # ---------------------------------------------------------
        if (
            tool_required
            and available_tools
            and evidence["matching_tool_successes"] > 0
            and evidence["matching_tool_failures"] == 0
        ):
            return {
                "mode": "tool",
                "confidence": 0.99,
                "reason": (
                    "historical evidence shows the deterministic tool "
                    "successfully solved this task signature."
                ),
                "task_signature": task_signature,
                "attempt": attempt,
                "available_tools": available_tools,
                "history": evidence,
            }

        # ---------------------------------------------------------
        # Historical exact tool failures
        #
        # A deterministic failure for the same operation is stronger
        # evidence than a generic calculation capability match.
        # ---------------------------------------------------------
        if (
            tool_required
            and evidence["matching_tool_failures"] > 0
            and evidence["matching_tool_successes"] == 0
        ):
            return {
                "mode": "agent",
                "confidence": 0.94,
                "reason": (
                    "historical evidence shows the tool previously failed "
                    "for this exact task signature; escalating directly "
                    "to the general worker."
                ),
                "task_signature": task_signature,
                "attempt": attempt,
                "available_tools": available_tools,
                "history": evidence,
            }

        # ---------------------------------------------------------
        # Historical agent success
        # ---------------------------------------------------------
        if evidence["matching_agent_successes"] > 0 and not available_tools:
            return {
                "mode": "agent",
                "confidence": 0.95,
                "reason": (
                    "historical evidence shows the general worker "
                    "successfully solved this task signature."
                ),
                "task_signature": task_signature,
                "attempt": attempt,
                "available_tools": available_tools,
                "history": evidence,
            }

        # ---------------------------------------------------------
        # Deterministic tool available but no strong history
        # ---------------------------------------------------------
        if tool_required and available_tools:
            return {
                "mode": "tool",
                "confidence": 0.90,
                "reason": (
                    "a registered deterministic tool is available and "
                    "there is no conflicting historical evidence."
                ),
                "task_signature": task_signature,
                "attempt": attempt,
                "available_tools": available_tools,
                "history": evidence,
            }

        # ---------------------------------------------------------
        # Default general worker
        # ---------------------------------------------------------
        return {
            "mode": "agent",
            "confidence": 0.90,
            "reason": (
                f"task type '{task_type}' requires general worker intelligence."
            ),
            "task_signature": task_signature,
            "attempt": attempt,
            "available_tools": available_tools,
            "history": evidence,
        }

    # =============================================================
    # TASK SIGNATURE
    # =============================================================

    def _task_signature(
        self,
        task: str,
        task_analysis: dict[str, Any],
    ) -> str:

        task_type = str(
            task_analysis.get("task_type", "unknown")
        ).lower()

        text = task.lower().strip()

        if task_type == "calculation":
            if self._contains_any(
                text,
                [
                    "multiply",
                    "multiplied",
                    "multiplication",
                    "product",
                    "*",
                ],
            ):
                return "calculation:multiply"

            if self._contains_any(
                text,
                [
                    "add",
                    "sum",
                    "plus",
                    "addition",
                    "+",
                ],
            ):
                return "calculation:add"

            if self._contains_any(
                text,
                [
                    "subtract",
                    "subtraction",
                    "difference",
                    "minus",
                    "-",
                ],
            ):
                return "calculation:subtract"

            if self._contains_any(
                text,
                [
                    "divide",
                    "divided",
                    "division",
                    "quotient",
                    "/",
                ],
            ):
                return "calculation:divide"

            return "calculation:other"

        if task_type == "text":
            if self._contains_any(
                text,
                [
                    "length",
                    "character count",
                    "count characters",
                    "text length",
                ],
            ):
                return "text:length"

            return "text:other"

        if task_type == "coding":
            if self._contains_any(
                text,
                [
                    "function",
                    "def ",
                    "method",
                ],
            ):
                return "coding:function"

            if self._contains_any(
                text,
                [
                    "class ",
                ],
            ):
                return "coding:class"

            return "coding:general"

        if task_type == "debugging":
            return "debugging"

        if task_type == "planning":
            return "planning"

        if task_type == "analysis":
            return "analysis"

        if task_type == "generation":
            return "generation"

        if task_type == "reasoning":
            return "reasoning"

        return f"{task_type}:general"

    # =============================================================
    # MEMORY EVIDENCE
    # =============================================================

    def _historical_evidence(
        self,
        task: str,
        task_type: str,
        task_signature: str,
        memories: dict[str, Any],
    ) -> dict[str, Any]:

        episodes = memories.get("episodes", []) or []
        failures = memories.get("failures", []) or []

        matching_tool_successes = 0
        matching_tool_failures = 0
        matching_agent_successes = 0
        matching_agent_failures = 0

        matched_history: list[dict[str, Any]] = []

        # ---------------------------------------------------------
        # Successful episodes
        # ---------------------------------------------------------
        for episode in episodes:
            episode_signature = self._memory_signature(
                episode,
                task_type=task_type,
            )

            if episode_signature != task_signature:
                continue

            result = episode.get("result", {}) or {}
            evaluation = episode.get("evaluation", {}) or {}

            passed = bool(evaluation.get("passed"))
            agent = result.get("agent")

            if passed and agent == "tool":
                matching_tool_successes += 1

            elif passed and agent != "tool":
                matching_agent_successes += 1

            matched_history.append(
                {
                    "outcome": "success" if passed else "failure",
                    "agent": agent,
                    "strategy": episode.get("strategy"),
                    "signature": episode_signature,
                }
            )

        # ---------------------------------------------------------
        # Historical failures
        # ---------------------------------------------------------
        for failure in failures:
            failure_signature = self._memory_signature(
                failure,
                task_type=task_type,
            )

            if failure_signature != task_signature:
                continue

            result = failure.get("result", {}) or {}
            evaluation = failure.get("evaluation", {}) or {}

            passed = bool(evaluation.get("passed"))
            agent = result.get("agent")

            if not passed and agent == "tool":
                matching_tool_failures += 1

            elif not passed and agent != "tool":
                matching_agent_failures += 1

            matched_history.append(
                {
                    "outcome": "failure",
                    "agent": agent,
                    "strategy": failure.get("strategy"),
                    "signature": failure_signature,
                }
            )

        return {
            "task_signature": task_signature,
            "matching_tool_successes": matching_tool_successes,
            "matching_tool_failures": matching_tool_failures,
            "matching_agent_successes": matching_agent_successes,
            "matching_agent_failures": matching_agent_failures,
            "matches": matched_history[-10:],
        }

    # =============================================================
    # BACKWARD COMPATIBILITY
    # =============================================================

    def _memory_signature(
        self,
        item: dict[str, Any],
        task_type: str,
    ) -> str:

        explicit = item.get("task_signature")

        if explicit:
            return str(explicit)

        decision = item.get("decision", {}) or {}

        explicit = decision.get("task_signature")

        if explicit:
            return str(explicit)

        task = str(item.get("task", "") or "")

        # Infer signature from older Phase 28 memory entries.
        fake_analysis = {
            "task": task,
            "task_type": task_type,
        }

        return self._task_signature(task, fake_analysis)

    @staticmethod
    def _contains_any(text: str, markers: list[str]) -> bool:
        return any(marker in text for marker in markers)
