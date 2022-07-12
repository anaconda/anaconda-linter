import argparse, logging, sys

from conda_lint.utils import file_path, dir_path
from conda_lint.linters import *


def execute(args):
    # TODO: Make this more extensible, model after either conda-build or smithy
    parser = SBOMLinter(args)
    parser.lint()
        # will probably need to be able to handle tar.bgz eventually
        # TODO: find all meta.yaml
        # TODO: find index.json

def main():
    return execute(sys.argv[1:])

if __name__ == "__main__":
    main()