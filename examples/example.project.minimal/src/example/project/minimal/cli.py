#!/usr/bin/env python3
import argparse
import logging
import os
import sys
from dataclasses import dataclass, field

from ._version import __version__

logger = logging.getLogger(__name__)


@dataclass
class Application:
    parser: argparse.ArgumentParser = field(
        default_factory=lambda: argparse.ArgumentParser(add_help=True)
    )

    def __post_init__(self) -> None:
        parser = self.parser
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            dest="verbose",
            help="increase verbosity level",
            default=False,
        )
        parser.add_argument(
            "--version", action="version", version=f"%(prog)s {__version__}"
        )
        parser.set_defaults(handler=self.handle)
        current_parser = parser
        current_subparsers = current_parser.add_subparsers()
        current_parser = current_subparsers.add_parser("sub")
        current_subparsers = current_parser.add_subparsers()
        current_parser = current_subparsers.add_parser("leaf")
        current_parser.set_defaults(handler=self.cli_sub_leaf)
        current_parser.add_argument("target", nargs="*", type=str)

    def run(self, args: list[str]) -> None:
        parse_result = self.parser.parse_args(args)

        if parse_result.verbose:
            logging.root.propagate = True
            logging.root.setLevel(logging.DEBUG)

        logging.debug(
            "sys.executable = %s, args = %s, parse_result = %s, logging.level = %s",
            sys.executable,
            args,
            parse_result,
            logging.getLogger("").getEffectiveLevel(),
        )

        parse_result.handler(parse_result)

    def handle(self, parse_result: argparse.Namespace) -> None:
        logging.debug("entry ...")

    def cli_sub_leaf(self, parse_result: argparse.Namespace) -> None:
        logging.debug("entry ...")


def main() -> None:
    setup_logging()
    Application().run(sys.argv[1:])


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
