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
