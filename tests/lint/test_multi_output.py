"""
File:           test_multi_output.py
Description:    Tests multi-output-based rules
"""

from __future__ import annotations

import pytest
from conftest import assert_lint_messages, assert_no_lint_message, check


def test_output_missing_name_good(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
          - name: output2
        """
    )
    lint_check = "output_missing_name"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_output_missing_name_bad(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        outputs:
          - requirements:
              host:
                - python
          - requirements:
              host:
                - python
        """
    )
    lint_check = "output_missing_name"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("has no name" in msg.title for msg in messages)


@pytest.mark.parametrize(
    "file,",
    [
        "outputs_not_unique/outputs_unique.yaml",
    ],
)
def test_outputs_not_unique_outputs_unique(file: str) -> None:
    assert_no_lint_message(recipe_file=file, lint_check="outputs_not_unique")


@pytest.mark.parametrize(
    "file,msg_count",
    [
        ("outputs_not_unique/outputs_not_unique.yaml", 2),
        ("outputs_not_unique/outputs_not_unique_package_name.yaml", 1),
    ],
)
def test_outputs_not_unique_outputs_not_unique(file: str, msg_count: str) -> None:
    assert_lint_messages(
        recipe_file=file, lint_check="outputs_not_unique", msg_title="Output name is not unique", msg_count=msg_count
    )


def test_no_global_test_good(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            test:
              import:
                module1
          - name: output2
            test:
              import:
                module2
        """
    )
    lint_check = "no_global_test"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_no_global_test_bad(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
          - name: output2
        test:
          imports:
            - module
        """
    )
    lint_check = "no_global_test"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "Global tests" in messages[0].title


def test_output_missing_script_good(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            script: build_output1.sh
          - name: output2
            script: build_output2.sh
        """
    )
    lint_check = "output_missing_script"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_output_missing_script_subpackage(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            script: build_output1.sh
            requirements:
              run:
                - python
          - name: output2
            requirements:
              run:
                - python
                - {{ pin_subpackage('output1') }}
        """
    )
    lint_check = "output_missing_script"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_output_missing_script_bad(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
          - name: output2
        """
    )
    lint_check = "output_missing_script"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("Output is missing script" in msg.title for msg in messages)


def test_output_script_name_default_good(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            script: build_output1.sh
          - name: output2
            script: build_output2.sh
        """
    )
    lint_check = "output_script_name_default"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("script", ("build.sh", "bld.bat"))
def test_output_script_name_default_bad(base_yaml: str, script: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        outputs:
          - name: output1
            script: {script}
          - name: output2
            script: {script}
        """
    )
    lint_check = "output_script_name_default"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("default script names" in msg.title for msg in messages)
