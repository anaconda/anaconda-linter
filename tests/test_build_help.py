import pytest
from conftest import check, check_dir


@pytest.mark.parametrize(
    "compiler",
    (
        "cgo",
        "cuda",
        "dpcpp",
        "gcc",
        "go",
        "libgcc",
        "libgfortran",
        "llvm",
        "m2w64_c",
        "m2w64_cxx",
        "m2w64_fortran",
        "rust-gnu",
        "rust",
        "toolchain",
    ),
)
def test_should_use_compilers_good(base_yaml, compiler):
    lint_check = "should_use_compilers"
    yaml_str = (
        base_yaml
        + f"""
        requirements:
          build:
            - {{{{ compiler('{compiler}') }}}}
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize(
    "compiler",
    (
        "cgo",
        "cuda",
        "dpcpp",
        "gcc",
        "go",
        "libgcc",
        "libgfortran",
        "llvm",
        "m2w64_c",
        "m2w64_cxx",
        "m2w64_fortran",
        "rust-gnu",
        "rust",
        "toolchain",
    ),
)
def test_should_use_compilers_bad(base_yaml, compiler):
    lint_check = "should_use_compilers"
    yaml_str = (
        base_yaml
        + f"""
        requirements:
          build:
            - {compiler}
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "compiler directly" in messages[0].title


def test_should_use_compilers_bad_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            requirements:
              build:
                - gcc
          - name: output2
            requirements:
              build:
                - gcc
        """
    )
    lint_check = "should_use_compilers"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("compiler directly" in msg.title for msg in messages)


def test_compilers_must_be_in_build_good(base_yaml):
    lint_check = "compilers_must_be_in_build"
    yaml_str = (
        base_yaml
        + """
        requirements:
          build:
            - {{ compiler('c') }}
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_compilers_must_be_in_build_good_multi(base_yaml):
    lint_check = "compilers_must_be_in_build"
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            requirements:
              build:
                - {{ compiler('c') }}
          - name: output2
            requirements:
              build:
                - {{ compiler('c') }}
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("section", ["host", "run"])
def test_compilers_must_be_in_build_bad(base_yaml, section):
    lint_check = "compilers_must_be_in_build"
    yaml_str = (
        base_yaml
        + f"""
        requirements:
          {section}:
            - {{{{ compiler('c') }}}}
            """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "compiler in a section" in messages[0].title


@pytest.mark.parametrize("section", ["host", "run"])
def test_compilers_must_be_in_build_bad_multi(base_yaml, section):
    lint_check = "compilers_must_be_in_build"
    yaml_str = (
        base_yaml
        + f"""
        outputs:
          - name: output1
            requirements:
              {section}:
                - {{{{ compiler('c') }}}}
          - name: output2
            requirements:
              {section}:
                - {{{{ compiler('c') }}}}
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("compiler in a section" in msg.title for msg in messages)


def test_uses_setuptools_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        requirements:
          host:
            - setuptools
        """
    )
    lint_check = "uses_setuptools"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_uses_setuptools_good_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            requirements:
              host:
                - setuptools
          - name: output2
            requirements:
              host:
                - setuptools
        """
    )
    lint_check = "uses_setuptools"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_uses_setuptools_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        requirements:
          run:
            - setuptools
        """
    )
    lint_check = "uses_setuptools"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "uses setuptools in run depends" in messages[0].title


def test_uses_setuptools_bad_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            requirements:
              run:
                - setuptools
          - name: output2
            requirements:
              run:
                - setuptools
        """
    )
    lint_check = "uses_setuptools"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all(
        "uses setuptools in run depends" in msg.title for msg in messages
    )


def test_missing_wheel_url_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        requirements:
          host:
            - wheel
        """
    )
    lint_check = "missing_wheel"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_wheel_url_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        """
    )
    lint_check = "missing_wheel"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "wheel should be present" in messages[0].title


def test_missing_wheel_pip_install_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script: {{ PYTHON }} -m pip install .
        requirements:
          host:
            - wheel
        """
    )
    lint_check = "missing_wheel"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_wheel_pip_install_good_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            script: {{ PYTHON }} -m pip install .
            requirements:
              host:
                - wheel
          - name: output2
            script: {{ PYTHON }} -m pip install .
            requirements:
              host:
                - wheel
        """
    )
    lint_check = "missing_wheel"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_wheel_pip_install_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script: {{ PYTHON }} -m pip install .
        """
    )
    lint_check = "missing_wheel"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "wheel should be present" in messages[0].title


