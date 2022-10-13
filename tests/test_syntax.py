import pytest

from conftest import check


def test_version_constraints_missing_whitespace_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        requirements:
          host:
            - setuptools >=50
        """
    )
    lint_check = 'version_constraints_missing_whitespace'
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_version_constraints_missing_whitespace_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        requirements:
          host:
            - setuptools>=50
        """
    )
    lint_check = 'version_constraints_missing_whitespace'
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "version constraints" in messages[0].title
