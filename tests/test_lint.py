import os
import tempfile

import pytest
from conftest import check

from anaconda_linter import lint, utils
from anaconda_linter.lint import ERROR, INFO, WARNING
from anaconda_linter.recipe import Recipe, RecipeError


class dummy_info(lint.LintCheck):
    def check_recipe(self, recipe):
        self.message("Info message", severity=INFO)


class dummy_warning(lint.LintCheck):
    def check_recipe(self, recipe):
        self.message("Warning message", severity=WARNING)


class dummy_error(lint.LintCheck):
    def check_recipe(self, recipe):
        self.message("Error message", severity=ERROR)


def test_only_lint(base_yaml, linter):
    yaml_str = (
        base_yaml
        + """
        extra:
          only-lint:
            - dummy_info
            - dummy_error
            - dummy_warning
        """
    )
    recipes = [Recipe.from_string(yaml_str)]
    linter.lint(recipes)
    assert len(linter.get_messages()) == 3


def test_skip_lints(base_yaml, linter):
    yaml_str = (
        base_yaml
        + """
        extra:
          skip-lints:
            - dummy_info
            - dummy_error
            - dummy_warning
        """
    )
    recipes_base = [Recipe.from_string(base_yaml)]
    linter.lint(recipes_base)
    messages_base = linter.get_messages()
    linter.clear_messages()
    assert len(linter.get_messages()) == 0
    recipes_skip = [Recipe.from_string(yaml_str)]
    linter.lint(recipes_skip)
    messages_skip = linter.get_messages()
    assert len(messages_base) == len(messages_skip) + 3


def test_lint_none(base_yaml, linter):
    recipes = []
    return_code = linter.lint(recipes)
    assert return_code == 0 and len(linter.get_messages()) == 0


def test_lint_file(base_yaml, linter):
    yaml_str = (
        base_yaml
        + """
        extra:
          only-lint:
            - dummy_info
            - dummy_error
            - dummy_warning
        """
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        recipe_dir = os.path.join(tmpdir, "recipe")
        os.mkdir(recipe_dir)
        meta_yaml = os.path.join(recipe_dir, "meta.yaml")
        with open(meta_yaml, "w") as f:
            f.write(yaml_str)
        linter.lint([recipe_dir])
        assert len(linter.get_messages()) == 3


def test_severity_level(base_yaml):
    levels = [
        {
            "enum": INFO,
            "string": "notice",
            "check": "dummy_info",
        },
        {
            "enum": WARNING,
            "string": "warning",
            "check": "dummy_warning",
        },
        {
            "enum": ERROR,
            "string": "failure",
            "check": "dummy_error",
        },
    ]
    for lvl in levels:
        messages = check(lvl["check"], base_yaml)
        assert len(messages) == 1
        assert messages[0].severity == lvl["enum"]
        assert messages[0].get_level() == lvl["string"]


def test_severity_min(base_yaml):
    yaml_str = (
        base_yaml
        + """
        extra:
          only-lint:
            - dummy_info
            - dummy_error
            - dummy_warning
        """
    )
    recipes = [Recipe.from_string(yaml_str)]
    config_file = os.path.abspath(os.path.dirname(__file__) + "/../anaconda_linter/config.yaml")
    config = utils.load_config(config_file)
    # Test string representation
    for s, sev in enumerate(["INFO", "WARNING", "ERROR"]):
        linter = lint.Linter(config=config, severity_min=sev)
        linter.lint(recipes)
        assert len(linter.get_messages()) == 3 - s
    with pytest.raises(ValueError):
        linter = lint.Linter(config=config, severity_min="BADSEVERITY")

    # Test enum representation
    for s, sev in enumerate([INFO, WARNING, ERROR]):
        linter = lint.Linter(config=config, severity_min=sev)
        linter.lint(recipes)
        assert len(linter.get_messages()) == 3 - s


def test_lint_list():
    checks_file = os.path.abspath(os.path.dirname(__file__) + "/../anaconda_linter/lint_names.md")
    with open(checks_file) as f:
        lint_checks_file = [line.strip() for line in f.readlines() if line.strip()]
    lint_checks_lint = [str(chk) for chk in lint.get_checks() if not str(chk).startswith("dummy_")]
    assert sorted(lint_checks_file) == sorted(lint_checks_lint)


@pytest.mark.parametrize(
    "jinja_func,expected",
    [
        ("cran_mirror", False),
        ("compiler('c')", False),
        ("cdt('cdt-cos6-plop')", False),
        (
            "pin_compatible('dotnet-runtime', min_pin='x.x.x.x.x.x', max_pin='x', lower_bound=None, upper_bound=None)",
            False,
        ),
        ("pin_subpackage('dotnet-runtime', min_pin='x.x.x.x.x.x', max_pin='x', exact=True)", False),
        ("pin_subpackage('dotnet-runtime', min_pin='x.x.x.x.x.x', max_pin='x')", False),
        ("pin_subpackage('dotnet-runtime', exact=True)", False),
        ("pin_subpackage('dotnet-runtime', min_pin='x.x.x.x.x.x')", False),
        ("pin_subpackage('dotnet-runtime', exact=True, badParam=False)", True),
    ],
)
def test_jinja_functions(base_yaml, jinja_func, expected):
    def run_lint(yaml_str):
        config_file = os.path.abspath(os.path.dirname(__file__) + "/../anaconda_linter/config.yaml")
        config = utils.load_config(config_file)
        linter = lint.Linter(config=config)

        try:
            _recipe = Recipe.from_string(yaml_str)
            linter.lint([_recipe])
            messages = linter.get_messages()
        except RecipeError as exc:
            _recipe = Recipe("")
            check_cls = lint.recipe_error_to_lint_check.get(exc.__class__, lint.linter_failure)
            messages = [check_cls.make_message(recipe=_recipe, line=getattr(exc, "line"))]

        return messages

    yaml_str = (
        base_yaml
        + f"""
        build:
          number: 0

        outputs:
          - name: dotnet
            version: 1
            requirements:
              run:
                - {{{{ {jinja_func} }}}}

        """
    )

    lint_check = "jinja_render_failure"
    messages = run_lint(yaml_str)
    assert any([str(msg.check) == lint_check for msg in messages]) == expected


def test_error_report_line(base_yaml):
    yaml_str = (
        base_yaml
        + """
        plop # [aaa]
        plip # [aaa]
        plep # [aaa]
        about:
          license: BSE-3-Clause
        """
    )
    lint_check = "incorrect_license"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and messages[0].start_line == 5
