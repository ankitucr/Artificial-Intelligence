from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any


class LearningEngine:
    """
    PIKA Phase 34 — Actual Continual Learning.

    Learns from:
      - problem/error
      - root cause
      - successful solutions
      - failed solutions
      - verification evidence

    Important:
      Learning is NOT trusted merely because something was generated.
      A solution becomes reusable only after independent verification.
    """

    VERSION = 1

    def __init__(self, storage_path: str | Path):
        self.path = Path(storage_path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    # ---------------------------------------------------------
    # STORAGE
    # ---------------------------------------------------------

    def _default(self) -> dict[str, Any]:
        return {
            "version": self.VERSION,
            "experiences": [],
            "patterns": [],
        }

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._default()

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))

            if not isinstance(data, dict):
                return self._default()

            data.setdefault("version", self.VERSION)
            data.setdefault("experiences", [])
            data.setdefault("patterns", [])

            return data

        except Exception:
            return self._default()

    def _save(self) -> None:
        temp = self.path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(
                self.data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        temp.replace(self.path)

    # ---------------------------------------------------------
    # NORMALIZATION
    # ---------------------------------------------------------

    @staticmethod
    def normalize(value: Any) -> str:
        if value is None:
            return ""

        value = str(value).lower()

        value = re.sub(
            r"\d+",
            "<n>",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    @classmethod
    def problem_pattern(
        cls,
        task: str = "",
        error_type: str = "",
        root_cause: str = "",
        error_message: str = "",
    ) -> str:

        parts = [
            cls.normalize(task),
            cls.normalize(error_type),
            cls.normalize(root_cause),
            cls.normalize(error_message),
        ]

        parts = [x for x in parts if x]

        return " | ".join(parts)

    # ---------------------------------------------------------
    # LEARN
    # ---------------------------------------------------------

    def learn(
        self,
        *,
        task: str,
        error_type: str = "",
        root_cause: str = "",
        error_message: str = "",
        method: str = "",
        solution: str = "",
        verification: dict[str, Any] | None = None,
        success: bool = False,
        source: str = "local",
        metadata: dict[str, Any] | None = None,
        replay_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        verification = verification or {}
        metadata = metadata or {}
        replay_context = replay_context or {}

        pattern = self.problem_pattern(
            task=task,
            error_type=error_type,
            root_cause=root_cause,
            error_message=error_message,
        )

        record = {
            "timestamp": time.time(),
            "task": task,
            "problem_pattern": pattern,
            "error_type": error_type,
            "root_cause": root_cause,
            "error_message": error_message,
            "method": method,
            "solution": solution,
            "verification": verification,
            "success": bool(success),
            "trusted": bool(success and self._verified(verification)),
            "source": source,
            "metadata": metadata,
            "replay_context": {
                "target_path": replay_context.get("target_path", ""),
                "old_text": replay_context.get("old_text", ""),
                "test_path": replay_context.get("test_path", ""),
            },
        }

        self.data["experiences"].append(record)

        self._update_pattern(record)

        self._save()

        return record

    @staticmethod
    def _verified(verification: dict[str, Any]) -> bool:
        """
        Trust requires real verification.

        Accepted signals:
          syntax
          test
          independent_test
          execution
        """

        syntax = bool(
            verification.get("syntax")
            or verification.get("syntax_valid")
        )

        test = bool(
            verification.get("test")
            or verification.get("test_passed")
            or verification.get("independent_test")
        )

        execution = bool(
            verification.get("execution")
            or verification.get("execution_passed")
        )

        return test or (syntax and execution)

    # ---------------------------------------------------------
    # PATTERN DATABASE
    # ---------------------------------------------------------

    def _update_pattern(self, record: dict[str, Any]) -> None:
        pattern = record["problem_pattern"]

        if not pattern:
            return

        patterns = self.data["patterns"]

        existing = None

        for item in patterns:
            if item.get("problem_pattern") == pattern:
                existing = item
                break

        if existing is None:
            existing = {
                "problem_pattern": pattern,
                "error_type": record.get("error_type", ""),
                "root_causes": [],
                "solutions": [],
                "failed_methods": [],
                "attempts": 0,
                "successes": 0,
                "failures": 0,
                "confidence": 0.0,
                "updated_at": time.time(),
            }

            patterns.append(existing)

        existing["attempts"] += 1

        if record.get("success"):
            existing["successes"] += 1
        else:
            existing["failures"] += 1

        root = record.get("root_cause")

        if root and root not in existing["root_causes"]:
            existing["root_causes"].append(root)

        solution = record.get("solution")
        method = record.get("method") or "unknown"

        if solution:
            target = (
                existing["solutions"]
                if record.get("success")
                else existing["failed_methods"]
            )

            found = None

            for item in target:
                if self.normalize(item.get("solution")) == self.normalize(solution):
                    found = item
                    break

            if found is None:
                found = {
                    "method": method,
                    "solution": solution,
                    "success_count": 0,
                    "failure_count": 0,
                    "verified_count": 0,
                    "last_used": time.time(),
                    "replay_context": {
                        "target_path": record.get(
                            "replay_context", {}
                        ).get("target_path", ""),
                        "old_text": record.get(
                            "replay_context", {}
                        ).get("old_text", ""),
                        "test_path": record.get(
                            "replay_context", {}
                        ).get("test_path", ""),
                    },
                }
                target.append(found)

            if record.get("success"):
                found["success_count"] += 1
            else:
                found["failure_count"] += 1

            if record.get("trusted"):
                found["verified_count"] += 1

            found["last_used"] = time.time()

        attempts = existing["attempts"]

        if attempts:
            existing["confidence"] = round(
                existing["successes"] / attempts,
                4,
            )

        existing["updated_at"] = time.time()

    # ---------------------------------------------------------
    # RETRIEVAL
    # ---------------------------------------------------------

    def retrieve(
        self,
        *,
        task: str,
        error_type: str = "",
        root_cause: str = "",
        error_message: str = "",
        limit: int = 5,
    ) -> dict[str, Any]:

        query = self.problem_pattern(
            task=task,
            error_type=error_type,
            root_cause=root_cause,
            error_message=error_message,
        )

        query_tokens = self._tokens(query)

        matches = []

        for pattern in self.data.get("patterns", []):
            candidate = pattern.get("problem_pattern", "")
            candidate_tokens = self._tokens(candidate)

            if not candidate_tokens:
                continue

            overlap = len(query_tokens & candidate_tokens)

            similarity = overlap / max(
                1,
                len(query_tokens),
            )

            if similarity >= 0.20:
                matches.append(
                    (
                        similarity,
                        pattern,
                    )
                )

        matches.sort(
            key=lambda item: (
                item[0],
                item[1].get("confidence", 0.0),
                item[1].get("updated_at", 0.0),
            ),
            reverse=True,
        )

        results = []

        for similarity, pattern in matches[:max(1, limit)]:
            solutions = []

            for solution in pattern.get("solutions", []):
                if solution.get("verified_count", 0) <= 0:
                    continue

                success_count = solution.get(
                    "success_count",
                    0,
                )

                failure_count = solution.get(
                    "failure_count",
                    0,
                )

                score = (
                    success_count * 3.0
                    + solution.get("verified_count", 0) * 5.0
                    - failure_count * 2.0
                )

                solutions.append(
                    {
                        **solution,
                        "score": score,
                    }
                )

            solutions.sort(
                key=lambda x: x.get("score", 0.0),
                reverse=True,
            )

            results.append(
                {
                    "similarity": round(similarity, 4),
                    "problem_pattern": pattern.get(
                        "problem_pattern"
                    ),
                    "root_causes": pattern.get(
                        "root_causes",
                        [],
                    ),
                    "confidence": pattern.get(
                        "confidence",
                        0.0,
                    ),
                    "solutions": solutions,
                    "failed_methods": pattern.get(
                        "failed_methods",
                        [],
                    ),
                }
            )

        return {
            "known": bool(results),
            "query": query,
            "matches": results,
        }

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {
            token
            for token in re.findall(
                r"[a-zA-Z_][a-zA-Z0-9_]*",
                value.lower(),
            )
            if len(token) > 2
        }

    # ---------------------------------------------------------
    # REPLAY
    # ---------------------------------------------------------

    def best_solutions(
        self,
        *,
        task: str,
        error_type: str = "",
        root_cause: str = "",
        error_message: str = "",
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Return ranked, previously verified solutions only."""
        result = self.retrieve(
            task=task,
            error_type=error_type,
            root_cause=root_cause,
            error_message=error_message,
            limit=5,
        )
        if not result.get("known"):
            return []

        candidates = []
        seen = set()

        for match in result.get("matches", []):
            for solution in match.get("solutions", []):
                if solution.get("verified_count", 0) <= 0:
                    continue

                code = str(solution.get("solution", ""))
                normalized = self.normalize(code)
                if not normalized or normalized in seen:
                    continue
                seen.add(normalized)

                candidates.append({
                    **solution,
                    "similarity": match.get("similarity", 0.0),
                    "pattern": match.get("problem_pattern", ""),
                })

        candidates.sort(
            key=lambda item: (
                item.get("similarity", 0.0),
                item.get("score", 0.0),
                item.get("verified_count", 0),
                item.get("success_count", 0),
                -item.get("failure_count", 0),
            ),
            reverse=True,
        )
        return candidates[:max(1, int(limit))]

    def best_solution(
        self,
        *,
        task: str,
        error_type: str = "",
        root_cause: str = "",
        error_message: str = "",
    ) -> dict[str, Any] | None:
        """Backward-compatible single-solution API."""
        candidates = self.best_solutions(
            task=task,
            error_type=error_type,
            root_cause=root_cause,
            error_message=error_message,
            limit=1,
        )
        return candidates[0] if candidates else None

    # ---------------------------------------------------------
    # STATS
    # ---------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        experiences = self.data.get(
            "experiences",
            [],
        )

        trusted = sum(
            1
            for item in experiences
            if item.get("trusted")
        )

        successes = sum(
            1
            for item in experiences
            if item.get("success")
        )

        failures = sum(
            1
            for item in experiences
            if not item.get("success")
        )

        return {
            "version": self.VERSION,
            "experiences": len(experiences),
            "patterns": len(
                self.data.get("patterns", [])
            ),
            "successes": successes,
            "failures": failures,
            "trusted_solutions": trusted,
        }
