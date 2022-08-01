import hashlib
import itertools
import json
import logging
import os
import pickle
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Mapping, Set, TypeVar

import pytest
import yaml
from _pytest.mark.structures import ParameterSet
from cookiecutter.generate import generate_context
from cookiecutter.main import cookiecutter
from cookiecutter.prompt import prompt_for_config
from frozendict import frozendict

SCRIPT_PATH = Path(__file__)
PROJECT_PATH = SCRIPT_PATH.parent.parent
TEST_DATA_PATH = SCRIPT_PATH.parent / "data"


def load_test_config(name: str) -> Dict[str, Any]:
    config = yaml.safe_load(
        (TEST_DATA_PATH / "cookie-config" / f"{name}.yaml").read_text()
    )
    # default_context = config["default_context"]
    assert isinstance(config, dict)
    logging.info("name = %s, config = %s", name, config)
    return config


def escape_venv(environ: Mapping[str, str]) -> Dict[str, str]:
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
    project_path: Path
    context: Dict[str, Any]


AnyT = TypeVar("AnyT")

TEST_RAPID = json.loads(os.environ.get("TEST_RAPID", "false"))
assert isinstance(TEST_RAPID, bool)


def hash_path(
    root: Path,
    exclude_subdirs: Set[str],
    hash: Callable[[], "hashlib._Hash"] = hashlib.sha256,
) -> str:
    hasher = hash()
    for _dirpath, dirnames, filenames in os.walk(root):
        dirpath = Path(_dirpath)
        logging.info("exclude_subdirs = %s", exclude_subdirs)
        for dirname in list(dirnames):
            relative_dirname = (dirpath / dirname).relative_to(root)
            logging.debug("relative_dirname = %s", relative_dirname)
            if str(relative_dirname) in exclude_subdirs:
                dirnames.remove(dirname)
        dirnames.sort()
        filenames.sort()
        logging.info("dirpath = %s", dirpath)
        logging.info("dirnames = %s", dirnames)
        logging.info("filenames = %s", filenames)
        for dirname in dirnames:
            subdir_path = dirpath / dirname
            hasher.update(str(subdir_path).encode("utf-8"))
        for filename in filenames:
            file_path = dirpath / filename
            hasher.update(str(file_path).encode("utf-8"))
            hasher.update(file_path.read_bytes())

    return hasher.hexdigest()


def hash_object(
    object: Any, hash: Callable[[], "hashlib._Hash"] = hashlib.sha256
) -> str:
    pickled = pickle.dumps(object)
    hasher = hash()
    hasher.update(pickled)
    return hasher.hexdigest()


ESCAPED_ENV = escape_venv(os.environ)


class Baker:
    def __init__(self) -> None:
        # self._counter = 0
        # self._tmp_path = Path(mkdtemp(prefix=f"Baker-{__name__}-"))
        self._baked: Dict[BakeKey, BakeResult] = {}

    def bake(self, extra_context: Dict[str, Any], template_path: Path) -> BakeResult:
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
            return self._baked[key]

        output_path = Path(tempfile.gettempdir()) / f"baked-cookie-{key_hash}"
        output_context_path = output_path.parent / f"{output_path.name}-context.json"
        output_project_path = output_path.parent / f"{output_path.name}-project.json"

        if output_path.exists() and not TEST_RAPID:

            output_context = json.loads(output_context_path.read_text())
            output_project = json.loads(output_project_path.read_text())
            baked = BakeResult(
                template_path,
                template_path_hash,
                frozendict(extra_context),
                Path(output_project),
                output_context,
            )
            return baked

        output_path.mkdir(exist_ok=True, parents=True)

        # Render the context, so that we can store it on the Result
        context: Dict[str, Any] = prompt_for_config(
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
        )
        project_path = Path(project_dir)

        output_context_path.write_text(json.dumps(context))
        output_project_path.write_text(json.dumps(str(project_path)))

        baked = BakeResult(
            template_path,
            template_path_hash,
            frozendict(extra_context),
            project_path,
            context,
        )

        subprocess.run(
            cwd=baked.project_path,
            env=ESCAPED_ENV,
            check=True,
            args=[
                "bash",
                "-c",
                """
            set -x
            set -eo pipefail
            # env | sort
            task configure
            task validate:fix
        """,
            ],
        )

        return baked


BAKER = Baker()


def make_baked_cmd_cases() -> Generator[ParameterSet, None, None]:
    config_names = {"minimal", "basic"}
    for config_name, (cmd_name, cmd) in itertools.product(
        config_names,
        [
            (
                "validate",
                lambda result: "task validate",
            ),
            (
                "cli",
                lambda result: f'task venv:run -- {result.context["cli_name"]} -vvvv sub leaf',
            ),
        ],
    ):
        extra_context = load_test_config(config_name)["default_context"]
        if config_name == "everything":
            extra_context["init_git"] = "y"
        yield pytest.param(extra_context, cmd, id=f"{config_name}-{cmd_name}")


@pytest.mark.parametrize(["extra_context", "cmd"], make_baked_cmd_cases())
def test_baked_cmd(
    extra_context: Dict[str, Any], cmd: Callable[[BakeResult], str]
) -> None:
    result = BAKER.bake(extra_context, template_path=PROJECT_PATH)
    logging.info("result = %s", result)
    subprocess.run(
        cwd=result.project_path,
        env=ESCAPED_ENV,
        check=True,
        args=[
            "bash",
            "-c",
            f"""
set -eo pipefail
set -x
{cmd(result)}
    """,
        ],
    )
