# Req-1: Project Structure
1. The package should be installable with pip
2. It should support local installs, editable installs (pip install -e), as well as later i want to publish it on pypi
3. I want a pyproject.toml style project, for python version >=3.10

# Req-2: Publicly API Frontend
1. I want one central class, which gets constructed with a path to an linkinfo.xml file.
2. All different analysis should be accessible via methods on this class

# Req-3: Software Architecture Guidelines
1. Do not create one big class, split the logic into internal classes, functions etc. where reasonable
2. At the base i want some kind of parser class, which only parses the linkinfo files into python objects, which then can be used by all further analysis
3. Create a reasonanable project folder structure

# Req-4: Unit-tests
1. I want pytest-based tests for the package, using the example linkinfo.xml files in the "example_files/" folder
2. Keep the tests up-to-date
3. I want a code coverage report

# Req-5: Analysis with markdown output
Hint: This feature is already partly implemented in the internal markdown exporter.
1. This set of analysis outputs the linker data in a structured, hierarchical markdown file
2. On each hierachical level, i generally want to sort the items in descending byte size
3. Each item should show its accumulated byte size
4. This analysis should be one analysis function, which can be configured with arguments, which hierarchical levels should be added:
   1. One style is already implemented by "LinkInfoParser.export_sorted_input_files_markdown()": The top-level are the input files, the next level are the object components belonging to this file
   2. Another style i want is already implemented by "LinkInfoParser.export_memory_areas_hierarchy_markdown()": Above the Input-files there are the logical groups and the memory areas

# Req-6: Folder Grouping of input files
1. Using the "path" from the input-files, we can hierachically group the input files along the original source-files folder structure
2. This Information will be used by different analysis

# Req-7: Icicle Plot Analysis
1. I want an icicle plot using the plotly package
2. The Graph should group after the input files folder structure, then the input files, and then the object-components as the leaf
3. If a folder has only one subfolder, it can be grouped together to form one icicle section
4. The size of each section is based on the byte size of the respective folder (accumulated subfolders/inputfiles), input-file, object-component
5. I want the plot to be vertically: The highest level should be at the bottom.
6. The functions should be configured to show interactive figure or html if desired

# Req-8: Graph-based Analysis
1. Using networkx and pyvis.network packages we can do graph visualisations
2. The base graph is drawn on the input-file level
3. The nodes are input files, with size based on the accumulated byte size of all object components
4. The edges between nodes originate from the "refd_ro_sections" and "refd_rw_sections" of the object components, aggregated at the input-file level
5. I want to optionally supply a list of folder paths, which are added as folder nodes:
   1. All input-files which belong to one of these folders are removed as individual nodes and accumulated into these folder nodes
   2. The folder node size is equal to the sum of the input files belonging to it
   3. The edges between folder nodes and other folder/input-file nodes are aggregated from all links of the underlying input files
   4. Input files NOT in the specified folders remain as individual nodes
6. Export formats: pyvis HTML (interactive) and GraphML (for external tools)

# Req-9: Documentation
1. The main README.md is for everyone using this repository (developers, contributors)
2. For user documentation, which will later be also visible on pypi, create a separate readme under "docs/" which shows all required information: installation, exemplary usage, and more detailed explanation of all features
3. Update the documentation along the road

## Req-9.1: User Documentation (docs/README.md)
1. Create `docs/README.md` as the primary user-facing documentation (will be used as PyPI long_description)
2. Must be PyPI-compatible: standalone, no relative links to repo files outside docs/, use absolute URLs for external resources
3. Structure:
   - **Overview**: Brief description of what the tool does and who it's for
   - **Installation**: pip install instructions (from PyPI when available, from git URL for now)
   - **Quick Start**: Minimal working example with explanation
   - **Features**: Detailed explanation of each analysis type (markdown exports, graph exports, icicle plots)
   - **API Reference**: Public API documentation (LinkInfoAnalyzer methods with parameters and examples)
   - **Examples**: More complex usage scenarios
   - **Release Notes**: Integrated version history with notable changes
4. Keep examples concise but complete (full working code snippets)
5. Explain configuration options for each analysis method

## Req-9.2: Code Documentation Standards
1. Use **Google-style docstrings** for all public classes, methods, and functions
2. Minimum docstring content:
   - One-line summary
   - Args section for parameters (with types if not obvious from type hints)
   - Returns section if applicable
   - Raises section for expected exceptions
   - Example usage for complex public APIs (optional but encouraged)
3. Internal/private modules and functions should have at least a one-line docstring
4. Type hints are required for all public APIs (already enforced)

## Req-9.3: Architecture Documentation
1. Create `docs/ARCHITECTURE.md` explaining internal structure
2. Content:
   - High-level module overview and responsibilities
   - Data flow: XML → Parser → Models → Analyses → Outputs
   - Key data structures (LinkInfoData, InputFile, ObjectComponent, FolderNode)
   - Extension points for adding new analyses
   - Design decisions and rationale
3. Use text-based descriptions with ASCII diagrams if helpful
4. Keep it updated when major architectural changes occur

## Req-9.4: Developer Setup and Contributing
1. The main README.md should have clear developer setup instructions
2. Include:
   - Virtual environment setup
   - Installation with dev dependencies
   - Running tests with coverage
   - Project structure overview with brief file/folder descriptions
   - References to requirements.md and agents_tasklist.md workflow

## Req-9.5: Release Notes
1. Maintain integrated release notes in `docs/README.md` (no separate CHANGELOG.md for now)
2. Use semantic versioning (MAJOR.MINOR.PATCH)
3. Document notable changes, breaking changes, and new features
4. Start tracking from v0.1.0 (first structured release post-refactor)

# Req-10: Output Style
1. Analysis which output a file, should expect an output file path argument, which must be mandatory

# Req-11: Demos
1. In the "demo/" folder, i want scripts for me to be run manually, to inspect the ouputs of the different public api functions on the example linkinfo files.
