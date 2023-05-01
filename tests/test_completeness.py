import pytest
from conftest import check, check_dir


def test_missing_section_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        build:
          number: 0
        requirements:
          host:
            - python
        about:
          summary: test package
        """
    )
    lint_check = "missing_section"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_section_good_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        build:
          number: 0
        outputs:
          - name: output1
            requirements:
              host:
                - python
          - name: output2
            requirements:
              host:
                - python
        about:
          summary: test package
        """
    )
    lint_check = "missing_section"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_section_bad(base_yaml):
    lint_check = "missing_section"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 3 and all("section is missing" in msg.title for msg in messages)


def test_missing_section_bad_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
          - name: output2
        """
    )
    lint_check = "missing_section"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 4 and all("section is missing" in msg.title for msg in messages)


def test_missing_build_number_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        build:
          number: 0
        """
    )
    lint_check = "missing_build_number"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_build_number_bad(base_yaml):
    lint_check = "missing_build_number"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1 and "missing a build number" in messages[0].title


def test_missing_home_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
          home: https://www.sqlite.org/
        """
    )
    lint_check = "missing_home"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_home_bad(base_yaml):
    lint_check = "missing_home"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1 and "missing a homepage" in messages[0].title


def test_missing_summary_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
          summary: amazing package
        """
    )
    lint_check = "missing_summary"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_summary_bad(base_yaml):
    lint_check = "missing_summary"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1 and "missing a summary" in messages[0].title


def test_missing_license_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
          license: MIT
        """
    )
    lint_check = "missing_license"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_license_bad(base_yaml):
    lint_check = "missing_license"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1 and "about/license" in messages[0].title


@pytest.mark.parametrize("license_type", ("license_file", "license_url"))
def test_missing_license_file_good(base_yaml, license_type):
    yaml_str = (
        base_yaml
        + f"""
        about:
          {license_type}: LICENSE
        """
    )
    lint_check = "missing_license_file"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_license_file_bad(base_yaml):
    lint_check = "missing_license_file"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1 and "about/license_file" in messages[0].title


@pytest.mark.parametrize("license_type", ("license_file", "license_url"))
def test_license_file_overspecified_good(base_yaml, license_type):
    yaml_str = (
        base_yaml
        + f"""
        about:
          {license_type}: LICENSE
        """
    )
    lint_check = "license_file_overspecified"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_license_file_overspecified_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
          license_file: LICENSE
          license_url: https://url.com/LICENSE
        """
    )
    lint_check = "license_file_overspecified"
    messages = check(lint_check, yaml_str)
    assert (
        len(messages) == 1 and "license_file and license_url is overspecified" in messages[0].title
    )


def test_missing_license_family_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
          license_family: MIT
        """
    )
    lint_check = "missing_license_family"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_license_family_bad(base_yaml):
    lint_check = "missing_license_family"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1 and "about/license_family` key" in messages[0].title


def test_invalid_license_family(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
          license_family: AARP
        """
    )
    lint_check = "invalid_license_family"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "about/license_family` value" in messages[0].title


def test_missing_tests_good_import(base_yaml):
    yaml_str = (
        base_yaml
        + """
        test:
          imports:
            - module
        """
    )
    lint_check = "missing_tests"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_tests_good_command(base_yaml):
    yaml_str = (
        base_yaml
        + """
        test:
          commands:
            - pip check
        """
    )
    lint_check = "missing_tests"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_tests_good_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            test:
              requires:
                - pip
              commands:
                - pip check
          - name: output2
            test:
              imports:
                - module
        """
    )
    lint_check = "missing_tests"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("test_file_name", ["run_test.py", "run_test.sh", "run_test.pl"])
def test_missing_tests_good_scripts(base_yaml, test_file_name, recipe_dir):
    lint_check = "missing_tests"
    test_file = recipe_dir / test_file_name
    test_file.write_text("\n")
    messages = check_dir(lint_check, recipe_dir.parent, base_yaml)
    assert len(messages) == 0


def test_missing_tests_bad_missing(base_yaml):
    yaml_str = (
        base_yaml
        + """
        test:
          requires:
            - pip
        """
    )
    lint_check = "missing_tests"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "No tests were found" in messages[0].title


def test_missing_tests_bad_missing_section(base_yaml):
    lint_check = "missing_tests"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1 and "No tests were found" in messages[0].title


def test_missing_tests_bad_missing_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            test:
              requires:
                - pip
          - name: output2
            test:
              requires:
                - pip
        """
    )
    lint_check = "missing_tests"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("No tests were found" in msg.title for msg in messages)


