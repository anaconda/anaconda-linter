"""
File:           test_build_help.py
Description:    Tests build section rules
"""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import assert_lint_messages, assert_no_lint_message, check, check_dir

from anaconda_linter.lint.check_build_help import BUILD_TOOLS, PYTHON_BUILD_TOOLS


def test_host_section_needs_exact_pinnings_good(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        requirements:
            host:
              - mydep 0.13.7
        """
    )
    lint_check = "host_section_needs_exact_pinnings"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_host_section_needs_exact_pinnings_good_multi(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            requirements:
                host:
                  - mydep 0.13.7
          - name: output2
            requirements:
                host:
                  - mydep 0.13.7
        """
    )
    lint_check = "host_section_needs_exact_pinnings"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("package", ("python", "toml", "wheel", "packaging", "hatch-vcs", *PYTHON_BUILD_TOOLS))
def test_host_section_needs_exact_pinnings_good_exception(base_yaml: str, package: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        requirements:
            host:
              - {package}
        """
    )
    lint_check = "host_section_needs_exact_pinnings"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("package", ("python", "toml", "wheel", "packaging", *PYTHON_BUILD_TOOLS))
def test_host_section_needs_exact_pinnings_good_exception_multi(base_yaml: str, package: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        outputs:
          - name: output1
            requirements:
                host:
                  - {package}
          - name: output2
            requirements:
                host:
                  - {package}
        """
    )
    lint_check = "host_section_needs_exact_pinnings"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_host_section_needs_exact_pinnings_bad_cbc(base_yaml: str, recipe_dir: Path) -> None:
    yaml_str = (
        base_yaml
        + """
        requirements:
            host:
              - mydep
        """
    )
    cbc = """
    mydep:
      - 0.13.7
    """
    cbc_file = recipe_dir / "conda_build_config.yaml"
    cbc_file.write_text(cbc)
    lint_check = "host_section_needs_exact_pinnings"
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 1 and "Linked libraries host should have exact version pinnings." in messages[0].title


def test_host_section_needs_exact_pinnings_good_cbc_jinjavar(base_yaml: str, recipe_dir: Path) -> None:
    yaml_str = (
        base_yaml
        + """
        requirements:
            host:
              - openblas-devel  {{ openblas }}
        """
    )
    cbc = """
    openblas:
      - 0.3.20
    """
    cbc_file = recipe_dir / "conda_build_config.yaml"
    cbc_file.write_text(cbc)
    lint_check = "host_section_needs_exact_pinnings"
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 0


def test_host_section_needs_exact_pinnings_bad_cbc_multi(base_yaml: str, recipe_dir: Path) -> None:
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            requirements:
                host:
                  - mydep
          - name: output2
            requirements:
                host:
                  - mydep
        """
    )
    cbc = """
    mydep:
      - 0.13.7
    """
    cbc_file = recipe_dir / "conda_build_config.yaml"
    cbc_file.write_text(cbc)
    lint_check = "host_section_needs_exact_pinnings"
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 2 and all(
        "Linked libraries host should have exact version pinnings." in msg.title for msg in messages
    )


@pytest.mark.parametrize("constraint", ("", ">=0.13", "<0.14", "!=0.13.7"))
def test_host_section_needs_exact_pinnings_bad(base_yaml: str, constraint: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        requirements:
            host:
              - mydep {constraint}
        """
    )
    lint_check = "host_section_needs_exact_pinnings"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "Linked libraries host should have exact version pinnings." in messages[0].title


