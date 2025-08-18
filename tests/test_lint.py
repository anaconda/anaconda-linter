"""
File:           test_.py
Description:    Tests linting infrastructure
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest
from conda_recipe_manager.parser.recipe_reader_deps import RecipeReaderDeps
from conftest import check, check_dir
from percy.render._renderer import RendererType
from percy.render.exceptions import RecipeError
from percy.render.recipe import Recipe

from anaconda_linter import lint, utils
from anaconda_linter.lint import AutoFixState, Linter, LintMessage, Severity


class DummyInfo(lint.LintCheck):
    """
    Info message
    """

    def check_recipe(self, _) -> None:
        self.message(severity=Severity.INFO)


class DummyWarning(lint.LintCheck):
    """
    Warning message
    """

    def check_recipe(self, _) -> None:
        self.message(severity=Severity.WARNING)


class DummyError(lint.LintCheck):
    """
    Error message
    """

    def check_recipe(self, _) -> None:
        self.message(severity=Severity.ERROR)


class DummyErrorFormat(lint.LintCheck):
    """
    {} message of severity {}
    """

    def check_recipe(self, _) -> None:
        self.message("Dummy", "ERROR")


def test_only_lint(base_yaml: str, linter: Linter, recipe_dir: Path) -> None:
    yaml_str = (
        base_yaml
        + """
        extra:
          only-lint:
            - DummyInfo
            - DummyError
            - DummyWarning
        """
    )
    meta_yaml = recipe_dir / "meta.yaml"
    meta_yaml.write_text(yaml_str)
    linter.lint([str(recipe_dir)])
    assert len(linter.get_messages()) == 3


def test_skip_lints(base_yaml: str, linter: Linter, recipe_dir: Path) -> None:
    yaml_str = (
        base_yaml
        + """
        extra:
          skip-lints:
            - DummyInfo
            - DummyError
            - DummyWarning
        """
    )
    meta_yaml = recipe_dir / "meta.yaml"
    meta_yaml.write_text(base_yaml)
    linter.lint([str(recipe_dir)])
    messages_base = linter.get_messages()
    linter.clear_messages()
    assert len(linter.get_messages()) == 0
    meta_yaml.write_text(yaml_str)
    linter.lint([str(recipe_dir)])
    messages_skip = linter.get_messages()
    assert len(messages_base) == len(messages_skip) + 3


def test_lint_none(base_yaml: str, linter: Linter) -> None:  # pylint: disable=unused-argument
    recipes = []
    return_code = linter.lint(recipes)
    assert return_code == 0 and len(linter.get_messages()) == 0


def test_lint_file(base_yaml: str, linter, recipe_dir: Path) -> None:
    """
    Attempts to lint a fake recipe that should generate a known number of linting messages.
    """
    yaml_str = (
        base_yaml
        + """
        extra:
          only-lint:
            - DummyInfo
            - DummyError
            - DummyWarning
        """
    )
    meta_yaml = recipe_dir / "meta.yaml"
    meta_yaml.write_text(yaml_str)
    linter.lint([str(recipe_dir)])
    assert len(linter.get_messages()) == 3


def test_can_auto_fix(linter: lint.Linter):
    """
    Checks to see if the `can_auto_fix()` function is working as expected
    :param linter: Linter test fixture
    """

    # This class is auto-fixable as the function has been defined on the child class
    class DummyAutoFixableRule(lint.LintCheck):
        def fix(self) -> bool:
            return False

    # This class is not auto-fixable as it is using the default implementation of `fix()` in the parent class.
    class DummyNonAutoFixableRule(lint.LintCheck):
        pass

    assert DummyAutoFixableRule(linter).can_auto_fix()
    assert not DummyNonAutoFixableRule(linter).can_auto_fix()


@pytest.mark.parametrize(
    "level,string,lint_check",
    (
        (Severity.INFO, "notice", "DummyInfo"),
        (Severity.WARNING, "warning", "DummyWarning"),
        (Severity.ERROR, "failure", "DummyError"),
    ),
)
def test_severity_level(base_yaml: str, level: Severity, string: str, lint_check: str) -> None:
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1
    assert messages[0].severity == level
    assert messages[0].get_level() == string


@pytest.mark.parametrize("level,expected", ((Severity.INFO, 3), (Severity.WARNING, 2), (Severity.ERROR, 1)))
def test_severity_min_enum(base_yaml: str, level: Severity | str, expected: int, recipe_dir: Path) -> None:
    yaml_str = (
        base_yaml
        + """
        extra:
          only-lint:
            - DummyInfo
            - DummyError
            - DummyWarning
        """
    )
    meta_yaml = recipe_dir / "meta.yaml"
    meta_yaml.write_text(yaml_str)
    config_file = Path(__file__).parent / "config.yaml"
    config = utils.load_config(config_file)
    linter = lint.Linter(config=config, severity_min=level)
    linter.lint([str(recipe_dir)])
    assert len(linter.get_messages()) == expected


def test_lint_list() -> None:
    checks_file = Path(__file__).parent / "../anaconda_linter/lint_names.md"
    with open(checks_file.resolve(), encoding="utf-8") as f:
        lint_checks_file = [line.strip() for line in f.readlines() if line.strip()]
    lint_checks_lint = [str(chk) for chk in lint.get_checks() if not str(chk).startswith("Dummy")]
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
def test_jinja_functions(base_yaml: str, jinja_func: str, expected: bool, recipe_dir: Path) -> None:
    def run_lint(yaml_str: str) -> list[LintMessage]:
        config_file = Path(__file__).parent / "config.yaml"
        config = utils.load_config(config_file)
        linter = lint.Linter(config=config)

        # TODO figure out: 1 test fails if we remove this retry mechanism. Can we write the test differently so that
        # we don't have conditional logic in our tests?
        if not jinja_func == "pin_subpackage('dotnet-runtime', exact=True, badParam=False)":
            print(jinja_func)
            meta_yaml = recipe_dir / "meta.yaml"
            meta_yaml.write_text(yaml_str)
            linter.lint([str(recipe_dir)])
            messages = linter.get_messages()
            return messages

        # Only this test needs the weird exception handling
        # TODO: Investigate if we can remove this try/except block, and not pass a line to the section
        # argument in the make_message function
        try:
            recipe = Recipe.from_string(recipe_text=yaml_str, renderer=RendererType.RUAMEL)
        except RecipeError as exc:
            recipe = RecipeReaderDeps("")
            check_cls = lint.recipe_error_to_lint_check.get(exc.__class__, lint.linter_failure)
            messages = [check_cls.make_message(recipe=recipe, fname="recipe", section=getattr(exc, "line"))]
            return messages

        # Should not reach here
        assert 0

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
    assert any(str(msg.check) == lint_check for msg in messages) == expected


def test_error_report_line(base_yaml: str) -> None:
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
    assert len(messages) == 1 and messages[0].section == "/about/license"


def test_message_title(base_yaml: str) -> None:
    lint_check = "DummyError"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1 and messages[0].title == "Error message"


def test_message_title_format(base_yaml: str) -> None:
    lint_check = "DummyErrorFormat"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1 and messages[0].title == "Dummy message of severity ERROR"


def test_message_path(base_yaml: str, tmpdir: Path) -> None:
    recipe_directory_short = Path("fake_feedstock/recipe")
    recipe_directory = Path(tmpdir) / recipe_directory_short
    lint_check = "DummyError"
    messages = check_dir(lint_check, recipe_directory.parent, base_yaml)
    assert len(messages) == 1 and Path(messages[0].fname) == (recipe_directory_short / "meta.yaml")


def test_get_report_error() -> None:
    """
    Tests `get_report` for its ability to correctly format and return a report containing errors and warnings.
    """
    messages: Final[list[LintMessage]] = [
        LintMessage(
            severity=Severity.WARNING,
            recipe=None,
            fname="fake_feedstock/recipe/meta.yaml",
            check="dummy_warning",
            title="Warning message 1",
        ),
        LintMessage(
            severity=Severity.ERROR,
            recipe=None,
            fname="fake_feedstock/recipe/meta.yaml",
            check="dummy_error",
            title="Error message 1",
        ),
        LintMessage(
            severity=Severity.ERROR,
            recipe=None,
            fname="fake_feedstock/recipe/meta.yaml",
            check="dummy_error",
            title="Error message 2",
        ),
    ]

    report: Final[str] = Linter.get_report(messages)

    assert report == (
        "The following problems have been found:\n"
        "\n===== WARNINGS =====\n"
        "- fake_feedstock/recipe/meta.yaml:: dummy_warning: Warning message 1\n"
        "\n===== ERRORS ====="
        "\n- fake_feedstock/recipe/meta.yaml:: dummy_error: Error message 1\n"
        "- fake_feedstock/recipe/meta.yaml:: dummy_error: Error message 2\n"
        "===== Final Report: =====\n"
        "2 Errors and 1 Warning were found"
    )


def test_get_report_auto_fixes() -> None:
    """
    Ensures `get_report()` can report rules that have been automatically fixed successfully.
    """
    messages: Final[list[LintMessage]] = [
        LintMessage(
            severity=Severity.WARNING,
            recipe=None,
            fname="fake_feedstock/recipe/meta.yaml",
            check="dummy_warning",
            title="Warning message 1",
        ),
        LintMessage(
            severity=Severity.ERROR,
            recipe=None,
            fname="fake_feedstock/recipe/meta.yaml",
            check="dummy_error",
            title="Error message 1",
        ),
        LintMessage(
            severity=Severity.ERROR,
            recipe=None,
            fname="fake_feedstock/recipe/meta.yaml",
            check="auto_fix_1",
            title="Auto message 1",
            auto_fix_state=AutoFixState.FIX_PASSED,
        ),
        LintMessage(
            severity=Severity.ERROR,
            recipe=None,
            fname="fake_feedstock/recipe/meta.yaml",
            check="dummy_error",
            title="Error message 2",
        ),
        LintMessage(
            severity=Severity.WARNING,
            recipe=None,
            fname="fake_feedstock/recipe/meta.yaml",
            check="auto_fix_2",
            title="Auto message 2",
            auto_fix_state=AutoFixState.FIX_PASSED,
        ),
        LintMessage(
            severity=Severity.ERROR,
            recipe=None,
            fname="fake_feedstock/recipe/meta.yaml",
            check="auto_fix_3",
            title="Auto message 3",
            auto_fix_state=AutoFixState.FIX_FAILED,
        ),
    ]

    report: Final[str] = Linter.get_report(messages)

    assert report == (
        "The following problems have been found:\n"
        "\n===== Automatically Fixed =====\n"
        "- auto_fix_1\n"
        "- auto_fix_2\n"
        "\n===== WARNINGS =====\n"
        "- fake_feedstock/recipe/meta.yaml:: dummy_warning: Warning message 1\n"
        "\n===== ERRORS ====="
        "\n- fake_feedstock/recipe/meta.yaml:: dummy_error: Error message 1\n"
        "- fake_feedstock/recipe/meta.yaml:: dummy_error: Error message 2\n"
        "- fake_feedstock/recipe/meta.yaml:: auto_fix_3: Auto message 3\n"
        "===== Final Report: =====\n"
        "Automatically fixed 2 issues.\n"
        "3 Errors and 1 Warning were found"
    )


def test_get_report_no_error() -> None:
    """
    Tests the `get_report` for handling a scenario with no errors or warnings.
    """
    messages: Final[list[LintMessage]] = [
        LintMessage(
            severity=Severity.INFO,
            recipe=None,
            fname="fake_feedstock/recipe/meta.yaml",
            check="dummy_info",
            title="Info message",
        )
    ]
    report: Final[str] = Linter.get_report(messages)
    assert report == ("All checks OK")
