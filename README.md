# Conda Lint

This package is currently a very rough draft of a pure Python linter specifically to make sure
that packages' meta.yaml files adhere to certain Anaconda standards.

## Installation
1. conda create --name lint_test --file ./req.txt -c conda-forge -c bioconda
2. *Currently*: Navigate to the anaconda_linter directory and run `python run.py base/directory/of/file feedstock_name`.

## Usage
TBD

## Testing conda lint

`python run.py ../tests bad` - some tests fail
`python run.py ../tests good` - all tests pass

## TODO:
- Create a Makefile to auto-create a conda env and download dependencies
- Set up CI.
- Increase number of errors in bad-feedstock so that all lints are covered
- Add further lints
- Remove unneeded codes
- Test with Prefect Flow

## Contributions
This package is heavily inspired by conda-forge's conda-smithy [linter](https://github.com/conda-forge/conda-smithy/blob/5deae3b50c88eaf16a1514288b4dba8fe02dbf72/conda_smithy/lint_recipe.py).

This new package is more inspired by bioconda's [linter](https://github.com/bioconda/bioconda-utils/blob/master/bioconda_utils/lint/__init__.py).

Some of the code for suggesting hints comes from [Peter Norvig](http://norvig.com/spell-correct.html).

This README will continue to be fleshed out as time goes on.

