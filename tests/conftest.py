"""
File:           conftest.py
Description:    Provides utilities and test fixtures for test files.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final, Optional, Union
from unittest.mock import mock_open, patch

import pytest
from percy.render.recipe import Recipe, RendererType
from percy.render.variants import Variant, read_conda_build_config

from anaconda_linter import utils
from anaconda_linter.lint import Linter, LintMessage

# Locations of test files
TEST_FILES_PATH: Final[str] = "tests/test_aux_files"
TEST_AUTO_FIX_FILES_PATH: Final[str] = f"{TEST_FILES_PATH}/auto_fix"


@pytest.fixture()
def linter():
    """Sets up linter for use in other tests"""
    config_file = Path(__file__).parent / "config.yaml"
    config = utils.load_config(config_file)
    return Linter(config=config)


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


def load_file(file: Path | str) -> str:
    """
    Loads a file into a single string
    :param file:    Filename of the file to read
    :return: Text from the file
    """
    with open(Path(file), encoding="utf-8") as f:
        return f.read()


def load_linter_and_recipe(
    recipe_str: str, arch: str = "linux-64", expand_variant: Optional[Variant] = None
) -> tuple[Linter, Recipe]:
    """
    Convenience function that loads instantiates linter and recipe objects based on default configurations.
    :param recipe_str:      Recipe file, as a raw string
    :param arch:            (Optional) Target architecture to render recipe as
    :param expand_variant:  (Optional) Dictionary of variant information to augment the recipe with.
    :return: `Linter` and `Recipe` instances, as a tuple
    """
    config_file = Path(__file__).parent / "config.yaml"
    config = utils.load_config(str(config_file.resolve()))
    linter_obj = Linter(config=config)
    variant: Variant = config[arch]
    if expand_variant is not None:
        variant.update(expand_variant)
    recipe = Recipe.from_string(
        recipe_text=recipe_str,
        variant_id="dummy",
        variant=variant,
        renderer=RendererType.RUAMEL,
    )
    return linter_obj, recipe


def check(
    check_name: str,
    recipe_str: str,
    arch: str = "linux-64",
    expand_variant: Optional[Variant] = None,
) -> list[LintMessage]:
    """
    Utility function that checks a linting rule against a recipe file.
    :param check_name:      Name of the linting rule. This corresponds with input and output files.
    :param recipe_str:      Recipe file, as a single string.
    :param arch:            (Optional) Target architecture to render recipe as
    :param expand_variant:  (Optional) Dictionary of variant information to augment the recipe with.
    """
    linter_obj, recipe = load_linter_and_recipe(recipe_str, arch, expand_variant)
    messages = linter_obj.check_instances[check_name].run(recipe=recipe)
    return messages


def check_dir(
    check_name: str, feedstock_dir: Union[str, Path], recipe_str: str, arch: str = "linux-64"
) -> list[LintMessage]:
    """
    Utility function that checks a linting rule against a feedstock directory.
    :param check_name:      Name of the linting rule. This corresponds with input and output files.
    :param feedstock_dir:   Path to feedstock directory to use.
    :param recipe_str:      Recipe file, as a single string.
    :param arch:            (Optional) Target architecture to render recipe as
    """
    if not isinstance(feedstock_dir, Path):
        feedstock_dir = Path(feedstock_dir)
    config_file = Path(__file__).parent / "config.yaml"
    config = utils.load_config(str(config_file.resolve()))
    linter_obj = Linter(config=config)
    recipe_directory = feedstock_dir / "recipe"
    recipe_directory.mkdir(parents=True, exist_ok=True)
    meta_yaml = recipe_directory / "meta.yaml"
    meta_yaml.write_text(recipe_str)
    variants = read_conda_build_config(recipe_path=meta_yaml, subdir=arch)
    if variants:
        # for when a cbc is provided
        (vid, variant) = variants[0]
    else:
        # for when no cbc is provided
        vid = "dummy"
        variant = config[arch]
    recipe = Recipe.from_file(
        recipe_fname=str(meta_yaml), variant_id=vid, variant=variant, renderer=RendererType.RUAMEL
    )
    messages = linter_obj.check_instances[check_name].run(recipe=recipe)
    return messages


def assert_on_auto_fix(check_name: str, arch: str = "linux-64") -> None:
    """
    Utility function executes a fix function against an offending recipe file. Then asserts the resulting file against
    a known fixed equivalent of the offending recipe file.
    :param check_name:      Name of the linting rule. This corresponds with input and output files.
    :param arch:            (Optional) Target architecture to render recipe as
    """
    broken_file: Final[str] = f"{TEST_AUTO_FIX_FILES_PATH}/{check_name}.yaml"
    fixed_file: Final[str] = f"{TEST_AUTO_FIX_FILES_PATH}/{check_name}_fixed.yaml"

    linter_obj, recipe = load_linter_and_recipe(load_file(broken_file), arch)

    messages: list[LintMessage]
    # Prevent writing to the test file. The `Recipe` instance will contain the file contents of interest in a string
    with patch("builtins.open", mock_open()):
        messages = linter_obj.check_instances[check_name].run(recipe=recipe, fix=True)

    # Fixed issues emit no messages
    assert len(messages) == 0
    assert recipe.dump() == load_file(fixed_file)
