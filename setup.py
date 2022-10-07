from setuptools import setup

import anaconda_linter


def main():
    with open("README.md", mode="r", encoding="utf-8") as f:
        readme: str = f.read()

    run_lint = dict(
        name=anaconda_linter.__name__,
        version=anaconda_linter.__version__,
        author=anaconda_linter.__author__,
        author_email=anaconda_linter.__email__,
        license=anaconda_linter.__license__,
        description=anaconda_linter.__summary__,
        long_description=readme,
        long_description_content_type="text/markdown",
        url=anaconda_linter.__url__,
        python_requires=">=3.8",
        packages=["anaconda_linter", "anaconda_linter.lint"],
        package_dir={"anaconda_linter": "anaconda_linter"},
        package_data={
            "anaconda_linter": ["data/*.txt", "data/*.yaml", "config*.yaml", "build-fail-blocklist"]
        },
        include_package_data=True,
        entry_points={
            "console_scripts": [
                "conda-lint = anaconda_linter.run:main",
            ]
        },
        install_requires=[
            "conda-build",
            "jinja2>=3.0.3",
            "jsonschema",
            "license-expression",
            "networkx",
            "requests",
            "ruamel.yaml>=0.16.1",
            "tqdm",
        ],
        tests_require=["pytest", "pytest-cov", "pytest-html"],
        classifiers=[
            "Development Status :: 2 - Pre-Alpha",
            "Environment :: Console",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: BSD License",
            "Natural Language :: English",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3 :: Only",
            "Programming Language :: Python :: Implementation :: CPython",
            "Topic :: Software Development :: Quality Assurance",
            "Topic :: Software Development :: Libraries",
            "Topic :: Utilities",
        ],
    )
    setup(**run_lint)


if __name__ == "__main__":
    main()
