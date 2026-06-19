"""Filesystem tools for code agent."""

import os
from pathlib import Path
from typing import List, Optional


def get_working_dir() -> Path:
    """Get the sandboxed working directory."""
    work_dir = os.getenv("WORKING_DIR", "./workspace")
    path = Path(work_dir).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _validate_path(relative_path: str) -> Path:
    """Validate path is within working directory."""
    work_dir = get_working_dir()
    target = work_dir / relative_path
    target = target.resolve()

    # Ensure path is within working directory
    try:
        target.relative_to(work_dir)
    except ValueError:
        raise ValueError(f"Path {relative_path} is outside working directory")

    return target


async def read_file(relative_path: str) -> str:
    """
    Read contents of a file.

    Args:
        relative_path: Path relative to working directory

    Returns:
        File contents as string
    """
    target = _validate_path(relative_path)

    if not target.exists():
        raise FileNotFoundError(f"File not found: {relative_path}")

    if not target.is_file():
        raise ValueError(f"{relative_path} is not a file")

    return target.read_text(encoding="utf-8")


async def write_file(relative_path: str, content: str) -> dict:
    """
    Write content to a file.

    Args:
        relative_path: Path relative to working directory
        content: Content to write

    Returns:
        Dict with success info
    """
    target = _validate_path(relative_path)

    # Create parent directories if needed
    target.parent.mkdir(parents=True, exist_ok=True)

    target.write_text(content, encoding="utf-8")

    return {
        "success": True,
        "path": relative_path,
        "bytes_written": len(content.encode("utf-8")),
    }


async def list_files(relative_path: str = ".") -> List[dict]:
    """
    List files in a directory.

    Args:
        relative_path: Path relative to working directory

    Returns:
        List of file/directory info dicts
    """
    target = _validate_path(relative_path)

    if not target.exists():
        raise FileNotFoundError(f"Directory not found: {relative_path}")

    if not target.is_dir():
        raise ValueError(f"{relative_path} is not a directory")

    items = []
    for item in target.iterdir():
        stat = item.stat()
        items.append({
            "name": item.name,
            "path": str(item.relative_to(get_working_dir())),
            "type": "directory" if item.is_dir() else "file",
            "size": stat.st_size if item.is_file() else None,
        })

    return sorted(items, key=lambda x: (x["type"] != "directory", x["name"]))


async def execute_shell(command: str) -> dict:
    """
    Execute a shell command in the working directory.
    WARNING: This is sandboxed but still has filesystem access.

    Args:
        command: Shell command to execute

    Returns:
        Dict with stdout, stderr, and return code
    """
    import subprocess

    work_dir = get_working_dir()

    # Block dangerous commands
    dangerous = ["rm -rf /", "rm -rf /*", ":(){ :|:& };:", "> /dev/sda"]
    for d in dangerous:
        if d in command:
            raise ValueError(f"Dangerous command blocked: {d}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Command timed out after 30 seconds",
            "returncode": -1,
        }
