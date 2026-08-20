"""Guard the invariants that keep the cookiecutter template directly usable.

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


def make_symlink_cases() -> list[Path]:
    """Root-level symlinks that resolve to a *file* inside the template.

    Directory symlinks (`devtools`, `link_project`) are excluded - their
    contents are Jinja-templated by design.
    """
    return sorted(
        path
        for path in PROJECT_PATH.iterdir()
        if path.is_symlink()
        and path.resolve().is_file()
        and path.resolve().is_relative_to(TEMPLATE_PATH.resolve())
    )


@pytest.mark.parametrize("path", make_symlink_cases(), ids=lambda path: path.name)
def test_shared_file_is_jinja_free(path: Path) -> None:
    """A file shared with the root by symlink must not be Jinja-templated.

    The root has no cookiecutter context to render with, so it reads the
    template copy verbatim. Adding `{{ ... }}` or `{% ... %}` to one of these
    would silently corrupt the root's own config.
    """
    content = path.read_text()
    found = [marker for marker in ("{{", "}}", "{%") if marker in content]
    assert not found, f"{path} is shared with the root but contains {found}"
