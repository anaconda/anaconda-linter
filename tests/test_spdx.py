from anaconda_linter.lint.check_spdx import incorrect_license
from anaconda_linter.recipe import Recipe


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
