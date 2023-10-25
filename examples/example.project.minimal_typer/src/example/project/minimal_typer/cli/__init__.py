#!/usr/bin/env python3
import logging
import os
import sys
from typing import Annotated

import typer

from .._version import __version__
from .sub import cli_sub

logger = logging.getLogger(__name__)

"""
https://click.palletsprojects.com/en/7.x/api/#parameters
https://click.palletsprojects.com/en/7.x/options/
https://click.palletsprojects.com/en/7.x/arguments/
https://typer.tiangolo.com/
https://typer.tiangolo.com/tutorial/options/
"""


cli = typer.Typer(pretty_exceptions_enable=False)
cli.add_typer(cli_sub, name="sub")


@cli.callback()
def cli_callback(
    ctx: typer.Context, verbosity: Annotated[int, typer.Option("--verbose", "-v", count=True)] = 0
) -> None:
    if verbosity is not None:
        root_logger = logging.getLogger("")
        root_logger.propagate = True
        new_level = (
            root_logger.getEffectiveLevel()
            - (min(1, verbosity)) * 10
            - min(max(0, verbosity - 1), 9) * 1
        )
        root_logger.setLevel(new_level)
    logger.debug(
        "entry: ctx_parent_params = %s, ctx_params = %s",
        ({} if ctx.parent is None else ctx.parent.params),
        ctx.params,
    )
    logger.debug(
        "log info: logging_effective_level = %s",
        logging.getLogger("").getEffectiveLevel(),
    )


@cli.command("version")
def cli_version(ctx: typer.Context) -> None:
    sys.stderr.write(f"{__version__}\n")


def main() -> None:
    setup_logging()
    cli()


def setup_logging() -> None:
    logging.basicConfig(
        level=os.environ.get("PYTHON_LOGGING_LEVEL", logging.INFO),
        stream=sys.stderr,
        datefmt="%Y-%m-%dT%H:%M:%S",
        format=(
            "%(asctime)s.%(msecs)03d %(process)d %(thread)d %(levelno)03d:%(levelname)-8s "
            "%(name)-12s %(module)s:%(lineno)s:%(funcName)s %(message)s"
        ),
    )


if __name__ == "__main__":
    main()
