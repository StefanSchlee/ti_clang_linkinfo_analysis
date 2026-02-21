from __future__ import annotations

from typing import List
import os

from ._models import LinkInfoData, LogicalGroup, ObjectComponent


def export_sorted_input_files_markdown(data: LinkInfoData, output_path: str) -> None:
    """Write the sorted input files and their components to a Markdown file."""
    lines: List[str] = []
    lines.append(f"# Input Files ({len(data.input_files)}, sorted by total size)\n\n")

    # Calculate total size of all components
    total_all_components = sum(c.size or 0 for c in data.object_components.values())
    lines.append(f"**Total size (all components): {total_all_components} bytes**\n\n")

    # Find components without an input file first
    components_without_input = [
        comp for comp in data.object_components.values() if comp.input_file is None
    ]

    # Print section for components without input file at the top
    if components_without_input:
        sorted_comps = sorted(
            components_without_input, key=lambda x: x.size or 0, reverse=True
        )
        total_size_no_input = sum(c.size or 0 for c in sorted_comps)
        lines.append(
            "## Components without Input File "
            f"(total size: {total_size_no_input} bytes)\n\n"
        )

        names = [c.name or c.id for c in sorted_comps]
        max_name_len = max((len(n) for n in names), default=0)
        sizes = [str(c.size or 0) for c in sorted_comps]
        max_size_width = max((len(s) for s in sizes), default=0)

        for comp, name, size_str in zip(sorted_comps, names, sizes):
            lines.append(
                f"- {name.ljust(max_name_len)}  "
                f"(size: {size_str.rjust(max_size_width)})\n"
            )
        lines.append("\n")

    sorted_input_files = sorted(
        data.input_files.values(),
        key=lambda f: f.get_total_size(),
        reverse=True,
    )

    for input_file in sorted_input_files:
        lines.append(
            f"## {input_file.name or input_file.id} "
            f"({len(input_file.object_components)} components, "
            f"total size: {input_file.get_total_size()} bytes)\n"
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
                    f"- {name.ljust(max_name_len)}  "
                    f"(size: {size_str.rjust(max_size_width)})\n"
                )
        lines.append("\n")

    _write_output(output_path, lines)


def export_memory_areas_hierarchy_markdown(
    data: LinkInfoData, output_path: str
) -> None:
    """Write memory areas with hierarchical logical groups and components to Markdown."""
    lines: List[str] = []
    lines.append("# Memory Areas\n\n")

    for mem_area in data.memory_areas.values():
        if mem_area.name:
            length_str = f"{mem_area.length:,}" if mem_area.length is not None else "?"
            used_str = (
                f"{mem_area.used_space:,}" if mem_area.used_space is not None else "?"
            )
            lines.append(
                f"## {mem_area.name} "
                f"(length: {length_str} bytes, used: {used_str} bytes)\n\n"
            )

            # Process allocated spaces and their logical groups
            for usage in mem_area.usage_details:
                if usage.kind == "allocated" and usage.logical_group:
                    lg = usage.logical_group
                    _append_logical_group_hierarchy(lg, lines, level=3)

            lines.append("\n")

    _write_output(output_path, lines)


def _append_logical_group_hierarchy(
    lg: LogicalGroup, lines: List[str], level: int, indent: str = ""
) -> None:
    """Recursively append logical group hierarchy to lines."""
    heading = "#" * level
    size_str = f"{lg.size:,}" if lg.size is not None else "?"
    lines.append(f"{indent}{heading} {lg.name or lg.id} (size: {size_str} bytes)\n")

    # Group object components by input file
    comps_by_input_file: dict[str, List[ObjectComponent]] = {}

    for comp in lg.object_components:
        # Use special name for components without input file
        input_file_name = (
            comp.input_file.name or comp.input_file.id
            if comp.input_file
            else "(no input file)"
        )
        comps_by_input_file.setdefault(input_file_name, []).append(comp)

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
            f"{indent}- **{input_file_name}** "
            f"({len(comps)} components, total: {total_size_str} bytes)\n"
        )
        for comp in sorted(comps, key=lambda c: c.size or 0, reverse=True):
            comp_name = comp.name or comp.id
            comp_size = f"{comp.size:,}" if comp.size is not None else "?"
            lines.append(f"{indent}  - {comp_name} (size: {comp_size} bytes)\n")

    # Recursively append nested logical groups
    for sub_lg in lg.logical_groups:
        _append_logical_group_hierarchy(sub_lg, lines, level + 1, indent + "  ")


def _write_output(output_path: str, lines: List[str]) -> None:
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.writelines(lines)
