from __future__ import annotations

import enum
import hashlib
import itertools
import json
import logging
import os
import pickle
import subprocess
import tempfile
from collections.abc import Generator, Mapping
from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree
from typing import Any, Callable, TypeVar

import pytest
import yaml
from _pytest.mark.structures import ParameterSet
from cookiecutter.generate import generate_context
from cookiecutter.main import cookiecutter
from cookiecutter.prompt import prompt_for_config
from frozendict import frozendict

from hooks.post_gen_project import BuildTool

SCRIPT_PATH = Path(__file__)
PROJECT_PATH = SCRIPT_PATH.parent.parent
TEST_DATA_PATH = SCRIPT_PATH.parent / "data"


def load_test_config(name: str) -> dict[str, Any]:
    config = yaml.safe_load(
        (TEST_DATA_PATH / "cookie-config" / f"{name}.yaml").read_text()
    )
    # default_context = config["default_context"]
    assert isinstance(config, dict)
    logging.info("name = %s, config = %s", name, config)
    return config


def escape_venv(environ: Mapping[str, str]) -> dict[str, str]:
    result = {**environ}
    virtual_env_path = Path(result["VIRTUAL_ENV"])
    ospath_parts = result["PATH"].split(os.pathsep)
    use_ospath_parts = []
    for ospath_part in ospath_parts:
        ospath_part_path = Path(ospath_part)
        if not ospath_part_path.is_relative_to(virtual_env_path):
            use_ospath_parts.append(ospath_part)
    use_ospath = os.pathsep.join(use_ospath_parts)
    logging.info("use_ospath = %s", use_ospath)
    result["PATH"] = use_ospath
    del result["VIRTUAL_ENV"]
    return result


@dataclass(frozen=True)
class BakeKey:
    template_path: Path
    template_hash: str
    extra_context: frozendict[str, Any]


@dataclass(frozen=True)
class BakeResult(BakeKey):
    output_path: Path
    project_path: Path
    context: dict[str, Any]
    build_tool: BuildTool


AnyT = TypeVar("AnyT")

TEST_RAPID = json.loads(os.environ.get("TEST_RAPID", "true"))
assert isinstance(TEST_RAPID, bool)


def hash_path(
    root: Path,
    exclude_subdirs: set[str],
    hash: Callable[[], hashlib._Hash] = hashlib.sha256,
) -> str:
    hasher = hash()
    for _dirpath, dirnames, filenames in os.walk(root):
        dirpath = Path(_dirpath)
        logging.debug("exclude_subdirs = %s", exclude_subdirs)
        for dirname in list(dirnames):
            relative_dirname = (dirpath / dirname).relative_to(root)
            logging.debug("relative_dirname = %s", relative_dirname)
            if str(relative_dirname) in exclude_subdirs:
                dirnames.remove(dirname)
        dirnames.sort()
        filenames.sort()
        logging.debug("dirpath = %s", dirpath)
        logging.debug("dirnames = %s", dirnames)
        logging.debug("filenames = %s", filenames)
        for dirname in dirnames:
            subdir_path = dirpath / dirname
            hasher.update(str(subdir_path).encode("utf-8"))
        for filename in filenames:
            file_path = dirpath / filename
            hasher.update(str(file_path).encode("utf-8"))
            hasher.update(file_path.read_bytes())

    return hasher.hexdigest()


def hash_object(object: Any, hash: Callable[[], hashlib._Hash] = hashlib.sha256) -> str:
    pickled = pickle.dumps(object)
    hasher = hash()
    hasher.update(pickled)
    return hasher.hexdigest()


ESCAPED_ENV = escape_venv(os.environ)


