# Conda Lint

This package is currently a very rough draft of a pure Python linter specifically to make sure
that packages' meta.yaml files adhere to SPDX standards. In the future, I hope
that this can grow into being able to lint more files in accordance with Anaconda standards.

## Installation
1. Create a conda environment or Python venv.
2. Navigate to the same directory as this readme and run `python3 setup.py install`.

## Usage
`conda lint -f path/to/your/file/meta.yml`

`conda lint -p path/to/your/package`

## TODO:
- Auto-make a conda env and download dependencies
- ~Add finding of meta.yaml files in packages~
- Add linting tests
- ~Refactor argparsing~ (Probably need to re-refactor this though)
- Turn main utils.py functions into a class
- Get the lint command to be recognized by conda again (this broke for some reason)
- Turn this into a real linter (with rows and cols, not just loading yaml)
- Test with Prefect Flow

## Contributions
This package is heavily inspired by conda-forge's conda-smithy [linter](https://github.com/conda-forge/conda-smithy/blob/5deae3b50c88eaf16a1514288b4dba8fe02dbf72/conda_smithy/lint_recipe.py).

Some of the code for suggesting hints comes from [Peter Norvig](http://norvig.com/spell-correct.html).

This README will continue to be fleshed out as time goes on.

