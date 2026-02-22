"""Folder hierarchy builder for input files.

Constructs a tree representation of input files organized by their source paths,
with support for size accumulation and optional path compaction.
"""

from __future__ import annotations

from typing import List, Optional

from ._models import FolderNode, InputFile, LinkInfoData
from ._path_utils import get_filename, get_parent_path, split_path


class FolderHierarchy:
    """Builder and manager for input-file folder hierarchy.

    Constructs a tree structure from input-file paths, supporting:
    - Hierarchical grouping by folder structure
    - Size accumulation at folder and component levels
    - Optional path compaction (collapsing single-child folder chains)
    """

    def __init__(self) -> None:
        """Initialize an empty folder hierarchy."""
        self.root: Optional[FolderNode] = None

    @staticmethod
    def from_linkinfo_data(data: LinkInfoData, compact: bool = False) -> FolderNode:
        """Build folder hierarchy from LinkInfoData input files.

        Args:
            data: LinkInfoData object containing all input files.
            compact: If True, collapse single-child folder chains.

        Returns:
            Root FolderNode representing the folder hierarchy.
            Returns a root with name "root" and path "/" if data is empty.
        """
        builder = FolderHierarchy()

        # Build tree from all input files
        for input_file in data.input_files.values():
            if input_file.path:
                builder.add_input_file(input_file)

        root = builder.root or FolderNode(name="root", path="/")

        if compact:
            root = _compact_folder_tree(root)

        return root

    def add_input_file(self, input_file: InputFile) -> None:
        """Add an input file to the hierarchy based on its path.

        Args:
            input_file: InputFile to add to the hierarchy.
        """
        if not input_file.path:
            # No path info - add to root
            if self.root is None:
                self.root = FolderNode(name="root", path="/")
            self.root.input_files[input_file.id] = input_file
            return

        # Ensure root exists
        if self.root is None:
            self.root = FolderNode(name="root", path="/")

        # Get the parent directory (exclude filename)
        parent_dir = get_parent_path(input_file.path)
        path_components = split_path(parent_dir)
        if not path_components:
            # File at root
            self.root.input_files[input_file.id] = input_file
            return

        # Navigate/create folder structure
        current = self.root
        accumulated_path = ""

        for component in path_components:
            accumulated_path = (
                f"{accumulated_path}/{component}" if accumulated_path else component
            )

            if component not in current.children:
                current.children[component] = FolderNode(
                    name=component, path=accumulated_path
                )

            current = current.children[component]

        # Add input file to the final folder
        current.input_files[input_file.id] = input_file

    def get_root(self) -> FolderNode:
        """Get the root folder node.

        Returns:
            Root FolderNode, or an empty root if no files were added.
        """
        if self.root is None:
            self.root = FolderNode(name="root", path="/")
        return self.root


def _compact_folder_tree(node: FolderNode) -> FolderNode:
    """Recursively compact a folder tree by collapsing single-child chains.

    When a folder has exactly one child folder and no input files,
    merge it with the child using the combined path.

    Args:
        node: FolderNode to compact.

    Returns:
        Compacted FolderNode (may have a modified structure).
    """
    # First, recursively compact all children
    for child_name, child_node in list(node.children.items()):
        compacted_child = _compact_folder_tree(child_node)
        node.children[child_name] = compacted_child

    # Now compact this node if it has exactly one child and no input files
    while len(node.children) == 1 and not node.input_files:
        only_child_name = next(iter(node.children.keys()))
        only_child = node.children[only_child_name]

        # Merge child into parent and keep compaction visible in the name
        node.name = f"{node.name}/{only_child.name}"
        node.path = only_child.path
        node.children = only_child.children
        node.input_files = only_child.input_files
        node._accumulated_size = None  # Invalidate cache

    return node


def flatten_folder_hierarchy(root: FolderNode) -> dict[str, FolderNode]:
    """Flatten a folder hierarchy into a dict mapping paths to nodes.

    Args:
        root: Root FolderNode.

    Returns:
        Dictionary with normalized paths as keys and FolderNode objects as values.
    """
    result: dict[str, FolderNode] = {}

    def traverse(node: FolderNode) -> None:
        result[node.path] = node
        for child in node.children.values():
            traverse(child)

    traverse(root)
    return result


def get_all_input_files_in_folder(node: FolderNode) -> dict[str, InputFile]:
    """Get all input files in a folder and its subfolders.

    Args:
        node: FolderNode to search.

    Returns:
        Dictionary mapping input file IDs to InputFile objects.
    """
    result: dict[str, InputFile] = dict(node.input_files)
    for child in node.children.values():
        result.update(get_all_input_files_in_folder(child))
    return result


def get_depth(node: FolderNode) -> int:
    """Get the maximum depth of the folder hierarchy.

    Args:
        node: FolderNode to measure.

    Returns:
        Maximum depth (root has depth 0, its children have depth 1, etc.).
    """
    if not node.children:
        return 0
    return 1 + max(get_depth(child) for child in node.children.values())
