# Agent Instructions

Tools:

- `uv` for dependency management
- `task` as task runner
- `mise` pins every non-Python dev tool (see `.mise.toml` / `mise.lock`)

Other info:

- Code is formatted using `ruff`, `yamlfmt`, `shfmt` and `rumdl`
- Code is linted using `ruff`, `mypy`, `codespell`, `shellcheck`, `rumdl`,
  `zizmor` and `actionlint`
- To run formatting and fix autofixable issues: `task validate:fix`
- To run all static validation: `task validate:static`
- To run all tests: `task test`
- To run everything: `task validate`
- To regenerate the examples under `examples/`: `task examples:generate` then
  `task examples:run`
