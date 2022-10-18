from conftest import check


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


def test_missing_license_file_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
          license_file:
            - LICENSE.md
        """
    )
    lint_check = "missing_license_file"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_license_file_bad(base_yaml):
    lint_check = "missing_license_file"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1 and "about/license_file" in messages[0].title


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
    print(messages[0].title)
    assert len(messages) == 1 and "about/license_family` value" in messages[0].title


def test_missing_tests_import(base_yaml):
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


def test_missing_tests_command(base_yaml):
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


def test_missing_tests_missing(base_yaml):
    lint_check = "missing_tests"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1 and "missing tests" in messages[0].title


def test_missing_tests_family_bad(base_yaml):
    lint_check = "missing_tests"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 1 and "missing tests" in messages[0].title


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


def test_missing_source_good(base_yaml):
    source_types = ["url", "git_url", "hg_url", "svn_url"]

    lint_check = "missing_source"
    for src in source_types:
        yaml_str = (
            base_yaml
            + f"""
        source:
          {src}: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
          sha256: 5af07de982ba658fd91a03170c945f99c971f6955bc79df3266544373e39869c
            """
        )
        messages = check(lint_check, yaml_str)
        assert len(messages) == 0, f"{src} is not recognized as a valid URL source"


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


def test_non_url_source_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
          md5: 5af07de982ba658fd91a03170c945f99c971f6955bc79df3266544373e39869c
        """
    )
    lint_check = "non_url_source"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_non_url_source_bad(base_yaml):
    source_types = ["git_url", "hg_url", "svn_url"]

    lint_check = "non_url_source"
    for src in source_types:
        yaml_str = (
            base_yaml
            + f"""
        source:
          {src}: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
          sha256: 5af07de982ba658fd91a03170c945f99c971f6955bc79df3266544373e39869c
            """
        )
        messages = check(lint_check, yaml_str)
        assert (
            len(messages) == 1 and "not url of url type" in messages[0].title
        ), f"{src} is not recognized as a valid URL source"


def test_missing_doc_url_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
          doc_url: https://sqlite.com/
        """
    )
    lint_check = "missing_doc_url"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_doc_url_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
        """
    )
    lint_check = "missing_doc_url"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "doc_url" in messages[0].title


def test_missing_doc_source_url_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
          doc_source_url: https://sqlite.com/
        """
    )
    lint_check = "missing_doc_source_url"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_doc_source_url_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
        """
    )
    lint_check = "missing_doc_source_url"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "doc_source_url" in messages[0].title


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


def test_missing_license_url_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
          license_url: https://sqlite.com/copyright.html
        """
    )
    lint_check = "missing_license_url"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_license_url_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        about:
        """
    )
    lint_check = "missing_license_url"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "license_url" in messages[0].title


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
