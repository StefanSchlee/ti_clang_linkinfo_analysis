from dataclasses import dataclass, field
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET


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


# =========================
# Parser
# =========================


class LinkInfoParser:
    def __init__(self, xml_path: str, filter_debug: bool = False):
        self.xml_path = xml_path
        self.filter_debug = filter_debug
        self.input_files: Dict[str, InputFile] = {}
        self.object_components: Dict[str, ObjectComponent] = {}

    # ---------
    # Public API
    # ---------

    def parse(self) -> None:
        tree = ET.parse(self.xml_path)
        root = tree.getroot()

        self._parse_input_files(root)
        self._parse_object_components(root)
        self._resolve_cross_references()

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
                continue

            self.object_components[oc_id] = oc

    def _resolve_cross_references(self) -> None:
        # Resolve object_component -> input_file
        for oc in self.object_components.values():
            if isinstance(oc.input_file, str):
                input_file = self.input_files.get(oc.input_file)
                oc.input_file = input_file
                if input_file is not None:
                    input_file.add_component(oc)

    # ---------
    # Helpers
    # ---------

    @staticmethod
    def _get_text(elem: ET.Element, tag: str) -> Optional[str]:
        child = elem.find(tag)
        return child.text if child is not None else None

    @staticmethod
    def _get_hex(elem: ET.Element, tag: str) -> Optional[int]:
        text = LinkInfoParser._get_text(elem, tag)
        return int(text, 16) if text else None

    @staticmethod
    def _get_bool(elem: ET.Element, tag: str) -> Optional[bool]:
        text = LinkInfoParser._get_text(elem, tag)
        return text.lower() == "true" if text else None


# =========================
# Example usage
# =========================
if __name__ == "__main__":
    parser = LinkInfoParser(
        "example_files/dpl_demo_release_linkinfo.xml", filter_debug=True
    )
    parser.parse()

    # Example: list components per input file
    for input_file in parser.input_files.values():
        print(
            f"{input_file.name}: {len(input_file.object_components)} components (total size: {input_file.get_total_size()} bytes)"
        )
        for comp in input_file.get_sorted_components():
            print(f"  - {comp.name} (size: {comp.size})")
