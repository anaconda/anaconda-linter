# Anaconda Linter

## Table of Contents
<!-- TOC -->

- [Anaconda Linter](#anaconda-linter)
    - [Table of Contents](#table-of-contents)
    - [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
    - [Skipping Lints](#skipping-lints)
    - [Testing the Anaconda Linter](#testing-the-anaconda-linter)
- [Contributing](#contributing)
    - [Development setup](#development-setup)
    - [Release process](#release-process)
    - [Contributions](#contributions)
- [License](#license)

<!-- /TOC -->

## Overview
Anaconda Linter is a utility to validate that a recipe for a conda package
will render correctly.

The package is currently a very rough draft of a pure Python linter specifically to make sure
that packages' meta.yaml files adhere to certain Anaconda standards.


# Installation
```sh
$ make environment
$ conda activate anaconda-linter
```

# Usage

```sh
usage: conda-lint [-h] [-V] [-m VARIANT_CONFIG_FILES] [-e EXCLUSIVE_CONFIG_FILES] [-s SUBDIRS] [--severity {INFO,WARNING,ERROR}] [-v] [-f] RECIPE_PATH

positional arguments:
  RECIPE_PATH           Path to recipe directory.

options:
  -h, --help            show this help message and exit
  -V, --version         The version of anaconda-linter
  -m VARIANT_CONFIG_FILES, --variant-config-files VARIANT_CONFIG_FILES
                        Additional variant config files to add. These yaml files can contain keys such as `c_compiler` and `target_platform` to form a
                        build matrix.
  -e EXCLUSIVE_CONFIG_FILES, --exclusive-config-files EXCLUSIVE_CONFIG_FILES, --exclusive-config-file EXCLUSIVE_CONFIG_FILES
                        Exclusive variant config files to add. Providing files here disables searching in your home directory and in cwd. The files
                        specified here come at the start of the order, as opposed to the end with --variant-config-files. Any config files in recipes and
                        any config files specified with --variant-config-files will override values from these files.
  -s SUBDIRS, --subdirs SUBDIRS
                        List subdir to lint. Example: linux-64, win-64...
  --severity {INFO,WARNING,ERROR}
                        The minimum severity level displayed in the output.
  -v, --verbose         Enable verbose output. This displays all of the checks that the linter is running.
  -f, --fix             Attempt to fix issues.
```

The usage is similar to conda-build.

1. navigate into the folder of your main `conda_build_config.yaml` file:
`cd <path/to/aggregate/>`

2. run `conda-lint` with:  `conda-lint <path_to_feedstock>`

Concrete example:
`cd ~/work/recipes/aggregate/`
`conda-lint -v ../wip/airflow-feedstock`

Full usage details can be found under the help menu (`conda-lint -h`). New users may find it easier to run the script with the verbose flag, `-v` which will provide additional context for linting errors.

## Skipping Lints

In order to force the linter to ignore a certain type of lint, you can use the top-level `extra` key in a `meta.yaml file`. To skip lints individually, add lints from this [list of current lints](anaconda_linter/lint_names.md) to the `extra` key as a list with a `skip-lints` key. For example:

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

Make sure that your `anaconda-linter` environment is activated, then:

`pytest tests` OR `make test` (if you would like to see test reports)

It's that easy!

# Contributing

We welcome contributions for bug fixes, enhancements, or new tests.
For a list of projects, please see the [Issues page](https://github.com/anaconda-distribution/anaconda-linter/issues)

Before submitting a PR, please make sure to:

  * run `make pre-commit` to format your code using `flake8` and `black`.
  * run `make test` to make sure our unit tests pass.
  * add unit tests for new functionality. To print a coverage report, run `make coverage`.

If you would like to develop in a hosted linux environment, a [gitpod instance](https://gitpod.io/#https://github.com/anaconda-distribution/anaconda-linter/tree/gitpod-poc) is available to test linter changes with real life packages, without having to download them to your own machine.

## Development setup
To get started as a developer:
```sh
$ make dev
$ conda activate anaconda-linter
```
This will automatically configure `pre-commit` for the `anaconda-linter` environment. Our automated tooling will run
when you make a commit in this environment. Running `make dev` will also blow away any existing environments for a
clean install, every time.

Running `make help` will show all of the available commands. Here are some that may be immediately useful:
1. `make test`: Runs all the unit tests
1. `make test-cov`: Reports the current test coverage percentage and indicates
   which lines are currently untested.
1. `make lint`: Runs our `pylint` configuration, based on Google's Python
   standards.
1. `make format`: Automatically formats code
1. `make analyze`: Runs the static analyzer, `mypy`.
1. `make pre-commit`: Runs all the `pre-commit` checks

## Release process
Here is a rough outline of how to conduct a release of this project:
1. Update `CHANGELOG.md`
1. Update the version number in `anaconda_linter/__init__.py`
1. Ensure `environment.yaml` aligns with `recipe/meta.yaml` found in the feedstock
1. Create a new release on GitHub with a version tag.
1. The Anaconda packaging team will need to update
[the feedstock](https://github.com/AnacondaRecipes/anaconda-linter-feedstock)
and [aggregate](https://github.com/AnacondaRecipes/aggregate) and publish to `distro-tooling`

## Contributions
This package is inspired by bioconda's [linter](https://github.com/bioconda/bioconda-utils/blob/master/bioconda_utils/lint/__init__.py).

Some of the code for suggesting hints comes from [Peter Norvig](http://norvig.com/spell-correct.html).

# License
[BSD-3-Clause](https://choosealicense.com/licenses/bsd-3-clause/)
