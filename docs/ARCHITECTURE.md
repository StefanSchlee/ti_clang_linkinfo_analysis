# Architecture Documentation

## Overview

This document describes the internal architecture of `ti-clang-linkinfo-analysis`, explaining how the components work together to parse TI Clang linker XML files and generate various analysis outputs.

## Design Philosophy

The architecture follows these principles:

1. **Separation of concerns**: Parsing, data modeling, and analysis/export are separate layers
2. **Public API facade**: `LinkInfoAnalyzer` hides internal complexity from users
3. **Immutable data models**: Parsed data is read-only after construction
4. **Explicit dependencies**: Components reference each other through clear relationships
5. **Testability**: Each layer can be tested independently

## Module Overview

### Public API Layer

**Module:** `analyzer.py`

- **LinkInfoAnalyzer**: Main entry point for all operations
  - Constructs the XML parser and triggers parsing
  - Delegates to specialized exporters for different output formats
  - Exposes folder hierarchy and parsing issues as properties
  - All export methods require explicit output paths (no hidden defaults)

### Parsing Layer

**Module:** `_xml_parser.py`

- **LinkInfoXmlParser**: Reads and parses linkinfo.xml files
  - Uses Python's built-in `xml.etree.ElementTree` for XML parsing
  - Builds domain model objects from XML elements
  - Optionally filters debug sections (`.debug_*`)
  - Tracks parsing issues/warnings in a list
  - Constructs folder hierarchy from input file paths

**Module:** `_path_utils.py`

- Path normalization utilities
  - Converts Windows paths to POSIX format
  - Handles path sanitization for cross-platform compatibility

### Data Model Layer

**Module:** `_models.py`

Core data structures representing linker information:

- **LinkInfoData**: Top-level container
  - `memory_areas`: Dict[str, MemoryArea]
  - `logical_groups`: Dict[str, LogicalGroup]
  - `input_files`: Dict[str, InputFile]
  - `object_components`: Dict[str, ObjectComponent]
  - `folder_hierarchy`: FolderNode (root of folder tree)
  - `issues`: List[str] (parsing warnings)

- **MemoryArea**: Represents a memory section (e.g., `.text`, `.data`)
  - ID, name, size, origin, length attributes
  - Contains logical groups

- **LogicalGroup**: Named grouping within a memory area
  - ID, name attributes
  - Contains input files
  - Belongs to a memory area

- **InputFile**: An object file (`.o`) or archive (`.a`)
  - ID, name, path attributes
  - Contains object components
  - Can belong to a logical group

- **ObjectComponent**: A section within an input file
  - ID, name, size, address attributes
  - References to read-only and read-write sections it depends on
  - Belongs to an input file and memory area

- **FolderNode**: Hierarchical folder structure
  - Name and path
  - Subfolders (Dict[str, FolderNode])
  - Input files (List[InputFile])
  - Recursive size calculation

### Folder Hierarchy Layer

**Module:** `_folder_hierarchy.py`

- **FolderHierarchy**: Builds folder tree from input file paths
  - Extracts directory structure from input file paths
  - Creates normalized folder nodes with POSIX separators
  - Supports folder compacting (merging single-child folders)
  - Calculates accumulated sizes at each level

### Analysis/Export Layers

**Module:** `_markdown.py`

- **export_markdown()**: Generates hierarchical Markdown reports
  - Two modes: `input_file` and `memory_area`
  - Sorts all levels by descending size
  - Formats tables with aligned columns
  - Shows accumulated byte sizes at each level

**Module:** `linkinfo_graph.py`

- **LinkInfoGraphBuilder**: Creates dependency graphs
  - Uses `networkx.DiGraph` for graph structure
  - Aggregates component-level dependencies to file/folder level
  - Supports folder grouping (collapses input files into folder nodes)
  - Filters nodes by minimum size threshold
  - Exports to PyVis HTML (interactive) or GraphML (portable)
  - Color-codes node types (input files, folders, compiler-generated)

**Module:** `_icicle.py`

