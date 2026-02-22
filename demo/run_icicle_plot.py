"""Demo script for icicle plot visualization."""

from __future__ import annotations

from pathlib import Path

from ti_clang_linkinfo_analysis import LinkInfoAnalyzer


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    xml_path = repo_root / "example_files" / "dpl_demo_release_linkinfo.xml"
    output_dir = repo_root / "demo" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    analyzer = LinkInfoAnalyzer(str(xml_path), filter_debug=True)

    output_file = output_dir / "icicle_plot.html"
    print(f"Building icicle plot...")
    analyzer.export_icicle_plot(str(output_file), show=False)
    print(f"Icicle plot written to: {output_file}")
    print("Open the HTML file in a browser to interact with the visualization.")


if __name__ == "__main__":
    main()
