"""Tests for graph analysis with folder grouping."""

import tempfile
from pathlib import Path

import pytest
import networkx as nx

from ti_clang_linkinfo_analysis import LinkInfoAnalyzer


@pytest.fixture
def dpl_analyzer(example_files):
    """Analyzer for dpl_demo debug linkinfo."""
    return LinkInfoAnalyzer(str(example_files["dpl_demo_debug"]), filter_debug=True)


@pytest.fixture
def enet_analyzer(example_files):
    """Analyzer for enet_cli debug linkinfo."""
    return LinkInfoAnalyzer(str(example_files["enet_cli_debug"]), filter_debug=True)


class TestBasicInputFileGraph:
    """Test basic input-file level graph without folder grouping."""

    def test_graph_has_nodes(self, dpl_analyzer):
        """Test that basic graph has input file nodes."""
        from ti_clang_linkinfo_analysis.linkinfo_graph import LinkInfoGraphBuilder

        builder = LinkInfoGraphBuilder(dpl_analyzer._data)
        builder.build_graph()

        # Should have nodes for input files + pseudo node
        assert builder.graph.number_of_nodes() > 0
        assert (
            builder.graph.number_of_nodes() == len(dpl_analyzer._data.input_files) + 1
        )

    def test_graph_has_edges(self, dpl_analyzer):
        """Test that graph has edges between input files."""
        from ti_clang_linkinfo_analysis.linkinfo_graph import LinkInfoGraphBuilder

        builder = LinkInfoGraphBuilder(dpl_analyzer._data)
        builder.build_graph()

        # Should have edges from component references
        assert builder.graph.number_of_edges() > 0

    def test_nodes_have_size_attribute(self, dpl_analyzer):
        """Test that nodes have size attribute."""
        from ti_clang_linkinfo_analysis.linkinfo_graph import LinkInfoGraphBuilder

        builder = LinkInfoGraphBuilder(dpl_analyzer._data)
        builder.build_graph()

        for node, data in builder.graph.nodes(data=True):
            assert "size" in data
            assert data["size"] >= 0

    def test_nodes_have_label_attribute(self, dpl_analyzer):
        """Test that nodes have label attribute."""
        from ti_clang_linkinfo_analysis.linkinfo_graph import LinkInfoGraphBuilder

        builder = LinkInfoGraphBuilder(dpl_analyzer._data)
        builder.build_graph()

        for node, data in builder.graph.nodes(data=True):
            assert "label" in data
            assert isinstance(data["label"], str)

    def test_edges_have_details(self, dpl_analyzer):
        """Test that edges have details about component references."""
        from ti_clang_linkinfo_analysis.linkinfo_graph import LinkInfoGraphBuilder

        builder = LinkInfoGraphBuilder(dpl_analyzer._data)
        builder.build_graph()

        for src, dst, data in builder.graph.edges(data=True):
            assert "details" in data
            assert isinstance(data["details"], list)
            assert len(data["details"]) > 0


