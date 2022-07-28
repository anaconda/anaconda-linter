import sys
from conda_lint.linters import SBOMLinter

def execute(args):
    lints = []
    linters = [
        SBOMLinter,
    ]
    for l in linters:
        linter = l(args)
        if not args:
            args = linter.parse_args(["--help"])
        else:
            args = linter.parse_args()
        lints.extend(linter.lint(args))
    for line in lints:
        print(line)


def main():
    return execute(sys.argv[1:])


if __name__ == "__main__":
    main()
