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
from enum import IntEnum
from pathlib import Path
from typing import Any, Final, NamedTuple, Optional, Tuple, Union

import networkx as nx
import percy.render.recipe as _recipe
from percy.render.exceptions import EmptyRecipe, JinjaRenderFailure, MissingMetaYaml, RecipeError, YAMLRenderFailure
from percy.render.recipe import RendererType
from percy.render.variants import read_conda_build_config

from anaconda_linter import utils as _utils

logger = logging.getLogger(__name__)


class Severity(IntEnum):
    """Severities for lint checks"""

    #: Checks of this severity are purely informational
    INFO = 10

    #: Checks of this severity indicate possible problems
    WARNING = 20

    #: Checks of this severity must be fixed and will fail a recipe.
    ERROR = 30


INFO: Final[Severity] = Severity.INFO
WARNING: Final[Severity] = Severity.WARNING
ERROR: Final[Severity] = Severity.ERROR

SEVERITY_DEFAULT: Final[Severity] = ERROR
SEVERITY_MIN_DEFAULT: Final[Severity] = INFO


class LintMessage(NamedTuple):
    """
    Message issued by LintChecks
    """

    #: The recipe this message refers to
    recipe: _recipe.Recipe

    #: The check issuing the message
    check: "LintCheck"

    #: The severity of the message
    severity: Severity = SEVERITY_DEFAULT

    #: Message title to be presented to user
    title: str = ""

    #: Message body to be presented to user
    body: str = ""

    #: Line at which problem begins
    start_line: int = 0

    #: Line at which problem ends
    end_line: int = 0

    #: Name of file in which error was found
    fname: str = "meta.yaml"

    #: Whether the problem can be auto fixed
    canfix: bool = False

    def get_level(self) -> str:
        """
        Return level string as required by github
        """
        if self.severity < WARNING:
            return "notice"
        if self.severity < ERROR:
            return "warning"
        return "failure"

    def __eq__(self, other: LintMessage) -> bool:
        return (
            self.check == other.check
            and self.severity == other.severity
            and self.title == other.title
            and self.body == other.body
            and self.start_line == other.start_line
            and self.end_line == other.end_line
            and self.fname == other.fname
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.check,
                self.severity,
                self.title,
                self.body,
                self.start_line,
                self.end_line,
                self.fname,
            )
        )


