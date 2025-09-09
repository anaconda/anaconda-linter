"""
File:           check_multi_output.py
Description:    Contains linter checks for multi-output based rules.
"""

from __future__ import annotations

from conda_recipe_manager.parser.recipe_reader_deps import RecipeReaderDeps

from anaconda_linter import utils as _utils
from anaconda_linter.lint import LintCheck, Severity


class output_missing_name(LintCheck):
    """
    Output has no name.

    Each output must have a unique name. Please add:
    outputs:
      - name: <output name>
    """

    def check_recipe_legacy(self, recipe) -> None:
        if outputs := recipe.get("outputs", None):
            output_names = [recipe.get(f"outputs/{n}/name", None) for n in range(len(outputs))]
            for n, name in enumerate(output_names):
                if name is None:
                    self.message(section=f"outputs/{n}")


class outputs_not_unique(LintCheck):
    """
    Output name is not unique

    Please make sure all output names are unique
    and are not the same as the package name.
    """

    def check_recipe(self, recipe_name: str, arch_name: str, recipe: RecipeReaderDeps) -> None:
        unique_names: set[str] = set()
        for output in recipe.get_package_paths():
            name_path = "/package/name" if output == "/" else recipe.append_to_path(output, "/name")
            if not recipe.contains_value(name_path):
                self.message(
                    section=name_path, title_in="Failed to find package or output name, cannot run this check."
                )
                continue
            name = recipe.get_value(name_path)
            if name in unique_names:
                self.message(section=name_path)
            unique_names.add(name)


class no_global_test(LintCheck):
    """
    Global tests are ignored in multi-output recipes.

    Tests must be added to each individual output.
    """

    def check_recipe(self, recipe_name: str, arch_name: str, recipe: RecipeReaderDeps) -> None:
        if recipe.is_multi_output() and recipe.contains_value("/test"):
            self.message(section="/test")


class output_missing_script(LintCheck):
    """
    Output is missing script.

    Every output must have either a filename or a command in the script field.
    """

    def check_recipe_legacy(self, recipe) -> None:
        # May not need scripts if pin_subpackage is used.
        # Pinned subpackages are expanded to their names.
        outputs = recipe.get("outputs", [])
        output_names = {recipe.get(f"outputs/{n}/name", None) for n in range(len(outputs))}
        deps = _utils.get_deps_dict(recipe, "run")
        subpackages = output_names.intersection(set(deps.keys()))
        for o in range(len(recipe.get("outputs", []))):
            # True if subpackage is a run dependency
            if any(path.startswith(f"outputs/{o}/") for name in subpackages for path in deps[name]["paths"]):
                continue
            if recipe.get(f"outputs/{o}/script", "") == "":
                self.message(output=o, severity=Severity.INFO)


class output_script_name_default(LintCheck):
    """
    Output should not use default script names build.sh/bld.bat.
    """

    def check_recipe_legacy(self, recipe) -> None:
        default_scripts = ("build.sh", "bld.bat")
        for o in range(len(recipe.get("outputs", []))):
            if recipe.get(f"outputs/{o}/script", "") in default_scripts:
                self.message(output=o)
