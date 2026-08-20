"""Guard the "template files stay valid in their pre-rendered form" invariant.

Files under the cookiecutter template directory keep their Jinja control flow
inside native comments (`# {% if ... %}`, `# {%- raw %}`) precisely so that the
un-rendered file is still valid TOML/YAML/Python - editors, formatters and the
repo's own linters (yamlfmt, ruff, mypy) all read them that way. It is easy to
break by writing a bare `{% if %}` at the top level, so assert it.
"""

from __future__ import annotations

import ast
import tomllib
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

SCRIPT_PATH = Path(__file__)
PROJECT_PATH = SCRIPT_PATH.parent.parent
TEMPLATE_PATH = PROJECT_PATH / "{{cookiecutter.project_dirname}}"

PARSERS: dict[str, Callable[[str], object]] = {
    ".toml": tomllib.loads,
    ".lock": tomllib.loads,
    ".yml": yaml.safe_load,
    ".yaml": yaml.safe_load,
    ".py": ast.parse,
}


def make_cases() -> list[Path]:
    return sorted(
        path
        for path in TEMPLATE_PATH.rglob("*")
        if path.is_file() and path.suffix in PARSERS
    )


@pytest.mark.parametrize(
    "path", make_cases(), ids=lambda path: str(path.relative_to(TEMPLATE_PATH))
)
def test_template_file_parses_unrendered(path: Path) -> None:
    PARSERS[path.suffix](path.read_text())
