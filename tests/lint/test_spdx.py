"""
File:           test_spdx.py
Description:    Tests licensing rules using the SPDX database
"""

from __future__ import annotations

from conftest import check


def test_spdx_good(linter, base_yaml: str) -> None:  # pylint: disable=unused-argument
    yaml_str = (
        base_yaml
        + """
        about:
          license: BSD-3-Clause
        """
    )
    lint_check = "incorrect_license"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_spdx_bad(linter, base_yaml: str) -> None:  # pylint: disable=unused-argument
    yaml_str = (
        base_yaml
        + """
        about:
          license: AARP-50+
        """
    )
    lint_check = "incorrect_license"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "closest match" not in messages[0].title


def test_spdx_close(linter, base_yaml: str) -> None:  # pylint: disable=unused-argument
    yaml_str = (
        base_yaml
        + """
        about:
          license: BSE-3-Clause
        """
    )
    lint_check = "incorrect_license"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "closest match: BSD-3-Clause" in messages[0].title
