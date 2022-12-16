from . import WARNING, LintCheck


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