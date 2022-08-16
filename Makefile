SHELL := /bin/bash -o pipefail -o errexit

CONDA_ENV_NAME ?= anaconda-linter

# Folder for all the build artefacts to be archived by CI.
ARTIFACTS_PATH ?= artifacts

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

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
