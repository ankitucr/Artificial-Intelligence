from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any


class WorkspaceManager:
    """
    Controlled filesystem and command execution environment for PIKA.

    All filesystem operations are restricted to the PIKA workspace.
    Commands are executed without shell=True.
    """

    def __init__(
        self,
        root: str | Path = "~/pika/workspace",
        command_timeout: int = 30,
        max_file_size: int = 2_000_000,
    ):
        self.root = Path(root).expanduser().resolve()
        self.command_timeout = command_timeout
        self.max_file_size = max_file_size

        self.root.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # PATH SAFETY
    # ---------------------------------------------------------

    def resolve_path(self, relative_path: str) -> Path:
        if not relative_path:
            raise ValueError("Workspace path cannot be empty.")

        candidate = (self.root / relative_path).resolve()

        try:
            candidate.relative_to(self.root)
        except ValueError:
            raise PermissionError(
                f"Path escapes workspace: {relative_path}"
            )

        return candidate

    # ---------------------------------------------------------
    # LIST
    # ---------------------------------------------------------

    def list_files(self, relative_path: str = ".") -> dict[str, Any]:
        directory = self.resolve_path(relative_path)

        if not directory.exists():
            return {
                "success": False,
                "error": f"Path does not exist: {relative_path}",
            }

        if not directory.is_dir():
            return {
                "success": False,
                "error": f"Not a directory: {relative_path}",
            }

        entries = []

        for item in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
            entries.append(
                {
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "path": str(item.relative_to(self.root)),
                    "size": item.stat().st_size if item.is_file() else None,
                }
            )

        return {
            "success": True,
            "path": str(directory.relative_to(self.root)),
            "entries": entries,
        }

    # ---------------------------------------------------------
    # READ
    # ---------------------------------------------------------

    def read_file(self, relative_path: str) -> dict[str, Any]:
        path = self.resolve_path(relative_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"File does not exist: {relative_path}",
            }

        if not path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {relative_path}",
            }

        size = path.stat().st_size

        if size > self.max_file_size:
            return {
                "success": False,
                "error": "File exceeds workspace read size limit.",
            }

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return {
                "success": False,
                "error": "File is not valid UTF-8 text.",
            }

        return {
            "success": True,
            "path": str(path.relative_to(self.root)),
            "content": content,
            "size": size,
        }

    # ---------------------------------------------------------
    # WRITE
    # ---------------------------------------------------------

    def write_file(
        self,
        relative_path: str,
        content: str,
    ) -> dict[str, Any]:
        if not isinstance(content, str):
            raise TypeError("File content must be a string.")

        if len(content.encode("utf-8")) > self.max_file_size:
            return {
                "success": False,
                "error": "File exceeds workspace write size limit.",
            }

        path = self.resolve_path(relative_path)

        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(content, encoding="utf-8")

        return {
            "success": True,
            "path": str(path.relative_to(self.root)),
            "size": path.stat().st_size,
        }

    # ---------------------------------------------------------
    # REPLACE
    # ---------------------------------------------------------

    def replace_in_file(
        self,
        relative_path: str,
        old: str,
        new: str,
        replace_all: bool = False,
    ) -> dict[str, Any]:
        current = self.read_file(relative_path)

        if not current.get("success"):
            return current

        content = current["content"]

        if old not in content:
            return {
                "success": False,
                "error": "Target text was not found in file.",
            }

        if replace_all:
            updated = content.replace(old, new)
        else:
            updated = content.replace(old, new, 1)

        return self.write_file(relative_path, updated)

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------

    def delete_file(self, relative_path: str) -> dict[str, Any]:
        path = self.resolve_path(relative_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"File does not exist: {relative_path}",
            }

        if not path.is_file():
            return {
                "success": False,
                "error": "Only files can be deleted by this operation.",
            }

        path.unlink()

        return {
            "success": True,
            "path": relative_path,
        }

    # ---------------------------------------------------------
    # COMMAND EXECUTION
    # ---------------------------------------------------------

    def run_command(
        self,
        command: list[str],
        timeout: int | None = None,
    ) -> dict[str, Any]:
        if not isinstance(command, list) or not command:
            return {
                "success": False,
                "error": "Command must be a non-empty argument list.",
            }

        if any(not isinstance(arg, str) for arg in command):
            return {
                "success": False,
                "error": "All command arguments must be strings.",
            }

        allowed_commands = {
            "python",
            "python3",
            "pytest",
        }

        executable = os.path.basename(command[0])

        if executable not in allowed_commands:
            return {
                "success": False,
                "error": f"Command '{executable}' is not allowed.",
                "allowed_commands": sorted(allowed_commands),
            }

        # Never allow shell execution through command arguments.
        forbidden_arguments = {
            "-c",
            "--command",
            "sh",
            "bash",
            "zsh",
        }

        if any(arg in forbidden_arguments for arg in command[1:]):
            return {
                "success": False,
                "error": "Unsafe command argument is not allowed.",
            }

        # Python module execution is restricted to py_compile.
        if executable in {"python", "python3"}:
            if "-m" in command:
                try:
                    module_index = command.index("-m")
                    module_name = command[module_index + 1]
                except (ValueError, IndexError):
                    return {
                        "success": False,
                        "error": "Invalid Python module command.",
                    }

                if module_name != "py_compile":
                    return {
                        "success": False,
                        "error": (
                            "Only 'python -m py_compile' is allowed "
                            "through the workspace runtime."
                        ),
                    }

        # Reject absolute paths and traversal attempts in command arguments.
        for arg in command[1:]:
            if not isinstance(arg, str):
                continue

            candidate = Path(arg)

            if candidate.is_absolute():
                return {
                    "success": False,
                    "error": f"Absolute path is not allowed: {arg}",
                }

            if ".." in candidate.parts:
                return {
                    "success": False,
                    "error": f"Path traversal is not allowed: {arg}",
                }

        timeout = timeout or self.command_timeout

        try:
            process = subprocess.run(
                command,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )

            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "command": command,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "timeout": False,
            }

        except subprocess.TimeoutExpired as exc:
            return {
                "success": False,
                "returncode": None,
                "command": command,
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
                "timeout": True,
                "error": f"Command timed out after {timeout} seconds.",
            }

        except Exception as exc:
            return {
                "success": False,
                "returncode": None,
                "command": command,
                "stdout": "",
                "stderr": "",
                "timeout": False,
                "error": str(exc),
            }

    # ---------------------------------------------------------
    # PYTHON
    # ---------------------------------------------------------

    def run_python(
        self,
        relative_path: str,
        args: list[str] | None = None,
    ) -> dict[str, Any]:
        path = self.resolve_path(relative_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"Python file does not exist: {relative_path}",
            }

        if not path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {relative_path}",
            }

        command = [
            "python",
            str(path.relative_to(self.root)),
        ]

        if args:
            command.extend(args)

        return self.run_command(command)

    # ---------------------------------------------------------
    # PYTHON COMPILE CHECK
    # ---------------------------------------------------------

    def check_python(self, relative_path: str) -> dict[str, Any]:
        path = self.resolve_path(relative_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"Python file does not exist: {relative_path}",
            }

        command = [
            "python",
            "-m",
            "py_compile",
            str(path.relative_to(self.root)),
        ]

        return self.run_command(command)
