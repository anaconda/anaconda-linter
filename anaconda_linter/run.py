import lint
import os
import sys
import utils
import argparse
import textwrap

from typing import List


def parseArguments(argv: list[str]) -> argparse.Namespace:
    def checkPath(value):
        if not os.path.isdir(value):
            raise argparse.ArgumentTypeError("The specified directory does not exist")
        return os.path.abspath(value)

    parser = argparse.ArgumentParser(prog="anaconda-lint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
                anaconda-lint:
                Performs linting on conda recipes.'''))
    parser.add_argument("aggregatePath",
        type=checkPath,
        help="Location of the aggregate directory.")
    parser.add_argument("feedstockDir",
        help="Feedstock directory, located inside the aggregate directory.")
    parser.add_argument("-v", "--verbose",
        action="store_true",
        help="Enable verbose output. This displays all of the checks that the linter is running.")

    return parser.parse_args(argv)

if __name__ == "__main__":
    config_file = os.path.abspath(os.path.dirname(__file__) + "/config.yaml")
    config = utils.load_config(config_file)

    args = vars(parseArguments(sys.argv[1:]))
    aggregatePath = args['aggregatePath']
    recipes = [f"{aggregatePath}/{args['feedstockDir']}/recipe/"]
    linter = lint.Linter(config, aggregatePath, args['verbose'], None, True)
    result = linter.lint(recipes, 'linux-64')
    messages = linter.get_messages()

    if messages:
        print("The following problems have been found:\n")
        print(linter.get_report())

    if not result:
        print("All checks OK")
    elif result == lint.WARNING:
        print("Warnings were found")
    else:
        sys.exit("Errors were found")
