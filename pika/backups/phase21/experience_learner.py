from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class ExperienceLearner:
    """
    Phase 20:
    Converts execution/review results into reusable structured experience.

    This module does not modify code.
    It records what worked, what failed, and why.
    """

    def __init__(
        self,
        storage_path: str | Path,
    ):
        self.path = Path(storage_path).expanduser().resolve()
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.data = self._load()

    # --------------------------------------------------
    # Storage
    # --------------------------------------------------

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "version": 1,
                "experiences": [],
            }

        try:
            data = json.loads(
                self.path.read_text()
            )

            if not isinstance(data, dict):
                raise ValueError()

            data.setdefault(
                "version",
                1,
            )

            data.setdefault(
                "experiences",
                [],
            )

            return data

        except Exception:
            return {
                "version": 1,
                "experiences": [],
            }

    def _save(self) -> None:
        temp = self.path.with_suffix(
            ".tmp"
        )

        temp.write_text(
            json.dumps(
                self.data,
                indent=2,
                ensure_ascii=False,
            )
        )

        temp.replace(self.path)

    # --------------------------------------------------
    # Learn
    # --------------------------------------------------

    def learn(
        self,
        task: str,
        candidates: list[dict[str, Any]],
        final_result: dict[str, Any],
    ) -> dict[str, Any]:

        successful = []
        failed = []

        for candidate in candidates:

            item = {
                "candidate": candidate.get(
                    "candidate",
                    "",
                ),
                "rank": candidate.get(
                    "rank",
                ),
                "quality_score": candidate.get(
                    "quality_score",
                    0.0,
                ),
                "critic_passed": candidate.get(
                    "passed_critic",
                    False,
                ),
            }

            if candidate.get(
                "success",
                False,
            ):
                successful.append(item)
            else:
                failed.append(item)

        success = bool(
            final_result.get(
                "success",
                False,
            )
        )

        lesson = self._build_lesson(
            successful,
            failed,
            success,
        )

        experience = {
            "timestamp": time.time(),
            "task": task,
            "success": success,
            "successful_candidates": successful,
            "failed_candidates": failed,
            "lesson": lesson,
        }

        self.data["experiences"].append(
            experience
        )

        self._save()

        return experience

    # --------------------------------------------------
    # Lesson extraction
    # --------------------------------------------------

    @staticmethod
    def _build_lesson(
        successful: list[dict[str, Any]],
        failed: list[dict[str, Any]],
        success: bool,
    ) -> dict[str, Any]:

        if not success:
            return {
                "type": "failure",
                "rule": (
                    "Do not repeat an unsuccessful "
                    "candidate without new evidence."
                ),
                "confidence": 0.5,
            }

        if successful:
            best = max(
                successful,
                key=lambda item: (
                    item.get(
                        "quality_score",
                        0.0,
                    )
                ),
            )

            return {
                "type": "success",
                "rule": (
                    "Prefer candidates that pass "
                    "independent Critic review and "
                    "real execution."
                ),
                "best_rank": best.get(
                    "rank"
                ),
                "confidence": 1.0,
            }

        return {
            "type": "success",
            "rule": (
                "Successful execution is stronger "
                "evidence than ranking alone."
            ),
            "confidence": 0.8,
        }

    # --------------------------------------------------
    # Future ranking signal
    # --------------------------------------------------

    def get_ranking_signal(
        self,
        task: str,
    ) -> dict[str, Any]:

        experiences = self.data.get(
            "experiences",
            [],
        )

        if not experiences:
            return {
                "known": False,
                "success_count": 0,
                "failure_count": 0,
                "confidence": 0.0,
            }

        successful = sum(
            1
            for item in experiences
            if item.get("success") is True
        )

        failed = sum(
            1
            for item in experiences
            if item.get("success") is False
        )

        relevant = [
            item
            for item in experiences
            if self._similar_task(
                task,
                item.get("task", ""),
            )
        ]

        return {
            "known": bool(relevant),
            "success_count": successful,
            "failure_count": failed,
            "relevant_experiences": len(
                relevant
            ),
            "confidence": (
                min(
                    1.0,
                    len(relevant) / 3.0,
                )
                if relevant
                else 0.0
            ),
        }

    @staticmethod
    def _similar_task(
        left: str,
        right: str,
    ) -> bool:

        left_words = {
            word.lower()
            for word in left.split()
            if len(word) > 2
        }

        right_words = {
            word.lower()
            for word in right.split()
            if len(word) > 2
        }

        if not left_words or not right_words:
            return False

        overlap = left_words & right_words

        return (
            len(overlap)
            / max(
                1,
                len(left_words),
            )
            >= 0.3
        )

    # --------------------------------------------------
    # Stats
    # --------------------------------------------------

    def stats(self) -> dict[str, Any]:
        experiences = self.data.get(
            "experiences",
            [],
        )

        return {
            "experiences": len(
                experiences
            ),
            "successes": sum(
                1
                for item in experiences
                if item.get("success") is True
            ),
            "failures": sum(
                1
                for item in experiences
                if item.get("success") is False
            ),
        }
