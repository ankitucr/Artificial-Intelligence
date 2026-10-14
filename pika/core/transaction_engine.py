from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .snapshot_manager import SnapshotManager


class TransactionEngine:
    """
    Coordinates transactional workspace changes.

    Lifecycle:

        begin
          ↓
        active
          ↓
        commit OR rollback

    Only active transactions can be committed or rolled back.
    """

    def __init__(
        self,
        workspace_root: str | Path,
    ):
        self.workspace_root = Path(
            workspace_root
        ).resolve()

        self.snapshots = SnapshotManager(
            workspace_root=self.workspace_root,
        )

    @staticmethod
    def generate_id() -> str:
        timestamp = time.strftime(
            "%Y%m%d-%H%M%S"
        )

        millis = int(
            (time.time() % 1) * 1000
        )

        return (
            f"TX-{timestamp}-"
            f"{millis:03d}"
        )

    def begin(
        self,
        paths: list[str],
        transaction_id: str | None = None,
    ) -> dict[str, Any]:

        transaction_id = (
            transaction_id
            or self.generate_id()
        )

        result = self.snapshots.begin(
            transaction_id=transaction_id,
            paths=paths,
        )

        return result

    def commit(
        self,
        transaction_id: str,
    ) -> dict[str, Any]:

        return self.snapshots.commit(
            transaction_id
        )

    def rollback(
        self,
        transaction_id: str,
    ) -> dict[str, Any]:

        return self.snapshots.restore(
            transaction_id
        )

    def inspect(
        self,
        transaction_id: str,
    ) -> dict[str, Any]:

        return self.snapshots.inspect(
            transaction_id
        )
