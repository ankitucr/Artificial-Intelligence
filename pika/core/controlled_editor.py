from __future__ import annotations

from pathlib import Path

from core.backup_manager import BackupManager


class ControlledEditor:

    def __init__(
        self,
        workspace_root: str | Path,
    ):
        self.root = Path(
            workspace_root
        ).expanduser().resolve()

        self.backups = BackupManager(
            self.root
        )

    def _safe_path(
        self,
        relative_path: str,
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

    def replace_text(
        self,
        relative_path: str,
        old: str,
        new: str,
    ) -> dict:

        if not old:
            return {
                "success": False,
                "error": (
                    "Old text cannot be empty."
                ),
            }

        path = self._safe_path(
            relative_path
        )

        if not path.is_file():
            return {
                "success": False,
                "error": (
                    f"File not found: "
                    f"{relative_path}"
                ),
            }

        content = path.read_text(
            encoding="utf-8"
        )

        occurrences = content.count(old)

        if occurrences == 0:
            return {
                "success": False,
                "error": (
                    "Target text was not found."
                ),
                "occurrences": 0,
            }

        if occurrences > 1:
            return {
                "success": False,
                "error": (
                    "Target text occurs more than "
                    "once; refusing ambiguous edit."
                ),
                "occurrences": occurrences,
            }

        backup = self.backups.backup_file(
            relative_path
        )

        if not backup["success"]:
            return {
                "success": False,
                "error": (
                    "Backup failed. "
                    "Edit was not performed."
                ),
            }

        updated = content.replace(
            old,
            new,
            1,
        )

        path.write_text(
            updated,
            encoding="utf-8",
        )

        return {
            "success": True,
            "path": relative_path,
            "backup": backup["backup"],
            "occurrences": 1,
            "changed": content != updated,
        }

    def rollback(
        self,
        backup_relative_path: str,
        target_relative_path: str,
    ) -> dict:

        return self.backups.restore_backup(
            backup_relative_path,
            target_relative_path,
        )
