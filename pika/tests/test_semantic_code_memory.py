import tempfile
import unittest
from pathlib import Path

from core.semantic_code_memory import SemanticCodeMemory


class SemanticCodeMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Path(self.temp_dir.name) / "memory.json"
        self.memory = SemanticCodeMemory(self.db)

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_verified(self, intent, code, tags=None):
        return self.memory.remember(
            intent=intent,
            code=code,
            tags=tags or [],
            verification="test_verified",
            evidence=["Independent unit tests passed"],
            test_cases=[{"input": [3, 4], "expected": 7}],
        )

    def test_persistence_across_instances(self):
        item = self.add_verified(
            "add two numbers",
            "def add(a, b): return a + b",
            ["math", "addition"],
        )
        reloaded = SemanticCodeMemory(self.db)
        results = reloaded.retrieve("addition add two numbers")
        self.assertTrue(any(v["id"] == item["id"] for v in results))

    def test_unverified_not_returned_by_default(self):
        self.memory.remember(
            intent="calculate discount",
            code="def discount(price, percent): return price",
        )
        self.assertEqual(
            self.memory.retrieve("calculate discount"),
            [],
        )
        self.assertEqual(
            len(self.memory.retrieve("calculate discount", verified_only=False)),
            1,
        )

    def test_failed_variant_is_excluded(self):
        item = self.add_verified("sum two values", "def f(a,b): return a+b")
        self.memory.record_test_result(
            item["id"], passed=False, evidence="Boundary test failed"
        )
        self.assertEqual(self.memory.retrieve("sum two values"), [])

    def test_variants_are_preserved(self):
        self.add_verified("add two numbers", "def add(a,b): return a+b")
        self.add_verified(
            "add two numbers",
            "def add(a,b):\n    result = a+b\n    return result",
        )
        self.assertEqual(self.memory.stats()["total_variants"], 2)

    def test_tag_retrieval(self):
        self.add_verified(
            "apply percentage discount",
            "def discount(price, percent): return price * (1-percent/100)",
            ["pricing", "percentage"],
        )
        results = self.memory.retrieve(
            "price reduction", tags=["pricing"]
        )
        self.assertEqual(len(results), 1)

    def test_empty_input_rejected(self):
        with self.assertRaises(ValueError):
            self.memory.remember(intent="", code="x = 1")

    def test_equivalent_group_is_explicit(self):
        self.memory.remember(
            intent="add two numbers",
            code="def add(a,b): return a+b",
            verification="test_verified",
            evidence=["Tests passed"],
            equivalent_group="addition-v1",
        )
        self.memory.remember(
            intent="add two numbers",
            code="def add(a,b):\n    c=a+b\n    return c",
            verification="test_verified",
            evidence=["Tests passed"],
            equivalent_group="addition-v1",
        )
        self.assertEqual(len(self.memory.variants_in_group("addition-v1")), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
