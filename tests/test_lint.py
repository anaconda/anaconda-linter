from pathlib import Path

import pytest
from conftest import check, check_dir
from percy.render.recipe import Recipe, RecipeError, RendererType

from anaconda_linter import lint, utils
from anaconda_linter.lint import ERROR, INFO, WARNING


class dummy_info(lint.LintCheck):
    """Info message"""

    def check_recipe(self, recipe):
        self.message(severity=INFO)


class dummy_warning(lint.LintCheck):
    """Warning message"""

    def check_recipe(self, recipe):
        self.message(severity=WARNING)


class dummy_error(lint.LintCheck):
    """Error message"""

    def check_recipe(self, recipe):
        self.message(severity=ERROR)


class dummy_error_format(lint.LintCheck):
    """{} message of severity {}"""

    def check_recipe(self, recipe):
        self.message("Dummy", "ERROR")


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
    recipes = [Recipe.from_string(recipe_text=yaml_str, renderer=RendererType.RUAMEL)]
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
    recipes_base = [Recipe.from_string(recipe_text=base_yaml, renderer=RendererType.RUAMEL)]
    linter.lint(recipes_base)
    messages_base = linter.get_messages()
    linter.clear_messages()
    assert len(linter.get_messages()) == 0
    recipes_skip = [Recipe.from_string(recipe_text=yaml_str, renderer=RendererType.RUAMEL)]
    linter.lint(recipes_skip)
    messages_skip = linter.get_messages()
    assert len(messages_base) == len(messages_skip) + 3


def test_lint_none(base_yaml, linter):
    recipes = []
    return_code = linter.lint(recipes)
    assert return_code == 0 and len(linter.get_messages()) == 0


def test_lint_file(base_yaml, linter, recipe_dir):
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
    meta_yaml = recipe_dir / "meta.yaml"
    meta_yaml.write_text(yaml_str)
    linter.lint([str(recipe_dir)])
    assert len(linter.get_messages()) == 3


@pytest.mark.parametrize(
    "level,string,lint_check",
    (
        (INFO, "notice", "dummy_info"),
        (WARNING, "warning", "dummy_warning"),
        (ERROR, "failure", "dummy_error"),
    ),
)
def test_severity_level(base_yaml, level, string, lint_check):
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1
    assert messages[0].severity == level
    assert messages[0].get_level() == string


def test_severity_bad(base_yaml):
    with pytest.raises(ValueError):
        config_file = Path(__file__).parent / "config.yaml"
        config = utils.load_config(config_file)
        lint.Linter(config=config, severity_min="BADSEVERITY")


@pytest.mark.parametrize("level,expected", (("INFO", 3), ("WARNING", 2), ("ERROR", 1)))
def test_severity_min_string(base_yaml, level, expected):
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
    recipes = [Recipe.from_string(recipe_text=yaml_str, renderer=RendererType.RUAMEL)]
    config_file = Path(__file__).parent / "config.yaml"
    config = utils.load_config(config_file)
    linter = lint.Linter(config=config, severity_min=level)
    linter.lint(recipes)
    assert len(linter.get_messages()) == expected


@pytest.mark.parametrize("level,expected", ((INFO, 3), ("WARNING", 2), ("ERROR", 1)))
def test_severity_min_enum(base_yaml, level, expected):
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
    recipes = [Recipe.from_string(recipe_text=yaml_str, renderer=RendererType.RUAMEL)]
    config_file = Path(__file__).parent / "config.yaml"
    config = utils.load_config(config_file)
    linter = lint.Linter(config=config, severity_min=level)
    linter.lint(recipes)
    assert len(linter.get_messages()) == expected


def test_lint_list():
    checks_file = Path(__file__).parent / "../anaconda_linter/lint_names.md"
    with open(checks_file.resolve()) as f:
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
        config_file = Path(__file__).parent / "config.yaml"
        config = utils.load_config(config_file)
        linter = lint.Linter(config=config)

        try:
            _recipe = Recipe.from_string(recipe_text=yaml_str, renderer=RendererType.RUAMEL)
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


def test_message_title(base_yaml):
    lint_check = "dummy_error"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1 and messages[0].title == "Error message"


def test_message_title_format(base_yaml):
    lint_check = "dummy_error_format"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1 and messages[0].title == "Dummy message of severity ERROR"


def test_message_path(base_yaml, tmpdir):
    recipe_directory_short = Path("fake_feedstock/recipe")
    recipe_directory = Path(tmpdir) / recipe_directory_short
    lint_check = "dummy_error"
    messages = check_dir(lint_check, recipe_directory.parent, base_yaml)
    assert len(messages) == 1 and Path(messages[0].fname) == (recipe_directory_short / "meta.yaml")
