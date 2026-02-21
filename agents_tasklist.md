# Agents Tasklist (planning baseline)

Legend: `[ ]` open, `[x]` done  
Rule: fully done tasks will be removed over time.

## WP-02 Public API frontend design (Req-2, Req-3, Req-10)
- [x] Define central facade class (working name: `LinkInfoAnalyzer`) constructed with XML path.
- [x] Specify API surface of analysis methods (markdown, icicle, graph) with stable method signatures.
- [x] Enforce mandatory `output_path` argument for all file-writing analyses.
- [x] Keep parser/internal domain models non-public (or semi-public) and document boundaries.
- [x] Add deprecation/compatibility strategy for existing direct class usage.

## WP-03 Parser/domain refactor foundation (Req-2, Req-3)
- [x] Extract parser into dedicated internal module(s): XML parsing, model mapping, cross-reference resolution.
- [x] Normalize/validate domain dataclasses (typing consistency, IDs, optionality, computed size helpers).
- [x] Add robust error model for malformed/missing references.
- [x] Preserve debug-filter behavior and make it configurable through facade.

## WP-04 Input-file folder hierarchy model (Req-6)
- [ ] Implement path normalization (POSIX/Windows separators, absolute/relative handling).
- [ ] Build reusable folder tree representation from `input_file.path`.
- [ ] Add accumulation helpers for folder/input file/object component byte sizes.
- [ ] Add optional path compaction (single-child folder chain collapse) for visual analyses.

## WP-05 Unified markdown analysis API (Req-5, Req-2, Req-10)
- [ ] Define configurable markdown exporter interface (single API with hierarchy options).
- [ ] Re-implement existing markdown variants as configurations of one engine:
	- [ ] input-file -> object-component
	- [ ] memory-area -> logical-group -> input-file -> object-component
- [ ] Enforce descending size sort on each hierarchy level.
- [ ] Ensure each item shows accumulated byte size.
- [ ] Keep output deterministic (stable ordering on equal sizes).
- [ ] Ensure markdown export APIs always take explicit output file path.

## WP-06 Graph analysis API generalization (Req-8, Req-2, Req-6, Req-10)
- [ ] Define graph builder configuration model (enabled node levels, filters, optional grouped folders).
- [ ] Generalize current input-file graph to multi-level nodes (object component/input file/folder/logical group/memory area).
- [ ] Implement edge aggregation from object-component references to higher levels.
- [ ] Implement optional folder-node replacement behavior per requirement 8.9.
- [ ] Keep pyvis export and add GraphML export parity checks.
- [ ] Align graph export methods to mandatory output-path style for all file-producing graph APIs.

## WP-07 Icicle plot implementation (Req-7, Req-6, Req-10)
- [ ] Add plotly-based icicle builder module.
- [ ] Build hierarchy: compacted folders -> input files -> object components.
- [ ] Use accumulated byte size for node values.
- [ ] Configure vertical orientation with highest level at bottom.
- [ ] Implement configurable icicle API modes: interactive `Figure` return and optional HTML file output.
- [ ] If HTML output is requested, enforce mandatory output-path argument.

## WP-08 Testing architecture and coverage (Req-4)
- [x] Create `tests/` with parser/domain/API/analysis split.
- [x] Add fixtures for `example_files/*debug*` linkinfo inputs.
- [x] Add regression tests for current implemented behavior before refactor changes.
- [x] Add unit/integration tests for markdown export.
- [ ] Add unit/integration tests for icicle and graph config variants (graph tests deferred until graph feature work).
- [x] Add coverage tooling and threshold reporting (pytest-cov).

## WP-09 Documentation and developer workflow (Req-1, Req-2, Req-4, Req-9)
- [ ] Add README with installation, quickstart, and API examples.
- [ ] Document analysis configuration options with small examples.
- [ ] Add simple internal code documentation guidelines and apply them during refactor.
- [ ] Add dedicated internal architecture documentation file with high-level module/data-flow overview.
- [ ] Add contribution/dev setup notes (venv, tests, coverage command).
- [ ] Add changelog strategy (or release notes section).

## WP-10 Migration and output compatibility (Req-2, Req-5, Req-8)
- [ ] Define versioning milestone for first refactored release.

## Execution order proposal (commit-sized increments)
1. WP-08 (baseline regression tests) -> 2) WP-02 -> 3) WP-03 -> 4) WP-04 -> 5) WP-05 (markdown) -> 6) WP-07 (icicle) -> 7) WP-06 (graph) -> 8) WP-09 -> 9) WP-10

