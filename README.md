# Anaconda Linter

This package is currently a very rough draft of a pure Python linter specifically to make sure
that packages' meta.yaml files adhere to certain Anaconda standards.

## Installation
1. conda env create -f environment.yml
2. conda activate conda-lint
3. `python setup.py install`

## Usage

The usage is similar to conda-build.

1. navigate into the folder of your main `conda_build_config.yaml` file:
`cd <path/to/aggregate/>`

2. run `conda-lint`
`conda-lint <path_to_feedstock>`

Concrete example:
`cd ~/work/recipes/aggregate/`
`conda-lint -v ../wip/airflow-feedstock`

## Testing conda lint

`conda-lint ../tests/bad-feedstock` - some tests fail

`conda-lint ../tests/good-feedstock` - all tests pass

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
