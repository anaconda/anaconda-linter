import argparse, logging, sys

from conda_lint.linters import SBOMLinter


def execute(args):
    parser = SBOMLinter(args)
    parser.lint()

def main():
    return execute(sys.argv[1:])

if __name__ == "__main__":
    main()