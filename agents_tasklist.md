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

## WP-09 Documentation and developer workflow (Req-9, Req-9.1-9.5)
- [x] Update main README.md for repository contributors/developers.
- [x] Create docs/README.md with PyPI-compatible user documentation (Req-9.1)
  - [x] Overview and installation sections
  - [x] Quick start with minimal example
  - [x] Features section explaining all analysis types
  - [x] API reference with method documentation
  - [x] Examples section with complex scenarios
  - [x] Integrated release notes section (start with v0.1.0)
- [x] Standardize code documentation using Google-style docstrings (Req-9.2)
  - [x] Document all public API methods in LinkInfoAnalyzer
  - [x] Document LinkInfoGraphBuilder public methods
  - [x] Document export_markdown function
  - [x] Review and document other public-facing functions
  - [x] Add docstrings to key internal classes/functions
- [x] Create docs/ARCHITECTURE.md explaining internal structure (Req-9.3)
  - [x] Module overview and responsibilities
  - [x] Data flow diagram (XML → outputs)
  - [x] Key data structures explanation
  - [x] Extension points for new analyses
- [x] Enhance main README.md developer setup section (Req-9.4)
  - [x] Clarify venv setup for different shells
  - [x] Document dev dependencies installation
  - [x] Add example pytest commands with coverage
  - [x] Improve project structure descriptions

## WP-10 Migration and output compatibility (Req-2, Req-5, Req-8)
- [ ] Define versioning milestone for first refactored release.

## WP-11 License and contributing guidelines (Req-1)
- [x] Add LICENSE file (MIT License)
- [x] Add CONTRIBUTING.md with contribution guidelines

## Execution order proposal (commit-sized increments)
1. WP-08 (baseline regression tests) -> 2) WP-02 -> 3) WP-03 -> 4) WP-04 -> 5) WP-05 (markdown) -> 6) WP-07 (icicle) -> 7) WP-06 (graph) -> 8) WP-09 -> 9) WP-10

