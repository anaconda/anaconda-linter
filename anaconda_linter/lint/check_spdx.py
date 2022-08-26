"""Syntax

Verify that the recipe's syntax is correct.
"""

import os
import re
from pathlib import Path
from typing import Any

import license_expression

from . import LintCheck
from .. import utils

LICENSES_PATH = Path("..", "data", "licenses.txt")
EXCEPTIONS_PATH = Path("..", "data", "license_exceptions.txt")


class incorrect_license(LintCheck):
    """The recipe's ``about/license`` key is not an SPDX compliant license or license exception

    Please review::

        about:
           license: <name of license>

    """

    def message(
        self,
        section: str = None,
        fname: str = None,
        line: int = None,
        data: Any = None,
        hint: str = None,
    ) -> None:
        """Add a message to the lint results

        Also calls `fix` if we are supposed to be fixing.

        Args:
          section: If specified, a lint location within the recipe
                   meta.yaml pointing to this section/subsection will
                   be added to the message
          fname: If specified, the message will apply to this file, rather than the
                 recipe meta.yaml
          line: If specified, sets the line number for the message directly
          data: Data to be passed to `fix`. If check can fix, set this to
                something other than None.
        """
        message = self.make_message(self.recipe, section, fname, line, data is not None)

        if hint:
            print(hint)
        if data is not None and self.try_fix and self.fix(message, data):
            return
        self.messages.append(message)

    def check_recipe(self, recipe):
        licensing = license_expression.Licensing()
        license = recipe.get("about/license", "")
        parsed_exceptions = []
        hint = ""
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
                    hint = (
                        f"HINT: Current license value found: '{license}'. "
                        f"Did you mean: '{closest}'?"
                    )
                self.message(section="about/license", hint=hint)
        non_spdx_exceptions = set(parsed_exceptions) - expected_exceptions
        if non_spdx_exceptions:
            self.message(section="about/license", hint=hint)
