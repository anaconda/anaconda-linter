"""
Recipe Linter

Writing additional checks
~~~~~~~~~~~~~~~~~~~~~~~~~

Lint checks are defined in :py:mod:`bioconda_utils.lint.checks` as
subclasses of `LintCheck`. It might be easiest to have a look at that
module and the already existing checks and go from there.

Briefly, each class becomes a check by:

- The class name becomes the name of the check in the documentation
  and when skipping lints. The convention is to use lower case
  separated by underscore.

- The docstring is used to describe the check on the command line,
  on Github when the check fails and in the documentation.

  The first line is considered a title or one line summary used where
  a brief description is needed. The remainder is a long description
  and should include brief help on how to fix the detected issue.

- The input property ``severity`` defaults to ``ERROR`` but can be
  set to ``INFO`` or ``WARNING`` for informative checks that
  should not cause linting to fail.

- The class property ``requires`` may contain a list of other check
  classes that are required to have passed before this check is
  executed. Use this to avoid duplicate errors presented, or to
  ensure that assumptions made by your check are met by the recipe.

- Each class is instantiated once per linting run. Do slow preparation
  work in the constructor. E.g. the `recipe_in_blocklist` check
  loads and parses the blocklist here.

- As each recipe is linted, your check will get called on three
  functions: `check_recipe <LintCheck.check_recipe>`, `check_deps
  <LintCheck.check_deps>` and `check_source <LintCheck.check_source>`.

  The first is simply passed the `Recipe` object, which you can use to
  inspect the recipe in question. The latter two are for convenience
  and performance. The ``check_deps`` call receives a mapping of
  all dependencies mentioned in the recipe to a list of locations
  in which the dependency occurred. E.g.::

    {'setuptools': ['requirements/run',
                    'outputs/0/requirements/run']}

  The ``check_sources`` is called for each source listed in the
  recipe, whether ``source:`` is a dict or a source, eliminating the
  need to repeat handling of these two cases in each check. The value
  ``source`` passed is a dictionary of the source, the value
  ``section`` a path to the source section.

- When a check encounters an issue, it should use ``self.message()`` to
  record the issue. The message is commonly modified with a path in
  the meta data to point to the part of the ``meta.yaml`` that lead to
  the error. This will be used to position annotations on github.

  If a check never calls ``self.message()``, it is assumed to have
  passed (=no errors generated).

  You can also provide an alternate filename (``fname``) and/or
  specify the line number directly (``line``).

Module Autodocs
~~~~~~~~~~~~~~~

.. rubric:: Environment Variables

.. autosummary::
   :toctree:

   check_build_help
   check_completeness
   check_spdx
   check_syntax
   check_url

"""

from __future__ import annotations

import abc
import importlib
import inspect
import logging
import pkgutil
import re
from dataclasses import dataclass
from enum import IntEnum, auto
from io import StringIO
from pathlib import Path
from typing import Any, Final, Optional

import networkx as nx
import percy.render.recipe as _recipe
from conda_recipe_manager.parser.dependency import DependencyMap
from conda_recipe_manager.parser.recipe_parser_deps import RecipeParserDeps
from conda_recipe_manager.parser.recipe_reader_deps import RecipeReaderDeps
from percy.render._renderer import RendererType
from percy.render.exceptions import EmptyRecipe, JinjaRenderFailure, MissingMetaYaml, RecipeError, YAMLRenderFailure
from percy.render.variants import read_conda_build_config
from ruamel.yaml import YAML

from anaconda_linter import utils as _utils

logger = logging.getLogger(__name__)


class Severity(IntEnum):
    """Severities for lint checks"""

    # Indicates a "null" severity (no messages were produced)
    NONE = 0

    # Checks of this severity are purely informational
    INFO = 10

    # Checks of this severity indicate possible problems
    WARNING = 20

    # Checks of this severity must be fixed and will fail a recipe.
    ERROR = 30


class AutoFixState(IntEnum):
    """
    Indicates the auto-fix state of a rule.
    """

    # Fix was not attempted
    NOT_FIXED = auto()
    # Fix attempted and succeeded
    FIX_PASSED = auto()
    # Fix attempted but failed
    FIX_FAILED = auto()


SEVERITY_DEFAULT: Final[Severity] = Severity.ERROR
SEVERITY_MIN_DEFAULT: Final[Severity] = Severity.INFO


