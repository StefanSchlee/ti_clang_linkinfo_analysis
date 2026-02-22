from __future__ import annotations

from typing import Literal, Optional

from ._markdown import export_markdown
from ._models import FolderNode
from ._xml_parser import LinkInfoXmlParser
from .linkinfo_graph import LinkInfoGraphBuilder


class LinkInfoAnalyzer:
    """Public API facade for linkinfo.xml analysis.

    Construct with an XML path, then call analysis methods. The underlying parser and
    domain models are considered semi-public and may change; prefer this facade.

    Example:
        >>> analyzer = LinkInfoAnalyzer("build/linkinfo.xml", filter_debug=True)
        >>> analyzer.export_markdown("output.md", mode="input_file")
        >>> analyzer.export_inputfile_graph_pyvis("graph.html", show=True)
    """

    def __init__(self, xml_path: str, *, filter_debug: bool = False) -> None:
        """Initialize the analyzer with a linkinfo.xml file.

        Args:
            xml_path: Path to the linkinfo.xml file to analyze.
            filter_debug: If True, filters out debug-related sections like `.debug_*`.
                Defaults to False.
        """
        self._data = LinkInfoXmlParser(xml_path, filter_debug=filter_debug).parse()

    @property
    def issues(self):
        """Parsing issues detected while building the model.

        Returns:
            List of warning/error messages encountered during XML parsing.
        """
        return self._data.issues

    @property
    def folder_hierarchy(self) -> FolderNode:
        """Get the input-file folder hierarchy.

        Returns:
            Root FolderNode representing the folder structure of input files.
            Provides hierarchical grouping by source path for all analyses.
        """
        if self._data.folder_hierarchy is None:
            # Fallback: build on-demand (shouldn't happen with current parser)
            from ._folder_hierarchy import FolderHierarchy

            self._data.folder_hierarchy = FolderHierarchy.from_linkinfo_data(
                self._data, compact=False
            )
        return self._data.folder_hierarchy

    # -----------------
    # Markdown analyses
    # -----------------

    def export_markdown(
        self,
        output_path: str,
        *,
        mode: Literal["input_file", "memory_area"] = "input_file",
    ) -> None:
        """Export a hierarchical Markdown report sorted by size.

        Creates a Markdown file with size-sorted tables showing memory usage
        at different hierarchical levels. All items show accumulated byte sizes.

        Args:
            output_path: Path where the Markdown file will be written (required).
            mode: Hierarchy mode to use. Options:
                - "input_file" (default): Top-level input files, then components.
                - "memory_area": Memory areas → logical groups → input files → components.

        Raises:
            ValueError: If mode is not a supported value.

        Example:
            >>> analyzer.export_markdown("reports/files.md", mode="input_file")
            >>> analyzer.export_markdown("reports/memory.md", mode="memory_area")
        """
        export_markdown(self._data, output_path, mode=mode)

    # -----------------
    # Graph analyses
    # -----------------

    def export_inputfile_graph_pyvis(
        self,
        output_path: str,
        *,
        folder_paths: Optional[list[str]] = None,
        min_size: int = 0,
        show: bool = False,
    ) -> None:
        """Export interactive dependency graph as PyVis HTML.

        Creates an interactive graph visualization showing dependencies between
        input files. Node sizes reflect accumulated byte sizes. Edges show
        dependencies based on object component references.

        Args:
            output_path: Path where the HTML file will be written (required).
            folder_paths: Optional list of folder paths to group as nodes.
                Input files within these folders are collapsed into folder nodes.
                Files outside these folders remain as individual nodes.
                Use forward slashes (e.g., "src/drivers", "third_party/lwip").
            min_size: Minimum size in bytes for ungrouped input files.
                Files not in specified folders with size <= min_size are filtered out.
                Defaults to 0 (filters only empty files).
            show: If True, automatically opens the HTML in default browser.
                Defaults to False.

        Example:
            >>> analyzer.export_inputfile_graph_pyvis(
            ...     "graph.html",
            ...     folder_paths=["src/drivers", "src/app"],
            ...     min_size=2048,
            ...     show=True
            ... )
        """
        builder = LinkInfoGraphBuilder(
            self._data, folder_paths=folder_paths, min_size=min_size
        )
        builder.build_graph()
        builder.export_pyvis(output_path, show=show)

    def export_inputfile_graph_graphml(
        self,
        output_path: str,
        *,
        folder_paths: Optional[list[str]] = None,
        min_size: int = 0,
    ) -> None:
        """Export dependency graph as GraphML for external tools.

        Creates a GraphML file that can be imported into graph analysis tools
        like Gephi, yEd, or Cytoscape for advanced visualization and analysis.

        Args:
            output_path: Path where the GraphML file will be written (required).
            folder_paths: Optional list of folder paths to group as nodes.
                Input files within these folders are collapsed into folder nodes.
                Files outside these folders remain as individual nodes.
                Use forward slashes (e.g., "src/drivers", "third_party/lwip").
            min_size: Minimum size in bytes for ungrouped input files.
                Files not in specified folders with size <= min_size are filtered out.
                Defaults to 0 (filters only empty files).

        Example:
            >>> analyzer.export_inputfile_graph_graphml(
            ...     "deps.graphml",
            ...     folder_paths=["src/drivers"],
            ...     min_size=1024
            ... )
        """
        builder = LinkInfoGraphBuilder(
            self._data, folder_paths=folder_paths, min_size=min_size
        )
        builder.build_graph()
        builder.export_graphml(output_path)

    # -----------------
    # Icicle analysis
    # -----------------

    def export_icicle_plot(self, output_path: str, *, show: bool = False) -> None:
        """Export interactive hierarchical icicle plot as HTML.

        Creates a Plotly-based icicle plot showing hierarchical size distribution.
        The plot is vertically oriented with the root at the bottom. Hover over
        sections to see detailed size information.

        Hierarchy levels:
            - Top: Compacted folders (single-child chains collapsed)
            - Middle: Input files
            - Leaf: Object components

        Args:
            output_path: Path where the HTML file will be written (required).
            show: If True, automatically opens the plot in default browser.
                Defaults to False.

        Example:
            >>> analyzer.export_icicle_plot("size_viz.html", show=True)
        """
        from ._icicle import IcicleBuilder

        builder = IcicleBuilder(self._data)
        builder.export_html(output_path, show=show)
