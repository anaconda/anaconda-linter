import os

import pytest

from anaconda_linter.recipe import Recipe

try:
    from ruamel.yaml import YAML
except ModuleNotFoundError:
    from ruamel_yaml import YAML


yaml = YAML(typ="rt")  # pylint: disable=invalid-name
with open(os.path.join(os.path.dirname(__file__), "test_lint.yaml")) as data:
    TEST_DATA = yaml.load(data)
TEST_IDS = [datum["name"] for datum in TEST_DATA]


@pytest.mark.parametrize("test", TEST_DATA, ids=TEST_IDS)
def test_lint(linter, base_yaml, test):
    meta_yaml = yaml.load(base_yaml)
    meta_yaml.update(test.get("add", {}))
    recipe = Recipe.from_yaml(meta_yaml)
    check = test.get("check")
    messages = linter.check_instances[check].run(recipe=recipe)
    if test.get("pass", True):
        assert len(messages) == 0
    else:
        message = test.get("message", "")
        assert len(messages) == 1 and message in messages[0].title
