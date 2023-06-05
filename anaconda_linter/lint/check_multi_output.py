from .. import utils as _utils
from . import INFO, WARNING, LintCheck


class output_missing_name(LintCheck):
    """Output has no name.

    Each output must have a unique name. Please add:
    outputs:
      - name: <output name>
    """

    def check_recipe(self, recipe):
        if outputs := recipe.get("outputs", None):
            output_names = [recipe.get(f"outputs/{n}/name", None) for n in range(len(outputs))]
            for n, name in enumerate(output_names):
                if name is None:
                    self.message(section=f"outputs/{n}")


class outputs_not_unique(LintCheck):
    """Output name is not unique

    Please make sure all output names are unique
    and are not the same as the package name.
    """

    def check_recipe(self, recipe):
        if outputs := recipe.get("outputs", None):
            unique_names = [recipe.get("package/name")]
            output_names = [recipe.get(f"outputs/{n}/name", "") for n in range(len(outputs))]
            for n, name in enumerate(output_names):
                if name in unique_names:
                    self.message(section=f"outputs/{n}/name", output=n)
                else:
                    unique_names.append(name)


class no_global_test(LintCheck):
    """Global tests are ignored in multi-output recipes.

    Tests must be added to each individual output.
    """

    def check_recipe(self, recipe):
        if recipe.get("outputs", None) and recipe.get("test", None):
            self.message(severity=WARNING)


class output_missing_script(LintCheck):
    """Output is missing script.

    Every output must have either a filename or a command in the script field.
    """

    def check_recipe(self, recipe):
        # May not need scripts if pin_subpackage is used.
        # Pinned subpackages are expanded to their names.
        outputs = recipe.get("outputs", [])
        output_names = {recipe.get(f"outputs/{n}/name", None) for n in range(len(outputs))}
        deps = _utils.get_deps_dict(recipe, "run")
        subpackages = output_names.intersection(set(deps.keys()))
        for o in range(len(recipe.get("outputs", []))):
            # True if subpackage is a run dependency
            if any(
                path.startswith(f"outputs/{o}/")
                for name in subpackages
                for path in deps[name]["paths"]
            ):
                continue
            if recipe.get(f"outputs/{o}/script", "") == "":
                self.message(output=o, severity=INFO)


class output_script_name_default(LintCheck):
    """Output should not use default script names build.sh/bld.bat."""

    def check_recipe(self, recipe):
        default_scripts = ("build.sh", "bld.bat")
        for o in range(len(recipe.get("outputs", []))):
            if recipe.get(f"outputs/{o}/script", "") in default_scripts:
                self.message(output=o)
