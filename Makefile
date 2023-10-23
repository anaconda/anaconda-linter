# The `.ONESHELL` and setting `SHELL` allows us to run commands that require
# `conda activate`
.ONESHELL:
SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -o errexit
CONDA_ACTIVATE = source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate
# Resolve the path to `python3` and store it in a variable. Always invoke `python` using this variable. This prevents a
# nasty scenario where the GitHub Actions container fails to find `python` or `python3`, when running `make` commands.
PYTHON3 := $(shell which python3) #$(shell type python3 | awk '{ print $3 }')

.PHONY: clean clean-cov clean-build clean-env clean-pyc clean-test dist docs help install environment release dev test test-debug test-cov pre-commit lint format analyze
.DEFAULT_GOAL := help

CONDA_ENV_NAME ?= anaconda-linter

# Folder for all the build artifacts to be archived by CI.
ARTIFACTS_PATH ?= artifacts

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

# For now, most tools only run on new files, not the entire project.
LINTER_FILES := tests/*.py
# Tracks all python files. This will eventually be used by the auto formatter, linter, and static analyzer.
ALL_PY_FILES := anaconda_linter/**/*.py scripts/*.py tests/*.py

clean: clean-cov clean-build clean-env clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-cov:
	@rm -rf .coverage
	@rm -rf htmlcov
	@rm -rf reports/{*.html,*.png,*.js,*.css,*.json}
	@rm -rf pytest.xml
	@rm -rf pytest-coverage.txt

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-env:					## remove conda environment
	conda remove -y -n $(CONDA_ENV_NAME) --all

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr artifacts/
	rm -fr .pytest_cache

help:
	$(PYTHON3) -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

install: clean ## install the package to the active Python's site-packages
	pip install .

environment:       ## Handles environment creation
	conda env create -f environment.yaml --name $(CONDA_ENV_NAME) --force
	conda run --name $(CONDA_ENV_NAME) pip install -e .

release: dist ## package and upload a release
	twine upload dist/*

dist: clean ## builds source and wheel package
	python -m build
	ls -l dist

dev: clean  ## install the package's development version
	conda env create -f environment.yaml --name $(CONDA_ENV_NAME) --force
	conda run --name $(CONDA_ENV_NAME) pip install -e .
	$(CONDA_ACTIVATE) percy && pre-commit install

pre-commit:     ## runs pre-commit against files. NOTE: older files are disabled in the pre-commit config.
	pre-commit run --all-files

test:			## runs test cases
	$(PYTHON3) -m pytest -n auto --capture=no tests/

test-debug:		## runs test cases with debugging info enabled
	$(PYTHON3) -m pytest -n auto -vv --capture=no tests/

test-cov:		## checks test coverage requirements
	$(PYTHON3) -m pytest -n auto --cov-config=.coveragerc --cov=anaconda_linter tests/ --cov-fail-under=80 \
		--cov-report term-missing

lint:			## runs the linter against the project
	pylint --rcfile=.pylintrc $(LINTER_FILES)

format:			## runs the code auto-formatter
	isort --profile black --line-length=120 $(ALL_PY_FILES)
	black --line-length=120 $(ALL_PY_FILES)

analyze:		## runs static analyzer on the project
	mypy --config-file=.mypy.ini $(LINTER_FILES)
