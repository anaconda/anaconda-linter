.PHONY: clean clean-build clean-pyc clean-test coverage dist docs help install lint lint/flake8 lint/black
.DEFAULT_GOAL := help

SHELL := /bin/bash -o pipefail -o errexit

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

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

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

coverage: ## check code coverage quickly with the default Python
	coverage run --source anaconda_linter -m pytest
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

environment:       ## Handles environment creation
	conda env create -f environment.yaml --name $(CONDA_ENV_NAME) --force
	conda run --name $(CONDA_ENV_NAME) pip install -e .

pre-commit:        ## Runs pre-commit against files
	pre-commit run --all-files

test:              ## Run tests
	mkdir -p $(ARTIFACTS_PATH)
	python -m pytest \
		--junit-xml="$(ARTIFACTS_PATH)/test-report.xml" \
		--html="$(ARTIFACTS_PATH)/test-report.html" \
		--cov \
		--cov-report html --cov-report html:$(ARTIFACTS_PATH)/cov_html \
		--cov-report xml --cov-report xml:$(ARTIFACTS_PATH)/cobertura.xml \
		--show-capture=all -vv ./tests

release: dist ## package and upload a release
	twine upload dist/*

dist: clean ## builds source and wheel package
	python -m build
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	pip install .

dev: clean  ## install the package's development version
	pip install -e .
