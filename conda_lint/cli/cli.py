import argparse, logging, sys

from conda_lint.linters import SBOMLinter


def execute(args):
    linter = SBOMLinter(args)
    if not args:
        args = linter.parse_args(["--help"])
    else:
        args = linter.parse_args(args)
    linter.lint(args)

def main():
    return execute(sys.argv[1:])

if __name__ == "__main__":
    main()