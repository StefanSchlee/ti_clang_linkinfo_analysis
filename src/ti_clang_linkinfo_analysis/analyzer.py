from __future__ import annotations

from typing import Optional

from .linkinfo_parser import LinkInfoParser
from .linkinfo_graph import LinkInfoGraphBuilder


class LinkInfoAnalyzer:
    """Public API facade for linkinfo.xml analysis.

    Construct with an XML path, then call analysis methods. The underlying parser and
    domain models are considered semi-public and may change; prefer this facade.
    """

    def __init__(self, xml_path: str, *, filter_debug: bool = False) -> None:
        self._parser = LinkInfoParser(xml_path, filter_debug=filter_debug)

    @property
    def parser(self) -> LinkInfoParser:
        """Access to the underlying parser (semi-public, subject to change)."""
        return self._parser

    # -----------------
    # Markdown analyses
    # -----------------

    def export_sorted_input_files_markdown(self, output_path: str) -> None:
        """Export input-file → object-component hierarchy markdown."""
        self._parser.export_sorted_input_files_markdown(output_path)

    def export_memory_areas_hierarchy_markdown(self, output_path: str) -> None:
        """Export memory-area → logical-group → input-file hierarchy markdown."""
        self._parser.export_memory_areas_hierarchy_markdown(output_path)

    # -----------------
    # Graph analyses
    # -----------------

    def export_inputfile_graph_pyvis(self, output_path: str) -> None:
        """Export the input-file level graph as a pyvis HTML file."""
        builder = LinkInfoGraphBuilder(self._parser)
        builder.build_graph()
        builder.export_pyvis(output_path)

    def export_inputfile_graph_graphml(self, output_path: str) -> None:
        """Export the input-file level graph as GraphML."""
        builder = LinkInfoGraphBuilder(self._parser)
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
