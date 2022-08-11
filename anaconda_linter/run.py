import utils, lint, sys, os
from typing import List
import pdb


if __name__ == "__main__":
    config = utils.load_config("./config.yaml")

    aggregate_folder = f"{sys.argv[1]}"
    recipe_folder = f"{aggregate_folder}/{sys.argv[2]}-feedstock/recipe/"
    recipes = [recipe_folder]
    linter = lint.Linter(config, aggregate_folder, None, True)
    result = linter.lint(recipes)
    messages = linter.get_messages()
    #pdb.set_trace()
    print(linter.get_report())

    # if messages:
    #     print("The following problems have been found:\n")
    #     print(linter.get_report())

    if not result:
        print("All checks OK")
    else:
        sys.exit("Errors were found")

    
    #recipe = Recipe.from_file(f"{sys.argv[1]}", f"{sys.argv[1]}/{sys.argv[2]}-feedstock/recipe/", False)
    #print(recipe.meta)
    #print(recipe.conda_render())