@dataclass()
class LintMessage:
    """
    Message issued by LintChecks
    """

    #: The recipe this message refers to
    recipe: RecipeReaderDeps

    #: The check issuing the message
    check: "LintCheck"

    #: The severity of the message
    severity: Severity = SEVERITY_DEFAULT

    #: Message title to be presented to user
    title: str = ""

    #: Message body to be presented to user
    body: str = ""

    #: Section of the recipe in which the problem was found
    section: str = ""

    #: Name of file in which error was found
    fname: str = ""

    #: Whether the problem can be auto fixed
    canfix: bool = False

    #: Indicates the state of the auto-fix attempt
    auto_fix_state: AutoFixState = AutoFixState.NOT_FIXED

    def __eq__(self, other: object) -> bool:
        """
        Equivalency operator. `LintMessage`s must be hashable so they can be de-duped in a `set()`
        TODO Future: Use the default `dataclass` implementation when `recipe` instances are hashable.
        :param other: Other LintMessage instance to compare against.
        :returns: True if two `LintMessage` instances are equivalent.
        """
        if not isinstance(other, LintMessage):
            return False
        return (
            self.check == other.check
            and self.severity == other.severity
            and self.title == other.title
            and self.body == other.body
            and self.section == other.section
            and self.fname == other.fname
            and self.canfix == other.canfix
            and self.auto_fix_state == other.auto_fix_state
        )

    def __hash__(self) -> int:
        """
        Hash operator. `LintMessage`s must be hashable so they can be de-duped in a `set()`
        TODO Future: Use the default `dataclass` implementation when `recipe` instances are hashable.
        :returns: Unique hash code for this `LintMessage` instance.
        """
        return hash(
            (
                self.check,
                self.severity,
                self.title,
                self.body,
                self.section,
                self.fname,
                self.auto_fix_state,
            )
        )

    def get_level(self) -> str:
        """
        Return level string as required by github
        """
        if self.severity < Severity.WARNING:
            return "notice"
        if self.severity < Severity.ERROR:
            return "warning"
        return "failure"


class LintCheckMeta(abc.ABCMeta):
    """
    Meta class for lint checks

    Handles registry
    """

    registry: list["LintCheck"] = []

    def __new__(mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any], **kwargs) -> type:
        """
        Creates LintCheck classes
        """
        typ = super().__new__(mcs, name, bases, namespace, **kwargs)
        if name not in {"LintCheck", "ScriptCheck", "CDTCheck"}:  # don't register base classes
            mcs.registry.append(typ)
        return typ

    def __str__(cls) -> str:
        return cls.__name__


_checks_loaded = False


def get_checks() -> list[LintCheck]:
    """
    Loads and returns the available lint checks
    """
    global _checks_loaded
    if not _checks_loaded:
        for _, name, _ in pkgutil.iter_modules(__path__):
            if name.startswith("check_"):
                importlib.import_module(__name__ + "." + name)
        _checks_loaded = True
    return LintCheckMeta.registry


