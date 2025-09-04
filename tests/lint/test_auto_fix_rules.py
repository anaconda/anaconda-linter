"""
File:           test_auto_fix_rules.py
Description:    Tests the `fix()` function on linter rules, that allows us to "auto-fix" linter rules.

                All of these tests are maintained in this file to significantly reduce test-code-duplication.

                This feature can be easily tested with a utility function that looks for the names of two files:
                  - An input test file that triggers the target linting rule
                  - An output test file that matches an expected, automatically corrected, resulting file
"""

from __future__ import annotations

import pytest
from conftest import assert_on_auto_fix


# Format: (Check Name, File Suffix, Architecture, Number of Occurrences)
# Common file suffixes:
#   - `mo` -> For multi-output test cases
@pytest.mark.parametrize(
    "check,suffix,arch,occurrences",
    [
        ("license_file_overspecified", "", "linux-64", 1),
        ("license_file_overspecified", "", "win-64", 1),
        ("no_git_on_windows", "", "win-64", 1),
        ("patch_unnecessary", "", "linux-64", 1),
        ("avoid_noarch", "", "linux-64", 2),
        ("pip_install_args", "", "linux-64", 3),
    ],
)
def test_auto_fix_rule(check: str, suffix: str, arch: str, occurrences: int):
    """
    Tests auto-fixable rules by passing in a file with the issue and checking the output with an expected file.
    Files must be stored in the `test_aux_files/auto_fix/` directory, following our naming conventions.
    :param check: Name of the linter check
    :param suffix: File suffix, allowing developers to create multiple test files against a linter check.
    :param arch: Architecture to run the test against.
    """

    assert_on_auto_fix(check, suffix, arch, occurrences)
