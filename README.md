# Anaconda Linter

This package is currently a very rough draft of a pure Python linter specifically to make sure
that packages' meta.yaml files adhere to certain Anaconda standards.

## Installation
1. `conda env create -f environment.yaml`
2. `conda activate anaconda-linter`
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

## Skipping Lints

In order to force the linter to ignore a certain type of lint, you can use the top-level `extra` key in a `meta.yaml file`. To skip lints invidually, add lints from this [list of current lints](anaconda_linter/lint_names.md) to the `extra` key as a list with a `skip-lints` key. For example:

    extra:
      skip-lints:
        - unknown_selector
        - invalid_url

You can also do the opposite of this, and skip all other lints *except* the lints you want, with `only-lint`. For example:

    extra:
      only-lint:
        - missing_license
        - incorrect_license

Note: if you have both `skip-lints` and `only-lint`, any lints in `skip-lint` will override identical lints in `only-lint`.

## Testing the Anaconda Linter

`conda-lint ../tests/bad-feedstock` - some tests fail

`conda-lint ../tests/good-feedstock` - all tests pass

## TODO:
- Create a Makefile to auto-create a conda env and download dependencies
- Set up CI.
- Increase number of errors in bad-feedstock so that all lints are covered
- Add further lints
- Remove unneeded codes
- Test with Prefect Flow
- Set up Sphinx Docs

## Contributions
This new package is inspired by bioconda's [linter](https://github.com/bioconda/bioconda-utils/blob/master/bioconda_utils/lint/__init__.py).

Some of the code for suggesting hints comes from [Peter Norvig](http://norvig.com/spell-correct.html).

This README will continue to be fleshed out as time goes on.
