from __future__ import annotations

from workspace.manager import WorkspaceManager


_workspace = WorkspaceManager()


def _safe_call(function, *args, **kwargs):
    try:
        return function(*args, **kwargs)
    except PermissionError as exc:
        return {
            "success": False,
            "error": str(exc),
            "error_type": "permission",
        }
    except ValueError as exc:
        return {
            "success": False,
            "error": str(exc),
            "error_type": "validation",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "error_type": "workspace",
        }


def workspace_list(path: str = "."):
    return _safe_call(
        _workspace.list_files,
        path,
    )


def workspace_read(path: str):
    return _safe_call(
        _workspace.read_file,
        path,
    )


def workspace_write(path: str, content: str):
    return _safe_call(
        _workspace.write_file,
        path,
        content,
    )


def workspace_replace(
    path: str,
    old: str,
    new: str,
    replace_all: bool = False,
):
    return _safe_call(
        _workspace.replace_in_file,
        path,
        old,
        new,
        replace_all,
    )


def workspace_delete(path: str):
    return _safe_call(
        _workspace.delete_file,
        path,
    )


def workspace_run(command: list[str]):
    return _safe_call(
        _workspace.run_command,
        command,
    )


def workspace_run_python(
    path: str,
    args: list[str] | None = None,
):
    return _safe_call(
        _workspace.run_python,
        path,
        args,
    )


def workspace_check_python(path: str):
    return _safe_call(
        _workspace.check_python,
        path,
    )
