import utils, lint, sys, os
from typing import List


if __name__ == "__main__":
    config = utils.load_config("./config.yaml")

    # TODO: figure out distinction between recipe_folder and recipe, 
    # and whether such a distinction is useful for us
    recipe_folder = f"{sys.argv[1]}"
    recipes = [recipe_folder]
    linter = lint.Linter(config, recipe_folder, None)
    result = linter.lint(recipes)
    messages = linter.get_messages()

    if messages:
        print("The following problems have been found:\n")
        print(linter.get_report())

    if not result:
        print("All checks OK")
    else:
        sys.exit("Errors were found")