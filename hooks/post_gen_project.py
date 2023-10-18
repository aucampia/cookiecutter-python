# {% raw %}

from __future__ import annotations

import distutils.dir_util
import enum
import itertools
import json
import logging
import os
import os.path
import shutil
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# https://cookiecutter.readthedocs.io/en/latest/advanced/hooks.html

logger = logging.getLogger(
    __name__ if __name__ != "__main__" else "hooks.post_gen_project"
)

SCRIPT_PATH = Path(__file__)


SCRIPT_PATH = Path(__file__)
COOKIE_PATH = SCRIPT_PATH.parent.parent


class Variant(enum.Enum):
    BASIC = "basic"
    MINIMAL = "minimal"
    MINIMAL_TYPER = "minimal_typer"


class BuildTool(enum.Enum):
    GNU_MAKE = "gnu-make"
    GO_TASK = "go-task"
    POE = "poe"


BUILD_TOOL_FILES = {
    BuildTool.GNU_MAKE: {"Makefile"},
    BuildTool.GO_TASK: {"Taskfile.yml"},
}


@dataclass
class Answers:
    python_package_fqname: str
    variant: Variant
    build_tool: BuildTool
    git_init: bool
    git_commit: bool
    use_oci_devtools: bool

    def __post_init__(self) -> None:
        self.namespace_parts = self.python_package_fqname.split(".")

    @classmethod
    def _read_yn(cls, value: str) -> bool:
        if value == "y":
            return True
        elif value == "n":
            return False
        else:
            raise ValueError(f"Expected 'y' or 'n', got {value!r}")

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> Answers:
        return cls(
            python_package_fqname=values["python_package_fqname"],
            variant=Variant(values["variant"]),
            build_tool=BuildTool(values["build_tool"]),
            git_init=values["git_init"],
            git_commit=values["git_commit"],
            use_oci_devtools=cls._read_yn(values["use_oci_devtools"]),
        )


def apply() -> None:
    logger.info("entry: ...")
    logger.debug("os.getcwd() = %s", os.getcwd())
    logger.debug("SCRIPT_PATH = %s", SCRIPT_PATH.absolute())
    logger.debug("COOKIE_PATH = %s", COOKIE_PATH.absolute())

    # {% endraw %}
    cookiecutter_json = """{{ cookiecutter | tojson('  ') }}"""
    # {% raw %}
    logger.debug("cookiecutter_json = %s", cookiecutter_json)

    cookiecutter = json.loads(cookiecutter_json)
    if not isinstance(cookiecutter, dict):
        raise TypeError(
            f"Expected COOKIECUTTER to be a dict, got {type(cookiecutter).__name__}"
        )

    cwd_path = Path.cwd()

    answers = Answers.from_mapping(cookiecutter)

    # namespace_parts: List[str] = COOKIECUTTER["python_package_fqname"].split(".")
    # variant = Variant(COOKIECUTTER["variant"])
    # build_tool = BuildTool(COOKIECUTTER["build_tool"])
    pkg_files_path = cwd_path.joinpath("pkg_files", answers.variant.value)

    logger.debug("namespace_parts = %s", answers.namespace_parts)
    namespace_path = cwd_path.joinpath("src", *answers.namespace_parts)
    logger.debug("will make namespace_path.parent %s", namespace_path.parent)
    namespace_path.parent.mkdir(parents=True, exist_ok=True)
    logger.debug("will make namespace_path %s", namespace_path)
    namespace_path.mkdir(parents=True, exist_ok=True)
    logger.debug(
        "will copytree pkg_files_path %s to namespace_path %s",
        pkg_files_path,
        namespace_path,
    )
    distutils.dir_util.copy_tree(
        str(pkg_files_path),
        str(namespace_path),
        preserve_mode=0,
        preserve_times=0,
        preserve_symlinks=1,
        update=1,
        verbose=1,
    )
    logger.debug("will rmtree pkg_files_path %s", pkg_files_path.parent)
    shutil.rmtree(pkg_files_path.parent)

    cookiecutter_input_path = cwd_path.joinpath("cookiecutter-input.yaml")
    if not cookiecutter_input_path.exists():
        try:
            import yaml

            logger.info("Writing cookiecutter input to %s", cookiecutter_input_path)
            with cwd_path.joinpath("cookiecutter-input.yaml").open("w") as file_object:
                data = {"default_context": cookiecutter.copy()}
                for key in ("_template", "_output_dir"):
                    if key in data["default_context"]:
                        del data["default_context"][key]
                yaml.safe_dump(data, file_object)
        except ImportError:
            logger.warning(
                "yaml module not found, %s will not be written - install pyyaml to fix",
                cookiecutter_input_path,
            )
    else:
        logger.info("Not writing %s as it already exists", cookiecutter_input_path)

    remove_files: set[str] = set(itertools.chain(*BUILD_TOOL_FILES.values()))
    remove_files -= BUILD_TOOL_FILES.get(answers.build_tool, set())
    logger.info("removing unused build files %s", remove_files)
    for remove_file in remove_files:
        logger.info("removing unused build file %s", remove_file)
        (cwd_path / remove_file).unlink()

    if answers.git_init:
        subprocess.run(["git", "init"])


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("PYTHON_LOGGING_LEVEL", logging.INFO),
        stream=sys.stderr,
        datefmt="%Y-%m-%dT%H:%M:%S",
        format=(
            "%(asctime)s.%(msecs)03d %(process)d %(thread)d %(levelno)03d:%(levelname)-8s "
            "%(name)-12s %(module)s:%(lineno)s:%(funcName)s %(message)s"
        ),
    )
    apply()


if __name__ == "__main__":
    main()

# {% endraw %}
