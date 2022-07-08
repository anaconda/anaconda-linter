import argparse, logging, sys

from conda_lint.utils import file_path, dir_path
from conda_lint.linter import lint_bom


def execute(args):
    # TODO: Make this more extensible, model after either conda-build or smithy
    parser = argparse.ArgumentParser(
        description="a tool to validate SPDX license standards",
    )

    subparsers = parser.add_subparsers(help="sub-command help")

    lint = subparsers.add_parser(
        "lint",
        help="lint help"
    )
    lint.add_argument(
        "-f",
        "--file",
        action="extend",
        nargs="+",
        type=file_path,
        help="Lints one or more files in a given path for SPDX compatibility.",
    )
    
    lint.add_argument(
        "-p",
        "--package",
        type=dir_path,
        help="Searches for a meta.yaml file or index.json file in a directory and lints for SPDX compatibility."
    )


    if not args:
        args = parser.parse_args(["--help"])
    else:
        args = parser.parse_args(args)

    if args.file:
        for file in args.file:
            print(lint_bom(file))
    elif args.package:
        pass
        # will probably need to be able to handle tar.bgz eventually
        # TODO: find all meta.yaml
        # TODO: find index.json

def main():
    return execute(sys.argv[1:])

if __name__ == "__main__":
    main()