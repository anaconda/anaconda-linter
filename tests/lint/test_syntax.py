"""
File:           test_syntax.py
Description:    Tests syntax-based rules
"""
from __future__ import annotations

from conftest import check


def test_version_constraints_missing_whitespace_good(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        requirements:
          host:
            - setuptools >=50
            - pip =22
            - wheel <33.0
            - python !=3.7.6
            - tbb-devel 2021.*,<2021.6
            - jinja2
        """
    )
    lint_check = "version_constraints_missing_whitespace"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_version_constraints_missing_whitespace_bad(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        requirements:
          host:
            - setuptools>=50
        """
    )
    lint_check = "version_constraints_missing_whitespace"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "version constraints" in messages[0].title


def test_version_constraints_missing_whitespace_multi(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            requirements:
              host:
                - setuptools>=50
          - name: output2
            requirements:
              host:
                - setuptools>=50
        """
    )
    lint_check = "version_constraints_missing_whitespace"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("version constraints" in msg.title for msg in messages)
