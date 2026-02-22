# ti-clang-linkinfo-analysis

Analysis tools for the TI Clang `linkinfo.xml` output. The package hides the parser and model plumbing behind `ti_clang_linkinfo_analysis.LinkInfoAnalyzer`, so downstream consumers only need to focus on selecting the right analyses and exporting their preferred artifacts. The public API currently supports configurable markdown exports plus graph exports that can be rendered via pyvis or GraphML.

## Layout at a glance
- `src/ti_clang_linkinfo_analysis`: core package with the analyzer, parsers, markdown exporter, and graph builder.
- `tests/`: pytest suites that exercise the parser, folder hierarchy helpers, and markdown exporter using the `example_files/*debug*` inputs.
- `example_files/`: sample `dpl_demo` and `enet_cli` linkinfo outputs so the tests and demos run without external artifacts (favor the `*debug*` files when writing regressions).
- `demo/`: manual scripts that exercise the public API and write results to `demo/output/` so you can inspect Markdown or graph exports.
- `outputs/`: tracked output artifacts created by previous demo runs (serves as inspiration for expected Markdown layout, memory-area tables, and graphs).
- `requirements.md`, `agents_tasklist.md`, `TODO_for_human.md`, and `AGENTS.md`: governance and planning documents that you must consult before starting new work (edit `agents_tasklist.md` for every task, see the requirements for feature goals, and keep `TODO_for_human.md` in sync with your experiments).

## Getting started
### Prerequisites
1. Install Python **3.10 or newer**.
2. Create an isolated environment and activate it (the repository already provides `.venv`; use `source .venv/bin/activate.fish` in fish or the equivalent for bash/zsh).
3. Keep `example_files/` handy: the debug linkinfo exports there are referenced by the tests and the demo scripts.

### Installation
1. With the virtual environment activated, install the package and development extras:
	```bash
	pip install -e .[dev]
	```
2. To install the runtime dependencies only (e.g., for a release build), run:
	```bash
	pip install .
	```
3. The package is ready for local editable installs, normal installs, and future PyPI releases thanks to the `pyproject.toml` setup.

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
- `demo/run_markdown_exports.py`: exports both hierarchy styles of Markdown and writes them to `demo/output/`.
- `demo/run_graph_exports.py`: builds the current input-file graph, then emits a pyvis HTML (interactive) version plus a GraphML file for further tooling.

Run either script directly with the virtual environment active to preview exported Markdown or graph artifacts.

## Testing
Use the shared virtual environment whenever possible and keep tests green:
1. Install the dev extras (`pytest`, `pytest-cov`, etc.) via `pip install -e .[dev]` if you have not already.
2. From the repository root, run:
	```bash
	python -m pytest
	```
	The `pytest.ini` adds coverage reporting (`--cov=ti_clang_linkinfo_analysis --cov-report=term-missing`) automatically.
3. After major changes, rerun the suite to ensure the parser continues to handle the debug linkinfo examples and the markdown exporter produces stable, size-sorted tables.

## Task tracking & documentation governance
- Read `AGENTS.md` before making structural changes—you will find the high-level project description and the “how we develop together” expectations right there.
- Keep `requirements.md` in sync with feature goals, implementation constraints, and coding guidelines. When a requirement changes, update this file before or alongside code changes.
- Use `agents_tasklist.md` as your single source of truth for ongoing work. Every new work package should:
  1. Reference the relevant requirement numbers (Req-#) so future readers understand context.
  2. Be split into commit-sized items with checkboxes marking progress.
  3. Move completed entries out of the file (delete or archive them) once they are fully delivered.
- Capture ideas and experiments that do not qualify as immediate tickets inside `TODO_for_human.md`; refer coworkers there before reshuffling major architecture.

## Additional notes
- The Markdown exporter sorts each level in descending byte size and always shows accumulated sizes, which makes it straightforward to compare input files, memory areas, and logical groups.
- Graph exports rely on `networkx` and `pyvis`, so ensure those packages stay in sync with `pyproject.toml` when the dependencies evolve.
- For historical outputs and reference artifacts, inspect the `outputs/` folder alongside the demo scripts.
- Any new feature that writes to disk must accept an explicit `output_path` argument (Req-10) to keep the interface deterministic.
