import os

import pytest

from anaconda_linter import utils
from anaconda_linter.lint import Linter
from anaconda_linter.recipe import Recipe


@pytest.fixture()
def linter():
    """Sets up linter for use in other tests"""
    config_file = os.path.abspath(os.path.dirname(__file__) + "/../anaconda_linter/config.yaml")
    config = utils.load_config(config_file)
    linter = Linter(config)
    return linter


@pytest.fixture()
def base_yaml():
    """Adds the minimum keys needed for a meta.yaml file"""
    yaml_str = """\
        package:
          name: test_package
          version: 0.0.1
        """
    return yaml_str


def check(check_name, recipe_str):
    config_file = os.path.abspath(os.path.dirname(__file__) + "/../anaconda_linter/config.yaml")
    config = utils.load_config(config_file)
    linter = Linter(config)
    recipe = Recipe.from_string(recipe_str)
    messages = linter.check_instances[check_name].run(recipe=recipe)
    return messages
