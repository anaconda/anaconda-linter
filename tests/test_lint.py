"""
File:           test_.py
Description:    Tests linting infrastructure
"""
from __future__ import annotations

from pathlib import Path
from typing import Final, List

import pytest
from conftest import check, check_dir
from percy.render.exceptions import RecipeError
from percy.render.recipe import Recipe, RendererType

from anaconda_linter import lint, utils
from anaconda_linter.lint import ERROR, INFO, WARNING, Linter, LintMessage, Severity


class DummyInfo(lint.LintCheck):
    """
    Info message
    """

    def check_recipe(self, _) -> None:
        self.message(severity=INFO)


class DummyWarning(lint.LintCheck):
    """
    Warning message
    """

    def check_recipe(self, _) -> None:
        self.message(severity=WARNING)


class DummyError(lint.LintCheck):
    """
    Error message
    """

    def check_recipe(self, _) -> None:
        self.message(severity=ERROR)


class DummyErrorFormat(lint.LintCheck):
    """
    {} message of severity {}
    """

    def check_recipe(self, _) -> None:
        self.message("Dummy", "ERROR")


def test_only_lint(base_yaml: str, linter: Linter) -> None:
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
    recipes = [Recipe.from_string(recipe_text=yaml_str, renderer=RendererType.RUAMEL)]
    linter.lint(recipes)
    assert len(linter.get_messages()) == 3


def test_skip_lints(base_yaml: str, linter: Linter) -> None:
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
    recipes_base = [Recipe.from_string(recipe_text=base_yaml, renderer=RendererType.RUAMEL)]
    linter.lint(recipes_base)
    messages_base = linter.get_messages()
    linter.clear_messages()
    assert len(linter.get_messages()) == 0
    recipes_skip = [Recipe.from_string(recipe_text=yaml_str, renderer=RendererType.RUAMEL)]
    linter.lint(recipes_skip)
    messages_skip = linter.get_messages()
    assert len(messages_base) == len(messages_skip) + 3


def test_lint_none(base_yaml: str, linter: Linter) -> None:  # pylint: disable=unused-argument
    recipes = []
    return_code = linter.lint(recipes)
    assert return_code == 0 and len(linter.get_messages()) == 0


def test_lint_file(base_yaml: str, linter, recipe_dir: Path) -> None:
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


@pytest.mark.parametrize(
    "level,string,lint_check",
    (
        (INFO, "notice", "DummyInfo"),
        (WARNING, "warning", "DummyWarning"),
        (ERROR, "failure", "DummyError"),
    ),
)
def test_severity_level(base_yaml: str, level: Severity, string: str, lint_check: str) -> None:
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1
    assert messages[0].severity == level
    assert messages[0].get_level() == string


def test_severity_bad(base_yaml: str) -> None:  # pylint: disable=unused-argument
    with pytest.raises(ValueError):
        config_file = Path(__file__).parent / "config.yaml"
        config = utils.load_config(config_file)
        lint.Linter(config=config, severity_min="BADSEVERITY")


# TODO rm: de-risk this. Enforce `Severity` over `str` universally
@pytest.mark.parametrize("level,expected", (("INFO", 3), ("WARNING", 2), ("ERROR", 1)))
def test_severity_min_string(base_yaml: str, level: str, expected: int) -> None:
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
    recipes = [Recipe.from_string(recipe_text=yaml_str, renderer=RendererType.RUAMEL)]
    config_file = Path(__file__).parent / "config.yaml"
    config = utils.load_config(config_file)
    linter = lint.Linter(config=config, severity_min=level)
    linter.lint(recipes)
    assert len(linter.get_messages()) == expected


@pytest.mark.parametrize("level,expected", ((INFO, 3), ("WARNING", 2), ("ERROR", 1)))
def test_severity_min_enum(base_yaml: str, level: Severity | str, expected: int) -> None:
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
    recipes = [Recipe.from_string(recipe_text=yaml_str, renderer=RendererType.RUAMEL)]
    config_file = Path(__file__).parent / "config.yaml"
    config = utils.load_config(config_file)
    linter = lint.Linter(config=config, severity_min=level)
    linter.lint(recipes)
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
def test_jinja_functions(base_yaml: str, jinja_func: str, expected: bool) -> None:
    def run_lint(yaml_str: str) -> list[LintMessage]:
        config_file = Path(__file__).parent / "config.yaml"
        config = utils.load_config(config_file)
        linter = lint.Linter(config=config)

        # TODO figure out: 1 test fails if we remove this retry mechanism. Can we write the test differently so that
        # we don't have conditional logic in our tests?
        try:
            recipe = Recipe.from_string(recipe_text=yaml_str, renderer=RendererType.RUAMEL)
            linter.lint([recipe])
            messages = linter.get_messages()
        except RecipeError as exc:
            recipe = Recipe("")
            check_cls = lint.recipe_error_to_lint_check.get(exc.__class__, lint.linter_failure)
            messages = [check_cls.make_message(recipe=recipe, line=getattr(exc, "line"))]

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
    assert len(messages) == 1 and messages[0].start_line == 5


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


def test_get_report():
    messages: Final[List[LintMessage]] = [
        LintMessage(
            severity=WARNING,
            recipe=None,
            fname="fake_feedstock/recipe/meta.yaml",
            start_line=1,
            check="dummy_warning",
            title="Warning message 1",
        ),
        LintMessage(
            severity=ERROR,
            recipe=None,
            fname="fake_feedstock/recipe/meta.yaml",
            start_line=1,
            check="dummy_error",
            title="Error message 1",
        ),
        LintMessage(
            severity=ERROR,
            recipe=None,
            fname="fake_feedstock/recipe/meta.yaml",
            start_line=1,
            check="dummy_error",
            title="Error message 2",
        ),
    ]

    report: Final[str] = Linter.get_report(messages)

    assert report == (
        "\n===== WARNINGS ===== \n"
        "- fake_feedstock/recipe/meta.yaml:0: dummy_warning: Warning message 1\n"
        "\n===== ERRORS ===== "
        "\n- fake_feedstock/recipe/meta.yaml:0: dummy_error: Error message 1\n"
        "- fake_feedstock/recipe/meta.yaml:0: dummy_error: Error message 2\n"
        "===== Final Report: =====\n"
        "2 Errors and 1 Warning were found"
    )