class TestFolderGrouping:
    """Test folder grouping functionality."""

    def test_folder_node_created(self, dpl_analyzer):
        """Test that folder nodes are created for specified paths."""
        from ti_clang_linkinfo_analysis.linkinfo_graph import LinkInfoGraphBuilder

        folder_paths = [
            "C:/ti/mcu_plus_sdk_am243x_11_02_00_24/source/kernel/freertos/lib"
        ]
        builder = LinkInfoGraphBuilder(dpl_analyzer._data, folder_paths=folder_paths)
        builder.build_graph()

        # Folder should be a node
        normalized_folder = folder_paths[0].replace("\\", "/").rstrip("/")
        assert normalized_folder in builder.graph.nodes()

    def test_input_files_removed_from_nodes(self, dpl_analyzer):
        """Test that input files in folders are not individual nodes."""
        from ti_clang_linkinfo_analysis.linkinfo_graph import LinkInfoGraphBuilder

        folder_paths = [
            "C:/ti/mcu_plus_sdk_am243x_11_02_00_24/source/kernel/freertos/lib"
        ]

        # Build graph without folders
        builder_no_folders = LinkInfoGraphBuilder(dpl_analyzer._data)
        builder_no_folders.build_graph()
        nodes_without_folders = set(builder_no_folders.graph.nodes())

        # Build graph with folders
        builder_with_folders = LinkInfoGraphBuilder(
            dpl_analyzer._data, folder_paths=folder_paths
        )
        builder_with_folders.build_graph()
        nodes_with_folders = set(builder_with_folders.graph.nodes())

        # Should have fewer nodes when grouping by folder
        assert len(nodes_with_folders) < len(nodes_without_folders)

    def test_folder_size_accumulation(self, dpl_analyzer):
        """Test that folder node size equals sum of input files."""
        from ti_clang_linkinfo_analysis.linkinfo_graph import LinkInfoGraphBuilder

        folder_path = "C:/ti/mcu_plus_sdk_am243x_11_02_00_24/source/kernel/freertos/lib"
        folder_paths = [folder_path]

        builder = LinkInfoGraphBuilder(dpl_analyzer._data, folder_paths=folder_paths)
        builder.build_graph()

        # Get folder node size
        normalized_folder = folder_path.replace("\\", "/").rstrip("/")
        folder_size = builder.graph.nodes[normalized_folder]["size"]

        # Calculate expected size from input files in this folder
        expected_size = sum(
            dpl_analyzer._data.input_files[fid].get_total_size()
            for fid in builder.folder_to_inputfiles.get(normalized_folder, set())
            if fid in dpl_analyzer._data.input_files
        )

        assert folder_size == expected_size
        assert folder_size > 0

    def test_multiple_folder_grouping(self, dpl_analyzer):
        """Test grouping with multiple folders."""
        from ti_clang_linkinfo_analysis.linkinfo_graph import LinkInfoGraphBuilder

        folder_paths = [
            "C:/ti/mcu_plus_sdk_am243x_11_02_00_24/source/kernel/freertos/lib",
            "C:/ti/mcu_plus_sdk_am243x_11_02_00_24/source/drivers/lib",
        ]

        builder = LinkInfoGraphBuilder(dpl_analyzer._data, folder_paths=folder_paths)
        builder.build_graph()

        # Both folders should be nodes
        for folder_path in folder_paths:
            normalized = folder_path.replace("\\", "/").rstrip("/")
            if builder.folder_to_inputfiles.get(normalized):  # Only if folder has files
                assert normalized in builder.graph.nodes()

    def test_edges_aggregate_to_folders(self, dpl_analyzer):
        """Test that edges correctly aggregate from files to folders."""
        from ti_clang_linkinfo_analysis.linkinfo_graph import LinkInfoGraphBuilder

        folder_paths = [
            "C:/ti/mcu_plus_sdk_am243x_11_02_00_24/source/kernel/freertos/lib"
        ]

        builder = LinkInfoGraphBuilder(dpl_analyzer._data, folder_paths=folder_paths)
        builder.build_graph()

        # Check that edges exist
        assert builder.graph.number_of_edges() > 0

        # Edges should have details
        for src, dst, data in builder.graph.edges(data=True):
            assert "details" in data
            assert len(data["details"]) > 0

    def test_windows_and_unix_path_normalization(self, dpl_analyzer):
        """Test that both Windows and Unix style paths work."""
        from ti_clang_linkinfo_analysis.linkinfo_graph import LinkInfoGraphBuilder

        # Both should work and be equivalent
        folder_path_win = (
            "C:\\ti\\mcu_plus_sdk_am243x_11_02_00_24\\source\\kernel\\freertos\\lib"
        )
        folder_path_unix = (
            "C:/ti/mcu_plus_sdk_am243x_11_02_00_24/source/kernel/freertos/lib"
        )

        builder_win = LinkInfoGraphBuilder(
            dpl_analyzer._data, folder_paths=[folder_path_win]
        )
        builder_win.build_graph()

        builder_unix = LinkInfoGraphBuilder(
            dpl_analyzer._data, folder_paths=[folder_path_unix]
        )
        builder_unix.build_graph()

        # Should produce same graph structure
        assert (
            builder_win.graph.number_of_nodes() == builder_unix.graph.number_of_nodes()
        )
        assert (
            builder_win.graph.number_of_edges() == builder_unix.graph.number_of_edges()
        )

    def test_no_self_loops(self, dpl_analyzer):
        """Test that graphs don't have self-loops."""
        from ti_clang_linkinfo_analysis.linkinfo_graph import LinkInfoGraphBuilder

        folder_paths = [
            "C:/ti/mcu_plus_sdk_am243x_11_02_00_24/source/kernel/freertos/lib"
        ]

        builder = LinkInfoGraphBuilder(dpl_analyzer._data, folder_paths=folder_paths)
        builder.build_graph()

        # Check for self-loops
        for src, dst in builder.graph.edges():
            assert src != dst, f"Found self-loop: {src} -> {dst}"


