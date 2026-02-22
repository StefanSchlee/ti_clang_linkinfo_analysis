# ti-clang-linkinfo-analysis

**Analysis toolkit for Texas Instruments Clang ARM Compiler linkinfo.xml files**

This package provides a Python API for analyzing memory usage and dependencies from TI Clang's `linkinfo.xml` linker output files. It offers multiple visualization and export formats including Markdown reports, interactive graphs, and hierarchical icicle plots.

## Overview

The TI Clang ARM compiler can generate detailed linker information in XML format, showing how your code is distributed across memory areas, which input files contribute to the binary size, and how object components reference each other. This tool parses those XML files and provides:

- **Hierarchical Markdown reports** - Size-sorted tables showing memory areas, input files, and object components
- **Interactive dependency graphs** - Visualize relationships between input files with folder grouping support
- **Icicle plots** - Hierarchical visualization of code size distribution by folder/file/component
- **Flexible folder grouping** - Aggregate analysis by source folder structure

Perfect for firmware developers working with embedded systems who need to optimize binary size, understand dependencies, and track memory usage across builds.

## Installation

### From PyPI

```bash
pip install ti-clang-linkinfo-analysis
```

### From Git Repository

```bash
pip install git+https://github.com/StefanSchlee/ti_clang_linkinfo_analysis.git
```

### For Development

```bash
git clone https://github.com/StefanSchlee/ti_clang_linkinfo_analysis.git
cd ti_clang_linkinfo_analysis
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .[dev]
```

## Quick Start

```python
from ti_clang_linkinfo_analysis import LinkInfoAnalyzer

# Create analyzer instance with your linkinfo XML file
analyzer = LinkInfoAnalyzer("build/linkinfo.xml", filter_debug=True)

# Export Markdown reports
analyzer.export_markdown("reports/by_inputfile.md", mode="input_file")
analyzer.export_markdown("reports/by_memory.md", mode="memory_area")

# Export interactive graph visualization
analyzer.export_inputfile_graph_pyvis("reports/dependencies.html")

# Export icicle plot showing size distribution
analyzer.export_icicle_plot("reports/size_distribution.html")
```

After running this code, open the generated HTML files in your browser to explore the interactive visualizations.

## Features

### Markdown Exports

Generate hierarchical Markdown reports sorted by size with accumulated totals at each level.

**Two hierarchy modes:**

1. **Input File Mode** (`mode="input_file"`): Groups by input files (`.o`, `.a` files), then shows object components within each file.

2. **Memory Area Mode** (`mode="memory_area"`): Groups by memory areas (e.g., `.text`, `.data`, `.bss`), then logical groups, then input files, then components.

```python
analyzer = LinkInfoAnalyzer("linkinfo.xml", filter_debug=True)

# Top-level: input files → components
analyzer.export_markdown("input_files.md", mode="input_file")

# Top-level: memory areas → logical groups → input files → components  
analyzer.export_markdown("memory_areas.md", mode="memory_area")
```

**Configuration:**
- `output_path` (required): Where to write the Markdown file
- `mode` (required): Either `"input_file"` or `"memory_area"`

All tables show accumulated byte sizes and are sorted in descending order for easy identification of the largest contributors.

### Graph Visualizations

Visualize dependencies between input files based on how object components reference each other.

**PyVis Interactive HTML:**

```python
analyzer.export_inputfile_graph_pyvis(
    "dependencies.html",
    folder_paths=["src/drivers", "src/middleware"],
    min_size=1024,
    show=True
)
```

**Configuration:**
- `output_path` (required): Where to write the HTML file
- `folder_paths` (optional): List of folder paths to group as single nodes. All input files in these folders are collapsed into folder nodes. Input files NOT in these folders remain as individual nodes.
- `min_size` (optional, default=0): Minimum byte size threshold for ungrouped input files. Files not in folders with size ≤ min_size are filtered out.
- `show` (optional, default=False): Automatically open the HTML in a web browser

**GraphML Export for External Tools:**

```python
analyzer.export_inputfile_graph_graphml(
    "dependencies.graphml",
    folder_paths=["src/drivers", "src/middleware"],
    min_size=1024
)
```

Load the `.graphml` file in tools like Gephi, yEd, or Cytoscape for advanced graph analysis.

**Graph features:**
- Node sizes reflect accumulated byte sizes
- Edges show dependencies (from "refd_ro_sections" and "refd_rw_sections")
- Color-coded node types: input files (blue), folders (green), compiler-generated (orange)
- Interactive controls: zoom, pan, drag nodes, search

