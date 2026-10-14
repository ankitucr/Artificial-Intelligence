from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path


class BackupManager:

    def __init__(
        self,
        workspace_root: str | Path,
        backup_root: str | Path | None = None,
    ):
        self.root = Path(
            workspace_root
        ).expanduser().resolve()

        self.backup_root = (
            Path(backup_root).expanduser().resolve()
            if backup_root
            else self.root / "backups" / "phase13"
        )

    def _safe_path(
        self,
        relative_path: str | Path,
    ) -> Path:

        path = (
            self.root / relative_path
        ).resolve()

        try:
            path.relative_to(self.root)
        except ValueError:
            raise ValueError(
                "Path escapes workspace."
            )

        return path

    def backup_file(
        self,
        relative_path: str,
    ) -> dict:

        source = self._safe_path(
            relative_path
        )

        if not source.is_file():
            return {
                "success": False,
                "error": (
                    f"File not found: "
                    f"{relative_path}"
                ),
            }

        timestamp = datetime.now(
            timezone.utc
        ).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )

        destination = (
            self.backup_root
            / timestamp
            / relative_path
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source,
            destination,
        )

        return {
            "success": True,
            "source": relative_path,
            "backup": str(
                destination.relative_to(
                    self.root
                )
            ),
            "timestamp": timestamp,
        }

    def restore_backup(
        self,
        backup_relative_path: str,
        target_relative_path: str,
    ) -> dict:

        backup = self._safe_path(
            backup_relative_path
        )

        target = self._safe_path(
            target_relative_path
        )

        if not backup.is_file():
            return {
                "success": False,
                "error": (
                    f"Backup not found: "
                    f"{backup_relative_path}"
                ),
            }

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            backup,
            target,
        )

        return {
            "success": True,
            "restored": target_relative_path,
            "backup": backup_relative_path,
        }