class LintCheck(metaclass=LintCheckMeta):
    """
    Base class for lint checks
    """

    #: Checks that must have passed for this check to be executed.
    requires: list["LintCheck"] = []

    def __init__(self, linter: "Linter") -> None:  # pylint: disable=W0613
        #: Messages collected running tests
        self.messages: list[LintMessage] = []
        #: Recipe currently being checked
        self.recipe: RecipeReaderDeps = None
        # TODO: Remove this once we transition to CRM recipes
        #: Percy recipe currently being checked
        self.percy_recipe: _recipe.Recipe = None
        #: Whether we are supposed to fix
        self.try_fix: bool = False

    def __str__(self) -> str:
        return self.__class__.__name__

    # TODO: remove the Percy specific arguments once we transition to CRM recipes, and re-enable pylint
    # TODO: The LintCheck class passes its attributes in as arguments to its member functions,
    # we should remove them and call `self` directly instead.
    def run(  # pylint: disable=too-many-positional-arguments
        self,
        recipe: RecipeReaderDeps,
        unrendered_recipe: RecipeParserDeps,
        percy_recipe: _recipe.Recipe,
        recipe_name: str = "",
        arch_name: Optional[str] = None,
        fix: bool = False,
    ) -> list[LintMessage]:
        """
        Run the check on a recipe. Called by Linter

        :param recipe: The recipe to be linted
        :param unrendered_recipe: The unrendered recipe parser instance
        :param percy_recipe: The Percy recipe instance
        :param recipe_name: The name of the recipe
        :param arch_name: The architecture of the recipe
        :param fix: Whether to attempt to fix the recipe
        """
        self.messages: list[LintMessage] = []
        self.recipe: RecipeReaderDeps = recipe
        self.unrendered_recipe: RecipeParserDeps = unrendered_recipe
        self.percy_recipe: _recipe.Recipe = percy_recipe
        self.recipe_path: Optional[Path] = percy_recipe.path

        self.try_fix = fix

        # Run general checks with CRM
        try:
            self.check_recipe(recipe_name, arch_name, self.recipe)
        except Exception:  # pylint: disable=broad-exception-caught
            message = self.make_message(
                recipe=self.recipe,
                fname=recipe_name,
                severity=Severity.ERROR,
                title_in="An unexpected error occurred in the linter. "
                "Please describe the issue in https://github.com/anaconda/anaconda-linter/issues/new, "
                "and we will fix it as soon as possible.",
                body_in="",
            )
            return [message]

        # Run general checks with Percy
        try:
            self.check_recipe_legacy(self.percy_recipe)
        except Exception:  # pylint: disable=broad-exception-caught
            message = self.make_message(
                recipe=self.percy_recipe,
                fname=recipe_name,
                severity=Severity.ERROR,
                title_in="An unexpected error occurred in the linter. "
                "Please describe the issue in https://github.com/anaconda/anaconda-linter/issues/new, "
                "and we will fix it as soon as possible.",
                body_in="",
            )
            return [message]

        # Run per source checks
        source = recipe.get_value("/source", None)
        if isinstance(source, dict):
            self.check_source(source, "source")
        elif isinstance(source, list):
            for num, src in enumerate(source):
                self.check_source(src, f"source/{num}")

        return self.messages

    def check_source(self, source: dict, section: str) -> None:
        """
        Execute check on each source

        :param source: dictionary containing the source section
        :param section: Path to the section. Can be `source` or `source/0` (1,2,3...).
        """

    def check_recipe_legacy(self, recipe: _recipe.Recipe) -> None:
        """
        Execute check on recipe

        Override this method in subclasses, using ``self.message()``
        to issue `LintMessage` as failures are encountered.

        :param recipe: The recipe under test.
        """

    def check_recipe(self, recipe_name: str, arch_name: str, recipe: RecipeReaderDeps) -> None:
        """
        Execute check on recipe using CRM

        Override this method in subclasses, using ``self.message()``
        to issue `LintMessage` as failures are encountered.

        :param recipe_name: Name of the recipe
        :param arch_name: Architecture of the recipe
        :param recipe: Recipe to be checked
        """

    def _validate_value(self, value: any) -> bool:  # pylint: disable=unused-argument
        """
        checks the value is valid

        :param value: Value to be checked
        """
        return False

    def _validate_if_recipe_path_is_missing(
        self,
        section_path: str,
        severity: Severity = SEVERITY_DEFAULT,
    ) -> None:
        """
        Validate if a recipe path is missing
        Helper function to check if a recipe path is missing.

        :param section_path: Path of the section to be checked
        :param severity: Severity of the message
        """
        recipe = self.recipe
        if recipe.contains_value(section_path):
            value = recipe.get_value(section_path)
            if value is not None and self._validate_value(value):
                return
            self.message(section=section_path, severity=severity)
            return
        if not recipe.is_multi_output():
            self.message(section=section_path, severity=severity)
            return
        output_paths: Final = recipe.get_package_paths()
        for package_path in output_paths:
            if package_path == "/":
                continue
            path: Final = recipe.append_to_path(package_path, section_path)
            if recipe.contains_value(path):
                value = recipe.get_value(path)
                if value is not None and self._validate_value(value):
                    continue
            self.message(section=path, severity=severity)

    def _get_all_dependencies(self, recipe: RecipeReaderDeps | RecipeParserDeps) -> Optional[DependencyMap]:
        """
        Get all dependencies from the recipe

        :param recipe: The recipe to get the dependencies from
        :returns: A dictionary of dependencies, or None if an error occurred
        """
        try:
            return recipe.get_all_dependencies()
        except (KeyError, ValueError):
            self.message(title_in=_utils.GET_ALL_DEPENDENCIES_ERROR_MESSAGE)
            return None

    def can_auto_fix(self) -> bool:
        """
        Indicates if a rule can be auto-fixed (which is a LintCheck child class that has the `fix()` function
        implemented)
        :returns: True if this rule supports auto-fixing. False otherwise.
        """
        # Adapted from:
        #   https://stackoverflow.com/questions/61052764/how-do-i-check-if-a-method-was-overwritten-by-a-child-class
        return type(self).fix is not LintCheck.fix

    def fix(self, message: LintMessage, data: Any) -> bool:  # pylint: disable=unused-argument
        """
        Attempt to automatically fix the linting error.
        :param message: Linting message emitted by the rule
        :param data: Information vector for the rule to communicate to the fix. TODO: standardize typing for all callers
        :returns: True if the fix succeeded. False otherwise
        """
        return False

    def message(
        self,
        *args,
        fname: str | Path | None = None,
        section: str = "",
        severity: Severity = SEVERITY_DEFAULT,
        data: Any = None,
        output: int = -1,
        title_in: str = None,
    ) -> None:
        """
        Add a message to the lint results

        Also calls `fix` if we are supposed to be fixing.

        :param args: Additional arguments to pass directly to the message
        :param fname: If specified, the message will apply to this file, rather than the recipe meta.yaml
        :param section: If specified, a lint location within the recipe meta.yaml pointing to this section/subsection
            will be added to the message
        :param severity: The severity level of the message.
        :param data: Data to be passed to `fix`. If check can fix, set this to something other than None.
        :param output: the output the error occurred in (multi-output recipes only)
        :param title_in: If specified, the title of the message will be set to this value
        """
        # In order to handle Percy-based rules generating messages with a section
        # We must adapt the section by prepending a slash
        if section and not section.startswith("/"):
            section = "/" + section
        if fname is None:
            if not self.recipe_path:
                # This should only happen during testing
                self.recipe_path = Path("meta.yaml")
            fname = self.recipe_path.relative_to(self.recipe_path.parent.parent.parent)
            fname = str(fname)
        else:
            fname = str(fname)
        message = self.make_message(
            *args,
            recipe=self.recipe,
            fname=fname,
            section=section,
            severity=severity,
            canfix=self.can_auto_fix(),
            output=output,
            title_in=title_in,
        )
        # If able, attempt to autofix the rule and mark the message object accordingly
        if self.try_fix and self.can_auto_fix():
            message.auto_fix_state = AutoFixState.FIX_PASSED if self.fix(message, data) else AutoFixState.FIX_FAILED
        self.messages.append(message)

    @classmethod
    def make_message(
        cls,
        *args: Any,
        recipe: RecipeReaderDeps,
        fname: str,
        section: str = "",
        severity: Severity = SEVERITY_DEFAULT,
        title_in: str = None,
        body_in: str = None,
        canfix: bool = False,
        output: int = -1,
    ) -> LintMessage:
        """
        Create a LintMessage

        :param args: Additional arguments to pass directly to the message
        :param recipe: Recipe instance being checked
        :param section: If specified, a lint location within the recipe meta.yaml pointing to this section/subsection
            will be added to the message
        :param severity: The severity level of the message.
        :param fname: If specified, the message will apply to this file, rather than the recipe meta.yaml
        :param title_in: If specified, the title of the message will be set to this value
        :param body_in: If specified, the body of the message will be set to this value
        :param canfix: If specified, indicates if the rule can/can't be auto-fixed
        :param output: The output the error occurred in (multi-output recipes only)
        """
        doc = inspect.getdoc(cls)
        doc = doc.replace("::", ":").replace("``", "`")
        title, _, body = doc.partition("\n")
        if len(args) > 0:
            title = title.format(*args)
        if output >= 0:
            name = recipe.get_value(f"/outputs/{output}/name", "")
            if name != "":
                title = f'output "{name}": {title}'
        title = title_in if title_in is not None else title
        body = body_in if body_in is not None else body
        return LintMessage(
            recipe=recipe,
            check=cls,
            severity=severity,
            title=title.strip(),
            body=body,
            fname=fname,
            section=section,
            canfix=canfix,
        )


