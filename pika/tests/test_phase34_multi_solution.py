import tempfile
from pathlib import Path

from core.learning_engine import LearningEngine


def main():
    with tempfile.TemporaryDirectory(
        prefix="pika_phase34_"
    ) as temp:
        db = Path(temp) / "learning_test.json"
        engine = LearningEngine(db)

        task = (
            "repair calculator add function "
            "when arithmetic addition test fails"
        )

        common = {
            "task": task,
            "error_type": "test_failure",
            "root_cause": "addition uses subtraction",
            "error_message": "expected 5 but received -1",
            "verification": {
                "syntax": True,
                "test": True,
                "independent_test": True,
            },
            "source": "phase34_acceptance",
            "replay_context": {
                "target_path": "calculator.py",
                "old_text": "return a - b",
                "test_path": "test_calculator.py",
            },
        }

        print("1. Recording verified solution A...")
        engine.learn(
            **common,
            method="direct_addition",
            solution="return a + b",
            success=True,
        )

        print("2. Recording verified solution B...")
        engine.learn(
            **common,
            method="builtin_sum",
            solution="return sum((a, b))",
            success=True,
        )

        print("3. Recording a failed method...")
        failed_record = dict(common)
        failed_record["verification"] = {
            "syntax": True,
            "test": False,
            "independent_test": False,
        }

        engine.learn(
            **failed_record,
            method="incorrect_formula",
            solution="return a * b",
            success=False,
        )

        data = engine.data
        assert len(data["experiences"]) == 3

        pattern = data["patterns"][0]
        assert len(pattern["solutions"]) == 2
        assert len(pattern["failed_methods"]) == 1

        assert all(
            item["verified_count"] > 0
            for item in pattern["solutions"]
        )

        assert pattern["failed_methods"][0]["solution"] == (
            "return a * b"
        )

        assert pattern["confidence"] == round(2 / 3, 4)

        print("PASS: two distinct verified solutions preserved")
        print("PASS: failed method stored separately")
        print("PASS: confidence reflects 2 successes / 3 attempts")

        print("4. Testing similar-problem retrieval...")
        result = engine.retrieve(
            task=(
                "fix calculator addition because "
                "the arithmetic test returns a negative answer"
            ),
            error_type="test_failure",
            root_cause="addition uses subtraction",
            error_message="expected 5 but received -1",
        )

        assert result["known"], (
            "Similar problem was not retrieved."
        )

        retrieved_solutions = [
            solution
            for match in result["matches"]
            for solution in match["solutions"]
        ]

        solution_texts = {
            item["solution"] for item in retrieved_solutions
        }

        assert "return a + b" in solution_texts
        assert "return sum((a, b))" in solution_texts
        assert "return a * b" not in solution_texts

        print("PASS: similar problem retrieved")
        print("PASS: both verified solutions are available")
        print("PASS: failed method excluded from trusted solutions")

        print("\nPHASE 34 MULTI-SOLUTION MEMORY TEST: PASS")
        print("Cohere calls: 0")
        print("Production learning database: untouched")


if __name__ == "__main__":
    main()
