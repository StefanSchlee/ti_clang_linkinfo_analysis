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
    """

    def __init__(self, xml_path: str, *, filter_debug: bool = False) -> None:
        self._data = LinkInfoXmlParser(xml_path, filter_debug=filter_debug).parse()

    @property
    def issues(self):
        """Parsing issues detected while building the model."""
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
        """Export a configurable markdown hierarchy.

        Args:
            mode: Chooses the highest hierarchy level:
                * "input_file" (default): top-level input files and their components.
                * "memory_area": inserts memory areas and logical groups above the input files.
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
        """Export the input-file level graph as a pyvis HTML file.

        Args:
            output_path: Path where the HTML file will be written.
            folder_paths: Optional list of folder paths to show as grouped nodes.
                All input files in these folders will be collapsed into folder nodes.
                Input files not in these folders remain as individual nodes.
                Paths should use forward slashes (e.g., "src/drivers").
            min_size: Minimum size threshold (in bytes) for ungrouped input files to be shown.
                Input files not in folders with size <= min_size will be filtered out.
                Default is 0, which filters out empty files.
            show: If True, open the graph in the default browser after creation.
                Default is False.
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
        """Export the input-file level graph as GraphML.

        Args:
            output_path: Path where the GraphML file will be written.
            folder_paths: Optional list of folder paths to show as grouped nodes.
                All input files in these folders will be collapsed into folder nodes.
                Input files not in these folders remain as individual nodes.
                Paths should use forward slashes (e.g., "src/drivers").
            min_size: Minimum size threshold (in bytes) for ungrouped input files to be shown.
                Input files not in folders with size <= min_size will be filtered out.
                Default is 0, which filters out empty files.
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
        """Export an interactive icicle plot visualization.

        The plot shows a hierarchical breakdown of memory usage:
        - Top level: compacted folders (single-child chains collapsed)
        - Middle level: input files
        - Leaf level: object components

        Args:
            output_path: Path where the HTML file will be written (mandatory).
            show: If True, open the plot in the default browser after creation.
                Default is False.
        """
        from ._icicle import IcicleBuilder

        builder = IcicleBuilder(self._data)
        builder.export_html(output_path, show=show)