class LintCheckMeta(abc.ABCMeta):
    """
    Meta class for lint checks

    Handles registry
    """

    registry: list["LintCheck"] = []

    def __new__(mcs, name: str, bases: Tuple[type, ...], namespace: dict[str, Any], **kwargs) -> type:
        """
        Creates LintCheck classes
        """
        typ = super().__new__(mcs, name, bases, namespace, **kwargs)
        if name != "LintCheck":  # don't register base class
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
        self.recipe: _recipe.Recipe = None
        #: Whether we are supposed to fix
        self.try_fix: bool = False

    def __str__(self) -> str:
        return self.__class__.__name__

    def run(self, recipe: _recipe.Recipe, fix: bool = False) -> list[LintMessage]:
        """
        Run the check on a recipe. Called by Linter

        :param recipe: The recipe to be linted
        :param fix: Whether to attempt to fix the recipe
        """
        self.messages: list[LintMessage] = []
        self.recipe: _recipe.Recipe = recipe
        self.try_fix = fix

        # Run general checks
        self.check_recipe(recipe)

        # Run per source checks
        source = recipe.get("source", None)
        if isinstance(source, dict):
            self.check_source(source, "source")
        elif isinstance(source, list):
            for num, src in enumerate(source):
                self.check_source(src, f"source/{num}")

        # Run depends checks
        self.check_deps(_utils.get_deps_dict(recipe))

        return self.messages

    def check_recipe(self, recipe: _recipe.Recipe) -> None:
        """
        Execute check on recipe

        Override this method in subclasses, using ``self.message()``
        to issue `LintMessage` as failures are encountered.

        :param recipe: The recipe under test.
        """

    def check_source(self, source: dict, section: str) -> None:
        """
        Execute check on each source

        :param source: dictionary containing the source section
        :param section: Path to the section. Can be `source` or `source/0` (1,2,3...).
        """

    def check_deps(self, deps: dict[str, list[str]]) -> None:
        """
        Execute check on recipe dependencies

        Example format for **deps**::

            {
              'setuptools': ['requirements/run',
                             'outputs/0/requirements/run/1'],
              'compiler_cxx': ['requirements/build/0']
            }

        You can use the values in the list directly as `section`
        parameter to `self.message()`.

        :param deps: dictionary mapping requirements occurring in the recipe to their locations within the recipe.
        """

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
        section: str = None,
        severity: Severity = SEVERITY_DEFAULT,
        fname: str = None,
        line: int = None,
        data: Any = None,
        output: int = -1,
    ) -> None:
        """
        Add a message to the lint results

        Also calls `fix` if we are supposed to be fixing.

        :param args: Additional arguments to pass directly to the message
        :param section: If specified, a lint location within the recipe meta.yaml pointing to this section/subsection
            will be added to the message
        :param severity: The severity level of the message.
        :param fname: If specified, the message will apply to this file, rather than the recipe meta.yaml
        :param line: If specified, sets the line number for the message directly
        :param data: Data to be passed to `fix`. If check can fix, set this to something other than None.
        :param output: the output the error occurred in (multi-output recipes only)
        """
        message = self.make_message(
            *args,
            recipe=self.recipe,
            section=section,
            severity=severity,
            fname=fname,
            line=line,
            canfix=data is not None,
            output=output,
        )
        if data is not None and self.try_fix and self.fix(message, data):
            return
        self.messages.append(message)

    @classmethod
    def make_message(
        cls,
        *args: Any,
        recipe: _recipe.Recipe,
        section: str = None,
        severity: Severity = SEVERITY_DEFAULT,
        fname: str = None,
        line: int = None,
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
        :param line: If specified, sets the line number for the message directly
        :param canfix: If specified, indicates if the rule can/can't be auto-fixed
        :param output: The output the error occurred in (multi-output recipes only)
        """
        doc = inspect.getdoc(cls)
        doc = doc.replace("::", ":").replace("``", "`")
        title, _, body = doc.partition("\n")
        if len(args) > 0:
            title = title.format(*args)
        if output >= 0:
            name = recipe.get(f"outputs/{output}/name", "")
            if name != "":
                title = f'output "{name}": {title}'
        if section:
            try:
                sl, _, el, ec = recipe.get_raw_range(section)
            except KeyError:
                sl, el, ec = 1, 1, 1
            if ec == 0:
                el = el - 1
            start_line = sl
            end_line = el
        else:
            start_line = end_line = line or 0

        if not fname:
            fname = recipe.path
        fname = str(Path(*Path(fname).parts[-3:]))
        return LintMessage(
            recipe=recipe,
            check=cls,
            severity=severity,
            title=title.strip(),
            body=body,
            fname=fname,
            start_line=start_line,
            end_line=end_line,
            canfix=canfix,
        )


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

    def __init__(
        self,
        config: dict,
        verbose: bool = False,
        exclude: list[str] = None,
        nocatch: bool = False,
        severity_min: Optional[Severity | str] = None,
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
        self._messages = []
        # TODO rm: de-risk this. Enforce `Severity` over `str` universally
        if isinstance(severity_min, Severity):
            self.severity_min = severity_min
        elif isinstance(severity_min, str):
            try:
                self.severity_min = Severity[severity_min]
            except KeyError as e:
                raise ValueError(f"Unrecognized severity level {severity_min}") from e
        else:
            self.severity_min = SEVERITY_MIN_DEFAULT

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
            key=lambda d: (d.fname, d.end_line),
        )

    def clear_messages(self) -> None:
        """
        Clears the lint messages stored in linter
        """
        self._messages = []

    @classmethod
    def get_report(
        cls,
        messages: list[LintMessage],
        verbose: bool = False,  # pylint: disable=unused-argument
    ) -> str:
        """
        Returns a report of all the linting messages.
        :param messages: list of messages to process.
        :param verbose: (Optional) Enables additional reporting.
        :returns: String, containing information about all the linting messages, as a report.
        """
        messages_grouped: dict[Severity, List[LintMessage]] = {sev: [] for sev in Severity}
        num_errors: dict[Severity, int] = {sev: 0 for sev in [Severity.ERROR, Severity.WARNING]}

        for msg in messages:
            messages_grouped[msg.severity].append(msg)
            if msg.severity in [Severity.ERROR, Severity.WARNING]:
                num_errors[msg.severity] += 1

        report: str = ""
        report_sections: List[str] = []

        for severity in [Severity.WARNING, Severity.ERROR]:
            if messages_grouped[severity]:
                report_sections.append(
                    f"===== {severity.name.upper()}S ===== \n"
                    + "\n".join(
                        f"- {msg.fname}:{msg.end_line}: {msg.check}: {msg.title}" for msg in messages_grouped[severity]
                    )  # if verbose add msg.body
                    + "\n"
                )
        if report_sections:
            report += "\n".join(report_sections)

        report += (
            "\n"
            f"===== Final Report: =====\n"
            f"{num_errors[Severity.ERROR]} Error{'s' if num_errors[Severity.ERROR] != 1 else ''} "
            f"and {num_errors[Severity.WARNING]} Warning{'s' if num_errors[Severity.WARNING] != 1 else ''} were found"
        )
        return report

    def lint(
        self,
        recipes: list[Union[str, _recipe.Recipe]],
        arch_name: str = "linux-64",
        variant_config_files: Optional[list[str]] = None,
        exclusive_config_files: Optional[list[str]] = None,
        fix: bool = False,
    ) -> bool:
        """
        Run linter on multiple recipes

        Lint messages are collected in the linter. They can be retrieved
        with `get_messages` and the list cleared with `clear_messages`.

        :param recipes: list of names of recipes or Recipe objects to lint
        :param arch_name: Target architecture to run against
        :param variant_config_files: Configuration information for variants
        :param exclusive_config_files: Configuration information for exclusive files
        :param fix: Whether checks should attempt to fix detected issues

        :returns: True if issues with errors were found
        """
        if variant_config_files is None:
            variant_config_files = []
        if exclusive_config_files is None:
            exclusive_config_files = []
        if len(recipes) == 0:
            return 0
        if isinstance(recipes[0], str):
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
                    msgs = [linter_failure.make_message(recipe=recipe)]
                self._messages.extend(msgs)
        elif isinstance(recipes[0], _recipe.Recipe):
            for recipe in recipes:
                try:
                    msgs = self.lint_recipe(
                        recipe,
                        fix=fix,
                    )
                except Exception:  # pylint: disable=broad-exception-caught
                    if self.nocatch:
                        raise
                    logger.exception("Unexpected exception in lint")
                    msgs = [linter_failure.make_message(recipe=recipe)]
                self._messages.extend(msgs)

        result = 0
        for message in self._messages:
            if message.severity == ERROR:
                result = ERROR
                break
            elif message.severity == WARNING:
                result = WARNING

        return result

    def lint_file(
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
        variants = None
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
        except RecipeError as exc:
            recipe = _recipe.Recipe(recipe_name)
            check_cls = recipe_error_to_lint_check.get(exc.__class__, linter_failure)
            return [check_cls.make_message(recipe=recipe, line=getattr(exc, "line"))]

        # lint variants
        messages = set()
        try:
            for vid, variant in variants:
                logging.debug("Linting variant %s", vid)
                recipe = _recipe.Recipe.from_file(
                    recipe_fname=str(meta_yaml),
                    variant_id=vid,
                    variant=variant,
                    renderer=RendererType.RUAMEL,
                )
                if not recipe.skip:
                    messages.update(
                        self.lint_recipe(
                            recipe,
                            fix=fix,
                        )
                    )
                    if fix and recipe.is_modified():
                        with open(recipe.path, "w", encoding="utf-8") as fdes:
                            fdes.write(recipe.dump())
        except RecipeError as exc:
            recipe = _recipe.Recipe(recipe_name)
            check_cls = recipe_error_to_lint_check.get(exc.__class__, linter_failure)
            return [check_cls.make_message(recipe=recipe, line=getattr(exc, "line"))]

        return list(messages)

    def lint_recipe(
        self,
        recipe: _recipe.Recipe,
        fix: bool = False,
    ) -> list[LintMessage]:
        """
        Lints a recipe
        :param recipe: Recipe to lint against.
        :param fix: (Optional) Enables auto-fixing of the lint checks
        :returns: list of linting messages returned from executing checks against the linter.
        """
        # collect checks to skip
        checks_to_skip = set(self.exclude)

        # currently skip-lints will overwrite only-lint, we can check for the key
        # being in checks_to_skip, but I think letting the user do this is best?
        checks_to_skip.update(recipe.get("extra/skip-lints", []))
        if only_lint := recipe.get("extra/only-lint", []):
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
                res = self.check_instances[check].run(recipe, fix)
            except Exception:  # pylint: disable=broad-exception-caught
                if self.nocatch:
                    raise
                logger.exception("Unexpected exception in lint_recipe")
                res = [
                    LintMessage(
                        recipe=recipe,
                        check=check,
                        severity=ERROR,
                        title="Check raised an unexpected exception",
                    )
                ]

            if res:  # skip checks depending on failed checks
                checks_to_skip.update(nx.ancestors(self.checks_dag, str(check)))
            messages.extend(res)

        for message in messages:
            logger.debug("Found: %s", message)

        return messages