class TestGraphExports:
    """Test graph export functionality."""

    def test_pyvis_export_basic(self, dpl_analyzer, tmp_path):
        """Test pyvis HTML export without folder grouping."""
        output_file = tmp_path / "test_graph.html"
        dpl_analyzer.export_inputfile_graph_pyvis(str(output_file))

        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_pyvis_export_with_folders(self, dpl_analyzer, tmp_path):
        """Test pyvis HTML export with folder grouping."""
        output_file = tmp_path / "test_graph_folders.html"
        folder_paths = [
            "C:/ti/mcu_plus_sdk_am243x_11_02_00_24/source/kernel/freertos/lib"
        ]

        dpl_analyzer.export_inputfile_graph_pyvis(
            str(output_file), folder_paths=folder_paths
        )

        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_graphml_export_basic(self, dpl_analyzer, tmp_path):
        """Test GraphML export without folder grouping."""
        output_file = tmp_path / "test_graph.graphml"
        dpl_analyzer.export_inputfile_graph_graphml(str(output_file))

        assert output_file.exists()
        assert output_file.stat().st_size > 0

        # Verify it's valid GraphML by reading it back
        g = nx.read_graphml(str(output_file))
        assert g.number_of_nodes() > 0

    def test_graphml_export_with_folders(self, dpl_analyzer, tmp_path):
        """Test GraphML export with folder grouping."""
        output_file = tmp_path / "test_graph_folders.graphml"
        folder_paths = [
            "C:/ti/mcu_plus_sdk_am243x_11_02_00_24/source/kernel/freertos/lib"
        ]

        dpl_analyzer.export_inputfile_graph_graphml(
            str(output_file), folder_paths=folder_paths
        )

        assert output_file.exists()
        assert output_file.stat().st_size > 0

        # Verify it's valid GraphML
        g = nx.read_graphml(str(output_file))
        assert g.number_of_nodes() > 0

    def test_graphml_edge_details_are_strings(self, dpl_analyzer, tmp_path):
        """Test that GraphML export converts edge details to strings."""
        output_file = tmp_path / "test_graph.graphml"
        dpl_analyzer.export_inputfile_graph_graphml(str(output_file))

        # Read back and check edge attributes
        g = nx.read_graphml(str(output_file))

        for src, dst, data in g.edges(data=True):
            if "details" in data:
                # Should be a string in GraphML
                assert isinstance(data["details"], str)


class TestLargerProject:
    """Test with larger enet_cli project."""

    def test_enet_basic_graph(self, enet_analyzer):
        """Test basic graph generation on larger project."""
        from ti_clang_linkinfo_analysis.linkinfo_graph import LinkInfoGraphBuilder

        builder = LinkInfoGraphBuilder(enet_analyzer._data)
        builder.build_graph()

        # Should have many nodes for larger project
        assert builder.graph.number_of_nodes() > 50
        assert builder.graph.number_of_edges() > 0

    def test_enet_with_folders(self, enet_analyzer, tmp_path):
        """Test folder grouping on larger project."""
        folder_paths = [
            "C:/ti/mcu_plus_sdk_am243x_11_02_00_24/source/kernel",
            "C:/ti/mcu_plus_sdk_am243x_11_02_00_24/source/drivers",
        ]

        output_file = tmp_path / "enet_graph_folders.html"
        enet_analyzer.export_inputfile_graph_pyvis(
            str(output_file), folder_paths=folder_paths
        )

        assert output_file.exists()
        assert output_file.stat().st_size > 0
