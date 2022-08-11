"""Syntax checks

These checks verify syntax (schema), in particular for the ``extra``
section that is otherwise free-form.

"""
import re

from . import LintCheck, ERROR, WARNING, INFO


class version_constraints_missing_whitespace(LintCheck):
    """Packages and their version constraints must be space separated

    Example::

        host:
            python >=3

    """
    def check_recipe(self, recipe):
        check_paths = []
        for section in ('build', 'run', 'host'):
            check_paths.append(f'requirements/{section}')

        constraints = re.compile("(.*?)([<=>].*)")
        for path in check_paths:
            for n, spec in enumerate(recipe.get(path, [])):
                has_constraints = constraints.search(spec)
                if has_constraints:
                    space_separated = has_constraints[1].endswith(" ")
                    if not space_separated:
                        self.message(section=f"{path}/{n}", data=True)

    def fix(self, _message, _data):
        check_paths = []
        for section in ('build', 'run', 'host'):
            check_paths.append(f'requirements/{section}')

        constraints = re.compile("(.*?)([<=>].*)")
        for path in check_paths:
            for spec in self.recipe.get(path, []):
                has_constraints = constraints.search(spec)
                if has_constraints:
                    space_separated = has_constraints[1].endswith(" ")
                    if not space_separated:
                        dep, ver = has_constraints.groups()
                        self.recipe.replace(spec, f"{dep} {ver}", within='requirements')
        return True