class Planner:

    def plan(self, task: str) -> list[str]:
        """
        Bootstrap planner.
        A model-driven planner will replace this later.
        """

        return [
            f"Understand task: {task}",
            "Select required capability",
            "Execute through agent",
            "Evaluate result",
            "Store experience",
        ]
