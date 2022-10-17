"""Syntax

Verify that the recipe's syntax is correct.
"""

import os
import re
from pathlib import Path

import license_expression

from .. import utils
from . import LintCheck

LICENSES_PATH = Path("..", "data", "licenses.txt")
EXCEPTIONS_PATH = Path("..", "data", "license_exceptions.txt")


reset_text = """{}

    Please review::

        about:
           license: <name of license>

"""


class incorrect_license(LintCheck):
    """{}

    Please review::

        about:
           license: <name of license>

    """

    def check_recipe(self, recipe):
        licensing = license_expression.Licensing()
        license = recipe.get("about/license", "")
        parsed_exceptions = []
        try:
            parsed_licenses = []
            parsed_licenses_with_exception = licensing.license_symbols(
                license.strip(), decompose=False
            )
            for l in parsed_licenses_with_exception:  # noqa
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

        with open(os.path.join(os.path.dirname(__file__), LICENSES_PATH)) as f:
            expected_licenses = f.readlines()
            expected_licenses = {l.strip() for l in expected_licenses}  # noqa
        with open(os.path.join(os.path.dirname(__file__), EXCEPTIONS_PATH)) as f:
            expected_exceptions = f.readlines()
            expected_exceptions = {l.strip() for l in expected_exceptions}  # noqa
        non_spdx_licenses = set(filtered_licenses) - expected_licenses
        if non_spdx_licenses:
            for license in non_spdx_licenses:
                closest = utils.find_closest_match(license)
                if closest:
                    self.__class__.__doc__ = self.__class__.__doc__.format(
                        "The recipe's `about/license` key is not an SPDX compliant"
                        f" license or license exception, closest match: {closest}"
                    )
                else:
                    self.__class__.__doc__ = self.__class__.__doc__.format(
                        "The recipe's `about/license` key is not an SPDX compliant"
                        " license or license exception, reference https://spdx.org/licenses/"
                    )
                self.message(section="about/license")
                self.__class__.__doc__ = reset_text
        non_spdx_exceptions = set(parsed_exceptions) - expected_exceptions
        if non_spdx_exceptions:
            self.__class__.__doc__ = self.__class__.__doc__.format(
                "The recipe's `about/license` key is not an SPDX compliant license"
                " or license exception, reference https://spdx.org/licenses/exceptions-index.html"
            )
            self.message(section="about/license")
            self.__class__.__doc__ = reset_text