- **build_icicle_plot()**: Creates hierarchical size visualizations
  - Uses Plotly for interactive icicle plots
  - Hierarchy: folders → input files → object components
  - Vertically oriented (root at bottom)
  - Supports compact mode for single-child folders
  - Optional auto-display in browser

### Error Handling

**Module:** `_errors.py`

- Custom exception types for clear error reporting
- Currently contains placeholder for future error types

## Data Flow

```
linkinfo.xml
    ↓
┌───────────────────────────────────┐
│  LinkInfoXmlParser                │
│  - Reads XML                      │
│  - Filters debug sections         │
│  - Tracks issues                  │
└───────────────────────────────────┘
    ↓
┌───────────────────────────────────┐
│  Domain Models                    │
│  - MemoryArea                     │
│  - LogicalGroup                   │
│  - InputFile                      │
│  - ObjectComponent                │
└───────────────────────────────────┘
    ↓
┌───────────────────────────────────┐
│  FolderHierarchy                  │
│  - Extracts paths                 │
│  - Builds FolderNode tree         │
│  - Compacts single folders        │
└───────────────────────────────────┘
    ↓
┌───────────────────────────────────┐
│  LinkInfoData                     │
│  - Aggregates all models          │
│  - References folder hierarchy    │
│  - Stores parsing issues          │
└───────────────────────────────────┘
    ↓
┌───────────────────────────────────┐
│  LinkInfoAnalyzer (Facade)        │
│  - Exposes clean public API       │
│  - Delegates to exporters         │
└───────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────┐
│  Analysis/Export Functions                        │
│  - export_markdown() → .md files                  │
│  - LinkInfoGraphBuilder → .html/.graphml graphs   │
│  - build_icicle_plot() → .html icicle plots       │
└───────────────────────────────────────────────────┘
    ↓
Output Files (.md, .html, .graphml)
```

## Key Data Structures

### LinkInfoData

The central data container that holds all parsed information:

```python
@dataclass
class LinkInfoData:
    memory_areas: Dict[str, MemoryArea]       # All memory sections
    logical_groups: Dict[str, LogicalGroup]   # Named groups within memory areas
    input_files: Dict[str, InputFile]         # Object files and archives
    object_components: Dict[str, ObjectComponent]  # Individual sections
    folder_hierarchy: Optional[FolderNode]    # Folder tree built from paths
    issues: List[str]                          # Parsing warnings
```

### Relationship Graph

```
MemoryArea (1) ──┐
                 ├─► LogicalGroup (N) ──┐
                                        ├─► InputFile (N) ──┐
                                        │                   ├─► ObjectComponent (N)
                                        │                   │
FolderNode (tree) ──────────────────────┘                   │
                                                            │
ObjectComponent.refd_ro_sections ───────────────────────────┘
ObjectComponent.refd_rw_sections ───────────────────────────┘
```

- Memory areas contain logical groups
- Logical groups contain input files
- Input files contain object components
- Object components reference other object components (for dependencies)
- Folder hierarchy mirrors input file paths

### FolderNode Structure

Recursive tree structure for organizing input files by their source paths:

```python
@dataclass
class FolderNode:
    name: str                              # Folder name
    path: str                              # Full path from root
    subfolders: Dict[str, FolderNode]      # Child folders
    input_files: List[InputFile]           # Files directly in this folder
    
    def get_total_size(self) -> int:       # Recursive size calculation
        # Sum of all input files + all subfolders
```

Example hierarchy:
```
root/
├── src/
│   ├── drivers/
│   │   ├── uart.o (InputFile)
│   │   └── spi.o (InputFile)
│   └── app/
│       └── main.o (InputFile)
└── third_party/
    └── lib.a (InputFile)
```

## Extension Points

### Adding a New Analysis Type

To add a new analysis/export feature:

1. **Create a new module** (e.g., `_my_analysis.py`) in `src/ti_clang_linkinfo_analysis/`

2. **Implement the analysis function** that takes `LinkInfoData` as input:
   ```python
   def export_my_analysis(data: LinkInfoData, output_path: str, **options) -> None:
       """Export analysis with specific format.
       
       Args:
           data: Parsed linkinfo data
           output_path: Where to write output (required)
           **options: Analysis-specific configuration
       """
       # Your analysis logic here
       pass
   ```

