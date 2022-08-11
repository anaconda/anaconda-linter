import utils, lint, sys, os
from typing import List

packages="*"
cache=None
list_checks=False
exclude=None
push_status=False
user='bioconda'
commit=None
push_comment=False
pull_request=None
git_range=None
full_report=False
try_fix=False

def get_recipes(config, recipe_folder, packages, git_range) -> List[str]:
    """Gets list of paths to recipe folders to be built

    Considers all recipes matching globs in packages, constrains to
    recipes modified or unblacklisted in the git_range if given, then
    removes blacklisted recipes.

    """
    recipes = list(utils.get_recipes(recipe_folder, packages))
    print("Considering total of %s recipes%s.",
                len(recipes), utils.ellipsize_recipes(recipes, recipe_folder))

    if git_range:
        changed_recipes = get_recipes_to_build(git_range, recipe_folder)
        print("Constraining to %s git modified recipes%s.", len(changed_recipes),
                    utils.ellipsize_recipes(changed_recipes, recipe_folder))
        recipes = [recipe for recipe in recipes if recipe in set(changed_recipes)]
        if len(recipes) != len(changed_recipes):
            logger.info("Overlap was %s recipes%s.", len(recipes),
                        utils.ellipsize_recipes(recipes, recipe_folder))

    blacklist = utils.get_blacklist(config, recipe_folder)
    blacklisted = []
    for recipe in recipes:
        if os.path.relpath(recipe, recipe_folder) in blacklist:
            blacklisted.append(recipe)
    if blacklisted:
        print("Ignoring %s blacklisted recipes%s.", len(blacklisted),
                    utils.ellipsize_recipes(blacklisted, recipe_folder))
        recipes = [recipe for recipe in recipes if recipe not in set(blacklisted)]
    print("Processing %s recipes%s.", len(recipes),
                utils.ellipsize_recipes(recipes, recipe_folder))
    return recipes

if __name__ == "__main__":
    config = utils.load_config("./config.yaml")

    if cache is not None:
        utils.RepoData().set_cache(cache)

    recipe_folder = f"{sys.argv[1]}/{sys.argv[2]}-feedstock/recipe/"
    recipes = get_recipes(config, recipe_folder, packages, git_range)
    linter = lint.Linter(config, recipe_folder, exclude)
    result = linter.lint(recipes, fix=try_fix)
    messages = linter.get_messages()
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