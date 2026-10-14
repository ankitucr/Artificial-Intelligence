from typing import Any


class TaskAnalyzer:
    """
    Phase 27 task intelligence.

    Classifies the user's intent before selecting tools or workers.

    Priority:
        1. Coding / implementation
        2. Debugging
        3. Explicit deterministic calculation
        4. Text analysis
        5. Planning
        6. General analysis / reasoning
    """

    def analyze(
        self,
        task: str,
        memories: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        text = task.lower().strip()

        capabilities: list[str] = []
        tool_capabilities: list[str] = []

        # ---------------------------------------------------------
        # INTENT SIGNALS
        # ---------------------------------------------------------

        coding_markers = [
            "write a function",
            "create a function",
            "define a function",
            "implement a function",
            "write code",
            "create code",
            "generate code",
            "python code",
            "javascript code",
            "typescript code",
            "class ",
            "def ",
            "function ",
            "implement ",
            "program ",
            "script ",
            "api ",
            "debug ",
            "refactor ",
        ]

        coding_intent = any(
            marker in text
            for marker in coding_markers
        )

        debugging_markers = [
            "debug",
            "error",
            "exception",
            "traceback",
            "fix",
            "broken",
            "not working",
            "fails",
            "failure",
            "bug",
        ]

        debugging_intent = any(
            marker in text
            for marker in debugging_markers
        )

        # ---------------------------------------------------------
        # CODING
        #
        # Coding takes precedence over calculation words such as
        # "multiply", "sum", "add", etc.
        # ---------------------------------------------------------

        if coding_intent:
            capabilities.append("coding")

        # ---------------------------------------------------------
        # DEBUGGING
        # ---------------------------------------------------------

        if debugging_intent:
            capabilities.append("debugging")

        # ---------------------------------------------------------
        # EXPLICIT DETERMINISTIC CALCULATION
        #
        # Only classify as a tool calculation when the user's
        # primary intent is actually to calculate a value.
        # ---------------------------------------------------------

        calculation_markers = [
            "calculate",
            "calculation",
            "what is the sum",
            "what is the product",
            "what is the difference",
            "what is the result",
            "add ",
            "subtract ",
            "divide ",
            "multiply ",
        ]

        calculation_intent = any(
            marker in text
            for marker in calculation_markers
        )

        # A coding request containing words such as "multiply"
        # should NOT become a deterministic calculation task.
        if calculation_intent and not coding_intent:
            capabilities.append("calculation")
            tool_capabilities.append("calculation")

        # ---------------------------------------------------------
        # TEXT
        # ---------------------------------------------------------

        text_markers = [
            "length of this text",
            "character count",
            "count characters",
            "text length",
        ]

        if any(
            marker in text
            for marker in text_markers
        ):
            capabilities.append("text")
            tool_capabilities.append("text")

        # ---------------------------------------------------------
        # ANALYSIS
        # ---------------------------------------------------------

        analysis_markers = [
            "analyze",
            "analysis",
            "compare",
            "explain",
            "evaluate",
            "inspect",
            "review",
            "why",
        ]

        if any(
            marker in text
            for marker in analysis_markers
        ):
            capabilities.append("analysis")

        # ---------------------------------------------------------
        # PLANNING
        # ---------------------------------------------------------

        planning_markers = [
            "plan",
            "planning",
            "architecture",
            "design",
            "roadmap",
            "strategy",
        ]

        if any(
            marker in text
            for marker in planning_markers
        ):
            capabilities.append("planning")

        # ---------------------------------------------------------
        # GENERATION
        # ---------------------------------------------------------

        generation_markers = [
            "write",
            "create",
            "generate",
            "build",
            "make",
            "produce",
        ]

        if any(
            marker in text
            for marker in generation_markers
        ):
            capabilities.append("generation")

        # ---------------------------------------------------------
        # REASONING
        # ---------------------------------------------------------

        reasoning_markers = [
            "solve",
            "reason",
            "calculate",
            "logic",
            "figure out",
            "determine",
        ]

        if any(
            marker in text
            for marker in reasoning_markers
        ):
            capabilities.append("reasoning")

        # ---------------------------------------------------------
        # REMOVE DUPLICATES
        # ---------------------------------------------------------

        capabilities = list(
            dict.fromkeys(capabilities)
        )

        tool_capabilities = list(
            dict.fromkeys(tool_capabilities)
        )

        if not capabilities:
            capabilities.append("reasoning")

        # ---------------------------------------------------------
        # TASK TYPE
        #
        # Intent priority is important here.
        # ---------------------------------------------------------

        if coding_intent:
            task_type = "coding"

        elif debugging_intent:
            task_type = "debugging"

        elif "calculation" in capabilities:
            task_type = "calculation"

        elif "text" in capabilities:
            task_type = "text"

        elif "planning" in capabilities:
            task_type = "planning"

        elif "analysis" in capabilities:
            task_type = "analysis"

        elif "generation" in capabilities:
            task_type = "generation"

        else:
            task_type = "reasoning"

        # ---------------------------------------------------------
        # COMPLEXITY
        # ---------------------------------------------------------

        complexity = self._complexity(
            text,
            capabilities,
        )

        # ---------------------------------------------------------
        # TOOL DECISION
        # ---------------------------------------------------------

        tool_required = bool(
            tool_capabilities
        )

        strategy = self._strategy(
            task_type,
            complexity,
            tool_required,
        )

        return {
            "task": task,
            "task_type": task_type,
            "capabilities": capabilities,
            "tool_capabilities": tool_capabilities,
            "tool_required": tool_required,
            "complexity": complexity,
            "strategy": strategy,
            "memory_available": bool(memories),
        }

    @staticmethod
    def _complexity(
        text: str,
        capabilities: list[str],
    ) -> str:

        score = 0

        if len(text) > 120:
            score += 1

        if len(text) > 300:
            score += 1

        complex_markers = [
            "architecture",
            "system",
            "multiple",
            "integrate",
            "refactor",
            "production",
            "security",
            "database",
            "distributed",
            "optimize",
        ]

        score += sum(
            1
            for marker in complex_markers
            if marker in text
        )

        if len(capabilities) >= 3:
            score += 1

        if score >= 4:
            return "high"

        if score >= 2:
            return "medium"

        return "low"

    @staticmethod
    def _strategy(
        task_type: str,
        complexity: str,
        tool_required: bool,
    ) -> str:

        if tool_required:
            return (
                "Use a registered deterministic tool when it "
                "directly satisfies the user's calculation or "
                "text operation."
            )

        if task_type == "debugging":
            return (
                "Inspect the failure, identify the root cause, "
                "produce a correction, then independently validate it."
            )

        if task_type == "coding":
            return (
                "Understand the requested behavior, implement "
                "the solution, then independently validate it."
            )

        if task_type == "planning":
            return (
                "Decompose the objective into ordered steps "
                "and identify required capabilities."
            )

        if task_type == "analysis":
            return (
                "Extract relevant evidence, analyze it, "
                "and produce a justified result."
            )

        return (
            "Break the task into logical steps and verify "
            "the resulting answer."
        )