def test_missing_wheel_pip_install_bad_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            script: {{ PYTHON }} -m pip install .
            requirements:
              host:
          - name: output2
            script: {{ PYTHON }} -m pip install .
            requirements:
              host:
        """
    )
    lint_check = "missing_wheel"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("wheel should be present" in msg.title for msg in messages)


def test_uses_setup_py_good_missing(base_yaml):
    lint_check = "uses_setup_py"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 0


def test_uses_setup_py_good_cmd(base_yaml):
    yaml_str = (
        base_yaml
        + """
        build:
          script: {{ PYTHON }} -m pip install . --no-deps
        requirements:
          host:
            - setuptools
        """
    )
    lint_check = "uses_setup_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_uses_setup_py_good_script(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        requirements:
          host:
            - setuptools
        """
    )
    lint_check = "uses_setup_py"
    test_file = recipe_dir / "build.sh"
    test_file.write_text("{{ PYTHON }} -m pip install . --no-deps\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 0


def test_uses_setup_py_bad_cmd(base_yaml):
    yaml_str = (
        base_yaml
        + """
        build:
          script: {{ PYTHON }} -m setup.py install
        requirements:
          host:
            - setuptools
        """
    )
    lint_check = "uses_setup_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "python setup.py install" in messages[0].title


def test_uses_setup_py_bad_cmd_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            script: {{ PYTHON }} -m setup.py install
            requirements:
              host:
                - setuptools
          - name: output2
            script: {{ PYTHON }} -m setup.py install
            requirements:
              host:
                - setuptools
        """
    )
    lint_check = "uses_setup_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("python setup.py install" in msg.title for msg in messages)


def test_uses_setup_py_bad_script(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        requirements:
          host:
            - setuptools
        """
    )
    lint_check = "uses_setup_py"
    test_file = recipe_dir / "build.sh"
    test_file.write_text("{{ PYTHON }} -m setup.py install\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 1 and "python setup.py install" in messages[0].title


def test_uses_setup_py_bad_script_multi(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            script: build_output.sh
            requirements:
              host:
                - setuptools
          - name: output2
            script: build_output.sh
            requirements:
              host:
                - setuptools
        """
    )
    lint_check = "uses_setup_py"
    test_file = recipe_dir / "build_output.sh"
    test_file.write_text("{{ PYTHON }} -m setup.py install\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 2 and all("python setup.py install" in msg.title for msg in messages)


def test_pip_install_args_good_missing(base_yaml):
    lint_check = "pip_install_args"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 0


def test_pip_install_args_good_cmd(base_yaml):
    yaml_str = (
        base_yaml
        + """
        build:
          script: {{ PYTHON }} -m pip install . --no-deps
        requirements:
          host:
            - pip
        """
    )
    lint_check = "pip_install_args"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_pip_install_args_good_script(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        requirements:
          host:
            - pip
        """
    )
    lint_check = "pip_install_args"
    test_file = recipe_dir / "build.sh"
    test_file.write_text("{{ PYTHON }} -m pip install . --no-deps\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 0


def test_pip_install_args_bad_cmd(base_yaml):
    yaml_str = (
        base_yaml
        + """
        build:
          script: {{ PYTHON }} -m pip install .
        requirements:
          host:
            - pip
        """
    )
    lint_check = "pip_install_args"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "should be run with --no-deps" in messages[0].title


def test_pip_install_args_bad_cmd_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            script: {{ PYTHON }} -m pip install
            requirements:
              host:
                - pip
          - name: output2
            script: {{ PYTHON }} -m pip install
            requirements:
              host:
                - pip
        """
    )
    lint_check = "pip_install_args"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all(
        "should be run with --no-deps" in msg.title for msg in messages
    )


def test_pip_install_args_bad_script(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        requirements:
          host:
            - pip
        """
    )
    lint_check = "pip_install_args"
    test_file = recipe_dir / "build.sh"
    test_file.write_text("{{ PYTHON }} -m pip install .\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 1 and "should be run with --no-deps" in messages[0].title


def test_pip_install_args_bad_script_multi(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            script: build_output.sh
            requirements:
              host:
                - pip
          - name: output2
            script: build_output.sh
            requirements:
              host:
                - pip
        """
    )
    lint_check = "pip_install_args"
    test_file = recipe_dir / "build_output.sh"
    test_file.write_text("{{ PYTHON }} -m pip install .\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 2 and all(
        "should be run with --no-deps" in msg.title for msg in messages
    )


def test_cython_must_be_in_host_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        requirements:
          host:
            - cython
        """
    )
    lint_check = "cython_must_be_in_host"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_cython_must_be_in_host_good_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            requirements:
              host:
                - cython
          - name: output2
            requirements:
              host:
                - cython
        """
    )
    lint_check = "cython_must_be_in_host"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("section", ["build", "run"])
def test_cython_must_be_in_host_bad(base_yaml, section):
    lint_check = "cython_must_be_in_host"
    yaml_str = (
        base_yaml
        + f"""
        requirements:
          {section}:
            - cython
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "Cython should be" in messages[0].title


@pytest.mark.parametrize("section", ["build", "run"])
def test_cython_must_be_in_host_bad_multi(base_yaml, section):
    lint_check = "cython_must_be_in_host"
    yaml_str = (
        base_yaml
        + f"""
        outputs:
          - name: output1
            requirements:
              {section}:
                - cython
          - name: output2
            requirements:
              {section}:
                - cython
    """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("Cython should be" in msg.title for msg in messages)


def test_cython_needs_compiler_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        requirements:
          build:
            - {{ compiler('c') }}
          host:
            - cython
        """
    )
    lint_check = "cython_needs_compiler"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_cython_needs_compiler_good_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            requirements:
              build:
                - {{ compiler('c') }}
              host:
                - cython
          - name: output2
            requirements:
              build:
                - {{ compiler('c') }}
              host:
                - cython
        """
    )
    lint_check = "cython_needs_compiler"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_cython_needs_compiler_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        requirements:
          build:
            - {{ compiler('cxx') }}
          host:
            - cython
        """
    )
    lint_check = "cython_needs_compiler"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "Cython generates C code" in messages[0].title


def test_cython_needs_compiler_bad_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            requirements:
              build:
                - {{ compiler('cxx') }}
              host:
                - cython
          - name: output2
            requirements:
              build:
                - {{ compiler('cxx') }}
              host:
                - cython
        """
    )
    lint_check = "cython_needs_compiler"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("Cython generates C code" in msg.title for msg in messages)


def test_avoid_noarch_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        build:
          noarch: generic
        """
    )
    lint_check = "avoid_noarch"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_avoid_noarch_good_build_number(base_yaml):
    yaml_str = (
        base_yaml
        + """
        build:
          noarch: python
          number: 2
        """
    )
    lint_check = "avoid_noarch"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_avoid_noarch_good_osx_app(base_yaml):
    yaml_str = (
        base_yaml
        + """
        build:
          noarch: python
          osx_is_app: true
        """
    )
    lint_check = "avoid_noarch"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_avoid_noarch_good_app(base_yaml):
    yaml_str = (
        base_yaml
        + """
        build:
          noarch: python
        app:
          icon: logo.png
        """
    )
    lint_check = "avoid_noarch"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_avoid_noarch_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        build:
          noarch: python
        """
    )
    lint_check = "avoid_noarch"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "noarch: python" in messages[0].title


