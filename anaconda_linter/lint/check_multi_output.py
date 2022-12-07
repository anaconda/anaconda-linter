from . import LintCheck


class outputs_not_unique(LintCheck):
    """The output name {} is not unique

    Please make sure all output names are unique
    and are not the same as the package name.
    """

    def check_recipe(self, recipe):
        if outputs := recipe.get("outputs", None):
            reset_text = self.__class__.__doc__
            unique_names = [recipe.get("package/name")]
            output_names = [output.get("name") for output in outputs]
            for n, name in enumerate(output_names):
                if name in unique_names:
                    self.__class__.__doc__ = reset_text.format(name)
                    self.message(section=f"outputs/{n}/name")
                    self.__class__.__doc__ = reset_text
                else:
                    unique_names.append(name)
