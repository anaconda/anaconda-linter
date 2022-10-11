import os

import pytest
from ruamel_yaml import YAML

import anaconda_linter.utils as utils
from anaconda_linter.lint import Linter
from anaconda_linter.lint.check_spdx import incorrect_license
from anaconda_linter.recipe import Recipe

yaml = YAML(typ="rt")


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


def test_spdx_good(linter, base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
          license: BSD-3-Clause
        """
    )
    recipe = Recipe.from_string(yaml_str)
    recipe.render()
    lintcheck = incorrect_license(_linter=linter)
    messages = lintcheck.run(recipe=recipe)
    assert len(messages) == 0


def test_spdx_bad(linter, base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
          license: AARP-50+
        """
    )
    recipe = Recipe.from_string(yaml_str)
    recipe.render()
    lintcheck = incorrect_license(_linter=linter)
    messages = lintcheck.run(recipe=recipe)
    assert len(messages) == 1 and "closest match" not in messages[0].title


def test_spdx_close(linter, base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
          license: BSE-3-Clause
        """
    )
    recipe = Recipe.from_string(yaml_str)
    recipe.render()
    lintcheck = incorrect_license(_linter=linter)
    messages = lintcheck.run(recipe=recipe)
    assert len(messages) == 1 and "closest match: BSD-3-Clause" in messages[0].title
