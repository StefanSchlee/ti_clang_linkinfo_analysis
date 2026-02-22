from __future__ import annotations

from typing import Optional
import xml.etree.ElementTree as ET

from ._errors import LinkInfoIssue, LinkInfoParseError
from ._folder_hierarchy import FolderHierarchy
from ._models import (
    InputFile,
    LinkInfoData,
    LogicalGroup,
    MemoryArea,
    MemoryUsage,
    ObjectComponent,
)


class LinkInfoXmlParser:
    def __init__(self, xml_path: str, *, filter_debug: bool = False) -> None:
        self.xml_path = xml_path
        self.filter_debug = filter_debug

    def parse(self) -> LinkInfoData:
        data = LinkInfoData()
        try:
            tree = ET.parse(self.xml_path)
        except (ET.ParseError, FileNotFoundError, OSError) as exc:
            raise LinkInfoParseError(f"Failed to parse {self.xml_path}: {exc}") from exc

        root = tree.getroot()

        self._parse_input_files(root, data)
        self._parse_object_components(root, data)
        self._parse_logical_groups(root, data)
        self._parse_placement_map(root, data)
        self._resolve_cross_references(data)

        # Build folder hierarchy from input files
        data.folder_hierarchy = FolderHierarchy.from_linkinfo_data(data, compact=False)

        return data

    def _parse_input_files(self, root: ET.Element, data: LinkInfoData) -> None:
        input_file_list = root.find("input_file_list")
        if input_file_list is None:
            return

        for elem in input_file_list.findall("input_file"):
            file_id = elem.attrib["id"]

            name = self._get_text(elem, "name")
            path = self._get_text(elem, "path")

            data.input_files[file_id] = InputFile(
                id=file_id,
                name=name,
                path=path,
            )

    def _parse_object_components(self, root: ET.Element, data: LinkInfoData) -> None:
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
                data.filtered_component_ids.add(oc_id)
                continue

            data.object_components[oc_id] = oc

    def _parse_logical_groups(self, root: ET.Element, data: LinkInfoData) -> None:
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

            data.logical_groups[lg_id] = lg

    def _parse_placement_map(self, root: ET.Element, data: LinkInfoData) -> None:
        placement = root.find("placement_map")
        if placement is None:
            return

        for mem in placement.findall("memory_area"):
            mem_name = self._get_text(mem, "name")
            length = self._get_hex(mem, "length")
            used = self._get_hex(mem, "used_space")

            mem_area = MemoryArea(name=mem_name, length=length, used_space=used)

            usage_details = mem.find("usage_details")
            if usage_details is not None:
                for usage in list(usage_details):
                    kind = usage.attrib.get("kind")
                    if kind is None:
                        if usage.tag == "allocated_space":
                            kind = "allocated"
                        elif usage.tag == "available_space":
                            kind = "available"
                        else:
                            kind = usage.tag

                    start_addr = self._get_hex(usage, "start_address")
                    size = self._get_hex(usage, "size")

                    mu = MemoryUsage(kind=kind, start_address=start_addr, size=size)

                    lref = usage.find("logical_group_ref")
                    if lref is not None:
                        lg_id = lref.attrib.get("idref")
                        if lg_id:
                            mu.logical_group = lg_id

                    mem_area.add_usage(mu)

            if mem_name:
                data.memory_areas[mem_name] = mem_area

    def _resolve_cross_references(self, data: LinkInfoData) -> None:
        # 1) Resolve ObjectComponent -> InputFile
        for comp in data.object_components.values():
            if isinstance(comp.input_file, str):
                input_file = data.input_files.get(comp.input_file)
                if input_file is None:
                    data.issues.append(
                        LinkInfoIssue(
                            code="missing_input_file_ref",
                            message="ObjectComponent references missing InputFile",
                            context={
                                "object_component_id": comp.id,
                                "input_file_id": comp.input_file,
                            },
                        )
                    )
                    comp.input_file = None
                else:
                    comp.input_file = input_file
                    # Add component to input file
                    input_file.add_component(comp)

        # 2) Resolve LogicalGroup object components and nested groups
        for lg in data.logical_groups.values():
            # Resolve object components
            resolved_components = []
            for c in lg.object_components:
                if isinstance(c, ObjectComponent):
                    # Only placeholder with id, so resolve
                    real_comp = data.object_components.get(c.id)
                    if real_comp:
                        resolved_components.append(real_comp)
                    else:
                        if c.id not in data.filtered_component_ids:
                            data.issues.append(
                                LinkInfoIssue(
                                    code="missing_object_component",
                                    message="LogicalGroup references missing ObjectComponent",
                                    context={
                                        "logical_group_id": lg.id,
                                        "object_component_id": c.id,
                                    },
                                )
                            )
            lg.object_components = resolved_components

            # Resolve nested logical groups
            resolved_subgroups = []
            for sub in lg.logical_groups:
                if isinstance(sub, str):
                    sub_lg = data.logical_groups.get(sub)
                    if sub_lg:
                        resolved_subgroups.append(sub_lg)
                    else:
                        data.issues.append(
                            LinkInfoIssue(
                                code="missing_logical_group",
                                message="LogicalGroup references missing LogicalGroup",
                                context={
                                    "logical_group_id": lg.id,
                                    "logical_group_ref": sub,
                                },
                            )
                        )
            lg.logical_groups = resolved_subgroups

        # 3) Resolve MemoryUsage -> LogicalGroup
        for mem_area in data.memory_areas.values():
            for usage in mem_area.usage_details:
                if isinstance(usage.logical_group, str):
                    logical_group = data.logical_groups.get(usage.logical_group)
                    if logical_group is None:
                        data.issues.append(
                            LinkInfoIssue(
                                code="missing_memory_logical_group",
                                message="MemoryUsage references missing LogicalGroup",
                                context={
                                    "memory_area": mem_area.name,
                                    "logical_group_id": usage.logical_group,
                                },
                            )
                        )
                    usage.logical_group = logical_group

        # 4) Validate component references (RO/RW)
        for comp in data.object_components.values():
            for ref_id in comp.refd_ro_sections + comp.refd_rw_sections:
                if ref_id in data.object_components:
                    continue
                if ref_id in data.filtered_component_ids:
                    continue
                data.issues.append(
                    LinkInfoIssue(
                        code="missing_object_component_ref",
                        message="ObjectComponent references missing ObjectComponent in refd sections",
                        context={"object_component_id": comp.id, "ref_id": ref_id},
                    )
                )

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