class Baker:
    def __init__(self) -> None:
        self._baked: dict[BakeKey, BakeResult] = {}

    def bake(self, extra_context: dict[str, Any], template_path: Path) -> BakeResult:
        context_file = template_path / "cookiecutter.json"

        if TEST_RAPID:
            template_path_hash = hash_object(template_path)
        else:
            template_path_hash = hash_path(
                template_path,
                exclude_subdirs={
                    ".mypy_cache",
                    ".pytest_cache",
                    ".venv",
                    ".git",
                    "var",
                    "tests",
                },
            )

        key = BakeKey(template_path, template_path_hash, frozendict(extra_context))

        key_hash = hash_object(key)

        # dirkey = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

        if key in self._baked:
            logging.info("found baked key = %s", key)
            return self._baked[key]

        output_path = Path(tempfile.gettempdir()) / f"baked-cookie-{key_hash}"
        logging.info("output_path = %s", output_path)
        output_context_path = output_path.parent / f"{output_path.name}-context.json"
        output_project_path = output_path.parent / f"{output_path.name}-project.json"

        # if (
        #     output_path.exists()
        #     and (next(output_path.glob("*"), None) is not None)
        #     and TEST_RAPID
        # ):
        #     output_context = json.loads(output_context_path.read_text())
        #     output_project = json.loads(output_project_path.read_text())
        #     build_tool = BuildTool(output_context["build_tool"])
        #     baked = BakeResult(
        #         template_path,
        #         template_path_hash,
        #         frozendict(extra_context),
        #         output_path,
        #         Path(output_project),
        #         output_context,
        #         build_tool,
        #     )
        #     return baked

        output_path.mkdir(exist_ok=True, parents=True)

        if not TEST_RAPID:
            logging.info("cleaning output_path = %s", output_path)
            rmtree(
                output_path,
                ignore_errors=True,
                onerror=lambda function, path, excinfo: logging.info(
                    "rmtree error: function = %s, path = %s, excinfo = %s",
                    function,
                    path,
                    excinfo,
                ),
            )

        # Render the context, so that we can store it on the Result
        context: dict[str, Any] = prompt_for_config(
            generate_context(
                context_file=str(context_file), extra_context=extra_context
            ),
            no_input=True,
        )

        # Run cookiecutter to generate a new project
        project_dir = cookiecutter(
            str(template_path),
            no_input=True,
            extra_context=extra_context,
            output_dir=str(output_path),
            # config_file=str(self._config_file),
            overwrite_if_exists=True if TEST_RAPID else False,
            # overwrite_if_exists=True,
        )
        project_path = Path(project_dir)

        output_context_path.write_text(json.dumps(context))
        output_project_path.write_text(json.dumps(str(project_path)))
        logging.debug("project_path = %s", project_path)

        build_tool = BuildTool(context["build_tool"])
        baked = BakeResult(
            template_path,
            template_path_hash,
            frozendict(extra_context),
            output_path,
            project_path,
            context,
            build_tool,
        )

        if baked.build_tool == BuildTool.GNU_MAKE:
            configure_commands = """
make configure
make validate-fix
"""
        elif baked.build_tool == BuildTool.GO_TASK:
            configure_commands = """
task configure
task validate:fix
"""
        elif baked.build_tool == BuildTool.POE:
            configure_commands = """
poetry install
poetry run poe validate-fix
"""
        try:
            subprocess.run(
                cwd=baked.project_path,
                env=ESCAPED_ENV,
                check=True,
                args=[
                    "bash",
                    "-c",
                    f"""
    set -x
    set -eo pipefail
    # env | sort
    poetry lock
    {configure_commands}
    """,
                ],
            )
        except Exception:
            logging.error("failed to configure project, cleaning up %s", output_path)
            rmtree(
                output_path,
                ignore_errors=True,
                onerror=lambda function, path, excinfo: logging.info(
                    "rmtree error: function = %s, path = %s, excinfo = %s",
                    function,
                    path,
                    excinfo,
                ),
            )
            raise
        return baked


BAKER = Baker()


class WorkflowAction(enum.Enum):
    VALIDATE = "validate"
    CLI = "cli"


WORKFLOW_ACTION_FACTORIES: dict[
    tuple[WorkflowAction, BuildTool], Callable[[BakeResult], str]
] = {
    (WorkflowAction.VALIDATE, BuildTool.GNU_MAKE): lambda result: "make validate",
    (WorkflowAction.VALIDATE, BuildTool.GO_TASK): lambda result: "task validate",
    (WorkflowAction.VALIDATE, BuildTool.POE): lambda result: "poetry run poe validate",
    (
        WorkflowAction.CLI,
        BuildTool.GNU_MAKE,
    ): lambda result: f'poetry run {result.context["cli_name"]} -vvvv sub leaf 1 2 3',
    (
        WorkflowAction.CLI,
        BuildTool.GO_TASK,
    ): lambda result: f'task venv:run -- {result.context["cli_name"]} -vvvv sub leaf 1 2 3',
    (
        WorkflowAction.CLI,
        BuildTool.POE,
    ): lambda result: f'poetry run {result.context["cli_name"]} -vvvv sub leaf 1 2 3',
}


def make_baked_cmd_cases() -> Generator[ParameterSet, None, None]:
    config_names = {"minimal", "basic", "poe_minimal", "minimal_typer"}
    for config_name, workflow_action in itertools.product(
        config_names,
        WorkflowAction,
    ):
        extra_context = load_test_config(config_name)["default_context"]
        if config_name == "everything":
            extra_context["init_git"] = "y"
        yield pytest.param(
            extra_context, workflow_action, id=f"{config_name}-{workflow_action}"
        )


@pytest.mark.parametrize(["extra_context", "workflow_action"], make_baked_cmd_cases())
def test_baked_cmd(
    extra_context: dict[str, Any],
    workflow_action: WorkflowAction,
) -> None:
    result = BAKER.bake(extra_context, template_path=PROJECT_PATH)
    project_path = result.project_path
    logging.info("result = %s, project_path = %s", result, project_path)
    subprocess.run(
        cwd=project_path,
        env=ESCAPED_ENV,
        check=True,
        args=[
            "bash",
            "-c",
            f"""
set -eo pipefail
set -x
{WORKFLOW_ACTION_FACTORIES[workflow_action, result.build_tool](result)}
    """,
        ],
    )
