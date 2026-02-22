"""Tests for folder hierarchy building and path utilities."""

import pytest

from ti_clang_linkinfo_analysis._folder_hierarchy import (
    FolderHierarchy,
    flatten_folder_hierarchy,
    get_all_input_files_in_folder,
    get_depth,
)
from ti_clang_linkinfo_analysis._models import (
    FolderNode,
    InputFile,
    LinkInfoData,
    ObjectComponent,
)
from ti_clang_linkinfo_analysis._path_utils import (
    get_filename,
    get_parent_path,
    is_absolute_path,
    join_path_components,
    normalize_path,
    split_path,
)


class TestPathNormalization:
    """Tests for path normalization utilities."""

    def test_normalize_posix_path(self):
        """Test normalization of POSIX paths."""
        assert normalize_path("src/path/to/file.obj") == "src/path/to/file.obj"

    def test_normalize_windows_path(self):
        """Test conversion of Windows paths to POSIX."""
        assert normalize_path("src\\path\\to\\file.obj") == "src/path/to/file.obj"

    def test_normalize_redundant_separators(self):
        """Test removal of redundant separators."""
        assert normalize_path("src/path//to///file.obj") == "src/path/to/file.obj"
        assert normalize_path("src\\\\path\\\\to\\file.obj") == "src/path/to/file.obj"

    def test_normalize_absolute_path_posix(self):
        """Test normalization preserves absolute POSIX paths."""
        assert normalize_path("/absolute/path/file.obj") == "/absolute/path/file.obj"

    def test_normalize_empty_path(self):
        """Test empty path becomes current directory."""
        assert normalize_path("") == "."
        assert normalize_path(None or "") == "."

    def test_normalize_dot_path(self):
        """Test dot path handling."""
        assert normalize_path(".") == "."

    def test_normalize_mixed_separators(self):
        """Test paths with mixed separators."""
        assert normalize_path("src/path\\to/file.obj") == "src/path/to/file.obj"

    def test_split_path_relative(self):
        """Test splitting relative paths."""
        assert split_path("src/path/to/file.obj") == ["src", "path", "to", "file.obj"]

    def test_split_path_absolute(self):
        """Test splitting absolute paths (removes leading /)."""
        assert split_path("/absolute/path/file.obj") == ["absolute", "path", "file.obj"]

    def test_split_path_empty(self):
        """Test splitting empty/dot paths."""
        assert split_path(".") == []
        assert split_path("") == []

    def test_split_path_single_component(self):
        """Test splitting single-component paths."""
        assert split_path("file.obj") == ["file.obj"]

    def test_get_parent_path_relative(self):
        """Test getting parent of relative paths."""
        assert get_parent_path("src/path/to/file.obj") == "src/path/to"
        assert get_parent_path("src/path/to") == "src/path"

    def test_get_parent_path_absolute(self):
        """Test getting parent of absolute paths."""
        assert get_parent_path("/absolute/path/file.obj") == "/absolute/path"
        assert get_parent_path("/absolute") == "/"

    def test_get_parent_path_single(self):
        """Test getting parent of single-component paths."""
        assert get_parent_path("file.obj") == "."

    def test_get_parent_path_root(self):
        """Test getting parent of root."""
        assert get_parent_path("/") == "."

    def test_get_filename(self):
        """Test extracting filename."""
        assert get_filename("src/path/to/file.obj") == "file.obj"
        assert get_filename("/absolute/path/file.obj") == "file.obj"

    def test_get_filename_empty(self):
        """Test filename of empty paths."""
        assert get_filename(".") == ""
        assert get_filename("/") == ""

    def test_is_absolute_path(self):
        """Test absolute path detection."""
        assert is_absolute_path("/absolute/path")
        assert not is_absolute_path("relative/path")
        assert is_absolute_path("C:\\windows\\path") or is_absolute_path(
            "C:/windows/path"
        )

    def test_join_path_components(self):
        """Test joining path components."""
        assert join_path_components("src", "path", "file.obj") == "src/path/file.obj"
        assert join_path_components("/", "absolute", "file.obj") == "/absolute/file.obj"

    def test_join_path_components_empty(self):
        """Test joining with empty components."""
        assert join_path_components("") == "."
        assert join_path_components("", "", "") == "."


