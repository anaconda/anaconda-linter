import argparse
import os
import textwrap

from anaconda_linter import __version__, lint, utils


def lint_parser() -> argparse.ArgumentParser:
    def check_path(value):
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
        default=[
            "linux-64",
            "linux-aarch64",
            "linux-ppc64le",
            "linux-s390x",
            "osx-64",
            "osx-arm64",
            "win-64",
        ],
        action="append",
        help="""List subdir to lint. Example: linux-64, win-64...""",
    )
    parser.add_argument(
        "--severity",
        choices=["INFO", "WARNING", "ERROR"],
        type=str.upper,
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


def main():
    # parse arguments
    parser = lint_parser()
    args, _ = parser.parse_known_args()

    # load global configuration
    config_file = os.path.abspath(os.path.dirname(__file__) + "/config.yaml")
    config = utils.load_config(config_file)

    # set up linter
    linter = lint.Linter(config=config, verbose=args.verbose, exclude=None, nocatch=True, severity_min=args.severity)

    # run linter
    recipes = [f"{args.recipe}/recipe/"]
    messages = set()
    overall_result = 0
    for subdir in args.subdirs:
        result = linter.lint(recipes, subdir, args.variant_config_files, args.exclusive_config_files, args.fix)
        if result > overall_result:
            overall_result = result
        messages = messages | set(linter.get_messages())

    # print report
    if messages:
        print("The following problems have been found:\n")
        print(lint.Linter.get_report(messages, args.verbose))
    if not overall_result:
        print("All checks OK")
    elif overall_result == lint.WARNING:
        print("Warnings were found")
    else:
        print("Errors were found")


if __name__ == "__main__":
    main()
