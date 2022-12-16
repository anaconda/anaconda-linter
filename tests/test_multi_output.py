import pytest
from conftest import check


def test_output_missing_name_good(base_yaml):
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


def test_output_missing_name_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - requirements
          - requirements
        """
    )
    lint_check = "output_missing_name"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("has no name" in msg.title for msg in messages)


def test_outputs_not_unique_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
          - name: output2
        """
    )
    lint_check = "outputs_not_unique"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_outputs_not_unique_bad_package_name(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
          - name: test_package
        """
    )
    lint_check = "outputs_not_unique"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "not unique" in messages[0].title


def test_output_message(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
          - name: output2
          - name: output2
        """
    )
    lint_check = "outputs_not_unique"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and messages[0].title.startswith('output "output2": ')


def test_outputs_not_unique_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
          - name: output2
          - name: output2
        """
    )
    lint_check = "outputs_not_unique"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "not unique" in messages[0].title


def test_no_global_test_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - output1:
            test:
              import:
                module1
          - output2:
            test:
              import:
                module2
        """
    )
    lint_check = "no_global_test"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_no_global_test_bad(base_yaml):
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


def test_output_missing_script_good(base_yaml):
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


def test_output_missing_script_subpackage(base_yaml):
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


def test_output_missing_script_bad(base_yaml):
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


def test_output_script_name_default_good(base_yaml):
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
def test_output_script_name_default_bad(base_yaml, script):
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
