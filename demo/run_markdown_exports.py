from __future__ import annotations

from pathlib import Path

from ti_clang_linkinfo_analysis import LinkInfoAnalyzer


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    xml_path = repo_root / "example_files" / "dpl_demo_release_linkinfo.xml"
    output_dir = repo_root / "demo" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    analyzer = LinkInfoAnalyzer(str(xml_path), filter_debug=True)

    analyzer.export_markdown(
        str(output_dir / "input_files.md"),
        hierarchy=("input_file", "object_component"),
    )

    analyzer.export_markdown(
        str(output_dir / "memory_areas.md"),
        hierarchy=(
            "memory_area",
            "logical_group",
            "input_file",
            "object_component",
        ),
    )

    print(f"Wrote markdown outputs to: {output_dir}")


if __name__ == "__main__":
    main()