@pytest.mark.parametrize("constraint", ("", ">=0.13", "<0.14", "!=0.13.7"))
def test_host_section_needs_exact_pinnings_bad_multi(base_yaml: str, constraint: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        outputs:
          - name: output1
            requirements:
                host:
                  - mydep {constraint}
          - name: output2
            requirements:
                host:
                  - mydep {constraint}
        """
    )
    lint_check = "host_section_needs_exact_pinnings"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all(
        "Linked libraries host should have exact version pinnings." in msg.title for msg in messages
    )


@pytest.mark.parametrize(
    "file,",
    [
        ("should_use_compilers/using_compiler_function.yaml"),
    ],
)
def test_should_use_compilers_using_compilers(file: str) -> None:
    """
    This test checks the case where the "compiler" function is used.
    """
    assert_no_lint_message(
        recipe_file=file,
        lint_check="should_use_compilers",
    )


@pytest.mark.parametrize(
    "file,msg_count",
    [
        ("should_use_compilers/requesting_compilers_directly.yaml", 6),
    ],
)
def test_should_use_compilers_using_cgo_cuda_llvm(file: str, msg_count: int) -> None:
    """
    This test checks the case where the "compiler" function is not used, but compilers
    cgo, cuda, and llvm are requested directly.
    """
    assert_lint_messages(
        recipe_file=file,
        lint_check="should_use_compilers",
        msg_title="The recipe requires a compiler directly",
        msg_count=msg_count,
    )


@pytest.mark.parametrize("file,", ["should_use_stdlib/stdlib_present.yaml"])
def test_should_use_stdlib_present(file: str) -> None:
    assert_no_lint_message(recipe_file=file, lint_check="should_use_stdlib")


@pytest.mark.parametrize(
    "file,msg_count",
    [
        ("should_use_stdlib/stdlib_present_directly.yaml", 3),
        ("should_use_stdlib/stdlib_present_directly_multi.yaml", 15),
    ],
)
def test_should_use_stdlib_present_directly(file: str, msg_count: int) -> None:
    assert_lint_messages(
        recipe_file=file,
        lint_check="should_use_stdlib",
        msg_title="The recipe requires a {{ stdlib('c') }} dependency",
        msg_count=msg_count,
    )


@pytest.mark.parametrize(
    "file,msg_count",
    [
        ("should_use_stdlib/stdlib_missing.yaml", 1),
        ("should_use_stdlib/stdlib_missing_multi.yaml", 3),
    ],
)
def test_should_use_stdlib_missing(file: str, msg_count: int) -> None:
    assert_lint_messages(
        recipe_file=file,
        lint_check="should_use_stdlib",
        msg_title="The recipe requires a {{ stdlib('c') }} dependency",
        msg_count=msg_count,
    )


@pytest.mark.parametrize(
    "file",
    [
        "compilers_must_be_in_build/all_in_build.yaml",
        "compilers_must_be_in_build/no_compilers.yaml",
    ],
)
def test_compilers_must_be_in_build_all_compilers_in_build(file: str) -> None:
    """
    This test checks the cases where no compilers are found in a non-build section.
    """
    assert_no_lint_message(
        recipe_file=file,
        lint_check="compilers_must_be_in_build",
    )


@pytest.mark.parametrize(
    "file,msg_count",
    [
        ("compilers_must_be_in_build/single_output_2_in_host.yaml", 2),
    ],
)
def test_compilers_must_be_in_build_single_output_not_in_build(file: str, msg_count: int) -> None:
    """
    This test checks the case where compilers are found in the host section
    of single-output recipe.
    """
    assert_lint_messages(
        recipe_file=file,
        lint_check="compilers_must_be_in_build",
        msg_title="The recipe requests a compiler in a section other than build",
        msg_count=msg_count,
    )


@pytest.mark.parametrize(
    "file, msg_count",
    [
        ("compilers_must_be_in_build/top_level_1_in_host.yaml", 1),
        ("compilers_must_be_in_build/top_level_1_in_host_output_1_in_run.yaml", 2),
    ],
)
def test_compilers_must_be_in_build_multi_output_not_in_build(file: str, msg_count: int) -> None:
    """
    This test checks the case where compilers are found in non-build sections
    of multi-output recipes.
    """
    assert_lint_messages(
        recipe_file=file,
        lint_check="compilers_must_be_in_build",
        msg_title="The recipe requests a compiler in a section other than build",
        msg_count=msg_count,
    )


@pytest.mark.parametrize(
    "file",
    [
        "stdlib_must_be_in_build/single_output_in_build.yaml",
        "stdlib_must_be_in_build/multi_output_in_build.yaml",
    ],
)
def test_stdlib_must_be_in_build_in_build(file: str) -> None:
    """
    Test that the stdlib_must_be_in_build lint check passes when the recipe has a stdlib in the build section.
    """
    assert_no_lint_message(recipe_file=file, lint_check="stdlib_must_be_in_build")


@pytest.mark.parametrize(
    "file,msg_count",
    [
        ("stdlib_must_be_in_build/single_output_in_host_run.yaml", 2),
        ("stdlib_must_be_in_build/multi_output_in_host_run.yaml", 6),
    ],
)
def test_stdlib_must_be_in_build_in_host_run(file: str, msg_count: int) -> None:
    """
    Test that the stdlib_must_be_in_build lint check fails when the recipe has a stdlib in host or run.
    """
    assert_lint_messages(
        recipe_file=file,
        lint_check="stdlib_must_be_in_build",
        msg_title="The recipe requests a stdlib in a section other than build",
        msg_count=msg_count,
    )


@pytest.mark.parametrize("tool", BUILD_TOOLS)
def test_build_tools_must_be_in_build_good(base_yaml: str, tool: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        requirements:
          build:
            - {tool}
        """
    )
    lint_check = "build_tools_must_be_in_build"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("tool", BUILD_TOOLS)
def test_build_tools_must_be_in_build_good_multi(base_yaml: str, tool: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        outputs:
          - name: output1
            requirements:
              build:
                - {tool}
          - name: output2
            requirements:
              build:
                - {tool}
        """
    )
    lint_check = "build_tools_must_be_in_build"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("section", ("host", "run"))
@pytest.mark.parametrize("tool", BUILD_TOOLS)
def test_build_tools_must_be_in_build_bad(base_yaml: str, section: str, tool: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        requirements:
          {section}:
            - {tool}
        """
    )
    lint_check = "build_tools_must_be_in_build"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and f"build tool {tool} is not in the build section" in messages[0].title