def test_patch_unnecessary_good(base_yaml):
    lint_check = "patch_unnecessary"
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("patch", ["patch", "m2-patch"])
def test_patch_unnecessary_bad(base_yaml, patch):
    lint_check = "patch_unnecessary"
    yaml_str = (
        base_yaml
        + f"""
        source:
          url: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
        requirements:
          build:
            - {patch}
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "patch should not be" in messages[0].title


@pytest.mark.parametrize("patch", ["patch", "m2-patch"])
def test_patch_must_be_in_build_good(base_yaml, patch):
    lint_check = "patch_must_be_in_build"
    yaml_str = (
        base_yaml
        + f"""
        source:
          url: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
          patches:
            - some-patch.patch
        requirements:
          build:
            - {patch}
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_patch_must_be_in_build_bad(base_yaml):
    lint_check = "patch_must_be_in_build"
    for patch in ["patch", "m2-patch"]:
        for section in ["host", "run"]:
            yaml_str = (
                base_yaml
                + f"""
        source:
          url: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
          patches:
            - some-patch.patch
        requirements:
          {section}:
            - {patch}
            """
            )
            messages = check(lint_check, yaml_str)
            assert (
                len(messages) == 1 and "patch must be in build" and messages[0].title
            ), f"Check failed for {patch} in {section}"


@pytest.mark.parametrize("patch", ["patch", "m2-patch"])
@pytest.mark.parametrize("section", ["host", "run"])
def test_patch_must_be_in_build_list_bad(base_yaml, patch, section):
    lint_check = "patch_must_be_in_build"
    yaml_str = (
        base_yaml
        + f"""
        source:
          - url: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
          - url: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
            patches:
              - some-patch.patch
        requirements:
          {section}:
            - {patch}
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "patch must be in build" and messages[0].title


def test_patch_must_be_in_build_missing(base_yaml):
    lint_check = "patch_must_be_in_build"
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
          patches:
            - some-patch.patch
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "patch must be in build" in messages[0].title


def test_has_run_test_and_commands_good_cmd(base_yaml, tmpdir):
    yaml_str = (
        base_yaml
        + """
        test:
          commands:
            - pip check
        """
    )
    lint_check = "has_run_test_and_commands"
    messages = check_dir(lint_check, tmpdir, yaml_str)
    assert len(messages) == 0


def test_has_run_test_and_commands_good_script(base_yaml, recipe_dir):
    lint_check = "has_run_test_and_commands"
    for script in ["run_test.sh", "run_test.bat"]:
        test_file = recipe_dir / script
        test_file.write_text("pip check\n")
    messages = check_dir(lint_check, recipe_dir.parent, base_yaml)
    assert len(messages) == 0


def test_has_run_test_and_commands_good_cmd_multi(base_yaml, tmpdir):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            test:
              commands:
                - pip check
          - name: output2
            test:
              commands:
                - pip check
        """
    )
    lint_check = "has_run_test_and_commands"
    messages = check_dir(lint_check, tmpdir, yaml_str)
    assert len(messages) == 0


def test_has_run_test_and_commands_good_script_multi(base_yaml, tmpdir):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            test:
              script: test_module.sh
          - name: output2
            test:
              script: test_module2.sh
        """
    )
    lint_check = "has_run_test_and_commands"
    messages = check_dir(lint_check, tmpdir, yaml_str)
    assert len(messages) == 0


def test_has_run_test_and_commands_bad(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        test:
          commands:
            - pip check
        """
    )
    lint_check = "has_run_test_and_commands"
    for script in ["run_test.sh", "run_test.bat"]:
        test_file = recipe_dir / script
        test_file.write_text("pip check\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 1 and "Test commands are not executed" in messages[0].title


def test_has_run_test_and_commands_bad_multi(base_yaml, tmpdir):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            test:
              commands:
                - pip check
              script: test_module.sh
          - name: output2
            test:
              commands:
                - pip check
              script: test_module2.sh
        """
    )
    lint_check = "has_run_test_and_commands"
    messages = check_dir(lint_check, tmpdir, yaml_str)
    assert len(messages) == 2 and all(
        "Test commands are not executed" in msg.title for msg in messages
    )


def test_has_imports_and_run_test_py_good_imports(base_yaml):
    yaml_str = (
        base_yaml
        + """
        test:
          imports:
            - module
        """
    )
    lint_check = "has_imports_and_run_test_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_has_imports_and_run_test_py_good_script(base_yaml, recipe_dir):
    lint_check = "has_imports_and_run_test_py"
    test_file = recipe_dir / "run_test.py"
    test_file.write_text("import module\n")
    messages = check_dir(lint_check, recipe_dir.parent, base_yaml)
    assert len(messages) == 0


def test_has_imports_and_run_test_py_good_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            test:
              imports:
                - module1
          - name: output2
            test:
              script: test_output2.py
        """
    )
    lint_check = "has_imports_and_run_test_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_has_imports_and_run_test_py_good_multi_testsh(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            test:
              imports:
                - module1
              script: test_output1.sh
          - name: output2
            test:
              script: test_output2.py
        """
    )
    lint_check = "has_imports_and_run_test_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0

def test_has_imports_and_run_test_py_bad(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        test:
          imports:
            - module
        """
    )
    lint_check = "has_imports_and_run_test_py"
    test_file = recipe_dir / "run_test.py"
    test_file.write_text("import module\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 1 and "Imports and python test file" in messages[0].title


def test_has_imports_and_run_test_py_bad_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            test:
              script: test_output1.py
              imports:
                - module1
          - name: output2
            test:
              script: test_output2.py
              imports:
                - module2
        """
    )
    lint_check = "has_imports_and_run_test_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all(
        "Imports and python test file" in msg.title for msg in messages
    )


def test_missing_imports_or_run_test_py_good_imports(base_yaml):
    yaml_str = (
        base_yaml
        + """
        requirements:
          host:
            - python
        test:
          imports:
            - module
        """
    )
    lint_check = "missing_imports_or_run_test_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_imports_or_run_test_py_good_script(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        requirements:
          host:
            - python
        """
    )
    lint_check = "missing_imports_or_run_test_py"
    test_file = recipe_dir / "run_test.py"
    test_file.write_text("import module\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 0


def test_missing_imports_or_run_test_py_good_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            requirements:
              host:
                - python
            test:
              imports:
                - module1
          - name: output2
            requirements:
              host:
                - python
            test:
              script: test_output2.py
        """
    )
    lint_check = "missing_imports_or_run_test_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_imports_or_run_test_py_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        requirements:
          host:
            - python
        """
    )
    lint_check = "missing_imports_or_run_test_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "Python packages require imports" in messages[0].title


