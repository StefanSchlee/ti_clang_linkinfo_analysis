from dataclasses import dataclass, field
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
import os


# =========================
# Dataclasses
# =========================


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


# Additional dataclasses
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


# =========================
# Parser
# =========================


class LinkInfoParser:
    """Legacy parser API.

    Prefer using `LinkInfoAnalyzer` as the public facade. Direct usage of
    this parser is considered semi-public and may change across refactors.
    """

    def __init__(self, xml_path: str, filter_debug: bool = False):
        self.xml_path = xml_path
        self.filter_debug = filter_debug
        self.input_files: Dict[str, InputFile] = {}
        self.object_components: Dict[str, ObjectComponent] = {}
        self.logical_groups: Dict[str, LogicalGroup] = {}
        self.memory_areas: Dict[str, MemoryArea] = {}
        self.filtered_component_ids: set = set()

        # Parse XML directly in constructor
        tree = ET.parse(self.xml_path)
        root = tree.getroot()

        self._parse_input_files(root)
        self._parse_object_components(root)
        self._parse_logical_groups(root)
        self._parse_placement_map(root)
        self._resolve_cross_references()

    # ---------
    # Public API
    # ---------

    def get_sorted_input_files(self) -> List[InputFile]:
        """Returns input files sorted by total_size in descending order."""
        return sorted(
            self.input_files.values(), key=lambda f: f.get_total_size(), reverse=True
        )

    def export_sorted_input_files_markdown(self, output_path: str) -> None:
        """Write the sorted input files and their components to a Markdown file.

        Format example:

        # Input Files (sorted by total size)

        ## Components without Input File (total size: X bytes)

        - <component_name> (size: Y)
        - ...

        ## <input_name> (N components, total size: X bytes)

        - <component_name> (size: Y)
        - ...
        """
        lines: List[str] = []
        lines.append(
            f"# Input Files ({len(self.input_files)}, sorted by total size)\n\n"
        )

        # Calculate total size of all components
        total_all_components = sum(c.size or 0 for c in self.object_components.values())
        lines.append(
            f"**Total size (all components): {total_all_components} bytes**\n\n"
        )

        # Find components without an input file first
        components_without_input = [
            comp for comp in self.object_components.values() if comp.input_file is None
        ]

        # Print section for components without input file at the top
        if components_without_input:
            sorted_comps = sorted(
                components_without_input, key=lambda x: x.size or 0, reverse=True
            )
            total_size_no_input = sum(c.size or 0 for c in sorted_comps)
            lines.append(
                f"## Components without Input File (total size: {total_size_no_input} bytes)\n\n"
            )

            names = [c.name or c.id for c in sorted_comps]
            max_name_len = max((len(n) for n in names), default=0)
            sizes = [str(c.size or 0) for c in sorted_comps]
            max_size_width = max((len(s) for s in sizes), default=0)

            for comp, name, size_str in zip(sorted_comps, names, sizes):
                lines.append(
                    f"- {name.ljust(max_name_len)}  (size: {size_str.rjust(max_size_width)})\n"
                )
            lines.append("\n")

        for input_file in self.get_sorted_input_files():
            lines.append(
                f"## {input_file.name or input_file.id} ({len(input_file.object_components)} components, total size: {input_file.get_total_size()} bytes)\n"
            )
            if input_file.path:
                lines.append(f"**Path:** `{input_file.path}`\n\n")
            comps = input_file.get_sorted_components()
            if not comps:
                lines.append("_No components_\n")
            else:
                # Align component sizes within this input file
                names = [c.name or c.id for c in comps]
                max_name_len = max((len(n) for n in names), default=0)
                sizes = [str(c.size or 0) for c in comps]
                max_size_width = max((len(s) for s in sizes), default=0)

                for comp, name, size_str in zip(comps, names, sizes):
                    lines.append(
                        f"- {name.ljust(max_name_len)}  (size: {size_str.rjust(max_size_width)})\n"
                    )
            lines.append("\n")

        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as fh:
            fh.writelines(lines)

    def export_memory_areas_hierarchy_markdown(self, output_path: str) -> None:
        """Write memory areas with hierarchical logical groups and components to Markdown.

        Structure:
        # Memory Areas

        ## <memory_area_name> (length: X bytes, used: Y bytes)

        ### <logical_group_name> (size: Z bytes)
        - <object_component> (size: A bytes)
        - <nested_logical_group> (size: B bytes)
          - <object_component> (size: C bytes)
        """
        lines: List[str] = []
        lines.append("# Memory Areas\n\n")

        for mem_area in self.memory_areas.values():
            if mem_area.name:
                length_str = (
                    f"{mem_area.length:,}" if mem_area.length is not None else "?"
                )
                used_str = (
                    f"{mem_area.used_space:,}"
                    if mem_area.used_space is not None
                    else "?"
                )
                lines.append(
                    f"## {mem_area.name} (length: {length_str} bytes, used: {used_str} bytes)\n\n"
                )

                # Process allocated spaces and their logical groups
                for usage in mem_area.usage_details:
                    if usage.kind == "allocated" and usage.logical_group:
                        lg = usage.logical_group
                        self._append_logical_group_hierarchy(lg, lines, level=3)

                lines.append("\n")

        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as fh:
            fh.writelines(lines)

    def _append_logical_group_hierarchy(
        self, lg: LogicalGroup, lines: List[str], level: int, indent: str = ""
    ) -> None:
        """Recursively append logical group hierarchy to lines."""
        heading = "#" * level
        size_str = f"{lg.size:,}" if lg.size is not None else "?"
        lines.append(f"{indent}{heading} {lg.name or lg.id} (size: {size_str} bytes)\n")

        # Group object components by input file
        comps_by_input_file: Dict[str, List[ObjectComponent]] = {}

        for comp in lg.object_components:
            # Use special name for components without input file
            input_file_name = (
                comp.input_file.name or comp.input_file.id
                if comp.input_file
                else "(no input file)"
            )
            if input_file_name not in comps_by_input_file:
                comps_by_input_file[input_file_name] = []
            comps_by_input_file[input_file_name].append(comp)

        # sort input files groups by their size descending
        comps_by_input_file = dict(
            sorted(
                comps_by_input_file.items(),
                key=lambda item: sum(c.size or 0 for c in item[1]),
                reverse=True,
            )
        )

        # Append components grouped by input file
        for input_file_name in comps_by_input_file.keys():
            comps = comps_by_input_file[input_file_name]
            total_size = sum(c.size or 0 for c in comps)
            total_size_str = f"{total_size:,}" if total_size else "0"
            lines.append(
                f"{indent}- **{input_file_name}** ({len(comps)} components, total: {total_size_str} bytes)\n"
            )
            for comp in sorted(comps, key=lambda c: c.size or 0, reverse=True):
                comp_name = comp.name or comp.id
                comp_size = f"{comp.size:,}" if comp.size is not None else "?"
                lines.append(f"{indent}  - {comp_name} (size: {comp_size} bytes)\n")

        # Recursively append nested logical groups
        for sub_lg in lg.logical_groups:
            # Recurse with deeper indentation (heading will be added by recursion)
            self._append_logical_group_hierarchy(
                sub_lg, lines, level + 1, indent + "  "
            )

    # ---------
    # Internals
    # ---------

    def _parse_input_files(self, root: ET.Element) -> None:
        input_file_list = root.find("input_file_list")
        if input_file_list is None:
            return

        for elem in input_file_list.findall("input_file"):
            file_id = elem.attrib["id"]

            name = self._get_text(elem, "name")
            path = self._get_text(elem, "path")

            self.input_files[file_id] = InputFile(
                id=file_id,
                name=name,
                path=path,
            )

    def _parse_object_components(self, root: ET.Element) -> None:
        oc_list = root.find("object_component_list")
        if oc_list is None:
            return

        for elem in oc_list.findall("object_component"):
            oc_id = elem.attrib["id"]

            oc = ObjectComponent(
                id=oc_id,
                name=self._get_text(elem, "name"),
                load_address=self._get_hex(elem, "load_address"),
                run_address=self._get_hex(elem, "run_address"),
                size=self._get_hex(elem, "size"),
                alignment=self._get_hex(elem, "alignment"),
                readonly=self._get_bool(elem, "readonly"),
                executable=self._get_bool(elem, "executable"),
                value=self._get_text(elem, "value"),
            )

            # Input file reference
            input_ref = elem.find("input_file_ref")
            if input_ref is not None:
                oc.input_file = input_ref.attrib.get("idref")

            # RO references
            ro = elem.find("refd_ro_sections")
            if ro is not None:
                for ref in ro.findall("object_component_ref"):
                    oc.refd_ro_sections.append(ref.attrib["idref"])

            # RW references
            rw = elem.find("refd_rw_sections")
            if rw is not None:
                for ref in rw.findall("object_component_ref"):
                    oc.refd_rw_sections.append(ref.attrib["idref"])

            # Filter out .debug_ components if enabled
            if self.filter_debug and oc.name and oc.name.startswith(".debug_"):
                self.filtered_component_ids.add(oc_id)
                continue

            self.object_components[oc_id] = oc

    def _parse_logical_groups(self, root: ET.Element) -> None:
        lg_list = root.find("logical_group_list")
        if lg_list is None:
            return

        for elem in lg_list.findall("logical_group"):
            lg_id = elem.attrib.get("id")
            if not lg_id:
                continue

            lg = LogicalGroup(
                id=lg_id,
                name=self._get_text(elem, "name"),
                size=self._get_hex(elem, "size"),
            )

            contents = elem.find("contents")
            if contents is not None:
                for ref in contents.findall("object_component_ref"):
                    idref = ref.attrib.get("idref")
                    if idref:
                        placeholder = ObjectComponent(id=idref)
                        lg.object_components.append(placeholder)
                for ref in contents.findall("logical_group_ref"):
                    idref = ref.attrib.get("idref")
                    if idref:
                        # Store the id as a string; will resolve later
                        lg.logical_groups.append(idref)

            self.logical_groups[lg_id] = lg

    def _parse_placement_map(self, root: ET.Element) -> None:
        placement = root.find("placement_map")
        if placement is None:
            return

        for mem in placement.findall("memory_area"):
            mem_name = self._get_text(mem, "name")
            length = self._get_hex(mem, "length")
            used = self._get_hex(mem, "used_space")

            mem_area = MemoryArea(name=mem_name, length=length, used_space=used)

            usage_list = mem.find("usage_list")
            if usage_list is not None:
                for usage in usage_list.findall("usage"):
                    kind = usage.attrib.get("kind")
                    start_addr = self._get_hex(usage, "start_address")
                    size = self._get_hex(usage, "size")

                    mu = MemoryUsage(kind=kind, start_address=start_addr, size=size)

                    # If there's a logical group ref
                    lref = usage.find("logical_group_ref")
                    if lref is not None:
                        lg_id = lref.attrib.get("idref")
                        if lg_id:
                            # store the id for now
                            mu.logical_group = lg_id

                    mem_area.add_usage(mu)

            if mem_name:
                self.memory_areas[mem_name] = mem_area

    def _resolve_cross_references(self) -> None:
        # 1) Resolve ObjectComponent -> InputFile
        for comp in self.object_components.values():
            if isinstance(comp.input_file, str):
                comp.input_file = self.input_files.get(comp.input_file)

        # 2) Resolve LogicalGroup object components and nested groups
        for lg in self.logical_groups.values():
            # Resolve object components
            resolved_components = []
            for c in lg.object_components:
                if isinstance(c, ObjectComponent):
                    # Only placeholder with id, so resolve
                    real_comp = self.object_components.get(c.id)
                    if real_comp:
                        resolved_components.append(real_comp)
            lg.object_components = resolved_components

            # Resolve nested logical groups
            resolved_subgroups = []
            for sub in lg.logical_groups:
                if isinstance(sub, str):
                    sub_lg = self.logical_groups.get(sub)
                    if sub_lg:
                        resolved_subgroups.append(sub_lg)
            lg.logical_groups = resolved_subgroups

        # 3) Resolve MemoryUsage -> LogicalGroup
        for mem_area in self.memory_areas.values():
            for usage in mem_area.usage_details:
                if isinstance(usage.logical_group, str):
                    usage.logical_group = self.logical_groups.get(usage.logical_group)

    # -----------------
    # Helper Methods
    # -----------------

    @staticmethod
    def _get_text(elem: ET.Element, tag: str) -> Optional[str]:
        child = elem.find(tag)
        return child.text.strip() if child is not None and child.text else None

    @staticmethod
    def _get_hex(elem: ET.Element, tag: str) -> Optional[int]:
        child = elem.find(tag)
        if child is not None and child.text:
            try:
                return int(child.text.strip(), 16)
            except ValueError:
                return None
        return None

    @staticmethod
    def _get_bool(elem: ET.Element, tag: str) -> Optional[bool]:
        child = elem.find(tag)
        if child is not None and child.text:
            txt = child.text.strip().lower()
            if txt in ("true", "1"):
                return True
            if txt in ("false", "0"):
                return False
        return None