@pytest.mark.parametrize("section", ("host", "run"))
@pytest.mark.parametrize("tool", BUILD_TOOLS)
def test_build_tools_must_be_in_build_bad_multi(base_yaml: str, section: str, tool: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        outputs:
          - name: output1
            requirements:
              {section}:
                - {tool}
          - name: output2
            requirements:
              {section}:
                - {tool}
        """
    )
    lint_check = "build_tools_must_be_in_build"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all(f"build tool {tool} is not in the build section" in msg.title for msg in messages)


@pytest.mark.parametrize("tool", PYTHON_BUILD_TOOLS)
def test_python_build_tool_in_run_good(base_yaml: str, tool: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        requirements:
          host:
            - {tool}
        """
    )
    lint_check = "python_build_tool_in_run"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("tool", PYTHON_BUILD_TOOLS)
def test_python_build_tool_in_run_good_multi(base_yaml: str, tool: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        outputs:
          - name: output1
            requirements:
              host:
                - {tool}
          - name: output2
            requirements:
              host:
                - {tool}
        """
    )
    lint_check = "python_build_tool_in_run"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("tool", PYTHON_BUILD_TOOLS)
def test_python_build_tool_in_run_bad(base_yaml: str, tool: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        requirements:
          run:
            - {tool}
        """
    )
    lint_check = "python_build_tool_in_run"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and f"python build tool {tool} is in run" in messages[0].title


@pytest.mark.parametrize("tool", PYTHON_BUILD_TOOLS)
def test_python_build_tool_in_run_bad_multi(base_yaml: str, tool: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        outputs:
          - name: output1
            requirements:
              run:
                - {tool}
          - name: output2
            requirements:
              run:
                - {tool}
        """
    )
    lint_check = "python_build_tool_in_run"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all(f"python build tool {tool} is in run" in msg.title for msg in messages)


@pytest.mark.parametrize("tool", PYTHON_BUILD_TOOLS)
def test_missing_python_build_tool_url_good(base_yaml: str, tool: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        requirements:
          host:
            - {tool}
        """
    )
    lint_check = "missing_python_build_tool"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("tool", PYTHON_BUILD_TOOLS)
def test_missing_python_build_tool_url_good_multi(base_yaml: str, tool: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        outputs:
          - name: outpu1
            requirements:
              host:
                - {tool}
          - name: outpu2
            requirements:
              host:
                - {tool}
        """
    )
    lint_check = "missing_python_build_tool"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_python_build_tool_url_bad(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        requirements:
          host:
        """
    )
    lint_check = "missing_python_build_tool"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "require a python build tool" in messages[0].title


def test_missing_python_build_tool_url_bad_multi(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        outputs:
          - name: outpu1
            requirements:
              host:
          - name: outpu2
            requirements:
              host:
        """
    )
    lint_check = "missing_python_build_tool"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("require a python build tool" in msg.title for msg in messages)


@pytest.mark.parametrize("tool", PYTHON_BUILD_TOOLS)
def test_missing_python_build_tool_pip_install_good(base_yaml: str, tool: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script: {{{{ PYTHON }}}} -m pip install .
        requirements:
          host:
            - {tool}
        """
    )
    lint_check = "missing_python_build_tool"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("tool", PYTHON_BUILD_TOOLS)
def test_missing_python_build_tool_pip_install_good_list(base_yaml: str, tool: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script:
            - {{{{ PYTHON }}}} -m pip install .
        requirements:
          host:
            - {tool}
        """
    )
    lint_check = "missing_python_build_tool"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("tool", PYTHON_BUILD_TOOLS)
def test_missing_python_build_tool_pip_install_good_multi(base_yaml: str, tool: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        outputs:
          - name: output1
            script: {{{{ PYTHON }}}} -m pip install .
            requirements:
              host:
                - {tool}
          - name: output2
            script: {{{{ PYTHON }}}} -m pip install .
            requirements:
              host:
                - {tool}
        """
    )
    lint_check = "missing_python_build_tool"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("tool", PYTHON_BUILD_TOOLS)
def test_missing_python_build_tool_pip_install_good_multi_list(base_yaml: str, tool: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        outputs:
          - name: output1
            script:
              - {{{{ PYTHON }}}} -m pip install .
            requirements:
              host:
                - {tool}
          - name: output2
            script: {{{{ PYTHON }}}} -m pip install .
            requirements:
              host:
                - {tool}
        """
    )
    lint_check = "missing_python_build_tool"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_python_build_tool_pip_install_bad(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script: {{ PYTHON }} -m pip install .
        requirements:
          host:
        """
    )
    lint_check = "missing_python_build_tool"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "require a python build tool" in messages[0].title


def test_missing_python_build_tool_pip_install_bad_list(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script:
            - {{ PYTHON }} -m pip install .
        requirements:
          host:
        """
    )
    lint_check = "missing_python_build_tool"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "require a python build tool" in messages[0].title


def test_missing_python_build_tool_pip_install_bad_multi(base_yaml: str) -> None:
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
    lint_check = "missing_python_build_tool"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("require a python build tool" in msg.title for msg in messages)


def test_missing_python_build_tool_pip_install_bad_multi_list(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            script:
              - {{ PYTHON }} -m pip install .
            requirements:
              host:
          - name: output2
            script: {{ PYTHON }} -m pip install .
            requirements:
              host:
        """
    )
    lint_check = "missing_python_build_tool"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("require a python build tool" in msg.title for msg in messages)


def test_uses_setup_py_good_missing(base_yaml: str) -> None:
    lint_check = "uses_setup_py"
    messages = check(lint_check, base_yaml)
    assert len(messages) == 0


