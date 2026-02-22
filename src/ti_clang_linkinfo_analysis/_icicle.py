"""Icicle plot visualization for linkinfo hierarchical data.

Builds interactive icicle plots using plotly that show the hierarchical
breakdown of memory usage:
- Level 1 (bottom): Compacted folders (single-child chains collapsed)
- Level 2: Input files
- Level 3 (top, leaf): Object components
"""

from __future__ import annotations

from typing import List, Tuple

import plotly.graph_objects as go

from ._folder_hierarchy import _compact_folder_tree
from ._models import FolderNode, InputFile, LinkInfoData, ObjectComponent


class IcicleBuilder:
    """Builder for interactive icicle plots of linkinfo hierarchies.

    Constructs a plotly icicle figure with compacted folder structure,
    input files, and object components as levels, with byte sizes.
    """

    def __init__(self, data: LinkInfoData) -> None:
        """Initialize the icicle builder.

        Args:
            data: Parsed linkinfo data containing input files and folder hierarchy.
        """
        self._data = data
        self._labels: List[str] = []
        self._parents: List[str] = []
        self._values: List[int] = []
        self._ids: List[str] = []
        self._colors: List[int] = []  # For color scaling by size
        self._hover_texts: List[str] = []

    def export_html(self, output_path: str, *, show: bool = False) -> None:
        """Export the icicle plot as an interactive HTML file.

        Args:
            output_path: Path where the HTML file will be written.
            show: If True, open the plot in the default browser.
        """
        fig = self._build_figure()
        fig.write_html(output_path)
        if show:
            fig.show()

    def _build_figure(self) -> go.Figure:
        """Build and return the plotly Figure object.

        Returns:
            Configured plotly icicle Figure.
        """
        self._reset_data()

        # Get the folder hierarchy (already built by LinkInfoAnalyzer)
        folder_root = self._data.folder_hierarchy

        # Always compact the folder hierarchy for icicle display
        compacted_root = _compact_folder_tree(folder_root)

        orphan_components = [
            comp
            for comp in self._data.object_components.values()
            if comp.input_file is None
        ]
        orphan_size = sum(comp.size or 0 for comp in orphan_components)

        # Add root as top-level parent
        root_id = "root"
        root_size = compacted_root.get_accumulated_size()
        self._add_node(
            label=compacted_root.name,
            parent="",
            value=root_size,
            node_id=root_id,
            hover_text=f"Root<br>Size: {self._format_bytes(root_size)}",
        )

        # Recursively add folders, input files, and components
        self._add_folder_hierarchy(compacted_root, root_id)

        # Add orphan components (without input file) as a separate top-level group
        self._add_orphan_components("", orphan_components, orphan_size)

        # Create the figure
        fig = go.Figure(
            go.Icicle(
                labels=self._labels,
                parents=self._parents,
                values=self._values,
                ids=self._ids,
                branchvalues="total",
                marker=dict(
                    colorscale="RdYlGn_r",  # Red-Yellow-Green reversed (high=red)
                    cmid=sum(self._values) / len(self._values) if self._values else 0,
                ),
                text=self._hover_texts,
                hovertext=self._hover_texts,
                hoverinfo="label+text+value",
                textposition="middle center",
            )
        )

        fig.update_layout(
            title="Memory Usage Icicle Plot (Folder Structure)",
            font=dict(size=12),
            margin=dict(t=50, l=10, r=10, b=10),
        )

        return fig

    def _reset_data(self) -> None:
        """Reset internal data structures for building a new figure."""
        self._labels.clear()
        self._parents.clear()
        self._values.clear()
        self._ids.clear()
        self._colors.clear()
        self._hover_texts.clear()

    def _add_node(
        self,
        label: str,
        parent: str,
        value: int,
        node_id: str,
        hover_text: str,
    ) -> None:
        """Add a node to the icicle plot data.

        Args:
            label: Display label for the node.
            parent: Parent node ID (empty string for root).
            value: Size in bytes for this node.
            node_id: Unique ID for this node.
            hover_text: Hover text to display.
        """
        self._labels.append(label)
        self._parents.append(parent)
        self._values.append(value)
        self._ids.append(node_id)
        self._colors.append(value)
        self._hover_texts.append(hover_text)

    def _add_folder_hierarchy(self, folder: FolderNode, parent_id: str) -> None:
        """Recursively add folder node, its input files, and their components.

        Args:
            folder: FolderNode to process.
            parent_id: ID of the parent node.
        """
        # Add all input files in this folder
        for input_file in folder.input_files.values():
            self._add_input_file(input_file, parent_id)

        # Add all subfolders
        for child_folder in folder.children.values():
            folder_id = f"folder:{child_folder.path}"
            size = child_folder.get_accumulated_size()

            self._add_node(
                label=child_folder.name,
                parent=parent_id,
                value=size,
                node_id=folder_id,
                hover_text=f"Folder: {child_folder.path}<br>Size: {self._format_bytes(size)}",
            )

            # Recursively add subfolders and their files
            self._add_folder_hierarchy(child_folder, folder_id)

    def _add_input_file(self, input_file: InputFile, parent_id: str) -> None:
        """Add an input file node and its object components.

        Args:
            input_file: InputFile to add.
            parent_id: ID of the parent folder node.
        """
        file_id = f"file:{input_file.id}"
        file_size = input_file.get_total_size()

        self._add_node(
            label=input_file.name or input_file.id,
            parent=parent_id,
            value=file_size,
            node_id=file_id,
            hover_text=f"File: {input_file.name}<br>Size: {self._format_bytes(file_size)}",
        )

        # Add all object components in this file
        sorted_components = input_file.get_sorted_components()
        for component in sorted_components:
            component_id = f"comp:{component.id}"
            component_size = component.size or 0

            self._add_node(
                label=component.name or component.id,
                parent=file_id,
                value=component_size,
                node_id=component_id,
                hover_text=self._format_component_hover(component),
            )

    def _add_orphan_components(
        self,
        root_id: str,
        orphan_components: list[ObjectComponent],
        orphan_size: int,
    ) -> None:
        """Add object components without an input file under a dedicated group.

        Args:
            root_id: ID of the root node.
        """
        if not orphan_components:
            return

        group_id = "group:orphan_components"
        group_size = orphan_size

        self._add_node(
            label="(no input file)",
            parent=root_id,
            value=group_size,
            node_id=group_id,
            hover_text=f"No Input File Components<br>Size: {self._format_bytes(group_size)}",
        )

        for component in sorted(
            orphan_components, key=lambda x: x.size or 0, reverse=True
        ):
            component_id = f"comp:{component.id}"
            component_size = component.size or 0
            self._add_node(
                label=component.name or component.id,
                parent=group_id,
                value=component_size,
                node_id=component_id,
                hover_text=self._format_component_hover(component),
            )

    @staticmethod
    def _format_bytes(num_bytes: int) -> str:
        """Format byte count as human-readable string.

        Args:
            num_bytes: Number of bytes.

        Returns:
            Formatted string (e.g., "1.5 MB", "4.2 KB").
        """
        for unit in ["B", "KB", "MB", "GB"]:
            if num_bytes < 1024.0:
                return f"{num_bytes:.1f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.1f} TB"

    @staticmethod
    def _format_component_hover(component: ObjectComponent) -> str:
        """Format hover text for an object component.

        Args:
            component: ObjectComponent to format.

        Returns:
            Formatted hover text string.
        """
        lines = [f"Component: {component.name or component.id}"]
        if component.size:
            lines.append(f"Size: {IcicleBuilder._format_bytes(component.size)}")
        if component.load_address is not None:
            lines.append(f"Load: 0x{component.load_address:x}")
        if component.run_address is not None:
            lines.append(f"Run: 0x{component.run_address:x}")
        if component.readonly is not None:
            lines.append(f"Read-only: {component.readonly}")
        if component.executable is not None:
            lines.append(f"Executable: {component.executable}")
        return "<br>".join(lines)
