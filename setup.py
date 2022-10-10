"""The setup script."""

from setuptools import find_packages, setup

import anaconda_linter


def main():
    with open("CHANGELOG.md", encoding="utf-8") as changelog_file:
        changelog: str = changelog_file.read()

    with open("README.md", encoding="utf-8") as readme_file:
        readme: str = readme_file.read()

    requirements = [
        "conda-build",
        "jinja2>=3.0.3",
        "jsonschema",
        "license-expression",
        "networkx",
        "pyyaml",
        "requests",
        "ruamel.yaml>=0.16.1",
        "tqdm",
    ]
    test_requirements = ["pytest>=3", "pytest-cov", "pytest-html"]

    run_lint = dict(
        author_email=anaconda_linter.__email__,
        author=anaconda_linter.__author__,
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
        description=anaconda_linter.__summary__,
        entry_points={
            "console_scripts": [
                "conda-lint=anaconda_linter.run:main",
            ]
        },
        install_requires=requirements,
        keywords="anaconda_linter",
        license=anaconda_linter.__license__,
        long_description_content_type="text/markdown",
        long_description=readme + "\n\n" + changelog,
        name=anaconda_linter.__name__,
        package_data={
            "anaconda_linter": ["data/*.txt", "data/*.yaml", "config*.yaml", "build-fail-blocklist"]
        },
        package_dir={"anaconda_linter": "anaconda_linter"},
        packages=find_packages(include=["anaconda_linter", "anaconda_linter.*"]),
        python_requires=">=3.8",
        test_suite="tests",
        tests_require=test_requirements,
        url=anaconda_linter.__url__,
        version=anaconda_linter.__version__,
        zip_safe=False,
    )
    setup(**run_lint)


if __name__ == "__main__":
    main()
