#!/bin/bash
if [[ (! -d "/workspace/anaconda-linter") || "$OSTYPE" != "linux-gnu"* ]]
then
    echo "This script is intended to be run on a gitpod."
    echo "Try visiting gitpod.io/#https://github.com/anaconda-distribution/anaconda-linter/"
else
    if [ ! -d "/workspace/anaconda-linter/test_feedstocks" ]
    then
        git clone https://github.com/AnacondaRecipes/airflow-feedstock.git test_feedstocks/airflow
        git clone https://github.com/AnacondaRecipes/anaconda-linter-feedstock.git test_feedstocks/anaconda-linter
        git clone https://github.com/AnacondaRecipes/libtiff-feedstock.git test_feedstocks/libtiff
        git clone https://github.com/AnacondaRecipes/rust-feedstock.git test_feedstocks/rust
    fi

    for d in test_feedstocks/*/ ; do
        echo "Linting $d"
        conda-lint "$d"
        echo -e "\n"
    done

fi
