"""Unit tests for icicle plot visualization."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from ti_clang_linkinfo_analysis import LinkInfoAnalyzer
from ti_clang_linkinfo_analysis._icicle import IcicleBuilder


class TestIcicleBuilder:
    """Test IcicleBuilder functionality."""

    def test_icicle_builder_initialization(
        self, example_files: dict[str, Path]
    ) -> None:
        """Test that IcicleBuilder can be initialized with LinkInfoData."""
        xml_path = example_files["dpl_demo_debug"]
        analyzer = LinkInfoAnalyzer(str(xml_path), filter_debug=True)
        builder = IcicleBuilder(analyzer._data)

        assert builder is not None
        assert builder._data == analyzer._data

    def test_icicle_figure_creation(self, example_files: dict[str, Path]) -> None:
        """Test that an icicle figure can be built without errors."""
        xml_path = example_files["dpl_demo_debug"]
        analyzer = LinkInfoAnalyzer(str(xml_path), filter_debug=True)
        builder = IcicleBuilder(analyzer._data)

        fig = builder._build_figure()

        assert fig is not None
        assert len(fig.data) > 0
        assert fig.data[0].type == "icicle"

    def test_icicle_figure_has_data(self, example_files: dict[str, Path]) -> None:
        """Test that the figure contains labels, values, and hierarchy."""
        xml_path = example_files["dpl_demo_debug"]
        analyzer = LinkInfoAnalyzer(str(xml_path), filter_debug=True)
        builder = IcicleBuilder(analyzer._data)

        fig = builder._build_figure()
        icicle_data = fig.data[0]

        # Should have labels and parents (hierarchy)
        assert len(icicle_data.labels) > 0
        assert len(icicle_data.parents) > 0
        # Parents should match labels length
        assert len(icicle_data.parents) == len(icicle_data.labels)
        # Values should exist and be non-negative
        assert len(icicle_data.values) > 0
        assert all(v >= 0 for v in icicle_data.values)
        # At least the root and some children should have positive size
        assert any(v > 0 for v in icicle_data.values)

    def test_export_html(self, example_files: dict[str, Path]) -> None:
        """Test that HTML can be exported successfully."""
        xml_path = example_files["dpl_demo_debug"]
        analyzer = LinkInfoAnalyzer(str(xml_path), filter_debug=True)

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_icicle.html"
            builder = IcicleBuilder(analyzer._data)
            builder.export_html(str(output_path), show=False)

            # Check that file was created
            assert output_path.exists()
            # Check that it contains HTML content
            content = output_path.read_text()
            assert "<!DOCTYPE html>" in content or "<html" in content
            assert "plotly" in content.lower()


class TestLinkInfoAnalyzerIcicle:
    """Test LinkInfoAnalyzer icicle export interface."""

    def test_export_icicle_plot(self, example_files: dict[str, Path]) -> None:
        """Test the public API for exporting icicle plots."""
        xml_path = example_files["dpl_demo_debug"]
        analyzer = LinkInfoAnalyzer(str(xml_path), filter_debug=True)

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_icicle.html"
            analyzer.export_icicle_plot(str(output_path), show=False)

            assert output_path.exists()
            content = output_path.read_text()
            assert "plotly" in content.lower()

    def test_export_icicle_with_larger_project(
        self, example_files: dict[str, Path]
    ) -> None:
        """Test icicle export with a larger example file."""
        xml_path = example_files["enet_cli_debug"]
        analyzer = LinkInfoAnalyzer(str(xml_path), filter_debug=True)

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "enet_icicle.html"
            analyzer.export_icicle_plot(str(output_path), show=False)

            assert output_path.exists()
            content = output_path.read_text()
            assert "<!DOCTYPE html>" in content or "<html" in content


class TestIcicleDataFormatting:
    """Test helper methods for data formatting."""

    def test_format_bytes(self) -> None:
        """Test byte formatting helper."""
        assert IcicleBuilder._format_bytes(0) == "0.0 B"
        assert IcicleBuilder._format_bytes(512) == "512.0 B"
        assert IcicleBuilder._format_bytes(1024) == "1.0 KB"
        assert IcicleBuilder._format_bytes(1536) == "1.5 KB"
        assert IcicleBuilder._format_bytes(1024 * 1024) == "1.0 MB"
        assert IcicleBuilder._format_bytes(1024 * 1024 * 1024) == "1.0 GB"

    def test_format_component_hover(self, example_files: dict[str, Path]) -> None:
        """Test hover text formatting for components."""
        xml_path = example_files["dpl_demo_debug"]
        analyzer = LinkInfoAnalyzer(str(xml_path), filter_debug=True)

        # Get first component from data
        if analyzer._data.object_components:
            component = next(iter(analyzer._data.object_components.values()))
            hover_text = IcicleBuilder._format_component_hover(component)

            assert isinstance(hover_text, str)
            assert "Component:" in hover_text
            assert len(hover_text) > 0


class TestIcicleHierarchy:
    """Test that icicle correctly builds the hierarchy."""

    def test_hierarchy_depth(self, example_files: dict[str, Path]) -> None:
        """Test that the hierarchy includes folders, files, and components."""
        xml_path = example_files["dpl_demo_debug"]
        analyzer = LinkInfoAnalyzer(str(xml_path), filter_debug=True)
        builder = IcicleBuilder(analyzer._data)

        fig = builder._build_figure()
        icicle_data = fig.data[0]

        # Should have at least root, some files, and some components
        assert len(icicle_data.labels) >= 3

        # Check that hierarchy is correct: root -> folders/files -> components
        # Root should have empty parent
        assert icicle_data.parents[0] == ""

    def test_accumulated_sizes(self, example_files: dict[str, Path]) -> None:
        """Test that accumulated sizes are correctly computed."""
        xml_path = example_files["dpl_demo_debug"]
        analyzer = LinkInfoAnalyzer(str(xml_path), filter_debug=True)
        builder = IcicleBuilder(analyzer._data)

        fig = builder._build_figure()
        icicle_data = fig.data[0]

        # All values should be non-negative integers
        assert all(isinstance(v, int) and v >= 0 for v in icicle_data.values)

        # Root value should be positive (sum of all components)
        assert icicle_data.values[0] > 0
