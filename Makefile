SHELL := /bin/bash -o pipefail -o errexit

CONDA_ENV_NAME ?= conda-lint

# Folder for all the build artefacts to be archived by CI.
ARTIFACTS_PATH ?= artifacts

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

environment:       ## Handles environment creation
	conda env create -f environment.yaml --name $(CONDA_ENV_NAME) --force
	conda run --name $(CONDA_ENV_NAME) pip install -e .