def test_missing_imports_or_run_test_py_bad_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            requirements:
              host:
                - python
          - name: output2
            requirements:
              host:
                - python
        """
    )
    lint_check = "missing_imports_or_run_test_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all(
        "Python packages require imports" in msg.title for msg in messages
    )


def test_missing_pip_check_url_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        test:
          commands:
            - pip check
        """
    )
    lint_check = "missing_pip_check"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_pip_check_url_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        """
    )
    lint_check = "missing_pip_check"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "pip check should be present" in messages[0].title


# This test covers part of the is_pypi_source function
def test_missing_pip_check_url_list_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          - url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
          - url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        """
    )
    lint_check = "missing_pip_check"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "pip check should be present" in messages[0].title


def test_missing_pip_check_pip_install_cmd_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script: {{ PYTHON }} -m pip install .
        test:
          commands:
            - pip check
        """
    )
    lint_check = "missing_pip_check"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_pip_check_pip_install_cmd_good_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        outputs:
          - name: output1
          - name: output2
            script: {{ PYTHON }} -m pip install .
            test:
              commands:
                - pip check
        """
    )
    lint_check = "missing_pip_check"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_pip_check_pip_install_script_good(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script: {{ PYTHON }} -m pip install .
        """
    )
    lint_check = "missing_pip_check"
    test_file = recipe_dir / "run_test.sh"
    test_file.write_text("pip check\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 0


def test_missing_pip_check_pip_install_script_good_multi(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        outputs:
          - name: output1
          - name: output2
            script: {{ PYTHON }} -m pip install .
            test:
              script: test_output.sh
        """
    )
    lint_check = "missing_pip_check"
    test_file = recipe_dir / "test_output.sh"
    test_file.write_text("pip check\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 0


def test_missing_pip_check_pip_install_missing_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script: {{ PYTHON }} -m pip install .
        """
    )
    lint_check = "missing_pip_check"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "pip check should be present" in messages[0].title


def test_missing_pip_check_pip_install_missing_bad_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        outputs:
          - name: output1
            script: {{ PYTHON }} -m pip install .
          - name: output2
            script: {{ PYTHON }} -m pip install .
        """
    )
    lint_check = "missing_pip_check"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all(
        "pip check should be present" in msg.title for msg in messages
    )


