"""
File:           check_syntax.py
Description:    Contains linter checks for syntax rules.
"""

from __future__ import annotations

import re

from anaconda_linter.lint import LintCheck


class version_constraints_missing_whitespace(LintCheck):
    """
    Packages and their version constraints must be space separated

    Example::

        host:
            python >=3

    """

    def check_recipe(self, recipe) -> None:
        check_paths = []
        for section in ("build", "run", "host"):
            check_paths.append(f"requirements/{section}")
        if outputs := recipe.get("outputs", None):
            for n in range(len(outputs)):
                for section in ("build", "run", "host"):
                    check_paths.append(f"outputs/{n}/requirements/{section}")

        constraints = re.compile("(.*?)([!<=>].*)")
        for path in check_paths:
            output = -1 if not path.startswith("outputs") else int(path.split("/")[1])
            for n, spec in enumerate(recipe.get(path, [])):
                if spec is None:
                    continue

                has_constraints = constraints.search(spec)
                if has_constraints:
                    # The second condition is a fallback.
                    # See: https://github.com/anaconda-distribution/anaconda-linter/issues/113
                    space_separated = has_constraints[1].endswith(" ") or " " in has_constraints[0]
                    if not space_separated:
                        self.message(section=f"{path}/{n}", data=True, output=output)

    def fix(self, message, data) -> bool:
        check_paths = []
        for section in ("build", "run", "host"):
            check_paths.append(f"requirements/{section}")
        if outputs := self.percy_recipe.get("outputs", None):
            for n in range(len(outputs)):
                for section in ("build", "run", "host"):
                    check_paths.append(f"outputs/{n}/requirements/{section}")

        constraints = re.compile("(.*?)([!<=>].*)")
        for path in check_paths:
            for spec in self.percy_recipe.get(path, []):
                has_constraints = constraints.search(spec)
                if has_constraints:
                    # The second condition is a fallback.
                    # See: https://github.com/anaconda-distribution/anaconda-linter/issues/113
                    space_separated = has_constraints[1].endswith(" ") or " " in has_constraints[0]
                    if not space_separated:
                        dep, ver = has_constraints.groups()
                        self.percy_recipe.replace(spec, f"{dep} {ver}", within="requirements")
        return True
