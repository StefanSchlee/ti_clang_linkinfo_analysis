# Agents Tasklist (planning baseline)

Legend: `[ ]` open, `[x]` done  
Rule: fully done tasks will be removed over time.

## WP-08 Testing architecture and coverage (Req-4)
- [x] Create `tests/` with parser/domain/API/analysis split.
- [x] Add fixtures for `example_files/*debug*` linkinfo inputs.
- [x] Add regression tests for current implemented behavior before refactor changes.
- [x] Add unit/integration tests for markdown export.
- [x] Add unit/integration tests for icicle plotting.
- [x] Add unit/integration tests for graph with folder grouping.
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

