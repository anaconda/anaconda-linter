import os

import pytest

import anaconda_linter.utils as utils
from anaconda_linter.lint import Linter


@pytest.fixture()
def linter():
    """Sets up linter for use in other fixtures"""
    config_file = os.path.abspath(os.path.dirname(__file__) + "/../anaconda_linter/config.yaml")
    config = utils.load_config(config_file)
    linter = Linter(config)
    return linter


@pytest.fixture()
def base_yaml():
    yaml_str = """\
        package:
          name: test_package
          version: 0.0.1
        """
    return yaml_str
