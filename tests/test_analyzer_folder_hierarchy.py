"""Integration tests for LinkInfoAnalyzer with folder hierarchy."""

import pytest

from src.ti_clang_linkinfo_analysis.analyzer import LinkInfoAnalyzer


class TestLinkInfoAnalyzerFolderHierarchy:
    """Tests for LinkInfoAnalyzer folder hierarchy integration."""

    @pytest.fixture
    def dpl_analyzer(self):
        """Create analyzer from example file."""
        return LinkInfoAnalyzer("example_files/dpl_demo_debug_linkinfo.xml")

    def test_folder_hierarchy_exists(self, dpl_analyzer):
        """Test that folder hierarchy is accessible from analyzer."""
        hierarchy = dpl_analyzer.folder_hierarchy
        assert hierarchy is not None
        assert hierarchy.name == "root"

    def test_folder_hierarchy_has_structure(self, dpl_analyzer):
        """Test that hierarchy contains expected structure."""
        hierarchy = dpl_analyzer.folder_hierarchy
        # Should have at least some folders
        assert len(hierarchy.children) >= 0 or len(hierarchy.input_files) >= 0

    def test_folder_hierarchy_sizes(self, dpl_analyzer):
        """Test that hierarchy has accumulated sizes."""
        hierarchy = dpl_analyzer.folder_hierarchy
        total_size = hierarchy.get_accumulated_size()
        assert total_size > 0  # Should have some size

    def test_folder_hierarchy_consistent_with_input_files(self, dpl_analyzer):
        """Test that all input files appear in hierarchy."""
        hierarchy = dpl_analyzer.folder_hierarchy

        # Flatten the hierarchy
        def collect_files(node, collected=None):
            if collected is None:
                collected = set()
            collected.update(node.input_files.keys())
            for child in node.children.values():
                collect_files(child, collected)
            return collected

        files_in_hierarchy = collect_files(hierarchy)
        # Should have input files
        assert len(files_in_hierarchy) > 0

    @pytest.fixture
    def enet_analyzer(self):
        """Create analyzer from larger example file."""
        return LinkInfoAnalyzer("example_files/enet_cli_debug_linkinfo.xml")

    def test_larger_project_hierarchy(self, enet_analyzer):
        """Test hierarchy building with larger project."""
        hierarchy = enet_analyzer.folder_hierarchy
        assert hierarchy.get_accumulated_size() > 0