class ScriptCheck(LintCheck):
    """
    Base class for script checks
    """

    def _check_line(self, line: str) -> bool:
        """
        Check a line for an invalid or obsolete install command

        :returns: True if the line contains an invalid or obsolete install command
        """

    def _check_block(self, path: str, value: Any) -> str:
        """
        Check a line or a list of lines for an invalid or obsolete install command
        """
        if value is None:
            return ""
        if isinstance(value, str):
            if not self._check_line(value):
                return ""
            return path
        for idx, line in enumerate(value):
            if self._check_line(line):
                return path + "/" + str(idx)

    def _check_build_sh(self, recipe_dir: Optional[Path], build_script: Any) -> None:
        """
        Check a build.sh file for an invalid or obsolete install command
        """
        if build_script:
            if isinstance(build_script, list):
                return
            build_file = recipe_dir / build_script
        else:
            build_file = recipe_dir / "build.sh"
        if build_file.exists():
            with open(build_file, mode="r", encoding="utf-8") as build_sh:
                for line in build_sh:
                    if self._check_line(line):
                        self.message(section=f"build script: {str(build_file)}")

    def check_recipe(self, recipe_name: str, arch_name: str, recipe: RecipeReaderDeps) -> None:
        """
        Check the recipe build script, whether it's in the recipe or a standalone file
        """
        recipe_dir: Final[Optional[Path]] = Path(recipe_name) if recipe_name else None
        # Check root level
        build_script_path: Final[str] = "/build/script"
        build_script_val = None
        if recipe.contains_value(build_script_path):
            build_script_val = recipe.get_value(build_script_path)
            if build_script_path := self._check_block(build_script_path, build_script_val):
                self.message(section=build_script_path)
        if recipe_dir:
            self._check_build_sh(recipe_dir, build_script_val)
        # Check outputs
        for package in recipe.get_package_paths():
            if package == "/":
                continue
            script_path = recipe.append_to_path(package, "/script")
            output_build_script_path = recipe.append_to_path(package, "/build/script")
            script_val = None
            if recipe.contains_value(script_path):
                script_val = recipe.get_value(script_path)
                if script_path := self._check_block(script_path, script_val):
                    self.message(section=script_path)
            elif recipe.contains_value(output_build_script_path):
                script_val = recipe.get_value(output_build_script_path)
                if output_build_script_path := self._check_block(output_build_script_path, script_val):
                    self.message(section=output_build_script_path)
            if recipe_dir:
                self._check_build_sh(recipe_dir, script_val)

    def fix(self, message: LintMessage, data: Any) -> bool:
        section = message.section
        if section.startswith("build script: "):
            return False
        recipe = self.unrendered_recipe
        return recipe.patch(
            {
                "op": "replace",
                "path": section,
                "value": "{{ PYTHON }} -m pip install . --no-deps --no-build-isolation",
            }
        )


