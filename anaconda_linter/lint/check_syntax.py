"""
File:           check_syntax.py
Description:    Contains linter checks for syntax rules.
"""
from __future__ import annotations

import re
from typing import Final, cast

from percy.parser.recipe_parser import RecipeParser

from anaconda_linter.lint import LintCheck


class version_constraints_missing_whitespace(LintCheck):
    """
    Packages and their version constraints must be space separated

    Example::

        host:
            python >=3

    """

    # TODO Future: percy should eventually have support for constraints. This regex may not be
    # sufficient enough to catch all accepted formats
    _CONSTRAINTS_RE: Final[re.Pattern[str]] = re.compile("(.*?)([!<=>].*)")

    def check_recipe(self, recipe) -> None:
        # Whitespace will be the same in all rendered forums of the recipe, so we use the RecipeParser infrastructure.
        # TODO future: in these instances, recipes should not be rendered in all formats AND only look at the
        # raw recipe file.
        ro_parser: Final[RecipeParser] = recipe.get_read_only_parser()
        check_paths: Final[list[str]] = ro_parser.get_dependency_paths()

        # Search all dependencies for missing whitespace
        for path in check_paths:
            output: Final[int] = -1 if not path.startswith("/outputs") else int(path.split("/")[2])
            spec = cast(str, ro_parser.get_value(path))
            has_constraints = version_constraints_missing_whitespace._CONSTRAINTS_RE.search(spec)
            if not has_constraints:
                continue
            # The second condition is a fallback.
            # See: https://github.com/anaconda-distribution/anaconda-linter/issues/113
            space_separated = has_constraints[1].endswith(" ") or " " in has_constraints[0]
            if space_separated:
                continue
            dependency, version = has_constraints.groups()
            new_dependency: Final[str] = f"{dependency} {version}"
            self.message(
                section=path,
                data={"path": path, "new_dependency": new_dependency},
                output=output,
            )

    def fix(self, message, data) -> bool:
        path = cast(str, data["path"])
        new_dependency = cast(str, data["new_dependency"])

        def _add_whitespace(parser: RecipeParser):
            selector: Final[str] = (
                "" if not parser.contains_selector_at_path(path) else parser.get_selector_at_path(path)
            )
            parser.patch({"op": "replace", "path": path, "value": new_dependency})
            if selector:
                parser.add_selector(path, selector)

        return self.recipe.patch_with_parser(_add_whitespace)
