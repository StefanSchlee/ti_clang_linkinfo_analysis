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


# =========================
# Parser
# =========================


class LinkInfoParser:
    def __init__(self, xml_path: str, filter_debug: bool = False):
        self.xml_path = xml_path
        self.filter_debug = filter_debug
        self.input_files: Dict[str, InputFile] = {}
        self.object_components: Dict[str, ObjectComponent] = {}

        # Parse XML directly in constructor
        tree = ET.parse(self.xml_path)
        root = tree.getroot()

        self._parse_input_files(root)
        self._parse_object_components(root)
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

    # Example: print sorted input files by total size
    # sorted_files = parser.get_sorted_input_files()
    # for input_file in sorted_files:
    #     print(
    #         f"{input_file.name}: {len(input_file.object_components)} components (total size: {input_file.get_total_size()} bytes)"
    #     )
    #     for comp in input_file.get_sorted_components():
    #         print(f"  - {comp.name} (size: {comp.size})")

    # Export to markdown file
    parser.export_sorted_input_files_markdown("outputs/input_files.md")

    # Example: list components per input file
    # for input_file in parser.input_files.values():
    #     print(
    #         f"{input_file.name}: {len(input_file.object_components)} components (total size: {input_file.get_total_size()} bytes)"
    #     )
    #     for comp in input_file.get_sorted_components():
    #         print(f"  - {comp.name} (size: {comp.size})")
