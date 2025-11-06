# {% raw %}

import json
import logging
import os
import sys
from pathlib import Path

# https://cookiecutter.readthedocs.io/en/latest/advanced/hooks.html


logger = logging.getLogger(
    __name__ if __name__ != "__main__" else "hooks.pre_gen_project"
)

# {% endraw %}
COOKIECUTTER_JSON = """{{ cookiecutter | tojson('  ') }}"""
# {% raw %}
COOKIECUTTER = json.loads(COOKIECUTTER_JSON)

SCRIPT_PATH = Path(__file__)
COOKIE_PATH = SCRIPT_PATH.parent.parent


def apply() -> None:
    logger.info("entry: ...")
    logger.debug("os.getcwd() = %s", os.getcwd())
    logger.debug("SCRIPT_PATH = %s", SCRIPT_PATH.absolute())
    logger.debug("COOKIE_PATH = %s", COOKIE_PATH.absolute())
    logger.debug("cookiecutter_json = %s", COOKIECUTTER_JSON)


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("PYLOGGING_LEVEL", logging.INFO),
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
