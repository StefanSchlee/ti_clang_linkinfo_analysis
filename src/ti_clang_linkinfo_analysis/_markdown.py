from __future__ import annotations

from typing import Iterable, List, Sequence
import os

from ._models import LinkInfoData, LogicalGroup, ObjectComponent


def export_markdown(
    data: LinkInfoData, output_path: str, *, hierarchy: Sequence[str]
) -> None:
    """Export linkinfo data to markdown with a configurable hierarchy.

    Supported hierarchies:
      - ("input_file", "object_component")
      - ("memory_area", "logical_group", "input_file", "object_component")
    """
    if hierarchy == ("input_file", "object_component"):
        _export_input_file_hierarchy(data, output_path)
        return

    if hierarchy == (
        "memory_area",
        "logical_group",
        "input_file",
        "object_component",
    ):
        _export_memory_area_hierarchy(data, output_path)
        return

    raise ValueError(
        "Unsupported markdown hierarchy. Supported: "
        "('input_file', 'object_component') and "
        "('memory_area', 'logical_group', 'input_file', 'object_component')."
    )


def _export_input_file_hierarchy(data: LinkInfoData, output_path: str) -> None:
    lines: List[str] = []
    lines.append(f"# Input Files ({len(data.input_files)}, sorted by total size)\n\n")

    total_all_components = sum(c.size or 0 for c in data.object_components.values())
    lines.append(f"**Total size (all components): {total_all_components} bytes**\n\n")

    components_without_input = [
        comp for comp in data.object_components.values() if comp.input_file is None
    ]
    if components_without_input:
        sorted_comps = _sorted_by_size_then_name(
            components_without_input,
            size_fn=lambda c: c.size or 0,
            name_fn=lambda c: c.name or c.id,
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
                f"(size: {size_str.rjust(max_size_width)} bytes)\n"
            )
        lines.append("\n")

    sorted_input_files = _sorted_by_size_then_name(
        data.input_files.values(),
        size_fn=lambda f: f.get_total_size(),
        name_fn=lambda f: f.name or f.id,
    )

    for input_file in sorted_input_files:
        total_size = input_file.get_total_size()
        lines.append(
            f"## {input_file.name or input_file.id} "
            f"({len(input_file.object_components)} components, "
            f"total size: {total_size} bytes)\n"
        )
        if input_file.path:
            lines.append(f"**Path:** `{input_file.path}`\n\n")
        comps = _sorted_by_size_then_name(
            input_file.object_components,
            size_fn=lambda c: c.size or 0,
            name_fn=lambda c: c.name or c.id,
        )
        if not comps:
            lines.append("_No components_\n")
        else:
            names = [c.name or c.id for c in comps]
            max_name_len = max((len(n) for n in names), default=0)
            sizes = [str(c.size or 0) for c in comps]
            max_size_width = max((len(s) for s in sizes), default=0)
            for comp, name, size_str in zip(comps, names, sizes):
                lines.append(
                    f"- {name.ljust(max_name_len)}  "
                    f"(size: {size_str.rjust(max_size_width)} bytes)\n"
                )
        lines.append("\n")

    _write_output(output_path, lines)


def _export_memory_area_hierarchy(data: LinkInfoData, output_path: str) -> None:
    lines: List[str] = []
    lines.append("# Memory Areas\n\n")

    sorted_mem_areas = _sorted_by_size_then_name(
        data.memory_areas.values(),
        size_fn=_memory_area_accumulated_size,
        name_fn=lambda m: m.name or "",
    )

    for mem_area in sorted_mem_areas:
        if not mem_area.name:
            continue
        length_str = f"{mem_area.length:,}" if mem_area.length is not None else "?"
        used_str = (
            f"{mem_area.used_space:,}" if mem_area.used_space is not None else "?"
        )
        total_size = _memory_area_accumulated_size(mem_area)
        lines.append(
            f"## {mem_area.name} "
            f"(length: {length_str} bytes, used: {used_str} bytes, "
            f"total: {total_size} bytes)\n\n"
        )

        logical_groups: List[LogicalGroup] = []
        for usage in mem_area.usage_details:
            if usage.kind == "allocated" and usage.logical_group:
                logical_groups.append(usage.logical_group)

        for lg in _sorted_by_size_then_name(
            logical_groups,
            size_fn=_logical_group_accumulated_size,
            name_fn=lambda g: g.name or g.id,
        ):
            _append_logical_group_hierarchy(lg, lines, level=3)

        lines.append("\n")

    _write_output(output_path, lines)


def _append_logical_group_hierarchy(
    lg: LogicalGroup, lines: List[str], level: int, indent: str = ""
) -> None:
    """Recursively append logical group hierarchy to lines."""
    heading = "#" * level
    total_size = _logical_group_accumulated_size(lg)
    lines.append(f"{indent}{heading} {lg.name or lg.id} (size: {total_size} bytes)\n")

    comps_by_input_file: dict[str, List[ObjectComponent]] = {}
    for comp in lg.object_components:
        input_file_name = (
            comp.input_file.name or comp.input_file.id
            if comp.input_file
            else "(no input file)"
        )
        comps_by_input_file.setdefault(input_file_name, []).append(comp)

    sorted_input_files = _sorted_by_size_then_name(
        comps_by_input_file.items(),
        size_fn=lambda item: sum(c.size or 0 for c in item[1]),
        name_fn=lambda item: item[0],
    )

    for input_file_name, comps in sorted_input_files:
        total_size = sum(c.size or 0 for c in comps)
        lines.append(
            f"{indent}- **{input_file_name}** "
            f"({len(comps)} components, total: {total_size} bytes)\n"
        )
        sorted_comps = _sorted_by_size_then_name(
            comps, size_fn=lambda c: c.size or 0, name_fn=lambda c: c.name or c.id
        )
        names = [c.name or c.id for c in sorted_comps]
        max_name_len = max((len(n) for n in names), default=0)
        sizes = [str(c.size or 0) for c in sorted_comps]
        max_size_width = max((len(s) for s in sizes), default=0)
        for comp, name, size_str in zip(sorted_comps, names, sizes):
            lines.append(
                f"{indent}  - {name.ljust(max_name_len)}  "
                f"(size: {size_str.rjust(max_size_width)} bytes)\n"
            )

    for sub_lg in _sorted_by_size_then_name(
        lg.logical_groups,
        size_fn=_logical_group_accumulated_size,
        name_fn=lambda g: g.name or g.id,
    ):
        _append_logical_group_hierarchy(sub_lg, lines, level + 1, indent + "  ")


def _sorted_by_size_then_name(items: Iterable, *, size_fn, name_fn) -> List:
    return sorted(
        list(items),
        key=lambda item: (
            -int(size_fn(item) or 0),
            (name_fn(item) or "").lower(),
        ),
    )


def _logical_group_accumulated_size(lg: LogicalGroup) -> int:
    if lg.size is not None:
        return lg.size
    size = sum(comp.size or 0 for comp in lg.object_components)
    for sub_lg in lg.logical_groups:
        size += _logical_group_accumulated_size(sub_lg)
    return size


def _memory_area_accumulated_size(mem_area) -> int:
    if mem_area.used_space is not None:
        return mem_area.used_space
    size = 0
    for usage in mem_area.usage_details:
        if usage.kind == "allocated" and usage.logical_group:
            size += _logical_group_accumulated_size(usage.logical_group)
    return size


def _write_output(output_path: str, lines: List[str]) -> None:
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.writelines(lines)
