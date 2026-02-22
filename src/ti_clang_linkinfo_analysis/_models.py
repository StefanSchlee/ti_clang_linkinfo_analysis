from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ._errors import LinkInfoIssue


@dataclass
class InputFile:
    """Represents an object file (.o) or archive (.a) in the linkinfo.

    Attributes:
        id: Unique identifier for this input file.
        name: Display name of the file (e.g., "main.o", "libdriver.a").
        path: Full source path to the input file.
        object_components: List of ObjectComponents contained in this file.
    """

    id: str
    name: Optional[str] = None
    path: Optional[str] = None
    object_components: List["ObjectComponent"] = field(default_factory=list)

    def add_component(self, component: "ObjectComponent") -> None:
        """Add an object component to this input file.

        Args:
            component: ObjectComponent to add.
        """
        self.object_components.append(component)

    def get_sorted_components(self) -> List["ObjectComponent"]:
        """Get components sorted by size in descending order.

        Returns:
            List of ObjectComponents sorted by size (largest first).
        """
        return sorted(self.object_components, key=lambda x: x.size or 0, reverse=True)

    def get_total_size(self) -> int:
        """Get total size by summing all object component sizes.

        Returns:
            Total size in bytes of all components in this input file.
        """
        return sum(comp.size or 0 for comp in self.object_components)


@dataclass
class ObjectComponent:
    """Represents a section within an input file.

    Object components are the finest granularity of code/data in the linkinfo,
    corresponding to sections like .text, .data, .rodata, etc.

    Attributes:
        id: Unique identifier for this component.
        name: Display name (section name).
        load_address: Address where section is loaded.
        run_address: Address where section executes.
        size: Size in bytes.
        alignment: Required alignment.
        readonly: True if section is read-only.
        executable: True if section contains executable code.
        value: Additional metadata value.
        input_file: Parent InputFile containing this component.
        refd_ro_sections: IDs of read-only sections this component references.
        refd_rw_sections: IDs of read-write sections this component references.
    """

    id: str
    name: Optional[str] = None
    load_address: Optional[int] = None
    run_address: Optional[int] = None
    size: Optional[int] = None
    alignment: Optional[int] = None
    readonly: Optional[bool] = None
    executable: Optional[bool] = None
    value: Optional[str] = None

    input_file: Optional[InputFile] = None

    refd_ro_sections: List[str] = field(default_factory=list)
    refd_rw_sections: List[str] = field(default_factory=list)


@dataclass
class LogicalGroup:
    """Represents a named grouping within a memory area.

    Logical groups organize object components and sub-groups within
    memory areas for hierarchical reporting.

    Attributes:
        id: Unique identifier.
        name: Display name of the group.
        size: Total size of this group.
        object_components: Components directly in this group.
        logical_groups: Nested sub-groups.
    """

    id: str
    name: Optional[str] = None
    size: Optional[int] = None
    object_components: List[ObjectComponent] = field(default_factory=list)
    logical_groups: List["LogicalGroup"] = field(default_factory=list)

    def add_object_component(self, comp: ObjectComponent) -> None:
        """Add an object component to this group.

        Args:
            comp: ObjectComponent to add.
        """
        self.object_components.append(comp)

    def add_logical_group(self, lg: "LogicalGroup") -> None:
        """Add a nested logical group.

        Args:
            lg: LogicalGroup to add as a child.
        """
        self.logical_groups.append(lg)


@dataclass
class MemoryUsage:
    """Represents memory usage details for a memory area.

    Attributes:
        kind: Type of usage - "allocated" or "available".
        start_address: Starting address of this usage block.
        size: Size in bytes.
        logical_group: Associated LogicalGroup if applicable.
    """

    kind: str  # 'allocated' or 'available'
    start_address: Optional[int] = None
    size: Optional[int] = None
    logical_group: Optional["LogicalGroup"] = None


@dataclass
class MemoryArea:
    """Represents a memory section (e.g., .text, .data, .bss).

    Attributes:
        name: Memory area name.
        length: Total length of this memory area.
        used_space: Amount of space used.
        usage_details: List of MemoryUsage entries showing allocation.
    """

    name: Optional[str] = None
    length: Optional[int] = None
    used_space: Optional[int] = None
    usage_details: List[MemoryUsage] = field(default_factory=list)

    def add_usage(self, usage: MemoryUsage) -> None:
        """Add a memory usage entry.

        Args:
            usage: MemoryUsage to add.
        """
        self.usage_details.append(usage)


@dataclass
class FolderNode:
    """Represents a folder in the input-file hierarchy.

    Attributes:
        name: Folder name (last component of path).
        path: Normalized folder path (forward slashes).
        children: Child FolderNodes (subfolders).
        input_files: InputFiles directly in this folder.
        _accumulated_size: Cached accumulated size (computed lazily).
    """

    name: str
    path: str
    children: Dict[str, "FolderNode"] = field(default_factory=dict)
    input_files: Dict[str, InputFile] = field(default_factory=dict)
    _accumulated_size: Optional[int] = field(default=None, init=False, repr=False)

    def get_accumulated_size(self) -> int:
        """Get total size of all object components in this folder and subfolders.

        Returns:
            Sum of sizes from all input files and their components recursively.
        """
        if self._accumulated_size is None:
            size = 0
            # Add sizes from input files in this folder
            for input_file in self.input_files.values():
                size += input_file.get_total_size()
            # Add sizes from child folders
            for child in self.children.values():
                size += child.get_accumulated_size()
            self._accumulated_size = size
        return self._accumulated_size

    def invalidate_size_cache(self) -> None:
        """Invalidate accumulated size cache after structural changes."""
        self._accumulated_size = None


@dataclass
class LinkInfoData:
    """Top-level container for all parsed linkinfo data.

    Aggregates all entities extracted from the linkinfo.xml file.

    Attributes:
        input_files: Dictionary mapping input file IDs to InputFile objects.
        object_components: Dictionary mapping component IDs to ObjectComponent objects.
        logical_groups: Dictionary mapping group IDs to LogicalGroup objects.
        memory_areas: Dictionary mapping area names to MemoryArea objects.
        filtered_component_ids: Set of component IDs filtered out (e.g., debug sections).
        issues: List of parsing issues/warnings encountered.
        folder_hierarchy: Root FolderNode of the input file folder tree.
    """

    input_files: Dict[str, InputFile] = field(default_factory=dict)
    object_components: Dict[str, ObjectComponent] = field(default_factory=dict)
    logical_groups: Dict[str, LogicalGroup] = field(default_factory=dict)
    memory_areas: Dict[str, MemoryArea] = field(default_factory=dict)
    filtered_component_ids: set[str] = field(default_factory=set)
    issues: List[LinkInfoIssue] = field(default_factory=list)
    folder_hierarchy: Optional["FolderNode"] = field(default=None)