def test_missing_tests_bad_missing_section_multi(base_yaml):
    lint_check = "missing_tests"
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
          - name: output2
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("No tests were found" in msg.title for msg in messages)


def test_missing_hash_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
          sha256: 5af07de982ba658fd91a03170c945f99c971f6955bc79df3266544373e39869c
        """
    )
    lint_check = "missing_hash"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("exempt_type", ("git_url", "path"))
def test_missing_hash_good_exceptions(base_yaml, exempt_type):
    yaml_str = (
        base_yaml
        + f"""
        source:
          {exempt_type}: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
        """
    )
    lint_check = "missing_hash"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_hash_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
        """
    )
    lint_check = "missing_hash"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "missing a sha256" in messages[0].title


def test_missing_hash_bad_algorithm(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
          md5: 5af07de982ba658fd91a03170c945f99c971f6955bc79df3266544373e39869c
        """
    )
    lint_check = "missing_hash"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "missing a sha256" in messages[0].title


@pytest.mark.parametrize("src_type", ["url", "git_url", "hg_url", "svn_url"])
def test_missing_source_good(base_yaml, src_type):
    lint_check = "missing_source"
    yaml_str = (
        base_yaml
        + f"""
        source:
          {src_type}: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
          sha256: 5af07de982ba658fd91a03170c945f99c971f6955bc79df3266544373e39869c
     """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_source_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          md5: 5af07de982ba658fd91a03170c945f99c971f6955bc79df3266544373e39869c
        """
    )
    lint_check = "missing_source"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "missing a URL for the source" in messages[0].title


def test_missing_source_bad_type(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          urll: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
          md5: 5af07de982ba658fd91a03170c945f99c971f6955bc79df3266544373e39869c
        """
    )
    lint_check = "missing_source"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "missing a URL for the source" in messages[0].title


@pytest.mark.parametrize("src_type", ("url", "git_url", "path"))
def test_non_url_source_good(base_yaml, src_type):
    yaml_str = (
        base_yaml
        + """
        source:
          {src_type}: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
          md5: 5af07de982ba658fd91a03170c945f99c971f6955bc79df3266544373e39869c
        """
    )
    lint_check = "non_url_source"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("src_type", ("hg_url", "svn_url"))
def test_non_url_source_bad(base_yaml, src_type):
    lint_check = "non_url_source"
    yaml_str = (
        base_yaml
        + f"""
        source:
          {src_type}: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
          sha256: 5af07de982ba658fd91a03170c945f99c971f6955bc79df3266544373e39869c
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "not a valid type" in messages[0].title


@pytest.mark.parametrize("doc_type", ("doc_url", "doc_source_url"))
def test_missing_documentation_good(base_yaml, doc_type):
    yaml_str = (
        base_yaml
        + f"""
        about:
          {doc_type}: https://sqlite.com/
        """
    )
    lint_check = "missing_documentation"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_documentation_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
        """
    )
    lint_check = "missing_documentation"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "doc_url or doc_source_url" in messages[0].title


def test_documentation_specifies_language(base_yaml):
    yaml_str = (
        base_yaml
        + f"""
        about:
          doc_url: builder.readthedocs.io/en/latest
        """
    )
    lint_check = "documentation_specifies_language"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "Use the generic link not a language specific one" in messages[0].title

@pytest.mark.parametrize("doc_type", ("doc_url", "doc_source_url"))
def test_documentation_overspecified_good(base_yaml, doc_type):
    yaml_str = (
        base_yaml
        + f"""
        about:
          {doc_type}: https://sqlite.com/
        """
    )
    lint_check = "documentation_overspecified"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_documentation_overspecified_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
          doc_url: https://sqlite.com
          doc_source_url: https://sqlite.com
        """
    )
    lint_check = "documentation_overspecified"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "doc_url and doc_source_url is overspecified" in messages[0].title


def test_missing_dev_url_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
          dev_url: https://sqlite.com/
        """
    )
    lint_check = "missing_dev_url"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_dev_url_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
        """
    )
    lint_check = "missing_dev_url"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "dev_url" in messages[0].title


def test_missing_description_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
          description: very nice package
        """
    )
    lint_check = "missing_description"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_description_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
        """
    )
    lint_check = "missing_description"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "missing a description" in messages[0].title
