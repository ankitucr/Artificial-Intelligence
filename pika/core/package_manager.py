from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from typing import Any


class PackageManager:
    """
    Controlled Python dependency manager.

    Security rules:
    - package name must pass strict validation
    - no shell execution
    - no arbitrary pip flags
    - installation is bounded by a timeout
    """

    PACKAGE_PATTERN = re.compile(
        r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"
    )

    def __init__(self, timeout: int = 120):
        self.timeout = timeout

    @classmethod
    def validate_package_name(
        cls,
        package: str,
    ) -> bool:
        if not isinstance(package, str):
            return False

        package = package.strip()

        if not package:
            return False

        return bool(
            cls.PACKAGE_PATTERN.fullmatch(package)
        )

    @staticmethod
    def normalize_package_name(
        package: str,
    ) -> str:
        return package.strip()

    def is_available(
        self,
        package: str,
    ) -> bool:
        package = self.normalize_package_name(package)

        if not self.validate_package_name(package):
            return False

        try:
            return (
                importlib.util.find_spec(package)
                is not None
            )
        except (ImportError, ModuleNotFoundError, ValueError):
            return False

    def install(
        self,
        package: str,
    ) -> dict[str, Any]:

        package = self.normalize_package_name(package)

        if not self.validate_package_name(package):
            return {
                "success": False,
                "action": "install_dependency",
                "package": package,
                "error": (
                    "Package name rejected by "
                    "controlled package policy."
                ),
            }

        if self.is_available(package):
            return {
                "success": True,
                "action": "install_dependency",
                "package": package,
                "already_available": True,
                "available_after": True,
            }

        command = [
            sys.executable,
            "-m",
            "pip",
            "install",
            package,
        ]

        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                shell=False,
            )

            available_after = self.is_available(package)

            return {
                "success": (
                    process.returncode == 0
                    and available_after
                ),
                "action": "install_dependency",
                "package": package,
                "command": command,
                "returncode": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "timeout": False,
                "available_after": available_after,
            }

        except subprocess.TimeoutExpired as exc:
            return {
                "success": False,
                "action": "install_dependency",
                "package": package,
                "command": command,
                "returncode": None,
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
                "timeout": True,
                "error": (
                    f"Package installation timed out "
                    f"after {self.timeout} seconds."
                ),
            }

        except Exception as exc:
            return {
                "success": False,
                "action": "install_dependency",
                "package": package,
                "command": command,
                "returncode": None,
                "stdout": "",
                "stderr": "",
                "timeout": False,
                "error": str(exc),
            }
