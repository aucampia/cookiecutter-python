import logging

from example.project.everything import package_function


def test_something() -> None:
    logging.info("entry: ...")
    assert package_function() == "value"
