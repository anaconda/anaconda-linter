# from pathlib import Path

from setuptools import setup

import conda_lint


def main():
    run_lint = dict(
        name=conda_lint.__name__,
        version=conda_lint.__version__,
        author=conda_lint.__author__,
        author_email=conda_lint.__email__,
        license=conda_lint.__license__,
        description=conda_lint.__summary__,
        long_description=conda_lint.__long_description__,
        url=conda_lint.__url__,
        python_requires=">=3.8",
        packages=["conda_lint", "conda_lint.cli", "conda_lint.lint"],
        package_dir={"conda_lint": "conda_lint"},
        package_data={"conda_lint": ["data/*.txt"]},
        entry_points={
            "console_scripts": [
                "conda-lint = conda_lint.cli.cli:main",
            ]
        },
        install_requires=["ruamel.yaml>=0.16.1", "license-expression", "jinja2>=3.0.3"],
    )
    setup(**run_lint)


if __name__ == "__main__":
    main()
