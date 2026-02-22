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
    def __init__(
        self,
        data: LinkInfoData,
        folder_paths: Optional[List[str]] = None,
        min_size: int = 0,
    ):
        """Initialize the graph builder.

        Args:
            data: The parsed linkinfo data.
            folder_paths: Optional list of folder paths to show as grouped nodes.
                All input files in these folders will be collapsed into folder nodes.
                Input files not in these folders remain as individual nodes.
                Paths should use forward slashes (e.g., "src/drivers").
            min_size: Minimum size threshold (in bytes) for ungrouped input files to be shown.
                Input files not in folders with size <= min_size will be filtered out.
                Default is 0, which filters out empty files.
        """
        self.data = data
        self.graph = nx.DiGraph()

        # Folder grouping configuration
        self.folder_paths = folder_paths or []
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
        """Normalize folder path to use forward slashes and no trailing slash."""
        return path.replace("\\", "/").rstrip("/")

    def _build_folder_mapping(self) -> None:
        """Build mappings between folders and input files."""
        if not self.folder_paths:
            return

        # Normalize all folder paths
        normalized_folders = [
            self._normalize_folder_path(fp) for fp in self.folder_paths
        ]

        # For each input file, check if it belongs to one of the specified folders
        for input_file in self.data.input_files.values():
            if not input_file.path:
                continue

            normalized_file_path = self._normalize_folder_path(input_file.path)

            # Check if this file is in one of the specified folders
            for folder_path in normalized_folders:
                # Check if the file path starts with the folder path
                if (
                    normalized_file_path == folder_path
                    or normalized_file_path.startswith(folder_path + "/")
                ):
                    # Add to mapping
                    if folder_path not in self.folder_to_inputfiles:
                        self.folder_to_inputfiles[folder_path] = set()
                    self.folder_to_inputfiles[folder_path].add(input_file.id)
                    self.inputfile_to_folder[input_file.id] = folder_path
                    break  # Each input file belongs to at most one folder

    # -------------------------------------------------------------

    def build_graph(self) -> None:
        self._add_nodes()
        self._process_component_references()
        self._add_edges_to_graph()

    # -------------------------------------------------------------

    def export_pyvis(self, output_html: str, *, show: bool = False) -> None:
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

    # Optional: for Gephi
    def export_graphml(self, output_path: str) -> None:
        """Export graph as GraphML.

        Note: Edge details are converted to strings for GraphML compatibility.
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
        """Generate a detailed tooltip showing all components in a node."""
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
        """Add nodes to the graph: either folder nodes or individual input-file nodes."""
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
        """Get the node ID for a component (either folder, input-file, or pseudo node)."""
        if comp.input_file is None:
            return PSEUDO_NODE_ID

        # Check if this input file is part of a folder node
        file_id = comp.input_file.id
        if file_id in self.inputfile_to_folder:
            return self.inputfile_to_folder[file_id]

        return file_id

    # -------------------------------------------------------------

    def _process_component_references(self) -> None:
        """Process component references and aggregate them into node-level edges."""
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
        for (src, dst), details in self.edge_details.items():
            # Only add edge if both nodes exist in the graph (they may have been filtered)
            if src in self.graph and dst in self.graph:
                self.graph.add_edge(src, dst, details=details)


if __name__ == "__main__":
    parser = LinkInfoParser(
        "example_files/enet_cli_debug_linkinfo.xml", filter_debug=True
    )

    builder = LinkInfoGraphBuilder(parser)
    builder.build_graph()
    builder.export_pyvis("outputs/inputfile_graph.html")
