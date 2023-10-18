from pathlib import Path

import pytest
from percy.render.recipe import Recipe, RendererType
from percy.render.variants import read_conda_build_config

from anaconda_linter import utils
from anaconda_linter.lint import Linter


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


def check(check_name, recipe_str, arch="linux-64", expand_variant=None):
    config_file = Path(__file__).parent / "config.yaml"
    config = utils.load_config(str(config_file.resolve()))
    linter = Linter(config=config)
    variant = config[arch]
    if expand_variant:
        variant.update(expand_variant)
    recipe = Recipe.from_string(
        recipe_text=recipe_str,
        variant_id="dummy",
        variant=variant,
        renderer=RendererType.RUAMEL,
    )
    messages = linter.check_instances[check_name].run(recipe=recipe)
    return messages


def check_dir(check_name, feedstock_dir, recipe_str, arch="linux-64"):
    if not isinstance(feedstock_dir, Path):
        feedstock_dir = Path(feedstock_dir)
    config_file = Path(__file__).parent / "config.yaml"
    config = utils.load_config(str(config_file.resolve()))
    linter = Linter(config=config)
    recipe_dir = feedstock_dir / "recipe"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    meta_yaml = recipe_dir / "meta.yaml"
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
    messages = linter.check_instances[check_name].run(recipe=recipe)
    return messages