def test_missing_pip_check_pip_install_cmd_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script: {{ PYTHON }} -m pip install .
        test:
          commands:
            - other_test_command
        """
    )
    lint_check = "missing_pip_check"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "pip check should be present" in messages[0].title


def test_missing_pip_check_pip_install_cmd_bad_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        outputs:
          - name: output1
            script: {{ PYTHON }} -m pip install .
            test:
              commands:
                - other_test_command
          - name: output2
            script: {{ PYTHON }} -m pip install .
            test:
              commands:
                - other_test_command
        """
    )
    lint_check = "missing_pip_check"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all(
        "pip check should be present" in msg.title for msg in messages
    )


def test_missing_pip_check_pip_install_script_bad(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script: {{ PYTHON }} -m pip install .
        """
    )
    lint_check = "missing_pip_check"
    test_file = recipe_dir / "run_test.sh"
    test_file.write_text("other_test_command\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 1 and "pip check should be present" in messages[0].title


def test_missing_pip_check_pip_install_script_bad_multi(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        outputs:
          - name: output1
            script: {{ PYTHON }} -m pip install .
            test:
              script: test_output.sh
          - name: output2
            script: {{ PYTHON }} -m pip install .
            test:
              script: test_output.sh
        """
    )
    lint_check = "missing_pip_check"
    test_file = recipe_dir / "test_output.sh"
    test_file.write_text("other_test_command\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 2 and all(
        "pip check should be present" in msg.title for msg in messages
    )