def test_uses_setup_py_good_missing_file(base_yaml: str, recipe_dir: Path) -> None:
    yaml_str = (
        base_yaml
        + """
        requirements:
          host:
            - setuptools
        """
    )
    lint_check = "uses_setup_py"
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 0


def test_uses_setup_py_good_cmd(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        build:
          script: {{ PYTHON }} -m pip install . --no-deps --no-build-isolation
        requirements:
          host:
            - setuptools
        """
    )
    lint_check = "uses_setup_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_uses_setup_py_good_script(base_yaml: str, recipe_dir: Path) -> None:
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
    test_file.write_text("{{ PYTHON }} -m pip install . --no-deps --no-build-isolation\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("arg_test", ["", "--no-deps", "--no-build-isolation"])
def test_uses_setup_py_bad_cmd(base_yaml: str, arg_test: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        build:
          script: {{{{ PYTHON }}}} -m setup.py install {arg_test}
        requirements:
          host:
            - setuptools
        """
    )
    lint_check = "uses_setup_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "python setup.py install" in messages[0].title


@pytest.mark.parametrize("arg_test", ["", "--no-deps", "--no-build-isolation"])
def test_uses_setup_py_bad_cmd_list(base_yaml: str, arg_test: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        build:
          script:
            - {{{{ PYTHON }}}} -m setup.py install {arg_test}
        requirements:
          host:
            - setuptools
        """
    )
    lint_check = "uses_setup_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "python setup.py install" in messages[0].title


@pytest.mark.parametrize("arg_test", ["", "--no-deps", "--no-build-isolation"])
def test_uses_setup_py_bad_cmd_multi(base_yaml: str, arg_test: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        outputs:
          - name: output1
            script: {{{{ PYTHON }}}} -m setup.py install {arg_test}
            requirements:
              host:
                - setuptools
          - name: output2
            script: {{{{ PYTHON }}}} -m setup.py install {arg_test}
            requirements:
              host:
                - setuptools
        """
    )
    lint_check = "uses_setup_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("python setup.py install" in msg.title for msg in messages)


@pytest.mark.parametrize("arg_test", ["", "--no-deps", "--no-build-isolation"])
def test_uses_setup_py_bad_cmd_multi_list(base_yaml: str, arg_test: str) -> None:
    yaml_str = (
        base_yaml
        + f"""
        outputs:
          - name: output1
            script:
              - {{{{ PYTHON }}}} -m setup.py install {arg_test}
            requirements:
              host:
                - setuptools
          - name: output2
            script: {{{{ PYTHON }}}} -m setup.py install {arg_test}
            requirements:
              host:
                - setuptools
        """
    )
    lint_check = "uses_setup_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("python setup.py install" in msg.title for msg in messages)


