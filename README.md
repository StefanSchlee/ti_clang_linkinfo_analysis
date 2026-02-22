# ti-clang-linkinfo-analysis

Analysis tools for the TI Clang `linkinfo.xml` output. The package hides the parser and model plumbing behind `ti_clang_linkinfo_analysis.LinkInfoAnalyzer`, so downstream consumers only need to focus on selecting the right analyses and exporting their preferred artifacts.

## Documentation

For detailed information about this project, please refer to the [docs](docs/) directory:
- [Architecture Guide](docs/ARCHITECTURE.md): Technical design and internal structure
- [Project README](docs/README.md): Comprehensive overview and feature descriptions

## Layout at a glance
- `src/ti_clang_linkinfo_analysis`: core package with the analyzer, parsers, markdown exporter, and graph builder.
- `tests/`: pytest suites that exercise the parser, folder hierarchy helpers, and markdown exporter using the `example_files/*debug*` inputs.
- `example_files/`: sample `dpl_demo` and `enet_cli` linkinfo outputs so the tests and demos run without external artifacts (favor the `*debug*` files when writing regressions).
- `demo/`: manual scripts that exercise the public API and write results to `demo/output/` so you can inspect Markdown or graph exports.
- `docs/`: User-facing documentation (README for PyPI, ARCHITECTURE guide, release notes).
- `requirements.md`, `agents_tasklist.md`, `TODO_for_human.md`, and `AGENTS.md`: governance and planning documents that you must consult before starting new work (edit `agents_tasklist.md` for every task, see the requirements for feature goals, and keep `TODO_for_human.md` in sync with your experiments).

## Getting started

### Prerequisites
1. Install Python **3.10 or newer**.
2. Create an isolated virtual environment (the repository already provides `.venv` for convenience).
3. The `example_files/` folder contains sample linkinfo files used by tests and demos (use the `*debug*` files for testing).

### Installation for Development

**Step 1: Clone the repository**
```bash
git clone https://github.com/yourusername/ti_clang_linkinfo_analysis.git
cd ti_clang_linkinfo_analysis
```

**Step 2: Create and activate virtual environment**

Using bash/zsh:
```bash
python -m venv .venv
source .venv/bin/activate
```

Using fish shell:
```fish
python -m venv .venv
source .venv/bin/activate.fish
```

Using Windows PowerShell:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Step 3: Install package with development dependencies**
```bash
pip install -e .[dev]
```

This installs the package in editable mode along with:
- `pytest` and `pytest-cov` for testing
- `plotly`, `networkx`, `pyvis` for visualizations
- All other runtime dependencies

**Alternative: Runtime dependencies only**

To install without development tools (e.g., for production use):
```bash
pip install .
```

## Programmatic API
```python
from ti_clang_linkinfo_analysis import LinkInfoAnalyzer

analyzer = LinkInfoAnalyzer("example_files/dpl_demo_debug_linkinfo.xml", filter_debug=True)

analyzer.export_markdown("outputs/input_files.md", mode="input_file")
analyzer.export_markdown("outputs/memory_areas.md", mode="memory_area")
analyzer.export_inputfile_graph_pyvis("outputs/inputfile_graph.html")
analyzer.export_inputfile_graph_graphml("outputs/inputfile_graph.graphml")
```
- All methods that write files require an explicit `output_path` so that nobody relies on hidden defaults (`mode` is the configuration knob for the markdown exporter).
- The `mode` argument currently supports `input_file` (top-level input files and components) and `memory_area` (logical groups + memory areas above the input-file hierarchy).
- `LinkInfoAnalyzer.folder_hierarchy` exposes the input-file folder tree (normalized to POSIX separators) for use in future analyses.
- The icicle plot API is planned but not available yet (see `LinkInfoAnalyzer.build_icicle_plot` raising `NotImplementedError`).

## Demo scripts

The `demo/` folder contains scripts demonstrating the public API on example linkinfo files:

- `demo/run_markdown_exports.py`: Exports both hierarchy styles of Markdown to `demo/output/`.
- `demo/run_graph_exports.py`: Builds input-file graphs and exports as PyVis HTML (interactive) and GraphML.
- `demo/run_icicle_plot.py`: Creates an interactive icicle plot showing hierarchical size distribution.

**Running demos:**
```bash
# Ensure virtual environment is active
source .venv/bin/activate  # or .venv/bin/activate.fish

# Run individual demos
python demo/run_markdown_exports.py
python demo/run_graph_exports.py
python demo/run_icicle_plot.py
```

Output files are written to `demo/output/` where you can inspect the generated reports and visualizations.

## Testing

The test suite uses pytest with automatic coverage reporting configured in `pytest.ini`.

**Run all tests:**
```bash
python -m pytest
```

**Run tests with verbose output:**
```bash
python -m pytest -v
```

**Run tests with detailed coverage report:**
```bash
python -m pytest --cov=src/ti_clang_linkinfo_analysis --cov-report=term-missing
```

**Run specific test file:**
```bash
python -m pytest tests/test_parser_baseline.py -v
```

**Run tests matching a pattern:**
```bash
python -m pytest -k "graph" -v
```

Coverage reports show which lines aren't covered. After major changes, run the full suite to ensure all functionality still works correctly.

## Contributing and Development Workflow

This project uses an AI agent-assisted development workflow. Responsibilities are divided as follows:

### User (Human Developer) Responsibilities

**Define requirements and direction:**
- Specify feature requests and requirements in [`requirements.md`](requirements.md)
- Review and approve proposed requirement changes from the AI agent
- Provide clarification when the AI agent requests it
- Make final decisions on architecture and design choices

**Test and validate:**
- Run demo scripts to validate outputs
- Review generated code and documentation
- Provide feedback on implementation quality

### AI Agent Responsibilities

**Before starting work:**
1. Read [`AGENTS.md`](AGENTS.md) for project description and development philosophy
2. Check [`requirements.md`](requirements.md) for feature goals and coding guidelines
3. Review [`agents_tasklist.md`](agents_tasklist.md) for ongoing work and priorities

**When implementing features:**
1. Propose requirement clarifications or additions when needed
2. Create and maintain tasks in [`agents_tasklist.md`](agents_tasklist.md) with checkboxes and requirement references
3. Implement changes in small, testable increments
4. Add or update tests for new functionality
5. Update documentation (docstrings, README, docs/)
6. Run tests to verify changes
7. Mark tasks as completed and remove them when fully done

**Code standards (enforced by AI agent):**
- Google-style docstrings for all public APIs
- Type hints on all function signatures
- Explicit `output_path` arguments for all export functions (no hidden defaults)
- Tests for all new features using `example_files/*debug*` inputs

**Documentation maintained by AI agent:**
- User documentation: [`docs/README.md`](docs/README.md) (PyPI-ready)
- Architecture documentation: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Developer documentation: This README.md file
- Task tracking: [`agents_tasklist.md`](agents_tasklist.md)
## Contributing

Contributions are welcome! Please feel free to open a pull request on GitHub.

## License

This project is licensed under the MIT License – see the [`LICENSE`](LICENSE) file for details.