3. **Add a method to LinkInfoAnalyzer** in `analyzer.py`:
   ```python
   def export_my_analysis(self, output_path: str, **options) -> None:
       """User-facing method with documentation."""
       from ._my_analysis import export_my_analysis
       export_my_analysis(self._data, output_path, **options)
   ```

4. **Add tests** in `tests/test_my_analysis.py` using the example linkinfo files

5. **Update documentation** in `docs/README.md` with examples and API reference

### Extending the Data Model

If you need additional information from the XML:

1. **Extend the dataclass** in `_models.py`:
   ```python
   @dataclass
   class ObjectComponent:
       # ... existing fields ...
       my_new_field: Optional[str] = None
   ```

2. **Update the parser** in `_xml_parser.py` to extract the data:
   ```python
   def _parse_object_component(self, element):
       # ... existing parsing ...
       my_new_field = element.attrib.get("my_attribute")
       return ObjectComponent(..., my_new_field=my_new_field)
   ```

3. **Add tests** to verify parsing of the new field

### Custom Graph Layouts

The `LinkInfoGraphBuilder` can be extended for different graph types:

1. **Subclass or create a new builder** in `linkinfo_graph.py`
2. **Override node/edge creation** methods
3. **Add new export formats** by implementing different networkx exporters

## Design Decisions and Rationale

### Why a Facade Pattern?

`LinkInfoAnalyzer` serves as a facade to:
- Hide implementation details from users
- Allow internal refactoring without breaking the public API
- Provide a single, obvious entry point
- Enable lazy initialization of expensive operations

### Why Immutable Models?

Data models are read-only after construction because:
- Prevents accidental modification during analysis
- Enables safe concurrent access
- Makes testing more predictable
- Simplifies reasoning about data flow

### Why Separate Export Functions?

Instead of methods on data classes:
- Keeps models focused on data representation
- Allows multiple export formats without bloating models
- Makes it easier to add new export types
- Reduces coupling between parsing and presentation

### Why Explicit Output Paths?

All export methods require `output_path` because:
- No hidden defaults or magic file locations
- Users have full control over where files go
- Easier to use in build scripts and automation
- Prevents accidental overwrites

### Why networkx + PyVis?

- **networkx**: Industry-standard graph library with rich algorithms
- **PyVis**: Simple interactive visualization without heavy dependencies
- **GraphML**: Interoperability with external tools (Gephi, yEd, etc.)
- This combination provides both programmatic access and visualization

## Testing Strategy

The test suite follows this structure:

- **`test_parser_baseline.py`**: Verifies XML parsing produces expected data structures
- **`test_folder_hierarchy.py`**: Tests folder tree construction and size calculations
- **`test_markdown_exports.py`**: Validates Markdown output format and content
- **`test_graph_folder_grouping.py`**: Tests graph construction with folder grouping
- **`test_icicle_plot.py`**: Verifies icicle plot data structure
- **`conftest.py`**: Shared pytest fixtures for loading example files

All tests use the `example_files/*_debug_linkinfo.xml` files as input, ensuring coverage of real-world XML structure.

## Performance Considerations

Current implementation priorities:

1. **Correctness over speed**: Focus on accurate parsing and analysis
2. **Memory efficiency**: Data models use `__slots__` where beneficial
3. **Lazy evaluation**: Folder hierarchy built on-demand if needed
4. **Incremental improvement**: Profile before optimizing

For large linkinfo files (>10MB, >10,000 components):
- XML parsing is typically fast enough with `xml.etree.ElementTree`
- Graph construction may benefit from caching if called repeatedly
- Icicle plot rendering scales well with Plotly's optimizations

## Future Architecture Improvements

Potential enhancements:

1. **Plugin system** for custom analyses
2. **Streaming parser** for extremely large XML files
3. **Caching layer** for repeated analyses on same data
4. **Diff/comparison** framework for multiple linkinfo files
5. **Export format registry** for dynamic format discovery

See `agents_tasklist.md` and `requirements.md` for planned features and constraints.
