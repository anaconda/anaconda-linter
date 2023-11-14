"""
File:           check_spdx.py
Description:    Contains linter checks for SPDX licensing database based rules.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import license_expression

from anaconda_linter import utils
from anaconda_linter.lint import LintCheck

LICENSES_PATH = Path("..", "data", "licenses.txt")
EXCEPTIONS_PATH = Path("..", "data", "license_exceptions.txt")


class incorrect_license(LintCheck):
    """
    {}

    Please review::

        about:
           license: <name of license>

    """

    def check_recipe(self, recipe) -> None:
        licensing = license_expression.Licensing()
        license = recipe.get("about/license", "")  # pylint: disable=redefined-builtin
        parsed_exceptions = []
        try:
            parsed_licenses = []
            parsed_licenses_with_exception = licensing.license_symbols(license.strip(), decompose=False)
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
        for parsed_license in parsed_licenses:
            if not licenseref_regex.match(parsed_license):
                filtered_licenses.append(parsed_license)

        with open(os.path.join(os.path.dirname(__file__), LICENSES_PATH), encoding="utf-8") as f:
            expected_licenses = f.readlines()
            expected_licenses = {l.strip() for l in expected_licenses}
        with open(os.path.join(os.path.dirname(__file__), EXCEPTIONS_PATH), encoding="utf-8") as f:
            expected_exceptions = f.readlines()
            expected_exceptions = {l.strip() for l in expected_exceptions}
        non_spdx_licenses = set(filtered_licenses) - expected_licenses
        if non_spdx_licenses:
            for license in non_spdx_licenses:
                closest = utils.find_closest_match(license)
                if closest:
                    message_text = (
                        "The recipe's `about/license` key is not an SPDX compliant"
                        f" license or license exception, closest match: {closest}"
                    )
                else:
                    message_text = (
                        "The recipe's `about/license` key is not an SPDX compliant"
                        " license or license exception, reference https://spdx.org/licenses/"
                    )
                self.message(message_text, section="about/license")
        non_spdx_exceptions = set(parsed_exceptions) - expected_exceptions
        if non_spdx_exceptions:
            message_text = (
                "The recipe's `about/license` key is not an SPDX compliant license"
                " or license exception, reference https://spdx.org/licenses/exceptions-index.html"
            )
            self.message(message_text, section="about/license")