@pytest.mark.parametrize("arg_test", ["", "--no-deps", "--no-build-isolation"])
def test_uses_setup_py_bad_script(base_yaml: str, recipe_dir: Path, arg_test: str) -> None:
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
    test_file.write_text(f"{{{{ PYTHON }}}} -m setup.py install {arg_test}\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 1 and "python setup.py install" in messages[0].title


@pytest.mark.parametrize("arg_test", ["", "--no-deps", "--no-build-isolation"])
def test_uses_setup_py_bad_script_multi(base_yaml: str, recipe_dir: Path, arg_test: str) -> None:
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
    test_file.write_text(f"{{{{ PYTHON }} }}-m setup.py install {arg_test}\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 2 and all("python setup.py install" in msg.title for msg in messages)


@pytest.mark.parametrize("arg_test", ["", "--no-deps", "--no-build-isolation"])
def test_uses_setup_py_multi_script_missing(base_yaml: str, recipe_dir: Path, arg_test: str) -> None:
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
            requirements:
              host:
                - setuptools
        """
    )
    lint_check = "uses_setup_py"
    test_file = recipe_dir / "build_output.sh"
    test_file.write_text(f"{{{{ PYTHON }}}} -m setup.py install {arg_test}\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 1 and "python setup.py install" in messages[0].title


@pytest.mark.parametrize(
    "file,",
    [
        "pip_install_args/no_command.yaml",
    ],
)
def test_pip_install_args_no_command_no_script(file: str) -> None:
    assert_no_lint_message(recipe_file=file, lint_check="pip_install_args")


@pytest.mark.parametrize(
    "file,",
    [
        "pip_install_args/no_command.yaml",
    ],
)
def test_pip_install_args_no_command_valid_script(file: str, recipe_dir: Path) -> None:
    test_file = recipe_dir / "build.sh"
    test_file.write_text("$PYTHON -m pip install . --no-deps --no-build-isolation\n")
    assert_no_lint_message(recipe_file=file, lint_check="pip_install_args", feedstock_dir=recipe_dir.parent)


@pytest.mark.parametrize(
    "file,",
    [
        "pip_install_args/command_valid.yaml",
    ],
)
def test_pip_install_args_command_valid(file: str) -> None:
    assert_no_lint_message(recipe_file=file, lint_check="pip_install_args")


@pytest.mark.parametrize(
    "file,",
    [
        "pip_install_args/command_missing_no_deps.yaml",
        "pip_install_args/command_missing_no_build.yaml",
    ],
)
def test_pip_install_args_command_missing_args(file: str) -> None:
    assert_lint_messages(
        recipe_file=file,
        lint_check="pip_install_args",
        msg_title="should be run with --no-deps and --no-build-isolation",
        msg_count=1,
    )


@pytest.mark.parametrize(
    "file,",
    [
        "pip_install_args/command_missing_args_multi.yaml",
    ],
)
def test_pip_install_args_command_missing_args_multi(file: str) -> None:
    assert_lint_messages(
        recipe_file=file,
        lint_check="pip_install_args",
        msg_title="should be run with --no-deps and --no-build-isolation",
        msg_count=3,
    )


@pytest.mark.parametrize(
    "file,",
    [
        "pip_install_args/command_valid_multi.yaml",
    ],
)
def test_pip_install_args_command_valid_multi(file: str) -> None:
    assert_no_lint_message(recipe_file=file, lint_check="pip_install_args")


@pytest.mark.parametrize(
    "file,script_file,msg_count",
    [
        ("pip_install_args/no_command.yaml", "build.sh", 1),
        ("pip_install_args/script_command.yaml", "build_script.sh", 1),
        ("pip_install_args/script_command_multi.yaml", "build_output.sh", 3),
        ("pip_install_args/script_command_multi_missing_one.yaml", "build_output.sh", 2),
    ],
)
def test_pip_install_args_invalid_script(file: str, script_file: str, msg_count: int, recipe_dir: Path) -> None:
    test_file = recipe_dir / script_file
    test_file.write_text("{{ PYTHON }} -m pip install .\n")
    assert_lint_messages(
        recipe_file=file,
        lint_check="pip_install_args",
        msg_title="should be run with --no-deps and --no-build-isolation",
        msg_count=msg_count,
        feedstock_dir=recipe_dir.parent,
    )


def test_python_build_tools_in_host_all_in_host() -> None:
    """
    This is the ideal case with no errors.
    """
    assert_no_lint_message(
        recipe_file="python_build_tools_in_host/all_in_host.yaml",
        lint_check="python_build_tools_in_host",
    )


def test_python_build_tools_in_host_some_in_build() -> None:
    """
    This case tests python build tools being in build, which is invalid.
    """
    assert_lint_messages(
        recipe_file="python_build_tools_in_host/some_in_build.yaml",
        lint_check="python_build_tools_in_host",
        msg_title="Python build tools should be in the host section",
        msg_count=3,
    )


def test_python_build_tools_in_host_some_in_run() -> None:
    """
    This case tests python build tools being in run, which is invalid.
    """
    assert_lint_messages(
        recipe_file="python_build_tools_in_host/some_in_run.yaml",
        lint_check="python_build_tools_in_host",
        msg_title="Python build tools should be in the host section",
        msg_count=3,
    )


def test_python_build_tools_in_host_some_in_build_and_run() -> None:
    """
    This case tests python build tools being in build and run, which is invalid.
    """
    assert_lint_messages(
        recipe_file="python_build_tools_in_host/some_in_build_and_run.yaml",
        lint_check="python_build_tools_in_host",
        msg_title="Python build tools should be in the host section",
        msg_count=6,
    )


def test_cython_needs_compiler_no_cython_no_compiler() -> None:
    """
    This case tests no cython and no compiler, which is valid.
    """
    assert_no_lint_message(
        recipe_file="cython_needs_compiler/no_cython_no_compiler.yaml",
        lint_check="cython_needs_compiler",
    )


def test_cython_needs_compiler_output_cython_top_level_compiler() -> None:
    """
    This case tests a cython dependency in an output and the compiler at the top level, which is valid.
    """
    assert_no_lint_message(
        recipe_file="cython_needs_compiler/output_cython_top_level_compiler.yaml",
        lint_check="cython_needs_compiler",
    )


def test_cython_needs_compiler_output_cython_output_compiler() -> None:
    """
    This case tests a cython dependency in an output and the compiler in the output, which is valid.
    """
    assert_no_lint_message(
        recipe_file="cython_needs_compiler/output_cython_output_compiler.yaml",
        lint_check="cython_needs_compiler",
    )


def test_cython_needs_compiler_output_cython_output_compiler_in_host() -> None:
    """
    This case tests a cython dependency in an output and the compiler in the output's host, which is invalid.
    """
    assert_lint_messages(
        recipe_file="cython_needs_compiler/output_cython_output_compiler_in_host.yaml",
        lint_check="cython_needs_compiler",
        msg_title="Cython generates C code",
        msg_count=1,
    )


def test_cython_needs_compiler_output_cython_top_level_cpp_compiler() -> None:
    """
    This case tests a cython dependency in an output and a c++ compiler at the top level, which is invalid.
    """
    assert_lint_messages(
        recipe_file="cython_needs_compiler/output_cython_top_level_cpp_compiler.yaml",
        lint_check="cython_needs_compiler",
        msg_title="Cython generates C code",
        msg_count=1,
    )


@pytest.mark.parametrize(
    "file",
    [
        "avoid_noarch/avoid_noarch_multi_output_no_noarch.yaml",
    ],
)
def test_avoid_noarch_no_noarch(file: str) -> None:
    """
    This case tests a multi-output recipe with no noarch:python.
    """
    assert_no_lint_message(
        recipe_file=file,
        lint_check="avoid_noarch",
    )


@pytest.mark.parametrize(
    "file",
    [
        "avoid_noarch/avoid_noarch_top_level_and_output_noarch.yaml",
    ],
)
def test_avoid_noarch_top_level_and_output_noarch(file: str) -> None:
    """
    This case tests a recipe with noarch:python at the top level and in an output.
    """
    assert_lint_messages(
        recipe_file=file,
        lint_check="avoid_noarch",
        msg_title="noarch: python packages should be avoided",
        msg_count=2,
    )


def test_patch_unnecessary_good(base_yaml: str) -> None:
    lint_check = "patch_unnecessary"
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
          patches:
            - some-patch.patch
            - some-other-patch.patch
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


@pytest.mark.parametrize("patch", ["patch", "msys2-patch", "m2-patch"])
@pytest.mark.parametrize("section", ["build", "host"])
def test_patch_unnecessary_with_patches_bad(base_yaml: str, patch: str, section: str) -> None:
    lint_check = "patch_unnecessary"
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
    assert len(messages) == 1 and "patch should not be" in messages[0].title


@pytest.mark.parametrize("patch", ["patch", "msys2-patch", "m2-patch"])
@pytest.mark.parametrize("section", ["build", "host"])
def test_patch_unnecessary_without_patches_bad(base_yaml: str, patch: str, section: str) -> None:
    lint_check = "patch_unnecessary"
    yaml_str = (
        base_yaml
        + f"""
        source:
          url: https://sqlite.com/2022/sqlite-autoconf-3380500.tar.gz
        requirements:
          {section}:
            - {patch}
        """
    )
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "patch should not be" in messages[0].title


def test_has_run_test_and_commands_good_cmd(base_yaml: str, tmpdir: Path) -> None:
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


def test_has_run_test_and_commands_good_script(base_yaml: str, recipe_dir: Path) -> None:
    lint_check = "has_run_test_and_commands"
    for script in ["run_test.sh", "run_test.bat"]:
        test_file = recipe_dir / script
        test_file.write_text("pip check\n")
    messages = check_dir(lint_check, recipe_dir.parent, base_yaml)
    assert len(messages) == 0


def test_has_run_test_and_commands_good_cmd_multi(base_yaml: str, tmpdir: Path) -> None:
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


def test_has_run_test_and_commands_good_script_multi(base_yaml: str, tmpdir: Path) -> None:
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


def test_has_run_test_and_commands_bad(base_yaml: str, recipe_dir: Path) -> None:
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


def test_has_run_test_and_commands_bad_multi(base_yaml: str, tmpdir: Path) -> None:
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
    assert len(messages) == 2 and all("Test commands are not executed" in msg.title for msg in messages)


def test_missing_imports_or_run_test_py_good_imports(base_yaml: str) -> None:
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


def test_missing_imports_or_run_test_py_good_pypi(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        test:
          imports:
            - module
        """
    )
    lint_check = "missing_imports_or_run_test_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_imports_or_run_test_py_good_script(base_yaml: str, recipe_dir: Path) -> None:
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


def test_missing_imports_or_run_test_py_good_multi(base_yaml: str) -> None:
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


def test_missing_imports_or_run_test_py_good_multi_pypi(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
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
    lint_check = "missing_imports_or_run_test_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_imports_or_run_test_py_bad(base_yaml: str) -> None:
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


def test_missing_imports_or_run_test_py_bad_pypi(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        test:
        """
    )
    lint_check = "missing_imports_or_run_test_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "Python packages require imports" in messages[0].title


def test_missing_imports_or_run_test_py_bad_multi(base_yaml: str) -> None:
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
    assert len(messages) == 2 and all("Python packages require imports" in msg.title for msg in messages)


def test_missing_imports_or_run_test_py_bad_multi_pypi(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        outputs:
          - name: output1
            test:
          - name: output2
            test:
        """
    )
    lint_check = "missing_imports_or_run_test_py"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("Python packages require imports" in msg.title for msg in messages)


def test_missing_pip_check_url_good(base_yaml: str) -> None:
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


def test_missing_pip_check_url_bad(base_yaml: str) -> None:
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
def test_missing_pip_check_url_list_bad(base_yaml: str) -> None:
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


def test_missing_pip_check_pip_install_cmd_good(base_yaml: str) -> None:
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


def test_missing_pip_check_pip_install_cmd_good_list(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script:
            - {{ PYTHON }} -m pip install .
        test:
          commands:
            - pip check
        """
    )
    lint_check = "missing_pip_check"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_pip_check_pip_install_cmd_good_multi(base_yaml: str) -> None:
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


def test_missing_pip_check_pip_install_cmd_good_multi_list(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        outputs:
          - name: output1
          - name: output2
            script:
              - {{ PYTHON }} -m pip install .
            test:
              commands:
                - pip check
        """
    )
    lint_check = "missing_pip_check"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_missing_pip_check_pip_install_script_good(base_yaml: str, recipe_dir: Path) -> None:
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


def test_missing_pip_check_pip_install_script_good_list(base_yaml: str, recipe_dir: Path) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script:
            - {{ PYTHON }} -m pip install .
        """
    )
    lint_check = "missing_pip_check"
    test_file = recipe_dir / "run_test.sh"
    test_file.write_text("pip check\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 0


def test_missing_pip_check_pip_install_script_good_multi(base_yaml: str, recipe_dir: Path) -> None:
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


def test_missing_pip_check_pip_install_script_good_multi_list(base_yaml: str, recipe_dir: Path) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        outputs:
          - name: output1
          - name: output2
            script:
              - {{ PYTHON }} -m pip install .
            test:
              script: test_output.sh
        """
    )
    lint_check = "missing_pip_check"
    test_file = recipe_dir / "test_output.sh"
    test_file.write_text("pip check\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 0


def test_missing_pip_check_pip_install_missing_bad(base_yaml: str) -> None:
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


def test_missing_pip_check_pip_install_missing_bad_list(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script:
            - {{ PYTHON }} -m pip install .
        """
    )
    lint_check = "missing_pip_check"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "pip check should be present" in messages[0].title


def test_missing_pip_check_pip_install_missing_bad_multi(base_yaml: str) -> None:
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
    assert len(messages) == 2 and all("pip check should be present" in msg.title for msg in messages)


def test_missing_pip_check_pip_install_missing_bad_multi_list(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        outputs:
          - name: output1
            script:
              - {{ PYTHON }} -m pip install .
          - name: output2
            script: {{ PYTHON }} -m pip install .
        """
    )
    lint_check = "missing_pip_check"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("pip check should be present" in msg.title for msg in messages)


def test_missing_pip_check_pip_install_cmd_bad(base_yaml: str) -> None:
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


def test_missing_pip_check_pip_install_cmd_bad_list(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script:
            - {{ PYTHON }} -m pip install .
        test:
          commands:
            - other_test_command
        """
    )
    lint_check = "missing_pip_check"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1 and "pip check should be present" in messages[0].title


def test_missing_pip_check_pip_install_cmd_bad_multi(base_yaml: str) -> None:
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
    assert len(messages) == 2 and all("pip check should be present" in msg.title for msg in messages)


def test_missing_pip_check_pip_install_cmd_bad_multi_list(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        outputs:
          - name: output1
            script:
              - {{ PYTHON }} -m pip install .
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
    assert len(messages) == 2 and all("pip check should be present" in msg.title for msg in messages)


def test_missing_pip_check_pip_install_script_bad(base_yaml: str, recipe_dir: Path) -> None:
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


def test_missing_pip_check_pip_install_script_bad_list(base_yaml: str, recipe_dir: Path) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script:
            - {{ PYTHON }} -m pip install .
        """
    )
    lint_check = "missing_pip_check"
    test_file = recipe_dir / "run_test.sh"
    test_file.write_text("other_test_command\n")
    messages = check_dir(lint_check, recipe_dir.parent, yaml_str)
    assert len(messages) == 1 and "pip check should be present" in messages[0].title


def test_missing_pip_check_pip_install_script_bad_multi(base_yaml: str, recipe_dir: Path) -> None:
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
    assert len(messages) == 2 and all("pip check should be present" in msg.title for msg in messages)


def test_missing_pip_check_pip_install_script_bad_multi_list(base_yaml: str, recipe_dir: Path) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        outputs:
          - name: output1
            script:
              - {{ PYTHON }} -m pip install .
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
    assert len(messages) == 2 and all("pip check should be present" in msg.title for msg in messages)


def test_missing_test_requirement_pip_missing(base_yaml: str) -> None:
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


def test_missing_test_requirement_pip_missing_multi(base_yaml: str) -> None:
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


def test_missing_test_requirement_pip_script_missing(base_yaml: str, recipe_dir: Path) -> None:
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


def test_missing_test_requirement_pip_script_missing_multi(base_yaml: str, recipe_dir: Path) -> None:
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


def test_missing_test_requirement_pip_cmd_good(base_yaml: str) -> None:
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


def test_missing_test_requirement_pip_cmd_good_multi(base_yaml: str) -> None:
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


def test_missing_test_requirement_pip_script_good(base_yaml: str, recipe_dir: Path) -> None:
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


def test_missing_test_requirement_pip_script_good_multi(base_yaml: str, recipe_dir: Path) -> None:
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


def test_missing_test_requirement_pip_cmd_bad(base_yaml: str) -> None:
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


def test_missing_test_requirement_pip_cmd_bad_multi(base_yaml: str) -> None:
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


def test_missing_test_requirement_pip_script_bad(base_yaml: str, recipe_dir: Path) -> None:
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


def test_missing_test_requirement_pip_script_bad_multi(base_yaml: str, recipe_dir: Path) -> None:
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


def test_missing_python_url_good(base_yaml: str) -> None:
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


def test_missing_python_url_bad(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: ttps://pypi.io/packages/source/D/Django/Django-4.1.tar.gz
        """
    )
    lint_check = "missing_python"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("python should be present" in m.title for m in messages)


def test_missing_python_pip_install_good(base_yaml: str) -> None:
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


def test_missing_python_pip_install_good_list(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script:
            - {{ PYTHON }} -m pip install .
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


def test_missing_python_pip_install_good_multi(base_yaml: str) -> None:
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


def test_missing_python_pip_install_good_multi_list(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        outputs:
          - name: output1
            script:
              - {{ PYTHON }} -m pip install .
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


def test_missing_python_pip_install_bad(base_yaml: str) -> None:
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
    assert len(messages) == 2 and all("python should be present" in m.title for m in messages)


def test_missing_python_pip_install_bad_list(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        build:
          script:
            - {{ PYTHON }} -m pip install .
        """
    )
    lint_check = "missing_python"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 2 and all("python should be present" in m.title for m in messages)


def test_missing_python_pip_install_bad_multi(base_yaml: str) -> None:
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
    assert len(messages) == 4 and all("python should be present" in m.title for m in messages)


def test_missing_python_pip_install_bad_multi_list(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        source:
          url: https://github.com/joblib/joblib/archive/1.1.1.tar.gz
        outputs:
          - name: output1
            script:
              - {{ PYTHON }} -m pip install .
          - name: output2
            script: {{ PYTHON }} -m pip install .
        """
    )
    lint_check = "missing_python"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 4 and all("python should be present" in m.title for m in messages)


def test_remove_python_pinning_good(base_yaml: str) -> None:
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


def test_remove_python_pinning_good_multi(base_yaml: str) -> None:
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


def test_remove_python_pinning_bad(base_yaml: str) -> None:
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
    assert len(messages) == 2 and all("python deps should not be constrained" in m.title for m in messages)


def test_remove_python_pinning_bad_multi(base_yaml: str) -> None:
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
    assert len(messages) == 4 and all("python deps should not be constrained" in m.title for m in messages)


@pytest.mark.parametrize(
    "file",
    [
        "no_git_on_windows/no_git.yaml",
        "no_git_on_windows/git_w_selector.yaml",
    ],
)
def test_no_git_on_windows_git_absent(file: str) -> None:
    """
    This test checks files that do not contain git on Windows.
    Either through actual absence or appropriate use of selectors.
    """
    assert_no_lint_message(
        recipe_file=file,
        lint_check="no_git_on_windows",
        arch="win-64",
    )


def test_no_git_on_windows_git_present() -> None:
    """
    This test checks a file that do contains git on Windows since
    the necessary selectors weren't used.
    """
    assert_lint_messages(
        recipe_file="no_git_on_windows/git_present.yaml",
        lint_check="no_git_on_windows",
        msg_title="git should not be used as a dependency on Windows",
        msg_count=1,
        arch="win-64",
    )


def test_gui_app_good(base_yaml: str) -> None:
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
def test_gui_app_bad(base_yaml: str, gui: str) -> None:
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


def test_cbc_dep_in_run_missing_from_host_good(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        requirements:
            host:
              - python
              - hdf5
            run:
              - python
              - hdf5
        """
    )
    lint_check = "cbc_dep_in_run_missing_from_host"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_cbc_dep_in_run_missing_from_host_good_multi(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        outputs:
          - name: output1
            requirements:
              host:
                - python
                - hdf5
              run:
                - python
                - hdf5
          - name: output2
            requirements:
              host:
                - python
                - hdf5
              run:
                - python
                - hdf5
        """
    )
    lint_check = "cbc_dep_in_run_missing_from_host"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_cbc_dep_in_run_missing_from_host_bad(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """
        requirements:
            host:
              - python
            run:
              - python
              - hdf5
        """
    )
    lint_check = "cbc_dep_in_run_missing_from_host"
    messages = check(lint_check, yaml_str, "linux-64", {"hdf5": "1.2.3"})
    assert len(messages) == 1


def test_cbc_dep_in_run_missing_from_host_bad_multi(base_yaml: str) -> None:
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
                - hdf5
          - name: output2
            requirements:
              host:
                - python
              run:
                - python
                - hdf5
        """
    )
    lint_check = "cbc_dep_in_run_missing_from_host"
    messages = check(lint_check, yaml_str, "linux-64", {"hdf5": "1.2.3"})
    assert len(messages) == 2


def test_potentially_bad_ignore_run_exports_good(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """

        build:
          ignore_run_exports:
            - bb
        requirements:
            host:
              - aa
        """
    )
    lint_check = "potentially_bad_ignore_run_exports"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_potentially_bad_ignore_run_exports_good_multi(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """

        outputs:
          - name: output1
            build:
              ignore_run_exports:
                - bb
            requirements:
              host:
                - aa
        """
    )
    lint_check = "potentially_bad_ignore_run_exports"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 0


def test_potentially_bad_ignore_run_exports_bad(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """

        build:
          ignore_run_exports:
            - aa
        requirements:
            host:
              - aa
        """
    )
    lint_check = "potentially_bad_ignore_run_exports"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1


def test_potentially_bad_ignore_run_exports_bad_multi(base_yaml: str) -> None:
    yaml_str = (
        base_yaml
        + """

        outputs:
          - name: output1
            build:
              ignore_run_exports:
                - aa
            requirements:
              host:
                - aa
        """
    )
    lint_check = "potentially_bad_ignore_run_exports"
    messages = check(lint_check, yaml_str)
    assert len(messages) == 1
