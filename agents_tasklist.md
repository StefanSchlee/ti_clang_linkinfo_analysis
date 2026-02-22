# Agents Tasklist (planning baseline)

Legend: `[ ]` open, `[x]` done  
Rule: fully done tasks will be removed over time.

## WP-06 Graph analysis API generalization (Req-8, Req-2, Req-6, Req-10)
- [ ] Define a graph builder configuration model that lets callers toggle which node levels appear (object component, input file, folder, logical group, memory area).
- [ ] Generalize the existing input-file graph into a multi-level graph that aggregates the object-component references into higher-level nodes.
- [ ] Implement the edge aggregation logic so that the links between folder / group nodes derive from their underlying object components.
- [ ] Support optional folder-node grouping so that a folder node can collapse multiple input files while keeping the accumulated byte size accurate.
- [ ] Keep the pyvis and GraphML exporters in sync and enforce explicit `output_path` arguments for every file-producing graph export.

## WP-07 Icicle plot implementation (Req-7, Req-6, Req-10)
- [x] Add plotly as dependency to pyproject.toml.
- [x] Create `_icicle.py` module with IcicleBuilder class.
- [x] Build hierarchy: compacted folders -> input files -> object components using folder_hierarchy.
- [x] Accumulate byte sizes at each level.
- [x] Configure vertical orientation (highest level at bottom, leaf sections at top).
- [x] Implement HTML file output with mandatory output_path.
- [x] Add optional `show=True` parameter to open plot in browser.
- [x] Implement `export_icicle_plot()` in LinkInfoAnalyzer.
- [x] Create demo script `demo/run_icicle_plot.py`.
- [x] Add unit/integration tests for icicle plotting.

## WP-08 Testing architecture and coverage (Req-4)
- [x] Create `tests/` with parser/domain/API/analysis split.
- [x] Add fixtures for `example_files/*debug*` linkinfo inputs.
- [x] Add regression tests for current implemented behavior before refactor changes.
- [x] Add unit/integration tests for markdown export.
- [ ] Add unit/integration tests for icicle and graph config variants (graph tests deferred until graph feature work).
- [x] Add coverage tooling and threshold reporting (pytest-cov).

## WP-09 Documentation and developer workflow (Req-1, Req-2, Req-4, Req-9)
- [x] Update main README.md for repository contributors/developers.
- [ ] Create separate docs/README.md for PyPI-ready user documentation (installation, usage, features).
- [ ] Document analysis configuration options with small examples in user docs.
- [ ] Add simple internal code documentation guidelines and apply them during refactor.
- [ ] Add dedicated internal architecture documentation file with high-level module/data-flow overview.
- [ ] Add contribution/dev setup notes (venv, tests, coverage command).
- [ ] Add changelog strategy (or release notes section).

## WP-10 Migration and output compatibility (Req-2, Req-5, Req-8)
- [ ] Define versioning milestone for first refactored release.

## Execution order proposal (commit-sized increments)
1. WP-08 (baseline regression tests) -> 2) WP-02 -> 3) WP-03 -> 4) WP-04 -> 5) WP-05 (markdown) -> 6) WP-07 (icicle) -> 7) WP-06 (graph) -> 8) WP-09 -> 9) WP-10

