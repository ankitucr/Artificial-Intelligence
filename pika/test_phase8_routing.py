from core.router import AgentRouter
from core.task_analyzer import TaskAnalyzer


class CodingAgent:
    name = "coding-agent"
    capabilities = [
        "coding",
        "debugging",
        "generation",
    ]


class AnalysisAgent:
    name = "analysis-agent"
    capabilities = [
        "analysis",
        "reasoning",
    ]


class PlanningAgent:
    name = "planning-agent"
    capabilities = [
        "planning",
        "reasoning",
    ]


def main():

    print("=" * 60)
    print("PIKA PHASE 8")
    print("TASK INTELLIGENCE + CAPABILITY ROUTING")
    print("=" * 60)

    analyzer = TaskAnalyzer()

    router = AgentRouter()

    coding = CodingAgent()
    analysis = AnalysisAgent()
    planning = PlanningAgent()

    router.register(coding)
    router.register(analysis)
    router.register(planning)

    # ---------------------------------------------------------
    # Test 1: Coding
    # ---------------------------------------------------------

    coding_task = (
        "Write a Python function that calculates "
        "the factorial of a number."
    )

    coding_analysis = analyzer.analyze(
        coding_task
    )

    coding_selected = router.select(
        required_capabilities=(
            coding_analysis["capabilities"]
        )
    )

    print()
    print("CODING TASK:")
    print(coding_task)

    print()
    print("TASK ANALYSIS:")
    print(coding_analysis)

    print()
    print("SELECTED AGENT:")
    print(coding_selected.name)

    # ---------------------------------------------------------
    # Test 2: Analysis
    # ---------------------------------------------------------

    analysis_task = (
        "Analyze why this algorithm is slow "
        "and explain the performance bottleneck."
    )

    analysis_result = analyzer.analyze(
        analysis_task
    )

    analysis_selected = router.select(
        required_capabilities=(
            analysis_result["capabilities"]
        )
    )

    print()
    print("ANALYSIS TASK:")
    print(analysis_task)

    print()
    print("TASK ANALYSIS:")
    print(analysis_result)

    print()
    print("SELECTED AGENT:")
    print(analysis_selected.name)

    # ---------------------------------------------------------
    # Test 3: Planning
    # ---------------------------------------------------------

    planning_task = (
        "Design an architecture and roadmap "
        "for a scalable application."
    )

    planning_result = analyzer.analyze(
        planning_task
    )

    planning_selected = router.select(
        required_capabilities=(
            planning_result["capabilities"]
        )
    )

    print()
    print("PLANNING TASK:")
    print(planning_task)

    print()
    print("TASK ANALYSIS:")
    print(planning_result)

    print()
    print("SELECTED AGENT:")
    print(planning_selected.name)

    # ---------------------------------------------------------
    # Assertions
    # ---------------------------------------------------------

    passed = (
        coding_analysis["task_type"] == "coding"
        and "coding"
        in coding_analysis["capabilities"]
        and coding_selected.name == "coding-agent"

        and analysis_result["task_type"]
        == "analysis"
        and "analysis"
        in analysis_result["capabilities"]
        and analysis_selected.name
        == "analysis-agent"

        and planning_result["task_type"]
        == "planning"
        and "planning"
        in planning_result["capabilities"]
        and planning_selected.name
        == "planning-agent"
    )

    print()

    if passed:
        print(
            "PIKA PHASE 8 ROUTING TEST: PASSED"
        )
    else:
        print(
            "PIKA PHASE 8 ROUTING TEST: FAILED"
        )


if __name__ == "__main__":
    main()
