"""
File:           test_url.py
Description:    Tests URL-based rules
"""

from __future__ import annotations

import pytest
from conftest import check


def test_invalid_url_good(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
        """
    )
    lint_check = "invalid_url"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_invalid_url_good_sequence(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url:
           - https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
           - https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
        """
    )
    lint_check = "invalid_url"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_invalid_url_bad(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://sqlit.com/2022/sqlite-autoconf-3380500.tar.gz
        """
    )
    lint_check = "invalid_url"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1


def test_invalid_url_good_redirect(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/p/pydot/pydot-1.4.1.tar.gz
        """
    )
    lint_check = "invalid_url"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize(
    "url_field",
    (
        "home",
        "doc_url",
        "doc_source_url",
        "license_url",
        "dev_url",
    ),
)
def test_invalid_url_about_good(base_yaml: str, url_field: str) -> None:
    lint_check = "invalid_url"
    yaml_str = (
        base_yaml
        + f"""
        about:
          {url_field}: https://sqlite.org/
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize(
    "url_field",
    (
        "home",
        "doc_url",
        "doc_source_url",
        "license_url",
        "dev_url",
    ),
)
def test_invalid_url_about_bad(base_yaml: str, url_field: str) -> None:
    lint_check = "invalid_url"
    yaml_str = (
        base_yaml
        + f"""
        about:
          {url_field}: https://sqlit.org/
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1


def test_http_url_source_good(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
        """
    )
    lint_check = "http_url"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_http_url_source_bad(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: http://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
        """
    )
    lint_check = "http_url"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "is not https" in messages[0].title


def test_http_url_source_good_sequence(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url:
          - https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
          - https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
        """
    )
    lint_check = "http_url"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize(
    "url_field",
    (
        "home",
        "doc_url",
        "doc_source_url",
        "license_url",
        "dev_url",
    ),
)
def test_http_url_about_good(base_yaml: str, url_field: str) -> None:
    lint_check = "http_url"
    yaml_str = (
        base_yaml
        + f"""
        about:
          {url_field}: https://sqlite.org/
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize(
    "url_field",
    (
        "home",
        "doc_url",
        "doc_source_url",
        "license_url",
        "dev_url",
    ),
)
def test_http_url_about_bad(base_yaml: str, url_field: str) -> None:
    lint_check = "http_url"
    yaml_str = (
        base_yaml
        + f"""
        about:
          {url_field}: http://sqlite.org/
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "is not https" in messages[0].title
