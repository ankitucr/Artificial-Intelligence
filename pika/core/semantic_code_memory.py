"""PIKA Phase 35: Persistent Semantic Code Memory.

Stores code intent, implementations, preconditions, test cases and
verification evidence. Retrieval is lexical/metadata-based, not an LLM
semantic guarantee. Matching test outputs do not prove universal equivalence.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any


DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "semantic_code_memory.json"


def _tokens(value: str) -> set[str]:
    value = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(value))
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[0-9]+", value)
        if len(token) > 1
    }


def _digest(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


class SemanticCodeMemory:
    """Persistent memory for reusable code behavior and implementations."""

    SCHEMA_VERSION = 1

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else DEFAULT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _empty(self) -> dict[str, Any]:
        return {
            "schema_version": self.SCHEMA_VERSION,
            "experiences": [],
            "variants": [],
        }

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Memory root must be an object")
            data.setdefault("schema_version", self.SCHEMA_VERSION)
            data.setdefault("experiences", [])
            data.setdefault("variants", [])
            return data
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(
                f"Cannot safely load semantic memory at {self.path}: {exc}"
            ) from exc

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temp.replace(self.path)

    def remember(
        self,
        *,
        intent: str,
        code: str,
        language: str = "python",
        description: str = "",
        tags: list[str] | None = None,
        preconditions: list[str] | None = None,
        test_cases: list[dict[str, Any]] | None = None,
        verification: str = "unverified",
        evidence: list[str] | None = None,
        equivalent_group: str | None = None,
        replay_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Save one implementation. Verification must be supported by evidence.

        verification values:
          unverified, test_verified, formally_verified, failed
        """
        allowed = {
            "unverified", "test_verified", "formally_verified", "failed"
        }
        if verification not in allowed:
            raise ValueError(f"verification must be one of {sorted(allowed)}")
        if not intent.strip() or not code.strip():
            raise ValueError("intent and code cannot be empty")

        fingerprint = _digest(code)
        existing = next(
            (v for v in self.data["variants"] if v["code_hash"] == fingerprint),
            None,
        )
        if existing:
            # Never silently promote a failed or unverified variant.
            existing["last_seen"] = time.time()
            existing["intent"] = intent
            existing["description"] = description
            if replay_context:
                existing["replay_context"] = dict(replay_context)
            existing["tags"] = sorted(set(existing.get("tags", [])) | set(tags or []))
            existing["preconditions"] = list(preconditions or existing.get("preconditions", []))
            existing["test_cases"] = list(test_cases or existing.get("test_cases", []))
            existing["evidence"] = list(dict.fromkeys(
                existing.get("evidence", []) + (evidence or [])
            ))
            if verification == "failed":
                existing["verification"] = "failed"
            elif verification == "formally_verified" and evidence:
                existing["verification"] = "formally_verified"
            elif verification == "test_verified" and evidence:
                if existing["verification"] != "failed":
                    existing["verification"] = "test_verified"
            self._save()
            return dict(existing)

        record = {
            "id": fingerprint[:16],
            "code_hash": fingerprint,
            "intent": intent.strip(),
            "description": description.strip(),
            "language": language.strip().lower(),
            "code": code,
            "tags": sorted(set(tags or [])),
            "preconditions": list(preconditions or []),
            "test_cases": list(test_cases or []),
            "verification": verification,
            "evidence": list(evidence or []),
            "equivalent_group": equivalent_group,
            "replay_context": dict(replay_context or {}),
            "created_at": time.time(),
            "last_seen": time.time(),
            "uses": 0,
        }
        self.data["variants"].append(record)
        self._save()
        return dict(record)

    def record_test_result(
        self,
        variant_id: str,
        *,
        passed: bool,
        evidence: str,
    ) -> dict[str, Any]:
        """Record test evidence; a failed run demotes the implementation."""
        variant = self._find_variant(variant_id)
        variant.setdefault("evidence", []).append(str(evidence))
        variant["verification"] = "test_verified" if passed else "failed"
        variant["last_test_at"] = time.time()
        self._save()
        return dict(variant)

    def _find_variant(self, variant_id: str) -> dict[str, Any]:
        for variant in self.data["variants"]:
            if variant["id"] == variant_id or variant["code_hash"] == variant_id:
                return variant
        raise KeyError(f"Unknown code variant: {variant_id}")

    def retrieve(
        self,
        query: str,
        *,
        language: str | None = None,
        tags: list[str] | None = None,
        verified_only: bool = True,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Rank possible matches using intent, description, tags and code tokens.

        This is a candidate finder, not proof that two programs are equivalent.
        """
        query_tokens = _tokens(query)
        requested_tags = {t.lower() for t in (tags or [])}
        ranked = []

        for variant in self.data["variants"]:
            if verified_only and variant["verification"] not in {
                "test_verified", "formally_verified"
            }:
                continue
            if language and variant["language"] != language.lower():
                continue

            searchable = " ".join([
                variant["intent"],
                variant["description"],
                " ".join(variant["tags"]),
                variant["code"],
                " ".join(variant["preconditions"]),
            ])
            candidate_tokens = _tokens(searchable)
            overlap = len(query_tokens & candidate_tokens)
            if query_tokens and overlap == 0 and not (
                requested_tags & set(variant["tags"])
            ):
                continue

            score = overlap / max(1, len(query_tokens))
            tag_matches = len(requested_tags & set(variant["tags"]))
            score += 0.5 * tag_matches
            if variant["verification"] == "formally_verified":
                score += 0.1
            elif variant["verification"] == "test_verified":
                score += 0.05

            ranked.append((score, variant))

        ranked.sort(
            key=lambda item: (item[0], item[1].get("uses", 0)),
            reverse=True,
        )
        results = []
        for score, variant in ranked[:max(0, limit)]:
            item = dict(variant)
            item["relevance_score"] = round(score, 4)
            results.append(item)
        return results

    def mark_used(self, variant_id: str) -> dict[str, Any]:
        variant = self._find_variant(variant_id)
        variant["uses"] = int(variant.get("uses", 0)) + 1
        variant["last_seen"] = time.time()
        self._save()
        return dict(variant)

    def variants_in_group(self, equivalent_group: str) -> list[dict[str, Any]]:
        """Return variants explicitly grouped by the caller after comparison."""
        return [
            dict(v) for v in self.data["variants"]
            if v.get("equivalent_group") == equivalent_group
        ]

    def stats(self) -> dict[str, int]:
        variants = self.data["variants"]
        return {
            "total_variants": len(variants),
            "test_verified": sum(v["verification"] == "test_verified" for v in variants),
            "formally_verified": sum(v["verification"] == "formally_verified" for v in variants),
            "unverified": sum(v["verification"] == "unverified" for v in variants),
            "failed": sum(v["verification"] == "failed" for v in variants),
        }
