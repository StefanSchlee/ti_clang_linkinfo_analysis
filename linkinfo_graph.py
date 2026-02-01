# linkinfo_graph.py

from typing import Dict, List, Tuple
import networkx as nx
from pyvis.network import Network

# Adjust this import to your actual parser filename
from linkinfo_parser import LinkInfoParser, ObjectComponent


PSEUDO_NODE_ID = "__LINKER_GENERATED__"
PSEUDO_NODE_LABEL = "LINKER_GENERATED"


class LinkInfoGraphBuilder:
    def __init__(self, parser: LinkInfoParser):
        self.parser = parser
        self.graph = nx.DiGraph()

        # (src_file_id, dst_file_id) -> list of (src_comp, dst_comp, type)
        self.edge_details: Dict[Tuple[str, str], List[Tuple[str, str, str]]] = {}

    # -------------------------------------------------------------

    def build_graph(self) -> None:
        self._add_nodes()
        self._process_component_references()
        self._add_edges_to_graph()

    # -------------------------------------------------------------

    def export_pyvis(self, output_html: str) -> None:
        net = Network(height="900px", width="100%", directed=True)

        # Nodes
        for node_id, data in self.graph.nodes(data=True):
            net.add_node(
                node_id,
                label=data["label"],
                value=data["size"],  # controls node size
                title=data["label"],
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

        net.show(output_html, notebook=False)

    # Optional: for Gephi
    def export_graphml(self, output_path: str) -> None:
        nx.write_graphml(self.graph, output_path)

    # -------------------------------------------------------------
    # Internals
    # -------------------------------------------------------------

    def _add_nodes(self) -> None:
        for input_file in self.parser.input_files.values():
            total_size = input_file.get_total_size()
            label = f"{input_file.name}\n{total_size} bytes"

            self.graph.add_node(
                input_file.id,
                label=label,
                size=total_size,
            )

        # Calculate size of pseudo node (components without input file)
        pseudo_node_size = sum(
            comp.size or 0
            for comp in self.parser.object_components.values()
            if comp.input_file is None
        )

        # Pseudo node for components without input file
        pseudo_node_label = f"{PSEUDO_NODE_LABEL}\n{pseudo_node_size} bytes"
        self.graph.add_node(
            PSEUDO_NODE_ID,
            label=pseudo_node_label,
            size=pseudo_node_size if pseudo_node_size > 0 else 1,
        )

    # -------------------------------------------------------------

    def _get_inputfile_id(self, comp: ObjectComponent) -> str:
        if comp.input_file is None:
            return PSEUDO_NODE_ID
        return comp.input_file.id

    # -------------------------------------------------------------

    def _process_component_references(self) -> None:
        for comp in self.parser.object_components.values():
            src_file_id = self._get_inputfile_id(comp)

            refs = []
            refs.extend((r, "RO") for r in comp.refd_ro_sections)
            refs.extend((r, "RW") for r in comp.refd_rw_sections)

            for ref_id, ref_type in refs:
                target_comp = self.parser.object_components.get(ref_id)
                if target_comp is None:
                    # debug or filtered component → ignore
                    continue

                dst_file_id = self._get_inputfile_id(target_comp)

                # Ignore self loops
                if src_file_id == dst_file_id:
                    continue

                key = (src_file_id, dst_file_id)

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
            self.graph.add_edge(src, dst, details=details)


if __name__ == "__main__":
    parser = LinkInfoParser(
        "example_files/dpl_demo_release_linkinfo.xml", filter_debug=True
    )

    builder = LinkInfoGraphBuilder(parser)
    builder.build_graph()
    builder.export_pyvis("outputs/inputfile_graph.html")