class CDTCheck(LintCheck):
    """
    Base class for CDT checks
    """

    cdt_pattern = re.compile(r"{{ cdt\('[^']*'\) }}")

    @staticmethod
    def _detect_cdt(cdt: str) -> bool:
        """
        Detect a string that is a CDT macro such as {{ cdt('libudev-devel') }}
        using regex

        :param cdt: The string to examine
        :returns: True if the string is a CDT macro, False otherwise
        """
        return bool(re.match(CDTCheck.cdt_pattern, cdt))


class linter_failure(LintCheck):
    """
    An unexpected exception was raised during linting

    Please file an issue at the conda-lint repo
    """


class duplicate_key_in_meta_yaml(LintCheck):
    """
    The recipe meta.yaml contains a duplicate key

    This is invalid YAML, as it's unclear what the structure should
    become. Please merge the two offending sections
    """


class missing_version_or_name(LintCheck):
    """
    The recipe is missing name and/or version

    Please make sure the recipe has at least::

      package:
        name: package_name
        version: 0.12.34
    """


class empty_meta_yaml(LintCheck):
    """
    The recipe has an empty meta.yaml!?

    Please check if you forgot to commit its contents.
    """


class missing_build(LintCheck):
    """
    The recipe is missing a build section.

    Please add::

      build:
        number: 0
    """


class unknown_selector(LintCheck):
    """
    The recipe failed to parse due to selector lines

    Please request help from conda-lint.
    """


class missing_meta_yaml(LintCheck):
    """
    The recipe is missing a meta.yaml file

    Most commonly, this is because the file was accidentally
    named ``meta.yml``. If so, rename it to ``meta.yaml``.
    """


class conda_render_failure(LintCheck):
    """
    The recipe was not understood by conda-build

    Please request help from cconda-lint.
    """


class jinja_render_failure(LintCheck):
    """
    The recipe could not be rendered by Jinja2

    Check if you are missing quotes or curly braces in Jinja2 template
    expressions. (The parts with ``{{ something }}`` or ``{% set
    var="value" %}``).
    """


class yaml_load_failure(LintCheck):
    """
    The recipe could not be loaded by yaml

    Check your selectors and overall yaml validity.
    """


class unknown_check(LintCheck):
    """
    Something went wrong inside the linter

    Please request help from conda-lint.
    """


#: Maps `RecipeError` to `LintCheck`
recipe_error_to_lint_check: dict[RecipeError, LintCheck] = {
    EmptyRecipe: empty_meta_yaml,
    MissingMetaYaml: missing_meta_yaml,
    JinjaRenderFailure: jinja_render_failure,
    YAMLRenderFailure: yaml_load_failure,
}


