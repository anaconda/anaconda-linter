from argparse import ArgumentParser
import glob
import os
from pathlib import Path
import re
from typing import List

from jinja2 import Environment, BaseLoader
import license_expression
from ruamel.yaml import YAML
yaml = YAML(typ="safe", pure=True)

from conda_lint.utils import dir_path, file_path, find_closest_match

LICENSES_PATH = Path("data", "licenses.txt")
EXCEPTIONS_PATH = Path("data", "license_exceptions.txt")


class BasicLinter(ArgumentParser):
    def __init__(self, *args):
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
            help="Searches for a filename in a directory and lints for SPDX compatibility. Specify filename with -fn"
        )
    

class JinjaLinter(BasicLinter):
    def __init__(self, args=[]):
        super(JinjaLinter, self).__init__(*args)
        self.add_argument(
            "--return_yaml",
            action="store_true"
        )

    def lint(self, args):
        lints = []
        # figure out jinja lint logic later
        # also add -f and -p logic
        if args.return_yaml:
            text = self.remove_jinja(args.file[0])    
            return lints, text
    
    def remove_jinja(self, file: str) -> str:
        with open(file, "r") as f:
            text = f.read()
            no_curlies = text.replace('{{ ', '{{ "').replace(' }}', '" }}')
        try:
            content = yaml.load(
                                Environment(loader=BaseLoader())
                                .from_string(no_curlies).render()
                                )
            return content
        except Exception as e:
            print(e)
            return None



class SBOMLinter(BasicLinter):
    def __init__(self, args=[]):
        super(SBOMLinter, self).__init__(*args)
        self.description = "a tool to validate SPDX license standards"
        self.add_argument(
            "-fn",
            "--filename",
            nargs="?",
            default="meta.yaml",
            help="Specifies the filename to use when searching a --package."
        )

    def lint(self, args):
        if args.file:
            for file in args.file:
                linted = self.lint_license(file)
                if linted:
                    print(linted)
        elif args.package:
            files = glob.glob(str(Path(args.package, '**', args.filename)), recursive=True)
            for file in files:
                linted = self.lint_license(file)
                if linted:
                    print(linted)
        else:
            print("No files found to lint")

    def lint_license(self, metafile):
        lints = []
        jlint = JinjaLinter()
        args = jlint.parse_args(["-f", f"{metafile}", "--return_yaml"])
        jlints, jinja_check = jlint.lint(args)
        lints.extend(jlints)
        meta = jinja_check
        hints = []

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
