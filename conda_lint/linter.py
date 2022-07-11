import os
from pathlib import Path
import re

import license_expression
from ruamel.yaml import YAML
yaml = YAML(typ="safe", pure=True)

from conda_lint.utils import *
# what's being passed in here?
# list of things to lint / check existence
# originator
    # about: home or about: dev_url 
# license
    # check index.json['license'] and/or meta.yaml['about']['license']
    # check for non-spdx licenses
# copyright text




"""
about:
  home: https://www.python.org/
  license: PSF-2.0
  license_family: PSF
  license_file: LICENSE
  summary: General purpose programming language
  description: |
    Python is a widely used high-level, general-purpose, interpreted, dynamic
    programming language. Its design philosophy emphasizes code
    readability, and its syntax allows programmers to express concepts in
    fewer lines of code than would be possible in languages such as C++ or
    Java. The language provides constructs intended to enable clear programs
    on both a small and large scale.
  doc_url: https://www.python.org/doc/versions/
  doc_source_url: https://github.com/python/pythondotorg/blob/master/docs/source/index.rst
  dev_url: https://docs.python.org/devguide/

"""

# testing: python3 -m conda_lint.cli.cli lint -f ~/anaconda-distribution/conda-lint/conda_lint/tests/absl-py-0.1.10-py36_0/info/recipe/meta.yaml

#TODO: Do better license checking than just say "read it yourself"
def lint_bom(metafile):
    hints = []
    with open(metafile, "r") as f:
        meta = yaml.load(f)

    about_section = meta.get("about")
    license = about_section.get("license", "")
    print(f"Checking if '{license}' is valid")
    licensing = license_expression.Licensing()
    parsed_exceptions = []
    try:
        parsed_licenses = []
        parsed_licenses_with_exception = licensing.license_symbols(
            license.strip(), decompose=False
        )
        for l in parsed_licenses_with_exception:
            if isinstance(l, license_expression.LicenseWithExceptionSymbol):
                parsed_licenses.append(l.license_symbol.key)
                parsed_exceptions.append(l.exception_symbol.key)
            else:
                parsed_licenses.append(l.key)
    except license_expression.ExpressionError:
        parsed_licenses = [license]

    licenseref_regex = re.compile(r"^LicenseRef[a-zA-Z0-9\-.]*$")
    filtered_licenses = []
    for license in parsed_licenses:
        if not licenseref_regex.match(license):
            filtered_licenses.append(license)

    with open(
        os.path.join(os.path.dirname(__file__), Path("data", "licenses.txt")), "r"
    ) as f:
        expected_licenses = f.readlines()
        expected_licenses = set([l.strip() for l in expected_licenses])
    with open(
        os.path.join(os.path.dirname(__file__), Path("data", "license_exceptions.txt")), "r"
    ) as f:
        expected_exceptions = f.readlines()
        expected_exceptions = set([l.strip() for l in expected_exceptions])
    non_spdx_licenses = set(filtered_licenses) - expected_licenses
    if non_spdx_licenses:
        hints.append(
            "License is not an SPDX identifier (or a custom LicenseRef) nor an SPDX license expression.\n\n"
            "Documentation on acceptable licenses can be found "
            "[here]( https://conda-forge.org/docs/maintainer/adding_pkgs.html#spdx-identifiers-and-expressions )."
        )
        for license in non_spdx_licenses:
            closest = find_closest_match(license)
            if closest:
                hints.append(f"Original license name: {license}. Closest SPDX identifier found: {closest}")
            else:
                continue    
    non_spdx_exceptions = set(parsed_exceptions) - expected_exceptions
    if non_spdx_exceptions:
        hints.append(
            "License exception is not an SPDX exception.\n\n"
            "Documentation on acceptable licenses can be found "
            "[here]( https://conda-forge.org/docs/maintainer/adding_pkgs.html#spdx-identifiers-and-expressions )."
        )
    
    return hints