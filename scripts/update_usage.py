#!/usr/bin/env python3
# File:         update_usage.py
# Description:  Custom `pre-commit` script that automatically updates the usage
#               message printed by `conda lint -h`

import sys
from pathlib import Path

from anaconda_linter import run

# Path to the `README.md` file
README = Path("./README.md")

# Comment blocks indicating where text should be replaced
BEGIN_SECTION = "<!-- begin_to_update_usage -->\n"
END_SECTION = "<!-- end_to_update_usage -->\n"


def find_line(data: list[str], section: str) -> int:
    """
    Finds the line number of a commented usage section header
    :param: data    Lines of the `README.md` file to process
    :param: section Commented section header to target
    :return: Index of the particular section header. If not found, the script
             must exit immediately.
    """
    try:
        return data.index(section)
    except ValueError:
        print(f"Could not find usage section marker: {section}")
        sys.exit(1)


def main() -> None:
    """
    Main execution point of the script
    """
    # Formatted output from `-h`
    usage_list = f"```sh\n{run.lint_parser().format_help()}\n```\n".splitlines(True)

    data = None
    with open(README) as file:
        data = file.readlines()

    begin_idx = find_line(data, BEGIN_SECTION)
    end_idx = find_line(data, END_SECTION)

    # Remove the old message and insert the new one in-place
    data = data[: begin_idx + 1] + data[end_idx:]
    data[begin_idx + 1 : begin_idx + 1] = usage_list

    with open(README, "w") as file:
        file.writelines(data)


if __name__ == "__main__":
    main()
