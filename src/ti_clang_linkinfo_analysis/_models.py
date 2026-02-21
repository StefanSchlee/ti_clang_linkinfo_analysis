from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ._errors import LinkInfoIssue


@dataclass
class InputFile:
    id: str
    name: Optional[str] = None
    path: Optional[str] = None
    object_components: List["ObjectComponent"] = field(default_factory=list)

    def add_component(self, component: "ObjectComponent") -> None:
        self.object_components.append(component)

    def get_sorted_components(self) -> List["ObjectComponent"]:
        """Returns object_components sorted by size in descending order."""
        return sorted(self.object_components, key=lambda x: x.size or 0, reverse=True)

    def get_total_size(self) -> int:
        """Returns the total size by summing all object component sizes."""
        return sum(comp.size or 0 for comp in self.object_components)


@dataclass
class ObjectComponent:
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
    id: str
    name: Optional[str] = None
    size: Optional[int] = None
    object_components: List[ObjectComponent] = field(default_factory=list)
    logical_groups: List["LogicalGroup"] = field(default_factory=list)

    def add_object_component(self, comp: ObjectComponent) -> None:
        self.object_components.append(comp)

    def add_logical_group(self, lg: "LogicalGroup") -> None:
        self.logical_groups.append(lg)


@dataclass
class MemoryUsage:
    kind: str  # 'allocated' or 'available'
    start_address: Optional[int] = None
    size: Optional[int] = None
    logical_group: Optional["LogicalGroup"] = None


@dataclass
class MemoryArea:
    name: Optional[str] = None
    length: Optional[int] = None
    used_space: Optional[int] = None
    usage_details: List[MemoryUsage] = field(default_factory=list)

    def add_usage(self, usage: MemoryUsage) -> None:
        self.usage_details.append(usage)


@dataclass
class LinkInfoData:
    input_files: Dict[str, InputFile] = field(default_factory=dict)
    object_components: Dict[str, ObjectComponent] = field(default_factory=dict)
    logical_groups: Dict[str, LogicalGroup] = field(default_factory=dict)
    memory_areas: Dict[str, MemoryArea] = field(default_factory=dict)
    filtered_component_ids: set[str] = field(default_factory=set)
    issues: List[LinkInfoIssue] = field(default_factory=list)
