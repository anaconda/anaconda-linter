from argparse import ArgumentParser
import glob
import os
from pathlib import Path
import re
from typing import List

import license_expression
from ruamel.yaml import YAML
yaml = YAML(typ="safe", pure=True)

from conda_lint.utils import *

LICENSES_PATH = Path("data", "licenses.txt")
EXCEPTIONS_PATH = Path("data", "license_exceptions.txt")

class BasicLinter(ArgumentParser):
    def __init__(self, args: List):
        super(BasicLinter, self).__init__(*args)
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
            help="Searches for a meta.yaml file or index.json file in a directory and lints for SPDX compatibility."
        )
        # returns namespace
        if not args:
            self.args = self.parse_args(["--help"])
        else:
            self.args = self.parse_args(args)

class SBOMLinter(BasicLinter):
    def __init__(self, *args):
        super(SBOMLinter, self).__init__(*args)
        self.description = "a tool to validate SPDX license standards"

    def lint(self):
        if self.args.file:
            for file in self.args.file:
                linted = self.lint_bom(file)
                if linted:
                    print(linted)
        elif self.args.package:
            pass
        else:
            print("No files found to lint")

    def lint_bom(self, metafile):
        hints = []
        with open(metafile, "r") as f:
            meta = yaml.load(f)

        about_section = meta.get("about")
        license = about_section.get("license", "")
        licensing = license_expression.Licensing()
        parsed_exceptions = []
        try:
            parsed_licenses = []
            parsed_licenses_with_exception = licensing.license_symbols(
                license.strip(), decompose=False
            )
            for l in parsed_licenses_with_exception:
                if isinstance(l, license_expression.LicenseWithExceptionSymbol):
                    parsed_licenses.append(l.license_symbol.key)
                    parsed_exceptions.append(l.exception_symbol.key)
                else:
                    parsed_licenses.append(l.key)
        except license_expression.ExpressionError:
            parsed_licenses = [license]

        licenseref_regex = re.compile(r"^LicenseRef[a-zA-Z0-9\-.]*$")
        filtered_licenses = []
        for license in parsed_licenses:
            if not licenseref_regex.match(license):
                filtered_licenses.append(license)

        with open(
            os.path.join(os.path.dirname(__file__), LICENSES_PATH), "r"
        ) as f:
            expected_licenses = f.readlines()
            expected_licenses = set([l.strip() for l in expected_licenses])
        with open(
            os.path.join(os.path.dirname(__file__), EXCEPTIONS_PATH), "r"
        ) as f:
            expected_exceptions = f.readlines()
            expected_exceptions = set([l.strip() for l in expected_exceptions])
        non_spdx_licenses = set(filtered_licenses) - expected_licenses
        if non_spdx_licenses:
            hints.append(
                "License is not an SPDX identifier (or a custom LicenseRef) nor an SPDX license expression.\n\n"
                "Documentation on acceptable licenses can be found "
                "[here]( https://conda-forge.org/docs/maintainer/adding_pkgs.html#spdx-identifiers-and-expressions )."
            )
            for license in non_spdx_licenses:
                closest = find_closest_match(license)
                if closest:
                    hints.append(f"Original license name: {license}. Closest SPDX identifier found: {closest}")
                else:
                    continue    
        non_spdx_exceptions = set(parsed_exceptions) - expected_exceptions
        if non_spdx_exceptions:
            hints.append(
                "License exception is not an SPDX exception.\n\n"
                "Documentation on acceptable licenses can be found "
                "[here]( https://conda-forge.org/docs/maintainer/adding_pkgs.html#spdx-identifiers-and-expressions )."
            )
        
        return hints