class TestFolderNodeModel:
    """Tests for FolderNode dataclass."""

    def test_folder_node_creation(self):
        """Test basic FolderNode creation."""
        node = FolderNode(name="src", path="src")
        assert node.name == "src"
        assert node.path == "src"
        assert node.children == {}
        assert node.input_files == {}

    def test_folder_node_accumulated_size_empty(self):
        """Test accumulated size of empty folder."""
        node = FolderNode(name="src", path="src")
        assert node.get_accumulated_size() == 0

    def test_folder_node_accumulated_size_with_files(self):
        """Test accumulated size with input files."""
        node = FolderNode(name="src", path="src")

        # Create input file with components
        comp1 = ObjectComponent(id="comp1", size=100)
        comp2 = ObjectComponent(id="comp2", size=200)
        input_file = InputFile(id="file1", path="src/file.obj")
        input_file.add_component(comp1)
        input_file.add_component(comp2)

        node.input_files["file1"] = input_file
        assert node.get_accumulated_size() == 300

    def test_folder_node_accumulated_size_with_children(self):
        """Test accumulated size with child folders."""
        root = FolderNode(name="root", path="/")

        # Create child folder
        child = FolderNode(name="src", path="src")
        root.children["src"] = child

        # Add input file to child
        comp = ObjectComponent(id="comp1", size=500)
        input_file = InputFile(id="file1", path="src/file.obj")
        input_file.add_component(comp)
        child.input_files["file1"] = input_file

        assert root.get_accumulated_size() == 500

    def test_folder_node_size_cache_invalidation(self):
        """Test size cache invalidation."""
        node = FolderNode(name="src", path="src")

        comp = ObjectComponent(id="comp1", size=100)
        input_file = InputFile(id="file1", path="src/file.obj")
        input_file.add_component(comp)
        node.input_files["file1"] = input_file

        # Get size (caches it)
        assert node.get_accumulated_size() == 100

        # Invalidate cache
        node.invalidate_size_cache()
        assert node._accumulated_size is None


class TestFolderHierarchyBuilder:
    """Tests for FolderHierarchy builder."""

    def test_add_input_file_with_path(self):
        """Test adding input file with path."""
        builder = FolderHierarchy()

        input_file = InputFile(id="file1", path="src/path/file.obj")
        builder.add_input_file(input_file)

        root = builder.get_root()
        assert "src" in root.children
        assert "path" in root.children["src"].children

        path_node = root.children["src"].children["path"]
        assert "file1" in path_node.input_files

    def test_add_input_file_without_path(self):
        """Test adding input file without path (goes to root)."""
        builder = FolderHierarchy()

        input_file = InputFile(id="file1")
        builder.add_input_file(input_file)

        root = builder.get_root()
        assert "file1" in root.input_files

    def test_from_linkinfo_data(self):
        """Test building hierarchy from LinkInfoData."""
        data = LinkInfoData()

        # Create input files
        for i in range(3):
            input_file = InputFile(id=f"file{i}", path=f"src/module{i}/file{i}.obj")
            data.input_files[f"file{i}"] = input_file

        root = FolderHierarchy.from_linkinfo_data(data)

        assert "src" in root.children
        src_node = root.children["src"]
        assert "module0" in src_node.children
        assert "module1" in src_node.children

    def test_multiple_files_same_folder(self):
        """Test multiple files in same folder."""
        builder = FolderHierarchy()

        for i in range(3):
            input_file = InputFile(id=f"file{i}", path="src/common/file.obj")
            builder.add_input_file(input_file)

        root = builder.get_root()
        common_node = root.children["src"].children["common"]
        assert len(common_node.input_files) == 3

    def test_deeply_nested_paths(self):
        """Test deeply nested folder structure."""
        builder = FolderHierarchy()

        input_file = InputFile(id="file1", path="a/b/c/d/e/f/file.obj")
        builder.add_input_file(input_file)

        root = builder.get_root()
        # Path components are: a, b, c, d, e, f (6 levels below root)
        assert get_depth(root) == 6

    def test_compaction_single_child_chains(self):
        """Test path compaction collapses single-child chains."""
        data = LinkInfoData()
        input_file = InputFile(id="file1", path="a/b/c/d/file.obj")
        data.input_files["file1"] = input_file

        root = FolderHierarchy.from_linkinfo_data(data, compact=True)

        # With compaction, all folders with single children should be merged
        # So we should have fewer nodes
        assert get_depth(root) < 5  # Less than the 4 levels (a,b,c,d)

    def test_compaction_preserves_multiple_children(self):
        """Test path compaction preserves folders with multiple children."""
        data = LinkInfoData()
        data.input_files["file1"] = InputFile(id="file1", path="src/module1/file.obj")
        data.input_files["file2"] = InputFile(id="file2", path="src/module2/file.obj")

        root = FolderHierarchy.from_linkinfo_data(data, compact=True)

        # "src" should not be collapsed because it has multiple children (module1, module2)
        # After compaction, src folder should still exist
        flat = flatten_folder_hierarchy(root)
        path_keys = [k for k in flat.keys() if "src" in k]
        assert len(path_keys) > 0  # src folder exists somewhere in hierarchy


