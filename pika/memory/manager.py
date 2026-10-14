import json
import re
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
MEMORY_FILE = DATA_DIR / "memory.json"


class MemoryManager:
    """
    Persistent PIKA memory.

    Stores:
    - episodes
    - skills
    - failures
    - knowledge
    - lessons

    Memory survives process restarts.
    """

    def __init__(
        self,
        storage_path: str | Path | None = None,
    ):
        self.storage_path = Path(
            storage_path or MEMORY_FILE
        )

        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.episodes: list[dict[str, Any]] = []
        self.skills: list[dict[str, Any]] = []
        self.failures: list[dict[str, Any]] = []
        self.knowledge: list[dict[str, Any]] = []
        self.lessons: list[dict[str, Any]] = []

        self._load()

    # =========================================================
    # Persistence
    # =========================================================

    def _load(self) -> None:

        if not self.storage_path.exists():
            self._save()
            return

        try:
            data = json.loads(
                self.storage_path.read_text(
                    encoding="utf-8"
                )
            )

            self.episodes = data.get(
                "episodes",
                [],
            )

            self.skills = data.get(
                "skills",
                [],
            )

            self.failures = data.get(
                "failures",
                [],
            )

            self.knowledge = data.get(
                "knowledge",
                [],
            )

            self.lessons = data.get(
                "lessons",
                [],
            )

        except (
            json.JSONDecodeError,
            OSError,
            TypeError,
        ):
            # Do not destroy potentially useful memory.
            # Start clean and overwrite only on next successful save.
            self.episodes = []
            self.skills = []
            self.failures = []
            self.knowledge = []
            self.lessons = []

    def _save(self) -> None:

        data = {
            "episodes": self.episodes,
            "skills": self.skills,
            "failures": self.failures,
            "knowledge": self.knowledge,
            "lessons": self.lessons,
        }

        temporary = self.storage_path.with_suffix(
            ".tmp"
        )

        temporary.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        temporary.replace(
            self.storage_path
        )

    # =========================================================
    # Store
    # =========================================================

    def remember_episode(
        self,
        episode: dict[str, Any],
    ) -> None:

        self.episodes.append(episode)

        self._save()

    def remember_skill(
        self,
        skill: dict[str, Any],
    ) -> None:

        self.skills.append(skill)

        self._save()

    def remember_failure(
        self,
        failure: dict[str, Any],
    ) -> None:

        self.failures.append(failure)

        self._save()

    def remember_knowledge(
        self,
        knowledge: dict[str, Any],
    ) -> None:

        self.knowledge.append(knowledge)

        self._save()

    def remember_lesson(
        self,
        lesson: dict[str, Any],
    ) -> None:

        self.lessons.append(lesson)

        self._save()

    # =========================================================
    # Retrieval
    # =========================================================

    def retrieve(
        self,
        query: str,
        limit: int = 10,
    ) -> dict[str, Any]:

        return {
            "query": query,
            "episodes": self._relevant(
                self.episodes,
                query,
                limit,
            ),
            "skills": self._relevant(
                self.skills,
                query,
                limit,
            ),
            "failures": self._relevant(
                self.failures,
                query,
                limit,
            ),
            "knowledge": self._relevant(
                self.knowledge,
                query,
                limit,
            ),
            "lessons": self._relevant(
                self.lessons,
                query,
                limit,
            ),
        }

    def _relevant(
        self,
        items: list[dict[str, Any]],
        query: str,
        limit: int,
    ) -> list[dict[str, Any]]:

        if not items:
            return []

        query_words = self._tokens(query)

        if not query_words:
            return items[-limit:]

        scored = []

        for index, item in enumerate(items):

            text = json.dumps(
                item,
                ensure_ascii=False,
            ).lower()

            item_words = self._tokens(text)

            overlap = len(
                query_words.intersection(
                    item_words
                )
            )

            # Recency tie-breaker.
            scored.append(
                (
                    overlap,
                    index,
                    item,
                )
            )

        scored.sort(
            key=lambda x: (x[0], x[1]),
            reverse=True,
        )

        return [
            item
            for _, _, item
            in scored[:limit]
        ]

    @staticmethod
    def _tokens(
        text: str,
    ) -> set[str]:

        return {
            token
            for token in re.findall(
                r"[a-zA-Z_][a-zA-Z0-9_]*",
                text.lower(),
            )
            if len(token) > 2
        }

    # =========================================================
    # Diagnostics
    # =========================================================

    def stats(self) -> dict[str, int]:

        return {
            "episodes": len(self.episodes),
            "failures": len(self.failures),
            "skills": len(self.skills),
            "knowledge": len(self.knowledge),
            "lessons": len(self.lessons),
        }
