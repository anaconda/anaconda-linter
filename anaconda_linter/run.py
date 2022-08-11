import os
import sys

import lint
import utils

# from typing import List


if __name__ == "__main__":
    config_file = os.path.abspath(os.path.dirname(__file__) + "/config.yaml")
    config = utils.load_config(config_file)

    aggregate_folder = f"{sys.argv[1]}"
    recipes = [f"{aggregate_folder}/{sys.argv[2]}-feedstock/recipe/"]
    linter = lint.Linter(config, aggregate_folder, None, True)
    result = linter.lint(recipes, "linux-64")
    messages = linter.get_messages()

    if messages:
        print("The following problems have been found:\n")
        print(linter.get_report())

    if not result:
        print("All checks OK")
    elif result == lint.WARNING:
        print("Warnings were found")
    else:
        sys.exit("Errors were found")
