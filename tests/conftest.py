from pathlib import Path

import pytest

from anaconda_linter import utils
from anaconda_linter.lint import Linter
from anaconda_linter.recipe import Recipe


@pytest.fixture()
def linter():
    """Sets up linter for use in other tests"""
    config_file = Path(__file__).parent / "config.yaml"
    config = utils.load_config(config_file)
    linter = Linter(config=config)
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


@pytest.fixture()
def recipe_dir(tmpdir):
    recipe_directory = Path(tmpdir) / "recipe"
    recipe_directory.mkdir(parents=True, exist_ok=True)
    return recipe_directory


def check(check_name, recipe_str):
    config_file = Path(__file__).parent / "config.yaml"
    config = utils.load_config(str(config_file.resolve()))
    linter = Linter(config=config)
    recipe = Recipe.from_string(recipe_str)
    messages = linter.check_instances[check_name].run(recipe=recipe)
    return messages


def check_dir(check_name, feedstock_dir, recipe_str):
    if not isinstance(feedstock_dir, Path):
        feedstock_dir = Path(feedstock_dir)
    config_file = Path(__file__).parent / "config.yaml"
    config = utils.load_config(str(config_file.resolve()))
    linter = Linter(config=config)
    recipe_dir = feedstock_dir / "recipe"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    meta_yaml = recipe_dir / "meta.yaml"
    meta_yaml.write_text(recipe_str)
    recipe = Recipe.from_file(str(meta_yaml))
    messages = linter.check_instances[check_name].run(recipe=recipe)
    return messages
