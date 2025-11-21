import logging
import sys


def test_something() -> None:
    logging.info("entry: ...")
    assert sys.version_info >= (3, 8)