def test_missing_test_requirement_pip_missing(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        """
    )
    lint_check = "missing_test_requirement_pip"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_test_requirement_pip_missing_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        outputs:
          - name: output1
          - name: output2
        """
    )
    lint_check = "missing_test_requirement_pip"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_test_requirement_pip_script_missing(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        """
    )
    lint_check = "missing_test_requirement_pip"
    test_file = recipe_dir / "run_test.sh"
    test_file.write_text("other_test_command\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 0


def test_missing_test_requirement_pip_script_missing_multi(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        outputs:
          - name: output1
          - name: output2
            test:
              script: test_output.sh
        """
    )
    lint_check = "missing_test_requirement_pip"
    test_file = recipe_dir / "test_output.sh"
    test_file.write_text("other_test_command\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 0


def test_missing_test_requirement_pip_cmd_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        test:
          commands:
            - pip check
          requires:
            - pip
        """
    )
    lint_check = "missing_test_requirement_pip"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_test_requirement_pip_cmd_good_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        outputs:
          - name: output1
            test:
              commands:
                - pip check
              requires:
                - pip
          - name: output2
            test:
              commands:
                - pip check
              requires:
                - pip
        """
    )
    lint_check = "missing_test_requirement_pip"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_test_requirement_pip_script_good(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        test:
          requires:
            - pip
        """
    )
    lint_check = "missing_test_requirement_pip"
    test_file = recipe_dir / "run_test.sh"
    test_file.write_text("pip check\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 0


def test_missing_test_requirement_pip_script_good_multi(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        outputs:
          - name: output1
          - name: output2
            test:
              script: test_output.sh
              requires:
                - pip
        """
    )
    lint_check = "missing_test_requirement_pip"
    test_file = recipe_dir / "test_output.sh"
    test_file.write_text("pip check\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 0


def test_missing_test_requirement_pip_cmd_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        test:
          commands:
            - pip check
        """
    )
    lint_check = "missing_test_requirement_pip"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "pip is required" in messages[0].title


def test_missing_test_requirement_pip_cmd_bad_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        outputs:
          - name: output1
            test:
              commands:
                - pip check
          - name: output2
            test:
              commands:
                - pip check
        """
    )
    lint_check = "missing_test_requirement_pip"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("pip is required" in msg.title for msg in messages)


