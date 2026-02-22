from __future__ import annotations

from pathlib import Path

from ti_clang_linkinfo_analysis import LinkInfoAnalyzer


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    xml_path = repo_root / "example_files" / "dpl_demo_debug_linkinfo.xml"
    output_dir = repo_root / "demo" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    analyzer = LinkInfoAnalyzer(str(xml_path), filter_debug=True)

    analyzer.export_inputfile_graph_pyvis(str(output_dir / "inputfile_graph.html"))
    analyzer.export_inputfile_graph_graphml(str(output_dir / "inputfile_graph.graphml"))

    print(f"Wrote graph outputs to: {output_dir}")


if __name__ == "__main__":
    main()
