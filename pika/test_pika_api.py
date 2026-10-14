import asyncio

from agents.api_load_balancer import (
    APILoadBalancerAgent
)


async def main():

    print("=" * 70)
    print("PIKA API LOAD BALANCER TEST")
    print("=" * 70)

    agent = APILoadBalancerAgent()

    tasks = [
        (
            "coder",
            "Write a Python function that reverses a string. "
            "Return only the function."
        ),

        (
            "analyzer",
            "Explain in one sentence why eval() can be dangerous."
        ),

        (
            "planner",
            "Give a 3-step plan for building a coding agent."
        ),

        (
            "debugger",
            "Find the likely bug in: "
            "for i in range(5) print(i)"
        ),
    ]

    for role, task in tasks:

        print()
        print("-" * 70)
        print(f"ROLE: {role}")
        print("-" * 70)

        result = await agent.execute(
            task,
            context={
                "role": role,
                "memory": {},
                "plan": [],
            },
        )

        print()
        print("SUCCESS :", result["success"])
        print("AGENT   :", result["agent"])
        print("ROLE    :", result["role"])
        print("PROVIDER:", result["provider"])
        print("MODEL   :", result["model"])
        print("LATENCY :", result["latency"])
        print("OUTPUT  :")
        print(result["output"])

        if result["attempts"]:

            print()
            print("ATTEMPTS:")

            for attempt in result["attempts"]:

                print(
                    " -",
                    attempt.get("provider"),
                    "|",
                    attempt.get("model"),
                    "|",
                    attempt.get("status_code", "OK"),
                    "|",
                    attempt.get("error", ""),
                )

    print()
    print("=" * 70)
    print("PIKA API LOAD BALANCER TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