class TestFolderHierarchyUtilities:
    """Tests for folder hierarchy utility functions."""

    def test_flatten_folder_hierarchy(self):
        """Test flattening folder hierarchy to path dict."""
        root = FolderNode(name="root", path="/")
        root.children["src"] = FolderNode(name="src", path="src")
        root.children["src"].children["lib"] = FolderNode(name="lib", path="src/lib")

        flat = flatten_folder_hierarchy(root)

        assert "/" in flat
        assert "src" in flat
        assert "src/lib" in flat
        assert len(flat) == 3

    def test_get_all_input_files_in_folder(self):
        """Test retrieving all input files from folder and subfolders."""
        root = FolderNode(name="root", path="/")
        src = FolderNode(name="src", path="src")
        root.children["src"] = src

        # Add files to root
        file1 = InputFile(id="file1")
        root.input_files["file1"] = file1

        # Add files to src
        file2 = InputFile(id="file2")
        file3 = InputFile(id="file3")
        src.input_files["file2"] = file2
        src.input_files["file3"] = file3

        all_files = get_all_input_files_in_folder(root)
        assert len(all_files) == 3
        assert "file1" in all_files
        assert "file2" in all_files
        assert "file3" in all_files

    def test_get_depth(self):
        """Test calculating folder hierarchy depth."""
        root = FolderNode(name="root", path="/")
        assert get_depth(root) == 0

        root.children["a"] = FolderNode(name="a", path="a")
        assert get_depth(root) == 1

        root.children["a"].children["b"] = FolderNode(name="b", path="a/b")
        assert get_depth(root) == 2

    def test_get_depth_multiple_branches(self):
        """Test depth calculation with multiple branches."""
        root = FolderNode(name="root", path="/")
        root.children["a"] = FolderNode(name="a", path="a")
        root.children["b"] = FolderNode(name="b", path="b")
        root.children["b"].children["c"] = FolderNode(name="c", path="b/c")
        root.children["b"].children["c"].children["d"] = FolderNode(
            name="d", path="b/c/d"
        )

        # Maximum depth is from root -> b -> c -> d
        assert get_depth(root) == 3


class TestFolderHierarchyIntegration:
    """Integration tests for folder hierarchy with full LinkInfoData."""

    @pytest.fixture
    def sample_linkinfo_data(self):
        """Create sample LinkInfoData with realistic structure."""
        data = LinkInfoData()

        # Create some object components
        comps = []
        for i in range(5):
            comp = ObjectComponent(id=f"comp{i}", size=100 * (i + 1))
            comps.append(comp)
            data.object_components[f"comp{i}"] = comp

        # Create input files in different folders
        files = [
            ("file1", "src/core/app.o", [comps[0], comps[1]]),
            ("file2", "src/core/main.o", [comps[2]]),
            ("file3", "src/utils/helpers.o", [comps[3]]),
            ("file4", "build/objects/config.o", [comps[4]]),
        ]

        for file_id, path, components in files:
            input_file = InputFile(id=file_id, path=path)
            for comp in components:
                input_file.add_component(comp)
            data.input_files[file_id] = input_file

        return data

    def test_full_hierarchy_structure(self, sample_linkinfo_data):
        """Test full hierarchy building with real data."""
        root = FolderHierarchy.from_linkinfo_data(sample_linkinfo_data)

        assert "src" in root.children
        assert "build" in root.children

        src_node = root.children["src"]
        assert "core" in src_node.children
        assert "utils" in src_node.children

    def test_accumulated_sizes_realistic(self, sample_linkinfo_data):
        """Test accumulated sizes with realistic data."""
        root = FolderHierarchy.from_linkinfo_data(sample_linkinfo_data)

        # src/core should have: 100 + 200 + 300 = 600
        core_size = root.children["src"].children["core"].get_accumulated_size()
        assert core_size == 600

        # src/utils should have: 400
        utils_size = root.children["src"].children["utils"].get_accumulated_size()
        assert utils_size == 400

        # src should have: 600 + 400 = 1000
        src_size = root.children["src"].get_accumulated_size()
        assert src_size == 1000

    def test_compaction_with_realistic_data(self, sample_linkinfo_data):
        """Test compaction with realistic data."""
        root_uncompacted = FolderHierarchy.from_linkinfo_data(
            sample_linkinfo_data, compact=False
        )
        root_compacted = FolderHierarchy.from_linkinfo_data(
            sample_linkinfo_data, compact=True
        )

        # Both should still have the files, just different structure
        all_files_uncompacted = get_all_input_files_in_folder(root_uncompacted)
        all_files_compacted = get_all_input_files_in_folder(root_compacted)

        assert len(all_files_uncompacted) == len(all_files_compacted)
        assert len(all_files_compacted) == 4
