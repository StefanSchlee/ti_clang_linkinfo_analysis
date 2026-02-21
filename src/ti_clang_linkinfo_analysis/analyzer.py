from __future__ import annotations

from typing import Optional

from ._markdown import (
    export_memory_areas_hierarchy_markdown,
    export_sorted_input_files_markdown,
)
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

    def export_sorted_input_files_markdown(self, output_path: str) -> None:
        """Export input-file → object-component hierarchy markdown."""
        export_sorted_input_files_markdown(self._data, output_path)

    def export_memory_areas_hierarchy_markdown(self, output_path: str) -> None:
        """Export memory-area → logical-group → input-file hierarchy markdown."""
        export_memory_areas_hierarchy_markdown(self._data, output_path)

    # -----------------
    # Graph analyses
    # -----------------

    def export_inputfile_graph_pyvis(self, output_path: str) -> None:
        """Export the input-file level graph as a pyvis HTML file."""
        builder = LinkInfoGraphBuilder(self._data)
        builder.build_graph()
        builder.export_pyvis(output_path)

    def export_inputfile_graph_graphml(self, output_path: str) -> None:
        """Export the input-file level graph as GraphML."""
        builder = LinkInfoGraphBuilder(self._data)
        builder.build_graph()
        builder.export_graphml(output_path)

    # -----------------
    # Icicle analysis
    # -----------------

    def build_icicle_plot(
        self, *, output_path: Optional[str] = None, show: bool = False
    ) -> None:
        """Build the icicle plot (implemented in WP-07)."""
        raise NotImplementedError(
            "Icicle plot is not implemented yet. Planned for WP-07."
        )
