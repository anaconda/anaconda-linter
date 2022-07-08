# Conda Lint

This package is currently a very rough draft of a linter specifically to make sure
that packages' meta.yaml files adhere to SPDX standards. In the future, I hope
that this can grow into being able to lint more files in accordance with Anaconda standards.

## Installation
Navigate to the same directory as this readme and run `python3 setup.py install`.

## Usage
`conda lint -f path/to/your/file/meta.yml`

`conda lint -p path/to/your/package`

## Contributions
This package is heavily inspired by conda-forge's conda-smithy [linter](https://github.com/conda-forge/conda-smithy/blob/5deae3b50c88eaf16a1514288b4dba8fe02dbf72/conda_smithy/lint_recipe.py).

Some of the code for suggesting hints comes from [Peter Norvig](http://norvig.com/spell-correct.html).

This README will continue to be fleshed out as time goes on.

