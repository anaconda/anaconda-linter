"""
File:           run.py
Description:    Primary execution point of the linter's CLI
"""

from __future__ import annotations

import argparse
import os
import sys
import textwrap
import traceback
from enum import IntEnum
from typing import Final, Optional

from anaconda_linter import __version__, lint, utils

DEFAULT_SUBDIRS: Final[list[str]] = [
    "linux-64",
    "linux-aarch64",
    "linux-ppc64le",
    "linux-s390x",
    "osx-64",
    "osx-arm64",
    "win-64",
]


# POSIX style return codes
class ReturnCode(IntEnum):
    EXIT_SUCCESS = 0
    EXIT_UNCAUGHT_EXCEPTION = 42
    EXIT_LINTING_WARNINGS = 100
    EXIT_LINTING_ERRORS = 101


def _convert_severity(s: str) -> lint.Severity:
    """
    Converts the string provided by the argument parser to a Severity Enum.
    :param s: Sanitized, upper-cased Severity that is not `Severity.NONE`.
    :returns: Equivalent severity enumeration
    """
    s = s.upper()
    if s in lint.Severity.__members__:
        return lint.Severity.__members__[s]
    # It should not be possible to be here, but I'd rather default to a severity level than crash or throw.
    return lint.SEVERITY_DEFAULT


def _lint_parser() -> argparse.ArgumentParser:
    """
    Configures the `argparser` instance used for the linter's CLI
    :returns: An `argparser` instance to parse command line arguments
    """

    def check_path(value) -> str:
        if not os.path.isdir(value):
            raise argparse.ArgumentTypeError(f"The specified directory {value} does not exist")
        return os.path.abspath(value)

    parser = argparse.ArgumentParser(
        prog="anaconda-lint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
                anaconda-lint:
                Performs linting on conda recipes."""
        ),
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="The version of anaconda-linter",
    )
    parser.add_argument(
        "-m",
        "--variant-config-files",
        action="append",
        default=[],
        help="""Additional variant config files to add.  These yaml files can contain
        keys such as `c_compiler` and `target_platform` to form a build matrix.""",
    )
    parser.add_argument(
        "-e",
        "--exclusive-config-files",
        "--exclusive-config-file",
        action="append",
        default=[],
        help="""Exclusive variant config files to add. Providing files here disables
        searching in your home directory and in cwd.  The files specified here come at the
        start of the order, as opposed to the end with --variant-config-files.  Any config
        files in recipes and any config files specified with --variant-config-files will
        override values from these files.""",
    )
    parser.add_argument(
        "-s",
        "--subdirs",
        default=DEFAULT_SUBDIRS,
        action="append",
        help="""List subdir to lint. Example: linux-64, win-64...""",
    )
    parser.add_argument(
        "--severity",
        choices=[lint.Severity.INFO.name, lint.Severity.WARNING.name, lint.Severity.ERROR.name],
        default=lint.SEVERITY_MIN_DEFAULT.name,
        # Handles case-insensitive versions of the names
        type=lambda s: s.upper(),
        help="""The minimum severity level displayed in the output.""",
    )
    # we do this one separately because we only allow one entry to conda render
    parser.add_argument(
        "recipe",
        type=check_path,
        metavar="RECIPE_PATH",
        help="Path to recipe directory.",
    )
    # this is here because we have a different default than build
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output. This displays all of the checks that the linter is running.",
    )
    # this is here because we have a different default than build
    parser.add_argument(
        "-f",
        "--fix",
        action="store_true",
        help="Attempt to fix issues.",
    )
    return parser


def execute_linter(  # pylint: disable=too-many-positional-arguments
    recipe: str,
    config: Optional[utils.RecipeConfigType] = None,
    variant_config_files: Optional[list[str]] = None,
    exclusive_config_files: Optional[list[str]] = None,
    subdirs: Optional[list[str]] = None,
    severity: lint.Severity = lint.SEVERITY_MIN_DEFAULT,
    fix_flag: bool = False,
    verbose_flag: bool = False,
) -> tuple[ReturnCode, str]:
    """
    Contains the primary execution code that would be in `main()`. This gives us a few benefits:
      - Allows us to easily wrap and control return codes in unexpected failure cases.
      - Allows us to execute the linter work as a library call in another Python project.
    :param recipe: Path to the target feedstock (where `recipe/meta.yaml` can be found)
    :param config: (Optional) Defaults to the contents of the default config file provided in `config.yaml`.
    :param variant_config_files: (Optional) Configuration files for recipe variants
    :param exclusive_config_files: (Optional) Configuration files for exclusive recipe variants
    :param subdirs: (Optional) Target recipe architectures/platforms
    :param severity: (Optional) Minimum severity level of linting messages to report
    :param fix_flag: (Optional) If set to true, the linter will automatically attempt to make changes to the target
                     recipe file.
    :param verbose_flag: (Optional) Enables verbose debugging output.
    :returns: The appropriate error code and the final text report containing linter results.
    """
    # We want to remove our reliance on external files when the project is run as a library.
    if config is None:
        config = {
            "requirements": "requirements.txt",
            "blocklists": ["build-fail-blocklist"],
            "channels": ["defaults"],
        }

    if subdirs is None:
        subdirs = DEFAULT_SUBDIRS

    # set up linter
    linter = lint.Linter(config=config, verbose=verbose_flag, exclude=None, nocatch=True, severity_min=severity)

    # run linter
    recipes = [f"{recipe}/recipe/"]
    messages = set()
    overall_result = 0
    # TODO evaluate this: Not all of our rules require checking against variants now that we have the parser in percy.
    # TODO evaluate when the linter must be run on each variant,
    # and how to handle the auto-fixing. For now, auto-fixing is disabled.
    for subdir in subdirs:
        result = linter.lint(recipes, subdir, variant_config_files, exclusive_config_files, fix=fix_flag)
        if result > overall_result:  # pylint: disable=consider-using-max-builtin
            overall_result = result
        messages = messages | set(linter.get_messages())

    # Calculate the final report
    report: Final[str] = lint.Linter.get_report(messages, verbose_flag)

    # Return appropriate error code.
    if overall_result == lint.Severity.WARNING:
        return ReturnCode.EXIT_LINTING_WARNINGS, report
    elif overall_result >= lint.Severity.ERROR:
        return ReturnCode.EXIT_LINTING_ERRORS, report
    return ReturnCode.EXIT_SUCCESS, report


def main() -> None:
    """
    Primary execution point of the linter's CLI
    """
    args, _ = _lint_parser().parse_known_args()
    severity: Final[lint.Severity] = _convert_severity(args.severity)

    # load global configuration
    config_file: Final[str] = os.path.abspath(os.path.dirname(__file__) + "/config.yaml")
    config: Final[utils.RecipeConfigType] = utils.load_config(config_file)

    try:
        return_code, report = execute_linter(
            recipe=args.recipe,
            config=config,
            variant_config_files=args.variant_config_files,
            exclusive_config_files=args.exclusive_config_files,
            subdirs=args.subdirs,
            severity=severity,
            fix_flag=args.fix,
            verbose_flag=args.verbose,
        )
        print(report)
        sys.exit(return_code)
    except Exception:  # pylint: disable=broad-exception-caught
        traceback.print_exc()
        sys.exit(ReturnCode.EXIT_UNCAUGHT_EXCEPTION)


if __name__ == "__main__":
    main()
