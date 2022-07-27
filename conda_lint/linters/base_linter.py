from conda_lint.utils import dir_path, file_path

from argparse import ArgumentParser


class BaseLinter(ArgumentParser):
    def __init__(self, *args):
        super(BaseLinter, self).__init__(*args)
        self.add_argument(
            "-f",
            "--file",
            action="extend",
            nargs="+",
            type=file_path,
            help="Lints one or more files in a given path for SPDX compatibility.",
        )
        self.add_argument(
            "-p",
            "--package",
            type=dir_path,
            help=("Searches for a filename in a directory and lints for"
                  " SPDX compatibility. Specify filename with -fn")
        )
