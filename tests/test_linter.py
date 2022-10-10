import os
from collections import OrderedDict

import pytest
from ruamel_yaml import YAML

from anaconda_linter import utils
from anaconda_linter.lint import Linter
from anaconda_linter.lint.check_spdx import incorrect_license
from anaconda_linter.recipe import Recipe

yaml = YAML(typ="rt")


def test_stub():
    assert True


@pytest.fixture
def linter():
    """Sets up linter for use in other fixtures"""
    config_file = os.path.abspath(os.path.dirname(__file__) + "/../anaconda_linter/config.yaml")
    config = utils.load_config(config_file)
    linter = Linter(config)
    return linter


def test_spdx_good(linter):
    d = OrderedDict()
    d["about/license"] = "BSD-3-Clause"
    lintcheck = incorrect_license(_linter=linter)
    messages = lintcheck.check_recipe(recipe=d)
    assert messages is None


def test_spdx_bad(linter):
    # creating an ordered dict won't work,
    yaml_str = """\
        about:
          license: BSE-3-Clause
        """
    print(yaml_str)
    recipe = Recipe.from_file("tests/good-feedstock/recipe/meta.yaml")
    recipe.render()
    # one solution is to then insert a value into the recipe
    # recipe.meta['about'].insert(1, 'license', 'BSE-3-Clause')
    # data = yaml.load("good-feedstock/recipe/meta.yaml")
    # data['about'].insert(1, 'license', 'BSE-3-Clause')
    # create a recipe from this
    lintcheck = incorrect_license(_linter=linter)
    messages = lintcheck.check_recipe(recipe=recipe)
    assert len(messages) > 0
