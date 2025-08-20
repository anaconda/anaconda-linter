"""
File:           conftest.py
Description:    Provides utilities and test fixtures for test files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final, Optional
from unittest.mock import mock_open, patch

import pytest
from percy.render._renderer import RendererType
from percy.render.recipe import Recipe
from percy.render.variants import Variant, read_conda_build_config

from anaconda_linter import utils
from anaconda_linter.lint import AutoFixState, Linter, LintMessage

# Locations of test files
TEST_FILES_PATH: Final[str] = "tests/test_aux_files"
TEST_AUTO_FIX_FILES_PATH: Final[str] = f"{TEST_FILES_PATH}/auto_fix"


def get_test_path() -> Path:
    """
    Returns a path object that points to the directory containing all auxiliary testing files.
    """
    return Path(TEST_FILES_PATH)


@pytest.fixture()
def linter() -> Linter:
    """Sets up linter for use in other tests"""
    config_file = Path(__file__).parent / "config.yaml"
    config = utils.load_config(config_file)
    return Linter(config=config)


@pytest.fixture()
def base_yaml() -> str:
    """Adds the minimum keys needed for a meta.yaml file"""
    yaml_str = """\
        package:
          name: test_package
          version: 0.0.1
        """
    return yaml_str


@pytest.fixture()
def recipe_dir(tmpdir) -> Path:
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
    :return: A list containing errors or warnings for the target rule.
    """
    linter_obj, recipe = load_linter_and_recipe(recipe_str, arch, expand_variant)
    messages = linter_obj.check_instances[check_name].run(recipe=recipe)
    return messages


def check_dir(check_name: str, feedstock_dir: str | Path, recipe_str: str, arch: str = "linux-64") -> list[LintMessage]:
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


def read_recipe_content(recipe_file: str) -> str:
    """
    Helper function to read the content of a recipe file.
    :param recipe_file: Path to the recipe file to read
    :return: The content of the recipe file as a string
    """
    with open(recipe_file, encoding="utf-8") as f:
        return f.read()


def assert_lint_messages(recipe_file: str, lint_check: str, msg_title: str, msg_count: int = 1):
    """
    Assert that a recipe file has a specific number of lint messages for a specific lint check.
    :param recipe_file: Path to the recipe file to read
    :param lint_check: Name of the linting rule. This corresponds with input and output files.
    :param msg_title: Title of the lint message to check for
    :param msg_count: Number of lint messages to expect
    """
    recipe_file_path: Final[Path] = get_test_path() / recipe_file
    messages: Final = check(lint_check, read_recipe_content(recipe_file_path))
    assert len(messages) == msg_count and all(msg_title in msg.title for msg in messages)


def assert_no_lint_message(recipe_file: str, lint_check: str) -> None:
    """
    Assert that a recipe file has no lint messages for a specific lint check.
    :param recipe_file: Path to the recipe file to read
    :param lint_check: Name of the linting rule. This corresponds with input and output files.
    """
    recipe_file_path: Final[Path] = get_test_path() / recipe_file
    messages: Final = check(lint_check, read_recipe_content(recipe_file_path))
    assert len(messages) == 0


def assert_on_auto_fix(check_name: str, suffix: str, arch: str) -> None:
    """
    Utility function executes a fix function against an offending recipe file. Then asserts the resulting file against
    a known fixed equivalent of the offending recipe file.
    :param check_name:      Name of the linting rule. This corresponds with input and output files.
    :param suffix:          Standardized suffix used in the file format. This allows us to test multiple
                            variants of input-to-expected-output files. If non-empty, the files should be named:
                            `<check_name>_<suffix>.yaml` and `<check_name>_<suffix>_fixed.yaml`, respectively.
    :param arch:            Target architecture to render recipe as
    """
    suffix_adjusted: Final[str] = f"_{suffix}" if suffix else ""
    broken_file: Final[str] = f"{TEST_AUTO_FIX_FILES_PATH}/{check_name}{suffix_adjusted}.yaml"
    fixed_file: Final[str] = f"{TEST_AUTO_FIX_FILES_PATH}/{check_name}{suffix_adjusted}_fixed.yaml"

    linter_obj, recipe = load_linter_and_recipe(load_file(broken_file), arch)

    messages: list[LintMessage]
    # Prevent writing to the test file. The `Recipe` instance will contain the file contents of interest in a string
    with patch("builtins.open", mock_open()):
        messages = linter_obj.check_instances[check_name].run(recipe=recipe, fix=True)

    # Ensure that the rule triggered, that the correct rule triggered, and that the rule was actually fixed
    assert len(messages) == 1
    assert messages[0].auto_fix_state == AutoFixState.FIX_PASSED
    assert str(messages[0].check) == check_name
    # Ensure that the output matches the expected output
    assert recipe.dump() == load_file(fixed_file)
