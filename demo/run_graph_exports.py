"""Demo script for graph visualization with and without folder grouping."""

from __future__ import annotations

from pathlib import Path

from ti_clang_linkinfo_analysis import LinkInfoAnalyzer


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    xml_path = repo_root / "example_files" / "dpl_demo_debug_linkinfo.xml"
    output_dir = repo_root / "demo" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    analyzer = LinkInfoAnalyzer(str(xml_path), filter_debug=True)

    # Example 1: Basic input-file level graph
    print("Building input-file level graph...")
    output_file = output_dir / "graph_inputfiles.html"
    analyzer.export_inputfile_graph_pyvis(str(output_file))
    print(f"  -> {output_file}")

    # Example 2: Graph with folder grouping
    # Group files from specific SDK folders
    folder_paths = [
        "C:/ti/mcu_plus_sdk_am243x_11_02_00_24/source/kernel/freertos/lib",
        "C:/ti/mcu_plus_sdk_am243x_11_02_00_24/source/drivers/lib",
    ]

    print("\nBuilding graph with folder grouping...")
    print(f"  Grouping folders:")
    for fp in folder_paths:
        print(f"    - {fp}")

    output_file = output_dir / "graph_with_folders.html"
    analyzer.export_inputfile_graph_pyvis(str(output_file), folder_paths=folder_paths)
    print(f"  -> {output_file}")

    # Example 3: Export GraphML for Gephi/Cytoscape
    print("\nExporting GraphML format...")
    output_file = output_dir / "graph_inputfiles.graphml"
    analyzer.export_inputfile_graph_graphml(str(output_file))
    print(f"  -> {output_file}")

    output_file = output_dir / "graph_with_folders.graphml"
    analyzer.export_inputfile_graph_graphml(str(output_file), folder_paths=folder_paths)
    print(f"  -> {output_file}")

    print("\n✓ All graph exports completed!")
    print("Open the HTML files in a browser to interact with the visualizations.")


if __name__ == "__main__":
    main()