def test_missing_test_requirement_pip_script_bad(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        """
    )
    lint_check = "missing_test_requirement_pip"
    test_file = recipe_dir / "run_test.sh"
    test_file.write_text("pip check\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 1 and "pip is required" in messages[0].title


def test_missing_test_requirement_pip_script_bad_multi(base_yaml, recipe_dir):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        outputs:
          - name: output1
            test:
              script: test_output.sh
          - name: output2
            test:
              script: test_output.sh
        """
    )
    lint_check = "missing_test_requirement_pip"
    test_file = recipe_dir / "test_output.sh"
    test_file.write_text("pip check\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 2 and all("pip is required" in msg.title for msg in messages)


def test_missing_python_url_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        requirements:
          host:
            - python
          run:
            - python
        """
    )
    lint_check = "missing_python"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_python_url_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: ttps://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        """
    )
    lint_check = "missing_python"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all(["python should be present" in m.title for m in messages])


def test_missing_python_pip_install_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script: {{ PYTHON }} -m pip install .
        requirements:
          host:
            - python
          run:
            - python
        """
    )
    lint_check = "missing_python"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_python_pip_install_good_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        outputs:
          - name: output1
            script: {{ PYTHON }} -m pip install .
            requirements:
              host:
                - python
              run:
                - python
          - name: output2
            script: {{ PYTHON }} -m pip install .
            requirements:
              host:
                - python
              run:
                - python
        """
    )
    lint_check = "missing_python"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_python_pip_install_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script: {{ PYTHON }} -m pip install .
        """
    )
    lint_check = "missing_python"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all(["python should be present" in m.title for m in messages])


def test_missing_python_pip_install_bad_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        outputs:
          - name: output1
            script: {{ PYTHON }} -m pip install .
          - name: output2
            script: {{ PYTHON }} -m pip install .
        """
    )
    lint_check = "missing_python"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 4 and all(["python should be present" in m.title for m in messages])


def test_remove_python_pinning_good(base_yaml):
    yaml_str = (
        base_yaml
        + """
        requirements:
          host:
            - python
          run:
            - python
        """
    )
    lint_check = "remove_python_pinning"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_remove_python_pinning_good_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            requirements:
              host:
                - python
              run:
                - python
          - name: output2
            requirements:
              host:
                - python
              run:
                - python
        """
    )
    lint_check = "remove_python_pinning"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_remove_python_pinning_bad(base_yaml):
    yaml_str = (
        base_yaml
        + """
        requirements:
          host:
            - python >=3.8
          run:
            - python >=3.8
        """
    )
    lint_check = "remove_python_pinning"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all(
        "python deps should not be constrained" in m.title for m in messages
    )


def test_remove_python_pinning_bad_multi(base_yaml):
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            requirements:
              host:
                - python >=3.8
              run:
                - python >=3.8
          - name: output2
            requirements:
              host:
                - python >=3.8
              run:
                - python >=3.8
        """
    )
    lint_check = "remove_python_pinning"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 4 and all(
        "python deps should not be constrained" in m.title for m in messages
    )


def test_gui_app_good(base_yaml):
    lint_check = "gui_app"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 0


@pytest.mark.parametrize(
    "gui",
    (
        "enaml",
        "glue-core",
        "glueviz",
        "jupyterhub",
        "jupyterlab",
        "orange3",
        "pyqt",
        "qt3dstudio",
        "qtcreator",
        "qtpy",
        "spyder",
        "wxpython",
    ),
)
def test_gui_app_bad(base_yaml, gui):
    lint_check = "gui_app"
    yaml_str = (
        base_yaml
        + f"""
        requirements:
          run:
            - {gui}
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "GUI application" in messages[0].title