### Icicle Plots

Hierarchical icicle plots show the size distribution across your codebase using nested rectangles.

```python
analyzer.export_icicle_plot(
    "size_distribution.html",
    show=True
)
```

**Configuration:**
- `output_path` (required): Where to write the HTML file
- `show` (optional, default=False): Automatically open the HTML in a web browser

**Hierarchy:** Folders → Input Files → Object Components

The plot is vertically oriented with the highest level (folders) at the bottom. Hover over sections to see detailed size information. Single-child folders are automatically compacted for cleaner visualization.

### Folder Hierarchy Access

Access the parsed folder structure programmatically:

```python
# Get the root folder node
folder_hierarchy = analyzer.folder_hierarchy

# Traverse the hierarchy
for folder in folder_hierarchy.subfolders.values():
    print(f"{folder.name}: {folder.get_total_size()} bytes")
    for input_file in folder.input_files:
        print(f"  {input_file.name}: {input_file.get_total_size()} bytes")
```

The folder hierarchy is built from input file paths and provides:
- Normalized POSIX-style paths
- Accumulated size calculations at each level
- Easy traversal of the source tree structure


## Examples

### Example 1: Memory Optimization Workflow

Identify which components contribute most to your binary size:

```python
from ti_clang_linkinfo_analysis import LinkInfoAnalyzer

# Parse the linkinfo file
analyzer = LinkInfoAnalyzer("build/firmware_linkinfo.xml", filter_debug=True)

# Generate memory area report to see overall distribution
analyzer.export_markdown("reports/memory_overview.md", mode="memory_area")

# Generate input file report to find large object files
analyzer.export_markdown("reports/input_files.md", mode="input_file")

# Create icicle plot for visual size analysis
analyzer.export_icicle_plot("reports/size_viz.html", show=True)
```

Review `memory_overview.md` to identify memory areas using the most space, then drill down in `input_files.md` to find specific files to optimize.

### Example 2: Dependency Analysis

Understand how modules depend on each other:

```python
from ti_clang_linkinfo_analysis import LinkInfoAnalyzer

analyzer = LinkInfoAnalyzer("build/linkinfo.xml", filter_debug=True)

# Create graph with major subsystems grouped
analyzer.export_inputfile_graph_pyvis(
    "reports/dependencies.html",
    folder_paths=[
        "src/drivers",
        "src/middleware",
        "src/application",
        "third_party/lwip",
        "third_party/freertos"
    ],
    min_size=2048,  # Hide small ungrouped files
    show=True
)

# Export for detailed analysis in Gephi
analyzer.export_inputfile_graph_graphml(
    "reports/dependencies.graphml",
    folder_paths=[
        "src/drivers",
        "src/middleware",
        "src/application"
    ],
    min_size=2048
)
```

The interactive graph shows which subsystems depend on each other, helping identify circular dependencies or unexpected coupling.

### Example 3: Folder Structure Analysis

Programmatically analyze your folder hierarchy:

```python
from ti_clang_linkinfo_analysis import LinkInfoAnalyzer

analyzer = LinkInfoAnalyzer("build/linkinfo.xml", filter_debug=True)

# Get folder hierarchy
root = analyzer.folder_hierarchy

# Print top-level folders sorted by size
folders_sorted = sorted(
    root.subfolders.values(),
    key=lambda f: f.get_total_size(),
    reverse=True
)

print("Top-level folders by size:")
for folder in folders_sorted:
    size_kb = folder.get_total_size() / 1024
    print(f"  {folder.name}: {size_kb:.1f} KB")
    
    # Show largest input file in this folder
    if folder.input_files:
        largest = max(folder.input_files, key=lambda f: f.get_total_size())
        file_kb = largest.get_total_size() / 1024
        print(f"    └─ Largest: {largest.name} ({file_kb:.1f} KB)")
```

## Release Notes

### v1.0.x (2026-02-22)

Initial structured release.

**Features:**
- Markdown exports with configurable hierarchy modes (input_file, memory_area)
- Interactive PyVis graph visualizations with folder grouping
- GraphML export for external graph analysis tools
- Icicle plot visualizations showing hierarchical size distribution
- Folder hierarchy extraction from input file paths
- Google-style docstrings throughout the public API
- Comprehensive user and architecture documentation
- Full test coverage with pytest

## License

[Specify your license here]

## Contributing

Contributions are welcome! Please see the main repository for development setup instructions and contribution guidelines.

## Support

For issues, feature requests, or questions, please open an issue on the GitHub repository.
