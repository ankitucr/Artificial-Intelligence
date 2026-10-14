SKILL_VERSION = "1.0.0"
SKILL_DESCRIPTION = (
    "Basic demonstration skill that receives text "
    "and returns a structured response."
)


def run(args: dict) -> dict:
    text = str(
        args.get(
            "text",
            "hello from BEE5"
        )
    )

    return {
        "ok": True,
        "skill": "hello_skill",
        "text": text,
        "length": len(text)
    }


if __name__ == "__main__":
    print(run({}))
