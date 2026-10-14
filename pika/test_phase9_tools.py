from core.tool_runtime import ToolRuntime
from skills.builtin import register_builtin_skills
from skills.registry import SkillRegistry
from tools.builtin import register_builtin_tools
from tools.registry import ToolRegistry


def main():

    print("=" * 60)
    print("PIKA PHASE 9")
    print("SKILL + TOOL SYSTEM TEST")
    print("=" * 60)

    skills = SkillRegistry()
    tools = ToolRegistry()

    register_builtin_skills(
        skills
    )

    register_builtin_tools(
        tools
    )

    runtime = ToolRuntime(
        skills=skills,
        tools=tools,
    )

    print()
    print("REGISTERED SKILLS:")
    print(skills.list())

    print()
    print("REGISTERED TOOLS:")
    print(tools.list())

    # ---------------------------------------------------------
    # Discovery
    # ---------------------------------------------------------

    calculation = runtime.discover(
        [
            "calculation",
            "reasoning",
        ]
    )

    print()
    print("CALCULATION DISCOVERY:")
    print(calculation)

    text = runtime.discover(
        [
            "text",
            "analysis",
        ]
    )

    print()
    print("TEXT DISCOVERY:")
    print(text)

    # ---------------------------------------------------------
    # Execution
    # ---------------------------------------------------------

    sum_result = runtime.execute(
        "calculator_sum",
        a=10,
        b=32,
    )

    product_result = runtime.execute(
        "calculator_product",
        a=6,
        b=7,
    )

    length_result = runtime.execute(
        "text_length",
        text="PIKA",
    )

    print()
    print("TOOL RESULTS:")
    print("10 + 32 =", sum_result)
    print("6 * 7 =", product_result)
    print("len('PIKA') =", length_result)

    # ---------------------------------------------------------
    # Assertions
    # ---------------------------------------------------------

    passed = (
        "calculation"
        in skills.list()

        and "text_analysis"
        in skills.list()

        and "calculator_sum"
        in tools.list()

        and "calculator_product"
        in tools.list()

        and "text_length"
        in tools.list()

        and "calculator_sum"
        in calculation["tools"]

        and "calculator_product"
        in calculation["tools"]

        and "text_length"
        in text["tools"]

        and sum_result == 42

        and product_result == 42

        and length_result == 4
    )

    print()

    if passed:
        print(
            "PIKA PHASE 9 TOOL/SKILL TEST: PASSED"
        )
    else:
        print(
            "PIKA PHASE 9 TOOL/SKILL TEST: FAILED"
        )


if __name__ == "__main__":
    main()
