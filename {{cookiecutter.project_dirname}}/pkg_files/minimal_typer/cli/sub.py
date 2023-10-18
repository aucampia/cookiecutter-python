#!/usr/bin/env python3
from __future__ import annotations

import logging
from typing import Optional

import typer

logger = logging.getLogger(__name__)
cli_sub = typer.Typer()


@cli_sub.callback()
def cli_sub_callback(ctx: typer.Context) -> None:
    logger.debug(
        "entry: ctx_parent_params = %s, ctx_params = %s",
        ({} if ctx.parent is None else ctx.parent.params),
        ctx.params,
    )


@cli_sub.command("leaf")
def cli_sub_leaf(
    ctx: typer.Context,
    name: Optional[str] = typer.Option("fake", "--name", "-n", help="The name ..."),
    numbers: Optional[list[int]] = typer.Argument(None),
) -> None:
    logger.debug(
        "entry: ctx_parent_params = %s, ctx_params = %s",
        ({} if ctx.parent is None else ctx.parent.params),
        ctx.params,
    )