class Linter:
    """
    Lint executor class
    """

    def __init__(  # pylint: disable=too-many-positional-arguments
        self,
        config: dict,
        verbose: bool = False,
        exclude: list[str] = None,
        nocatch: bool = False,
        severity_min: Optional[Severity] = None,
    ) -> None:
        """
        Constructs a linter instance
        Arguments:
          config: Configuration dict as provided by `utils.load_config()`.
          verbose: Enables verbose logging
          exclude: list of function names in ``registry`` to skip globally.
                   When running on CI, this will be merged with anything
                   else detected from the commit message or LINT_SKIP
                   environment variable using the special string "[skip
                   lint <function name> for <recipe name>]". While those
                   other mechanisms define skipping on a recipe-specific
                   basis, this argument can be used to skip tests for all
                   recipes. Use sparingly.
          nocatch: Don't catch exceptions in lint checks and turn them into
                   linter_error lint messages. Used by tests.
          severity_min: The minimum severity level to display in messages.
        """
        self.config = config
        self.exclude = exclude or []
        self.nocatch = nocatch
        self.verbose = verbose
        self._messages: list[LintMessage] = []
        self.severity_min = SEVERITY_MIN_DEFAULT if severity_min is None else severity_min
        self.reload_checks()

    def reload_checks(self) -> None:
        """
        Reloads linter checks
        """
        dag = nx.DiGraph()
        dag.add_nodes_from(str(check) for check in get_checks())
        dag.add_edges_from((str(check), str(check_dep)) for check in get_checks() for check_dep in check.requires)
        self.checks_dag = dag

        try:
            self.checks_ordered = reversed(list(nx.topological_sort(dag)))
        except nx.NetworkXUnfeasible as e:
            raise RuntimeError("Cycle in LintCheck requirements!") from e
        self.check_instances: dict[str, LintCheck] = {str(check): check(self) for check in get_checks()}

    def get_messages(self) -> list[LintMessage]:
        """
        Returns the lint messages collected during linting
        """
        return sorted(
            [msg for msg in self._messages if msg.severity >= self.severity_min],
            key=lambda d: (d.fname, d.section),
        )

    def clear_messages(self) -> None:
        """
        Clears the lint messages stored in linter
        """
        self._messages: list[LintMessage] = []

    @classmethod
    def get_report(cls, messages: list[LintMessage], verbose: bool = False) -> str:
        """
        Returns a report of all the linting messages.
        :param messages: list of messages to process.
        :param verbose: (Optional) Enables additional reporting.
        :returns: String, containing information about all the linting messages, as a report.
        """
        severity_data: dict[Severity, list[LintMessage]] = {}
        successful_auto_fixes: list[str] = []

        for msg in messages:
            if msg.auto_fix_state == AutoFixState.FIX_PASSED:
                successful_auto_fixes.append(str(msg.check))
                continue

            if msg.severity not in severity_data:
                severity_data[msg.severity] = []
            severity_data[msg.severity].append(msg)

        report: str = "The following problems have been found:\n"
        report_sections: list[str] = []

        if successful_auto_fixes:
            report_sections.append("\n===== Automatically Fixed =====\n- " + "\n- ".join(successful_auto_fixes))

        for sev in [Severity.WARNING, Severity.ERROR]:
            if sev not in severity_data:
                continue
            info = severity_data[sev]
            severity_section = f"\n===== {sev.name.upper()}S =====\n"
            severity_section += "\n".join(
                f"- {msg.fname}:{msg.section}: {msg.check}: {msg.title}"
                + (f"\n Additional Details: {msg.body}" if verbose else "")
                for msg in info
            )
            report_sections.append(severity_section)

        if not report_sections:
            return "All checks OK"

        report += "\n".join(report_sections) + "\n"
        report += "===== Final Report: =====\n"
        auto_fix_count = len(successful_auto_fixes)
        error_count = len(severity_data.get(Severity.ERROR, []))
        warning_count = len(severity_data.get(Severity.WARNING, []))
        if auto_fix_count > 0:
            report += f"Automatically fixed {auto_fix_count} issue{'s' if auto_fix_count != 1 else ''}.\n"
        report += f"{error_count} Error{'s' if error_count != 1 else ''} "
        report += f"and {warning_count} Warning{'s' if warning_count != 1 else ''} were found"

        return report

    def lint(  # pylint: disable=too-many-positional-arguments
        self,
        recipes: list[str],
        arch_name: str = "linux-64",
        variant_config_files: Optional[list[str]] = None,
        exclusive_config_files: Optional[list[str]] = None,
        fix: bool = False,
    ) -> Severity:
        """
        Run linter on multiple recipes

        Lint messages are collected in the linter. They can be retrieved
        with `get_messages` and the list cleared with `clear_messages`.

        :param recipes: list of names of recipes
        :param arch_name: Target architecture to run against
        :param variant_config_files: Configuration information for variants
        :param exclusive_config_files: Configuration information for exclusive files
        :param fix: Whether checks should attempt to fix detected issues

        :returns: Maximum severity level of issues found (ERROR, WARNING, or NONE)
        """
        if variant_config_files is None:
            variant_config_files = []
        if exclusive_config_files is None:
            exclusive_config_files = []
        if len(recipes) == 0:
            return Severity.NONE
        for recipe_name in sorted(recipes):
            try:
                msgs = self.lint_file(
                    recipe_name,
                    arch_name=arch_name,
                    variant_config_files=variant_config_files,
                    exclusive_config_files=exclusive_config_files,
                    fix=fix,
                )
            except Exception:  # pylint: disable=broad-exception-caught
                if self.nocatch:
                    raise
                logger.exception("Unexpected exception in lint")
                recipe = _recipe.Recipe(recipe_name)
                msgs = [linter_failure.make_message(recipe=recipe, fname=recipe_name)]
            self._messages.extend(msgs)

        result: Severity = Severity.NONE
        for message in self._messages:
            if message.severity == Severity.ERROR:
                return Severity.ERROR
            if message.severity == Severity.WARNING:
                result = Severity.WARNING

        return result

    def lint_file(  # pylint: disable=too-many-positional-arguments
        self,
        recipe_name: str,
        arch_name: str = "linux-64",
        variant_config_files: Optional[list[str]] = None,
        exclusive_config_files: Optional[list[str]] = None,
        fix: bool = False,
    ) -> list[LintMessage]:
        """
        Run the linter on a single recipe for a subdir

        :param recipe_name: Name of recipe to lint
        :param arch_name: Architecture to consider
        :param variant_config_files: Configuration information for variants
        :param exclusive_config_files: Configuration information for exclusive files
        :param fix: Whether checks should attempt to fix detected issues

        :returns: List of collected messages
        """
        if variant_config_files is None:
            variant_config_files = []
        if exclusive_config_files is None:
            exclusive_config_files = []

        if self.verbose:
            print(f"Linting subdir:{arch_name} recipe:{recipe_name}")

        # Gather variants for specified subdir
        # As a stopgap, this process outputs a tuple per variant with
        # variants and variant info using Percy
        # TODO: replace with CRM variants generation -> CRM #399
        # TODO: track recipe variants (python version, arch, etc.) all the way to error reporting to ease fixing
        # anaconda-linter #403
        recipe_variants: list[tuple] = []
        try:
            meta_yaml = Path(recipe_name) / "meta.yaml"
            if (Path(__file__) / "conda_build_config.yaml").is_file():
                logging.debug("Using cbc in current path.")
                variants = read_conda_build_config(
                    recipe_path=meta_yaml,
                    subdir=arch_name,
                    variant_config_files=variant_config_files,
                    exclusive_config_files=exclusive_config_files,
                )
            else:
                logging.debug("No cbc in current path. Loading copy of aggregate cbc embedded in linter.")
                logging.debug("Please run from your aggregate dir for better results.")
                local_cbc = Path(__file__).parent.parent / "data" / "conda_build_config.yaml"
                var_config_files = variant_config_files
                var_config_files.append(str(local_cbc))
                variants = read_conda_build_config(
                    recipe_path=meta_yaml,
                    subdir=arch_name,
                    variant_config_files=var_config_files,
                    exclusive_config_files=exclusive_config_files,
                )
            for vid, variant in variants:
                percy_recipe = _recipe.Recipe.from_file(
                    recipe_fname=str(meta_yaml),
                    variant_id=vid,
                    variant=variant,
                    renderer=RendererType.RUAMEL,
                )
                buf = StringIO()
                yaml = YAML()
                yaml.indent(mapping=2, sequence=4, offset=2)
                yaml.dump(percy_recipe.meta, buf)
                recipe_content = buf.getvalue()
                recipe_variants.append((vid, variant, recipe_content, percy_recipe))
        except RecipeError as exc:
            recipe = _recipe.Recipe(recipe_name)
            check_cls = recipe_error_to_lint_check.get(exc.__class__, linter_failure)
            return [check_cls.make_message(recipe=recipe, fname=recipe_name, line=getattr(exc, "line"))]

        # lint variants
        messages = set()
        try:
            for vid, variant, recipe_content, percy_recipe in recipe_variants:
                logging.debug("Linting variant %s", vid)
                recipe = RecipeReaderDeps(recipe_content)
                unrendered_recipe = RecipeParserDeps(percy_recipe.dump())
                if not recipe.contains_value("/build/skip"):
                    messages.update(
                        self.lint_recipe(
                            recipe=recipe,
                            unrendered_recipe=unrendered_recipe,
                            percy_recipe=percy_recipe,
                            recipe_name=recipe_name,
                            arch_name=arch_name,
                            fix=fix,
                        )
                    )
                    # Auto-fixing
                    write_path = percy_recipe.path
                    if fix and unrendered_recipe.is_modified():
                        with open(write_path, "w", encoding="utf-8") as fdes:
                            fdes.write(unrendered_recipe.render())
        except Exception:  # pylint: disable=broad-exception-caught
            recipe = _recipe.Recipe(recipe_name)
            return [linter_failure.make_message(recipe=recipe, fname=recipe_name)]

        return list(messages)

    # TODO: Remove percy-specific arguments after percy is removed
    def lint_recipe(  # pylint: disable=too-many-positional-arguments
        self,
        recipe: RecipeReaderDeps,
        unrendered_recipe: RecipeParserDeps,
        percy_recipe: _recipe.Recipe,
        recipe_name: str,
        arch_name: str,
        fix: bool = False,
    ) -> list[LintMessage]:
        """
        Lints a recipe

        :param recipe: Recipe to lint against
        :param unrendered_recipe: The unrendered recipe parser instance
        :param percy_recipe: The Percy recipe instance
        :param recipe_name: Name of recipe to lint
        :param arch_name: Architecture to consider
        :param fix: (Optional) Enables auto-fixing of the lint checks
        :returns: list of linting messages returned from executing checks against the linter.
        """
        # collect checks to skip
        checks_to_skip = set(self.exclude)

        # currently skip-lints will overwrite only-lint, we can check for the key
        # being in checks_to_skip, but I think letting the user do this is best?
        checks_to_skip.update(recipe.get_value("/extra/skip-lints", []))
        if only_lint := recipe.get_value("/extra/only-lint", []):
            # getting the symmetric difference between all checks and only_lint
            all_other_checks = set(only_lint) ^ self.checks_dag.nodes
            checks_to_skip.update(all_other_checks)

        # also skip dependent checks
        for check in list(checks_to_skip):
            if check not in self.checks_dag:
                logger.error("Skipping unknown check %s", check)
                continue
            for check_dep in nx.ancestors(self.checks_dag, check):
                if check_dep not in checks_to_skip:
                    logger.info("Disabling %s because %s is disabled", check_dep, check)
                checks_to_skip.add(check_dep)

        # run checks
        messages: list[LintMessage] = []
        self.reload_checks()
        for check in self.checks_ordered:
            if str(check) in checks_to_skip:
                if self.verbose:
                    print("Skipping check: " + check)
                continue

            if self.verbose:
                print("Running check: " + check)

            try:
                res = self.check_instances[check].run(
                    recipe=recipe,
                    unrendered_recipe=unrendered_recipe,
                    percy_recipe=percy_recipe,
                    recipe_name=recipe_name,
                    arch_name=arch_name,
                    fix=fix,
                )
                # Merge the changes from the percy recipe into the CRM recipe,
                # and vice versa, in case of an auto-fix.
                if fix and percy_recipe.is_modified() and unrendered_recipe.is_modified():
                    raise ValueError(
                        "Error occurred during auto-fixing. "
                        "Please report this issue in https://github.com/anaconda/anaconda-linter/issues/new"
                    )
                if fix and percy_recipe.is_modified():
                    unrendered_recipe = RecipeParserDeps(percy_recipe.dump())
                    unrendered_recipe._is_modified = True  # pylint: disable=protected-access
                if fix and unrendered_recipe.is_modified():
                    percy_recipe = _recipe.Recipe.from_string(
                        unrendered_recipe.render(),
                        variant_id=percy_recipe.variant_id,
                        variant=percy_recipe.selector_dict,
                        renderer=RendererType.RUAMEL,
                    )
            except Exception as e:  # pylint: disable=broad-exception-caught
                if self.nocatch:
                    raise
                logger.exception("Unexpected exception in lint_recipe")
                res = [
                    LintMessage(
                        recipe=recipe,
                        check=check,
                        severity=Severity.ERROR,
                        title="Check raised an unexpected exception: " + str(e),
                    )
                ]

            if res:  # skip checks depending on failed checks
                checks_to_skip.update(nx.ancestors(self.checks_dag, str(check)))
            messages.extend(res)

        for message in messages:
            logger.debug("Found: %s", message)

        return messages
