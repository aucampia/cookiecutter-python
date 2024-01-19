#!/usr/bin/env python3
from __future__ import annotations

from typing import Annotated, Optional

import structlog
import typer
from structlog.types import FilteringBoundLogger

logger: FilteringBoundLogger = structlog.get_logger(__name__)

"""
https://click.palletsprojects.com/en/7.x/api/#parameters
https://click.palletsprojects.com/en/7.x/options/
https://click.palletsprojects.com/en/7.x/arguments/
https://typer.tiangolo.com/
https://typer.tiangolo.com/tutorial/options/
"""


cli_sub = typer.Typer()


@cli_sub.callback()
def cli_sub_callback(ctx: typer.Context) -> None:
    logger.debug(
        "entry",
        ctx_parent_params=({} if ctx.parent is None else ctx.parent.params),
        ctx_params=ctx.params,
    )


@cli_sub.command("leaf")
def cli_sub_leaf(
    ctx: typer.Context,
    namez: Annotated[
        Optional[str], typer.Option("--namex", "-n", help="The name ...")
    ] = "fake",
    numbers: Optional[list[int]] = typer.Argument(None),
) -> None:
    logger.debug(
        "entry",
        ctx_parent_params=({} if ctx.parent is None else ctx.parent.params),
        ctx_params=ctx.params,
    )
