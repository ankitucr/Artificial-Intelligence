from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Any


class SnapshotManager:
    """
    Creates and restores transactional snapshots of files inside
    the controlled PIKA workspace.

    A snapshot is immutable from the transaction manager's point
    of view and contains:
      - transaction id
      - original file state
      - file metadata
      - backup copies
      - manifest
    """

    def __init__(
        self,
        workspace_root: str | Path,
        transaction_root: str | Path | None = None,
    ):
        self.workspace_root = Path(workspace_root).resolve()

        if transaction_root is None:
            transaction_root = (
                self.workspace_root / ".pika" / "transactions"
            )

        self.transaction_root = Path(
            transaction_root
        ).resolve()

        self.transaction_root.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _resolve_workspace_path(
        self,
        relative_path: str,
    ) -> Path:

        candidate = (
            self.workspace_root / relative_path
        ).resolve()

        try:
            candidate.relative_to(
                self.workspace_root
            )
        except ValueError as exc:
            raise ValueError(
                f"Path escapes workspace: {relative_path}"
            ) from exc

        return candidate

    def _transaction_dir(
        self,
        transaction_id: str,
    ) -> Path:

        if not transaction_id:
            raise ValueError(
                "Transaction id cannot be empty."
            )

        path = (
            self.transaction_root /
            transaction_id
        ).resolve()

        try:
            path.relative_to(
                self.transaction_root
            )
        except ValueError as exc:
            raise ValueError(
                "Invalid transaction id."
            ) from exc

        return path

    @staticmethod
    def _sha256(path: Path) -> str:

        digest = hashlib.sha256()

        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)

                if not chunk:
                    break

                digest.update(chunk)

        return digest.hexdigest()

    def begin(
        self,
        transaction_id: str,
        paths: list[str],
    ) -> dict[str, Any]:

        if not paths:
            return {
                "success": False,
                "error": "No paths supplied for snapshot.",
            }

        transaction_dir = self._transaction_dir(
            transaction_id
        )

        if transaction_dir.exists():
            return {
                "success": False,
                "error": (
                    f"Transaction already exists: "
                    f"{transaction_id}"
                ),
            }

        backup_dir = transaction_dir / "backup"

        backup_dir.mkdir(
            parents=True,
            exist_ok=False,
        )

        files: list[dict[str, Any]] = []

        try:
            for relative_path in paths:

                source = self._resolve_workspace_path(
                    relative_path
                )

                record: dict[str, Any] = {
                    "path": relative_path,
                    "existed": source.exists(),
                    "is_file": source.is_file(),
                }

                if source.exists():

                    if not source.is_file():
                        raise ValueError(
                            f"Snapshot only supports files: "
                            f"{relative_path}"
                        )

                    backup_path = (
                        backup_dir / relative_path
                    )

                    backup_path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    shutil.copy2(
                        source,
                        backup_path,
                    )

                    record["size"] = source.stat().st_size
                    record["sha256"] = self._sha256(
                        source
                    )

                files.append(record)

            manifest = {
                "transaction_id": transaction_id,
                "created_at": time.time(),
                "workspace_root": str(
                    self.workspace_root
                ),
                "status": "active",
                "files": files,
            }

            manifest_path = (
                transaction_dir / "manifest.json"
            )

            manifest_path.write_text(
                json.dumps(
                    manifest,
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            return {
                "success": True,
                "transaction_id": transaction_id,
                "status": "active",
                "files": files,
                "manifest": str(manifest_path),
            }

        except Exception as exc:

            shutil.rmtree(
                transaction_dir,
                ignore_errors=True,
            )

            return {
                "success": False,
                "transaction_id": transaction_id,
                "error": str(exc),
            }

    def load(
        self,
        transaction_id: str,
    ) -> dict[str, Any]:

        transaction_dir = self._transaction_dir(
            transaction_id
        )

        manifest_path = (
            transaction_dir / "manifest.json"
        )

        if not manifest_path.exists():
            return {
                "success": False,
                "error": (
                    f"Transaction not found: "
                    f"{transaction_id}"
                ),
            }

        try:
            manifest = json.loads(
                manifest_path.read_text(
                    encoding="utf-8"
                )
            )

            return {
                "success": True,
                "manifest": manifest,
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
            }

    def restore(
        self,
        transaction_id: str,
    ) -> dict[str, Any]:

        loaded = self.load(transaction_id)

        if not loaded["success"]:
            return loaded

        manifest = loaded["manifest"]

        if manifest.get("status") == "committed":
            return {
                "success": False,
                "error": (
                    "Committed transaction cannot be "
                    "rolled back."
                ),
            }

        transaction_dir = self._transaction_dir(
            transaction_id
        )

        backup_dir = transaction_dir / "backup"

        restored: list[str] = []

        try:

            for record in manifest.get(
                "files",
                [],
            ):

                relative_path = record["path"]

                target = self._resolve_workspace_path(
                    relative_path
                )

                existed = bool(
                    record.get("existed")
                )

                if existed:

                    backup = (
                        backup_dir /
                        relative_path
                    )

                    if not backup.exists():
                        raise FileNotFoundError(
                            "Missing backup for "
                            f"{relative_path}"
                        )

                    target.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    shutil.copy2(
                        backup,
                        target,
                    )

                else:

                    if target.exists():

                        if target.is_file():
                            target.unlink()

                        else:
                            raise ValueError(
                                "Rollback expected a file "
                                f"but found directory: "
                                f"{relative_path}"
                            )

                restored.append(
                    relative_path
                )

            manifest["status"] = "rolled_back"
            manifest["rolled_back_at"] = time.time()

            (
                transaction_dir /
                "manifest.json"
            ).write_text(
                json.dumps(
                    manifest,
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            return {
                "success": True,
                "transaction_id": transaction_id,
                "status": "rolled_back",
                "restored": restored,
            }

        except Exception as exc:

            return {
                "success": False,
                "transaction_id": transaction_id,
                "error": str(exc),
                "restored": restored,
            }

    def commit(
        self,
        transaction_id: str,
    ) -> dict[str, Any]:

        loaded = self.load(transaction_id)

        if not loaded["success"]:
            return loaded

        manifest = loaded["manifest"]

        status = manifest.get("status")

        if status != "active":
            return {
                "success": False,
                "error": (
                    f"Transaction is not active: "
                    f"{status}"
                ),
            }

        transaction_dir = self._transaction_dir(
            transaction_id
        )

        manifest["status"] = "committed"
        manifest["committed_at"] = time.time()

        (
            transaction_dir /
            "manifest.json"
        ).write_text(
            json.dumps(
                manifest,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        return {
            "success": True,
            "transaction_id": transaction_id,
            "status": "committed",
        }

    def inspect(
        self,
        transaction_id: str,
    ) -> dict[str, Any]:

        return self.load(transaction_id)
