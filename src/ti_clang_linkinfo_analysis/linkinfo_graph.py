from typing import Dict, List, Tuple, Optional, Set
import webbrowser
import networkx as nx
from pyvis.network import Network

from ._models import LinkInfoData, ObjectComponent, InputFile, FolderNode


PSEUDO_NODE_ID = "__LINKER_GENERATED__"
PSEUDO_NODE_LABEL = "LINKER_GENERATED"

# Node type color constants
NODE_TYPE_INPUTFILE = "inputfile"
NODE_TYPE_FOLDER = "folder"
NODE_TYPE_COMPILER_GENERATED = "compiler_generated"

# Color scheme for node types
NODE_COLORS = {
    NODE_TYPE_INPUTFILE: "#4A90E2",  # Blue
    NODE_TYPE_FOLDER: "#7ED321",  # Green
    NODE_TYPE_COMPILER_GENERATED: "#F5A623",  # Orange
}


# Small helper classes so callers can do `net.options.nodes.scaling.max = 50`
class ScalingOptions:
    def __init__(self):
        self.min = 10
        self.max = 30


class NodeOptions:
    def __init__(self, scaling: Optional[ScalingOptions] = None):
        self.scaling = scaling or ScalingOptions()


class LinkInfoGraphBuilder:
    """Builds dependency graphs from linkinfo data.

    Creates networkx directed graphs showing dependencies between input files
    based on object component references. Supports folder grouping to collapse
    multiple input files into folder nodes.

    Attributes:
        data: The parsed linkinfo data.
        graph: The networkx DiGraph being constructed.
        folder_paths: Manual list of folder paths to group as nodes.
        auto_group_parent_folders: Whether to auto-group by discovered parent folders.
        min_size: Minimum size threshold for ungrouped input files.
        folder_to_inputfiles: Mapping from folder paths to input file IDs.
        inputfile_to_folder: Reverse mapping from input file IDs to folder paths.
        edge_details: Detailed information about component-level dependencies.
    """

    def __init__(
        self,
        data: LinkInfoData,
        folder_paths: Optional[List[str]] = None,
        auto_group_parent_folders: bool = False,
        min_size: int = 0,
    ):
        """Initialize the graph builder.

        Args:
            data: The parsed linkinfo data containing input files and components.
            folder_paths: Optional list of folder paths to group as nodes.
                Input files within these folders are collapsed into folder nodes.
                Files outside these folders remain as individual nodes.
                Use forward slashes (e.g., "src/drivers", "third_party/lwip").
            auto_group_parent_folders: If True, automatically groups input files
                by their parent folders discovered from input file paths.
                Can be combined with `folder_paths` for hybrid grouping.
                In hybrid mode, manual folders take precedence over automatic
                grouping for matching files.
            min_size: Minimum size in bytes for ungrouped input files.
                Files not in specified folders with size <= min_size are filtered out.
                Defaults to 0 (filters only empty files).
        """
        self.data = data
        self.graph = nx.DiGraph()

        # Folder grouping configuration
        self.folder_paths = folder_paths or []
        self.auto_group_parent_folders = auto_group_parent_folders
        self.min_size = min_size
        # Map: folder_path -> set of input_file ids in that folder
        self.folder_to_inputfiles: Dict[str, Set[str]] = {}
        # Map: input_file_id -> folder_path (reverse mapping)
        self.inputfile_to_folder: Dict[str, str] = {}

        # (src_node_id, dst_node_id) -> list of (src_comp, dst_comp, type)
        self.edge_details: Dict[Tuple[str, str], List[Tuple[str, str, str]]] = {}

        self._build_folder_mapping()

    # -------------------------------------------------------------

    def _normalize_folder_path(self, path: str) -> str:
        """Normalize folder path to use forward slashes and no trailing slash.

        Args:
            path: Folder path to normalize (may use backslashes or have trailing slash).

        Returns:
            Normalized path with forward slashes and no trailing slash.
        """
        return path.replace("\\", "/").rstrip("/")

    def _build_folder_mapping(self) -> None:
        """Build mappings between folders and input files."""
        if not self.folder_paths and not self.auto_group_parent_folders:
            return

        # Normalize and de-duplicate manual folder paths.
        normalized_folders = list(
            {
                self._normalize_folder_path(fp)
                for fp in self.folder_paths
                if self._normalize_folder_path(fp)
            }
        )

        # For each input file, determine the grouping folder (if any).
        for input_file in self.data.input_files.values():
            if not input_file.path:
                continue

            file_parent_folder = self._get_input_file_parent_folder(input_file)
            if not file_parent_folder:
                continue

            # Manual folder paths take precedence in hybrid mode.
            selected_folder = self._find_best_matching_manual_folder(
                file_parent_folder, normalized_folders
            )

            # Automatic mode groups by discovered parent folder.
            if selected_folder is None and self.auto_group_parent_folders:
                selected_folder = file_parent_folder

            if selected_folder is not None:
                if selected_folder not in self.folder_to_inputfiles:
                    self.folder_to_inputfiles[selected_folder] = set()
                self.folder_to_inputfiles[selected_folder].add(input_file.id)
                self.inputfile_to_folder[input_file.id] = selected_folder

    def _find_best_matching_manual_folder(
        self, file_parent_folder: str, manual_folders: List[str]
    ) -> Optional[str]:
        """Find the best matching manual folder for a file parent folder.

        Uses longest-prefix matching so nested folder paths map deterministically
        to the most specific manual folder.

        Args:
            file_parent_folder: Normalized parent folder for an input file.
            manual_folders: Normalized manual folder paths.

        Returns:
            Best matching manual folder path, or None if no match exists.
        """
        matches = [
            folder_path
            for folder_path in manual_folders
            if file_parent_folder == folder_path
            or file_parent_folder.startswith(folder_path + "/")
        ]
        if not matches:
            return None
        return max(matches, key=lambda p: (len(p), p))

    def _get_input_file_parent_folder(self, input_file: InputFile) -> Optional[str]:
        """Get a normalized parent folder for an input file.

        This handles two common variants from linker XML:
        - `input_file.path` already contains only the parent directory.
        - `input_file.path` contains a full path including filename.

        Args:
            input_file: Input file model from parsed linkinfo.

        Returns:
            Normalized parent folder path, or None if not derivable.
        """
        if not input_file.path:
            return None

        normalized_path = self._normalize_folder_path(input_file.path)
        if not normalized_path:
            return None

        file_name = (input_file.name or "").replace("\\", "/").split("/")[-1]
        if file_name:
            lower_path = normalized_path.lower()
            lower_name = file_name.lower()

            # Path is just the filename without folder.
            if lower_path == lower_name:
                return None

            # Path includes filename; strip it to get parent folder.
            suffix = "/" + lower_name
            if lower_path.endswith(suffix):
                parent = normalized_path[: -len(suffix)]
                return parent or None

        # Path is already a folder path.
        return normalized_path

    # -------------------------------------------------------------

    def build_graph(self) -> None:
        """Build the complete dependency graph.

        Constructs nodes (input files or folders) and edges (dependencies)
        from the linkinfo data. Must be called before exporting.

        The build process:
            1. Adds nodes (folders or individual input files)
            2. Processes component references to find dependencies
            3. Adds aggregated edges to the graph
        """
        self._add_nodes()
        self._process_component_references()
        self._add_edges_to_graph()

    # -------------------------------------------------------------

    def export_pyvis(self, output_html: str, *, show: bool = False) -> None:
        """Export graph as interactive PyVis HTML visualization.

        Creates an HTML file with an interactive graph using PyVis. The visualization
        includes zoom, pan, drag, and physics controls for exploring dependencies.

        Args:
            output_html: Path where the HTML file will be written.
            show: If True, automatically opens the HTML in default browser.
                Defaults to False.

        Note:
            Node sizes are scaled based on accumulated byte sizes. Edge tooltips
            show component-level dependency details.
        """
        net = Network(height="900px", width="100%", directed=True)

        # Nodes
        for node_id, data in self.graph.nodes(data=True):
            tooltip = self._generate_node_tooltip(node_id)
            node_color = data.get("color", NODE_COLORS[NODE_TYPE_INPUTFILE])
            net.add_node(
                node_id,
                label=data["label"],
                value=data["size"],  # controls node size
                title=tooltip,
                color=node_color,
            )

        # Edges
        for src, dst, data in self.graph.edges(data=True):
            details = data["details"]

            tooltip_lines = [f"{s}  →  {d}  ({t})" for s, d, t in details]
            tooltip = "\n".join(tooltip_lines)

            net.add_edge(
                src,
                dst,
                title=tooltip,
                arrows="to",
            )

        # ensure `net.options.nodes.scaling` exists so assignment works
        net.options.nodes = NodeOptions()
        # set node min/max size
        net.options.nodes.scaling.max = 60

        # set physics options
        net.options.physics.use_barnes_hut(
            {
                "gravity": -2000,
                "central_gravity": 0.3,
                "spring_length": 500,
                "spring_strength": 0.04,
                "damping": 0.3,
                "overlap": 0.5,
            }
        )

        # Show physics control panel
        net.show_buttons(filter_=["physics"])

        # Write to file
        net.write_html(output_html)

        # Optionally open in browser
        if show:
            webbrowser.open(output_html)

    def export_graphml(self, output_path: str) -> None:
        """Export graph as GraphML for external tools.

        Creates a GraphML file compatible with graph analysis tools like
        Gephi, yEd, and Cytoscape. All node and edge attributes are preserved.

        Args:
            output_path: Path where the GraphML file will be written.

        Note:
            Edge details (component-level dependencies) are converted to
            semicolon-separated strings for GraphML compatibility.
        """
        # Create a copy of the graph for GraphML export
        # GraphML doesn't support list attributes, so we convert details to strings
        g = self.graph.copy()

        for src, dst, data in g.edges(data=True):
            if "details" in data:
                details = data["details"]
                # Convert list of tuples to a readable string
                detail_strings = [f"{s} → {d} ({t})" for s, d, t in details]
                data["details"] = "; ".join(detail_strings)

        nx.write_graphml(g, output_path)

    # -------------------------------------------------------------
    # Internals
    # -------------------------------------------------------------

    def _generate_node_tooltip(self, node_id: str) -> str:
        """Generate a detailed tooltip showing all components in a node.

        Args:
            node_id: ID of the node (folder path, input file ID, or pseudo node).

        Returns:
            Multi-line string with node name, path, and component list with sizes.
        """
        lines = []
        comps = []

        if node_id == PSEUDO_NODE_ID:
            # Components without input file
            components = [
                comp
                for comp in self.data.object_components.values()
                if comp.input_file is None
            ]
            comps = sorted(components, key=lambda x: x.size or 0, reverse=True)
            lines.append(PSEUDO_NODE_LABEL)
        elif node_id in self.folder_to_inputfiles:
            # Folder node
            lines.append(f"Folder: {node_id}")
            lines.append(f"Input files ({len(self.folder_to_inputfiles[node_id])}):\n")

            # Get all input files in this folder and sort by size (descending)
            file_data = []
            for file_id in self.folder_to_inputfiles[node_id]:
                input_file = self.data.input_files.get(file_id)
                if input_file:
                    file_size = input_file.get_total_size()
                    file_data.append((input_file, file_size))

            # Sort by size descending
            file_data.sort(key=lambda x: x[1], reverse=True)

            # Add sorted input files to tooltip
            for input_file, file_size in file_data:
                lines.append(
                    f"  {input_file.name or input_file.id}  ({file_size} bytes)"
                )

            return "\n".join(lines)
        else:
            # Regular input file
            input_file = self.data.input_files.get(node_id)
            if input_file is None:
                return node_id

            lines.append(input_file.name or input_file.id)
            if input_file.path:
                lines.append(f"Path: {input_file.path}\n")

            comps = input_file.get_sorted_components()

        # Common component listing (for pseudo node and regular input files)
        if comps:
            for comp in comps:
                name = comp.name or comp.id
                size = comp.size or 0
                lines.append(f"{name}  (size: {size})")
        elif (
            node_id not in self.folder_to_inputfiles
        ):  # Don't show "No components" for folders
            lines.append("No components")

        return "\n".join(lines)

    def _add_nodes(self) -> None:
        """Add nodes to the graph: folder nodes or individual input file nodes.

        Creates nodes based on folder grouping configuration:
            - Folder nodes: Aggregate all input files in specified folders
            - Input file nodes: Individual files not in specified folders (filtered by min_size)
            - Pseudo node: Compiler-generated components without an input file

        Each node includes size, label, and color attributes.
        """
        added_as_folder = set()

        # Add folder nodes
        for folder_path, file_ids in self.folder_to_inputfiles.items():
            total_size = sum(
                self.data.input_files[fid].get_total_size()
                for fid in file_ids
                if fid in self.data.input_files
            )
            label = f"{folder_path}\n{total_size} bytes"

            self.graph.add_node(
                folder_path,
                label=label,
                size=total_size,
                color=NODE_COLORS[NODE_TYPE_FOLDER],
                node_type=NODE_TYPE_FOLDER,
            )
            added_as_folder.update(file_ids)

        # Add individual input file nodes (only those not in folders)
        for input_file in self.data.input_files.values():
            if input_file.id in added_as_folder:
                continue

            total_size = input_file.get_total_size()

            # Filter out small ungrouped input files
            if total_size <= self.min_size:
                continue

            label = f"{input_file.name}\n{total_size} bytes"

            self.graph.add_node(
                input_file.id,
                label=label,
                size=total_size,
                color=NODE_COLORS[NODE_TYPE_INPUTFILE],
                node_type=NODE_TYPE_INPUTFILE,
            )

        # Calculate size of pseudo node (components without input file)
        pseudo_node_size = sum(
            comp.size or 0
            for comp in self.data.object_components.values()
            if comp.input_file is None
        )

        # Pseudo node for components without input file
        pseudo_node_label = f"{PSEUDO_NODE_LABEL}\n{pseudo_node_size} bytes"
        self.graph.add_node(
            PSEUDO_NODE_ID,
            label=pseudo_node_label,
            size=pseudo_node_size if pseudo_node_size > 0 else 1,
            color=NODE_COLORS[NODE_TYPE_COMPILER_GENERATED],
            node_type=NODE_TYPE_COMPILER_GENERATED,
        )

    # -------------------------------------------------------------

    def _get_node_id(self, comp: ObjectComponent) -> str:
        """Get the node ID for a component (folder, input file, or pseudo node).

        Args:
            comp: Object component to look up.

        Returns:
            Node ID where this component belongs:
                - Folder path if component's input file is in a grouped folder
                - Input file ID if not in a grouped folder
                - Pseudo node ID if component has no input file
        """
        if comp.input_file is None:
            return PSEUDO_NODE_ID

        # Check if this input file is part of a folder node
        file_id = comp.input_file.id
        if file_id in self.inputfile_to_folder:
            return self.inputfile_to_folder[file_id]

        return file_id

    # -------------------------------------------------------------

    def _process_component_references(self) -> None:
        """Process component references and aggregate them into node-level edges.

        Examines refd_ro_sections and refd_rw_sections for each component,
        determines source and destination nodes, and accumulates edge details.
        Self-loops are ignored.
        """
        for comp in self.data.object_components.values():
            src_node_id = self._get_node_id(comp)

            refs = []
            refs.extend((r, "RO") for r in comp.refd_ro_sections)
            refs.extend((r, "RW") for r in comp.refd_rw_sections)

            for ref_id, ref_type in refs:
                target_comp = self.data.object_components.get(ref_id)
                if target_comp is None:
                    # debug or filtered component → ignore
                    continue

                dst_node_id = self._get_node_id(target_comp)

                # Ignore self loops
                if src_node_id == dst_node_id:
                    continue

                key = (src_node_id, dst_node_id)

                if key not in self.edge_details:
                    self.edge_details[key] = []

                self.edge_details[key].append(
                    (
                        comp.name or comp.id,
                        target_comp.name or target_comp.id,
                        ref_type,
                    )
                )

    # -------------------------------------------------------------

    def _add_edges_to_graph(self) -> None:
        """Add aggregated edges to the graph.

        Adds edges from edge_details dictionary to the networkx graph,
        filtering out edges where source or destination nodes don't exist
        (may have been filtered by min_size threshold).
        """
        for (src, dst), details in self.edge_details.items():
            # Only add edge if both nodes exist in the graph (they may have been filtered)
            if src in self.graph and dst in self.graph:
                self.graph.add_edge(src, dst, details=details)


if __name__ == "__main__":
    from ._xml_parser import LinkInfoXmlParser

    data = LinkInfoXmlParser(
        "example_files/enet_cli_debug_linkinfo.xml", filter_debug=True
    ).parse()

    builder = LinkInfoGraphBuilder(data)
    builder.build_graph()
    builder.export_pyvis("outputs/inputfile_graph.html")
