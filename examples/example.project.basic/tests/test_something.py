import logging

from example.project.basic import package_function


def test_something() -> None:
    logging.info("entry: ...")
    assert package_function() == "value"
