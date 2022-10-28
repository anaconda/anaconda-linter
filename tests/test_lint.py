import pytest
import os

from anaconda_linter import lint, utils
from anaconda_linter.lint import ERROR, INFO, WARNING
from anaconda_linter.recipe import Recipe


class dummy_info(lint.LintCheck):
    def check_recipe(self, recipe):
        self.message("Info message", severity=INFO)


class dummy_warning(lint.LintCheck):
    def check_recipe(self, recipe):
        self.message("Warning message", severity=WARNING)


class dummy_error(lint.LintCheck):
    def check_recipe(self, recipe):
        self.message("Error message", severity=ERROR)


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
    recipe = [Recipe.from_string(yaml_str)]
    config_file = os.path.abspath(os.path.dirname(__file__) + "/../anaconda_linter/config.yaml")
    config = utils.load_config(config_file)
    # Test string representation
    for s, sev in enumerate(["INFO", "WARNING", "ERROR"]):
        linter = lint.Linter(config=config, severity_min=sev)
        linter.lint(recipe)
        assert len(linter.get_messages()) == 3 - s
    with pytest.raises(ValueError) as e:
        linter = lint.Linter(config=config, severity_min="BADSEVERITY")

    # Test enum representation
    for s, sev in enumerate([INFO, WARNING, ERROR]):
        linter = lint.Linter(config=config, severity_min=sev)
        linter.lint(recipe)
        assert len(linter.get_messages()) == 3 - s


def test_lint_list():
    checks_file = os.path.abspath(os.path.dirname(__file__) + "/../anaconda_linter/lint_names.md")
    with open(checks_file) as f:
        lint_checks_file = [line.strip() for line in f.readlines() if line.strip()]
    lint_checks_lint = [str(chk) for chk in lint.get_checks() if not str(chk).startswith("dummy_")]
    assert sorted(lint_checks_file) == sorted(lint_checks_lint)
