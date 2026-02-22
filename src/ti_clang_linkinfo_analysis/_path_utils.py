"""Utilities for path normalization and manipulation.

Handles POSIX/Windows separators, absolute/relative path handling,
and provides robust path operations for folder hierarchy construction.
"""

from __future__ import annotations

from pathlib import Path
from typing import List


def normalize_path(path: str | Path) -> str:
    """Normalize a path to use forward slashes and remove redundant separators.

    Args:
        path: Path string or Path object, can be absolute or relative,
              with either POSIX (/) or Windows (\\) separators.

    Returns:
        Normalized path using forward slashes (POSIX style).
        Maintains relative vs absolute status (absolute paths lose drive letters).
        Empty path becomes "." (current directory).

    Examples:
        >>> normalize_path("src\\path\\to\\file.obj")
        'src/path/to/file.obj'
        >>> normalize_path("src/path//to/file.obj")
        'src/path/to/file.obj'
        >>> normalize_path("/absolute/path/file.obj")
        '/absolute/path/file.obj'
    """
    if not path:
        return "."

    path_str = str(path)

    # First, replace all backslashes with forward slashes (handle Windows paths)
    posix_path = path_str.replace("\\", "/")

    # Remove redundant separators
    normalized = "/".join(part for part in posix_path.split("/") if part)

    # Preserve leading slash for absolute paths
    if path_str.startswith("/") or (len(path_str) > 1 and path_str[1] == ":"):
        # It's an absolute path
        if not normalized.startswith("/"):
            normalized = "/" + normalized
    elif not normalized:
        normalized = "."

    return normalized


def split_path(path: str | Path) -> List[str]:
    """Split a normalized path into components.

    Args:
        path: Path string or Path object (will be normalized first).

    Returns:
        List of path components. Empty list for empty path or ".".
        Absolute paths do not include an empty component for the root "/".

    Examples:
        >>> split_path("src/path/to/file.obj")
        ['src', 'path', 'to', 'file.obj']
        >>> split_path("/absolute/path/file.obj")
        ['absolute', 'path', 'file.obj']
        >>> split_path(".")
        []
    """
    normalized = normalize_path(path)

    if normalized == ".":
        return []

    # Remove leading slash for absolute paths before splitting
    if normalized.startswith("/"):
        normalized = normalized[1:]

    return [part for part in normalized.split("/") if part]


def get_parent_path(path: str | Path) -> str:
    """Get the parent directory of a given path.

    Args:
        path: Path string or Path object.

    Returns:
        Parent path normalized, or "." if no parent.

    Examples:
        >>> get_parent_path("src/path/to/file.obj")
        'src/path/to'
        >>> get_parent_path("file.obj")
        '.'
        >>> get_parent_path("/absolute/path/file.obj")
        '/absolute/path'
    """
    normalized = normalize_path(path)

    if normalized == ".":
        return "."

    parts = split_path(normalized)
    if not parts:
        return "."

    # Check if it was absolute
    was_absolute = str(path).startswith("/") or (
        len(str(path)) > 1 and str(path)[1] == ":"
    )

    parent_parts = parts[:-1]
    if not parent_parts:
        return "/" if was_absolute else "."

    result = "/".join(parent_parts)
    if was_absolute:
        result = "/" + result

    return result


def get_filename(path: str | Path) -> str:
    """Extract the filename (last component) from a path.

    Args:
        path: Path string or Path object.

    Returns:
        The last component of the path, or empty string if path is "." or "/".

    Examples:
        >>> get_filename("src/path/to/file.obj")
        'file.obj'
        >>> get_filename("/absolute/path/file.obj")
        'file.obj'
        >>> get_filename(".")
        ''
    """
    normalized = normalize_path(path)
    parts = split_path(normalized)
    return parts[-1] if parts else ""


def is_absolute_path(path: str | Path) -> bool:
    """Check if a path is absolute.

    Args:
        path: Path string or Path object.

    Returns:
        True if path is absolute, False if relative.
    """
    path_str = str(path)
    return path_str.startswith("/") or (len(path_str) > 1 and path_str[1] == ":")


def join_path_components(*components: str) -> str:
    """Join path components using forward slashes.

    Args:
        *components: Path components to join.

    Returns:
        Joined path normalized, or "." if no components.

    Examples:
        >>> join_path_components("src", "path", "file.obj")
        'src/path/file.obj'
        >>> join_path_components("")
        '.'
    """
    if not components or all(not c for c in components):
        return "."

    filtered = [normalize_path(c) for c in components if c]
    if not filtered:
        return "."

    # Check if first component is absolute
    first = filtered[0]
    is_abs = first.startswith("/")

    # Join all parts
    all_parts = []
    for component in filtered:
        component_parts = split_path(component)
        all_parts.extend(component_parts)

    result = "/".join(all_parts) if all_parts else "."
    if is_abs:
        result = "/" + result

    return result
