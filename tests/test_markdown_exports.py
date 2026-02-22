from __future__ import annotations

from ti_clang_linkinfo_analysis import LinkInfoAnalyzer


def test_export_sorted_input_files_markdown(example_files, tmp_path) -> None:
    analyzer = LinkInfoAnalyzer(str(example_files["dpl_demo_debug"]), filter_debug=True)
    output_path = tmp_path / "input_files.md"

    analyzer.export_markdown(
        str(output_path), hierarchy=("input_file", "object_component")
    )

    content = output_path.read_text(encoding="utf-8")
    assert "# Input Files (133, sorted by total size)" in content
    assert "**Total size (all components): 134642 bytes**" in content
    assert "Components without Input File (total size: 19124 bytes)" in content


def test_export_memory_areas_hierarchy_markdown(example_files, tmp_path) -> None:
    analyzer = LinkInfoAnalyzer(str(example_files["dpl_demo_debug"]), filter_debug=True)
    output_path = tmp_path / "memory_areas.md"

    analyzer.export_markdown(
        str(output_path),
        hierarchy=(
            "memory_area",
            "logical_group",
            "input_file",
            "object_component",
        ),
    )

    content = output_path.read_text(encoding="utf-8")
    assert "# Memory Areas" in content
    assert "## FLASH" in content
    assert "## MSRAM" in content


def test_export_markdown_unified_api(example_files, tmp_path) -> None:
    analyzer = LinkInfoAnalyzer(str(example_files["dpl_demo_debug"]), filter_debug=True)
    output_path = tmp_path / "unified_input_files.md"

    analyzer.export_markdown(
        str(output_path), hierarchy=("input_file", "object_component")
    )

    content = output_path.read_text(encoding="utf-8")
    assert "# Input Files" in content
    assert "Total size (all components)" in content
