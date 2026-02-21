from __future__ import annotations

from ti_clang_linkinfo_analysis.linkinfo_parser import LinkInfoParser


def test_export_sorted_input_files_markdown(example_files, tmp_path) -> None:
    parser = LinkInfoParser(str(example_files["dpl_demo_debug"]), filter_debug=True)
    output_path = tmp_path / "input_files.md"

    parser.export_sorted_input_files_markdown(str(output_path))

    content = output_path.read_text(encoding="utf-8")
    assert "# Input Files (133, sorted by total size)" in content
    assert "**Total size (all components): 134642 bytes**" in content
    assert "Components without Input File (total size: 19124 bytes)" in content


def test_export_memory_areas_hierarchy_markdown(example_files, tmp_path) -> None:
    parser = LinkInfoParser(str(example_files["dpl_demo_debug"]), filter_debug=True)
    output_path = tmp_path / "memory_areas.md"

    parser.export_memory_areas_hierarchy_markdown(str(output_path))

    content = output_path.read_text(encoding="utf-8")
    assert "# Memory Areas" in content
    assert "## FLASH" in content
    assert "## MSRAM" in content
