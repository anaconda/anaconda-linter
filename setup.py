from setuptools import setup

import anaconda_linter


def main():
    run_lint = dict(
        name=anaconda_linter.__name__,
        version=anaconda_linter.__version__,
        author=anaconda_linter.__author__,
        author_email=anaconda_linter.__email__,
        license=anaconda_linter.__license__,
        description=anaconda_linter.__summary__,
        long_description=anaconda_linter.__long_description__,
        url=anaconda_linter.__url__,
        python_requires=">=3.8",
        packages=["anaconda_linter", "anaconda_linter.cli", "anaconda_linter.lint"],
        package_dir={"anaconda_linter": "anaconda_linter"},
        package_data={"anaconda_linter": ["data/*.txt"]},
        entry_points={
            "console_scripts": [
                "conda-lint = anaconda_linter.cli.cli:main",
            ]
        },
        install_requires=["ruamel.yaml>=0.16.1", "license-expression", "jinja2>=3.0.3"],
    )
    setup(**run_lint)


if __name__ == "__main__":
    main()
