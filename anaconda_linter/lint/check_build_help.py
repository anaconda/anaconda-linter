"""
File:           check_build_help.py
Description:    Contains linter checks for build section based rules.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from percy.parser.recipe_parser import RecipeParser, SelectorConflictMode
from percy.render.recipe import Recipe

from anaconda_linter import utils as _utils
from anaconda_linter.lint import LintCheck, Severity

# Does not include m2-tools, which should be checked using wild cards.
BUILD_TOOLS = (
    "autoconf",
    "automake",
    "bison",
    "cmake",
    "distutils",
    "flex",
    "git",
    "libtool",
    "m4",
    "make",
    "ninja",
    "patch",
    "pkg-config",
    "posix",
)

PYTHON_BUILD_TOOLS = (
    "cython",
    "flit",
    "flit-core",
    "hatch",
    "hatchling",
    "meson",
    "meson-python",
    "pdm",
    "pdm-pep517",
    "pip",
    "poetry",
    "poetry-core",
    "pybind11",
    "setuptools",
    "setuptools-rust",
    "setuptools_scm",
    "whey",
    "scikit-build-core",
    "scikit-build",
    "maturin",
    "python-build",
    "build",
)

# List of known PEP-517 backends (https://peps.python.org/pep-0517/) that are not setuptools
# and that don't require wheel since they create wheels themselves.
# The backend is defined using the pyproject.toml file (which was introduced by PEP-518).
# Historical note: pyproject.toml file was introduced initially to specify the build system (backend).
# Only later was the ability to specify all the project metadata (name, version, dependencies, etc)
# into it added, via PEP-621.
PYTHON_BUILD_BACKENDS = (
    "flit",  # Our packages are not supposed to depend on flit, but apparently they do, so we need to support it here.
    "flit-core",  # Backend of flit.
    "hatch",  # Same as flit, we should not depend on it. We should instead depend on hatchling, which is the backend.
    "hatchling",  # Backend of hatch.
    "meson-python",  # Backend that uses meson.
    "pdm-backend",  # Backend of pdm (new). Not yet in our repo, but if it ever does, we'll be able to handle it.
    "pdm-pep517",  # Deprecated backend of pdm but we still need to support it, see https://pypi.org/project/pdm-pep517
    "poetry-core",  # Backend of poetry.
    "scikit-build-core",  # Backend that uses cmake.
    "whey",
    "maturin",
)

COMPILERS = (
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
)


def is_pypi_source(recipe: Recipe) -> bool:
    """
    Determines if a recipe has it's source hosted on PyPi
    :param recipe: Recipe to check
    :returns: True if the recipe is hosted on PyPi. False otherwise.
    """
    # is it a pypi package?
    pypi_urls = ["pypi.io", "pypi.org", "pypi.python.org"]
    pypi_source = False
    source = recipe.get("source", None)
    if isinstance(source, dict):
        pypi_source = any(x in source.get("url", "") for x in pypi_urls)
    elif isinstance(source, list):
        for src in source:
            pypi_source = any(x in src.get("url", "") for x in pypi_urls)
            if pypi_source:
                break
    return pypi_source


def recipe_has_patches(recipe: Recipe) -> bool:
    """
    Determines if a recipe uses patch files.
    :param recipe: Recipe to check
    :returns: True if the recipe contains patches. False otherwise.
    """
    if source := recipe.get("source", None):
        if isinstance(source, dict):
            if source.get("patches", ""):
                return True
        elif isinstance(source, list):
            for src in source:
                if src.get("patches", ""):
                    return True
    return False


class host_section_needs_exact_pinnings(LintCheck):
    """
    Linked libraries host should have exact version pinnings.
    Other dependencies are case by case.

    Specifically, comparison operators must not be used. The version numbers can be
    specified in a conda_build_config.yaml file.
    """

    @staticmethod
    def is_exception(package: str) -> bool:
        """
        Determines if a package is an exception to this pinning linter check.
        :param package: Package name to check
        :returns: True if the package is an exception. False otherwise.
        """
        exceptions = (
            "python",
            "toml",
            "wheel",
            "packaging",
            *PYTHON_BUILD_TOOLS,
        )
        # It doesn't make sense to pin the versions of hatch plugins if we're not pinning
        # hatch. We could explicitly enumerate the 15 odd plugins in PYTHON_BUILD_TOOLS, but
        # this seemed lower maintenance
        return (package in exceptions) or any(package.startswith(f"{pkg}-") for pkg in PYTHON_BUILD_TOOLS)

    def check_recipe(self, recipe: Recipe) -> None:
        deps = _utils.get_deps_dict(recipe, "host")
        for package, dep in deps.items():
            if not self.is_exception(package) and not (
                package in recipe.selector_dict and recipe.selector_dict[package]
            ):
                for c, constraint in enumerate(dep["constraints"]):
                    if constraint == "" or re.search("^[<>!]", constraint) is not None:
                        path = dep["paths"][c]
                        output = -1 if not path.startswith("outputs") else int(path.split("/")[1])
                        self.message(section=path, severity=Severity.WARNING, output=output)


class cbc_dep_in_run_missing_from_host(LintCheck):
    """
    Run dependencies listed in the cbc should also be present in the host section.
    """

    def check_recipe(self, recipe: Recipe) -> None:
        for package in recipe.packages.values():
            for dep in package.run:
                if dep.pkg in recipe.selector_dict and recipe.selector_dict[dep.pkg]:
                    if not self.is_exception(dep.pkg) and not package.has_dep("host", dep.pkg):
                        dep_path = _utils.get_dep_path(recipe, dep)
                        self.message(
                            section=dep_path,
                            data=(recipe, f"{package.path_prefix}requirements/host", dep.pkg),
                        )

    @staticmethod
    def is_exception(package) -> bool:
        exceptions = (
            "python",
            "numpy",
        )
        return package in exceptions

    def fix(self, message, data) -> bool:
        (recipe, path, dep) = data
        op = [
            {
                "op": "add",
                "path": path,
                "match": f"{dep}.*",
                "value": [f"{dep} " + "{{ " + f"{dep}" + " }}"],
            },
        ]
        return recipe.patch(op)


class potentially_bad_ignore_run_exports(LintCheck):
    """
    Ignoring run_export of a host dependency. In some cases it is more appropriate to remove the `--error-overdepending`
    flag of conda-build.
    """

    def check_recipe(self, recipe: Recipe) -> None:
        for package in recipe.packages.values():
            for dep in package.host:
                if dep.pkg in package.ignore_run_exports:
                    self.message(section=_utils.get_dep_path(recipe, dep), severity=Severity.INFO)


class should_use_compilers(LintCheck):
    """
    The recipe requires a compiler directly

    Since version 3, ``conda-build`` uses a special syntax to require
    compilers for a given language matching the architecture for which
    a package is being build. Please use::

        requirements:
           build:
             - {{ compiler('language') }}

    Where language is one of ``c``, ``cxx``, ``fortran``, ``go`` or
    ``cgo``. You can specify multiple compilers if needed.

    There is no need to add ``libgfortran``, ``libgcc``, or
    ``toolchain`` to the dependencies as this will be handled by
    conda-build itself.

    """

    compilers = (
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
    )

    def check_deps(self, deps) -> None:
        for compiler in self.compilers:
            for location in deps.get(compiler, {}).get("paths", []):
                self.message(section=location)


class compilers_must_be_in_build(LintCheck):
    """
    The recipe requests a compiler in a section other than build

    Please move the ``{{ compiler('language') }}`` line into the
    ``requirements: build:`` section.

    """

    def check_deps(self, deps) -> None:
        for dep in deps:
            if dep.startswith("compiler_"):
                for location in deps[dep]["paths"]:
                    if "run" in location or "host" in location:
                        self.message(section=location)


class build_tools_must_be_in_build(LintCheck):
    """
    The build tool {} is not in the build section.

    Please add::
        requirements:
          build:
            - {}
    """

    def check_recipe(self, recipe: Recipe) -> None:
        deps = _utils.get_deps_dict(recipe, ["host", "run"])
        for tool, dep in deps.items():
            if tool.startswith("m2-") or tool in BUILD_TOOLS:
                for path in dep["paths"]:
                    o = -1 if not path.startswith("outputs") else int(path.split("/")[1])
                    self.message(tool, severity=Severity.WARNING, section=path, output=o)


class python_build_tool_in_run(LintCheck):
    """
    The python build tool {} is in run depends

    Most Python packages only need python build tools during installation.
    Check if the package really needs this build tool (e.g. because it uses
    pkg_resources or setuptools console scripts).

    """

    def check_recipe(self, recipe: Recipe) -> None:
        deps = _utils.get_deps_dict(recipe, "run")
        for tool in PYTHON_BUILD_TOOLS:
            if tool in deps:
                for path in deps[tool]["paths"]:
                    o = -1 if not path.startswith("outputs") else int(path.split("/")[1])
                    self.message(tool, severity=Severity.WARNING, section=path, output=o)


class missing_python_build_tool(LintCheck):
    """
    Python packages require a python build tool such as setuptools.

    Please add the build tool specified by the upstream package to the host section.
    """

    def check_recipe(self, recipe: Recipe) -> None:
        is_pypi = is_pypi_source(recipe)
        if outputs := recipe.get("outputs", None):
            deps = _utils.get_deps_dict(recipe, "host")
            for o in range(len(outputs)):
                # Create a list of build tool dependencies for each output
                tools = []
                for tool, dep in deps.items():
                    if tool in PYTHON_BUILD_TOOLS and any(path.startswith(f"outputs/{o}") for path in dep["paths"]):
                        tools.append(tool)
                if (is_pypi or recipe.contains(f"outputs/{o}/script", "pip install", "")) and len(tools) == 0:
                    self.message(section=f"outputs/{o}/requirements/host", output=o)
        elif is_pypi or recipe.contains("build/script", "pip install", ""):
            deps = _utils.get_deps(recipe, "host")
            if not any(tool in deps for tool in PYTHON_BUILD_TOOLS):
                self.message(section="requirements/host")


class missing_wheel(LintCheck):
    """
    For pypi packages, wheel should be present in the host section

    Add wheel to requirements/host:

      requirements:
        host:
          - wheel
    """

    def check_recipe(self, recipe: Recipe) -> None:
        is_pypi = is_pypi_source(recipe)

        for package in recipe.packages.values():
            if (
                is_pypi
                or recipe.contains(f"{package.path_prefix}build/script", "pip install", "")
                or recipe.contains(f"{package.path_prefix}script", "pip install", "")
            ):
                # Note that we do the assumption that if none of the backends defined in exceptions are present
                # and that setuptools is also not present, that setuptools will be used via the good old
                # setup.py file. This is because pip defaults to doing that for historical reasons.
                # This means that if pip is used in the install script and there is no host dependencies,
                # we want this check to raise a warning because wheel should be added there!
                #
                # In theory we would also need to warn if setuptools missing in the host
                # section and none of the new build backends are used.
                # TODO: add a missing_setuptools rule?
                if not package.has_dep("host", "wheel") and not set(PYTHON_BUILD_BACKENDS).intersection(
                    {dep.pkg.lower() for dep in package.get("host")}
                ):
                    self.message(
                        section=f"{package.path_prefix}requirements/host",
                        data=(recipe, package),
                    )

    def fix(self, message, data) -> bool:
        (recipe, package) = data
        op = [
            {
                "op": "add",
                "path": f"{package.path_prefix}requirements/host",
                "match": "wheel",
                "value": ["wheel"],
            },
        ]
        return recipe.patch(op)


class uses_setup_py(LintCheck):
    """
    `python setup.py install` is deprecated.

    Please use::

        $PYTHON -m pip install . --no-deps --no-build-isolation

    Or use another python build tool.
    """

    @staticmethod
    def _check_line(x: str) -> bool:
        """
        Check a line for a broken call to setup.py
        """
        if isinstance(x, str):
            x = [x]
        elif not isinstance(x, list):
            return True
        for line in x:
            if "setup.py install" in line:
                return False
        return True

    def check_recipe(self, recipe: Recipe) -> None:
        for package in recipe.packages.values():
            if not self._check_line(recipe.get(f"{package.path_prefix}build/script", None)):
                self.message(
                    section=f"{package.path_prefix}build/script",
                    data=(recipe, f"{package.path_prefix}build/script"),
                )
            elif not self._check_line(recipe.get(f"{package.path_prefix}script", None)):
                self.message(
                    section=f"{package.path_prefix}script",
                    data=(recipe, f"{package.path_prefix}script"),
                )
            elif self.recipe.dir:
                try:
                    build_file = self.recipe.get(f"{package.path_prefix}script", "")
                    if not build_file:
                        build_file = self.recipe.get(f"{package.path_prefix}build/script", "build.sh")
                    build_file = self.recipe.dir / Path(build_file)
                    if build_file.exists():
                        with open(str(build_file), encoding="utf-8") as buildsh:
                            for num, line in enumerate(buildsh):
                                if not self._check_line(line):
                                    if package.path_prefix.startswith("output"):
                                        output = int(package.path_prefix.split("/")[1])
                                    else:
                                        output = -1
                                    self.message(fname=build_file, line=num, output=output)
                except (FileNotFoundError, TypeError):
                    pass

    def fix(self, message, data) -> bool:
        (recipe, path) = data
        op = [
            {
                "op": "replace",
                "path": path,
                "match": ".* setup.py .*",
                "value": (
                    "{{PYTHON}} -m pip install . --no-deps --no-build-isolation --ignore-installed"
                    " --no-cache-dir -vv"
                ),
            },
        ]
        return recipe.patch(op)


class pip_install_args(LintCheck):
    """
    `pip install` should be run with --no-deps and --no-build-isolation.

    Please use::

        $PYTHON -m pip install . --no-deps --no-build-isolation

    """

    @staticmethod
    def _check_line(x: Any) -> bool:
        """
        Check a line (or list of lines) for a broken call to setup.py
        """
        if isinstance(x, str):
            x = [x]
        elif not isinstance(x, list):
            return True

        for line in x:
            if "pip install" in line:
                required_args = ["--no-deps", "--no-build-isolation"]
                if any(arg not in line for arg in required_args):
                    return False

        return True

    def check_recipe(self, recipe: Recipe) -> None:
        for package in recipe.packages.values():
            if not self._check_line(recipe.get(f"{package.path_prefix}build/script", None)):
                self.message(
                    section=f"{package.path_prefix}build/script",
                    data=(recipe, f"{package.path_prefix}build/script"),
                )
            elif not self._check_line(recipe.get(f"{package.path_prefix}script", None)):
                self.message(
                    section=f"{package.path_prefix}script",
                    data=(recipe, f"{package.path_prefix}script"),
                )
            elif self.recipe.dir:
                try:
                    build_file = self.recipe.get(f"{package.path_prefix}script", "")
                    if not build_file:
                        build_file = self.recipe.get(f"{package.path_prefix}build/script", "build.sh")
                    build_file = self.recipe.dir / Path(build_file)
                    if build_file.exists():
                        with open(str(build_file), encoding="utf-8") as buildsh:
                            for num, line in enumerate(buildsh):
                                if not self._check_line(line):
                                    if package.path_prefix.startswith("output"):
                                        output = int(package.path_prefix.split("/")[1])
                                    else:
                                        output = -1
                                    self.message(fname=build_file, line=num, output=output)
                except (FileNotFoundError, TypeError):
                    pass

    def fix(self, message, data) -> bool:
        (recipe, path) = data
        op = [
            {
                "op": "replace",
                "path": path,
                "match": r"(.*\s)?pip install(?!=.*--no-build-isolation).*",
                "value": (
                    "{{ PYTHON }} -m pip install . --no-deps --no-build-isolation --ignore-installed"
                    " --no-cache-dir -vv"
                ),
            },
        ]
        return recipe.patch(op)


class cython_must_be_in_host(LintCheck):
    """
    Cython should be in the host section

    Move cython to ``host``::

      requirements:
        host:
          - cython
    """

    def check_deps(self, deps) -> None:
        if "cython" in deps:
            for location in deps["cython"]["paths"]:
                if "/host" not in location:
                    self.message(section=location)


class cython_needs_compiler(LintCheck):
    """
    Cython generates C code, which will need to be compiled

    Add the compiler to the recipe::

      requirements:
        build:
          - {{ compiler('c') }}

    """

    def check_deps(self, deps) -> None:
        if "cython" in deps:
            for location in deps["cython"]["paths"]:
                if location.startswith("outputs"):
                    n = location.split("/")[1]
                    section = f"outputs/{n}/requirements/build"
                    output = int(n)
                else:
                    section = "requirements/build"
                    output = -1
                if "compiler_c" not in self.recipe.get(section, ""):
                    self.message(section=section, output=output)


class avoid_noarch(LintCheck):
    """
    noarch: python packages should be avoided

    Please remove::

        build:
            noarch: python

    Then add::

        requirements:
            host:
                - python
                - pip
                - setuptools
                - wheel
            run:
                - python

    noarch packages should be avoided because it is difficult to
    assess if a package actually includes no architecture specific binaries.
    Note:: Keep noarch if this is a rebuild of a package version
    that is currently noarch.

    """

    def check_recipe(self, recipe: Recipe) -> None:
        for package in recipe.packages.values():
            noarch = recipe.get(f"{package.path_prefix}build/noarch", "")
            if (
                noarch == "python"
                and int(recipe.get(f"{package.path_prefix}build/number", 0)) == 0
                and not recipe.get(f"{package.path_prefix}build/osx_is_app", False)
                and not recipe.get(f"{package.path_prefix}app", None)
            ):
                self.message(section=f"{package.path_prefix}build", severity=Severity.WARNING, data=(recipe, package))

    def fix(self, message, data) -> bool:
        (recipe, package) = data
        skip_selector = None
        sep_map = {
            ">=": "<",
            ">": "<=",
            "==": "!=",
            "!=": "==",
            "<=": ">",
            "<": ">=",
        }
        for dep in recipe.get(f"{package.path_prefix}requirements/run", []):
            if dep.startswith("python"):
                for sep, opp in sep_map.items():
                    s = dep.split(sep)
                    if len(s) > 1:
                        skip_selector = f" # [py{opp}{s[1].strip().replace('.','')}]"
                        break
                if skip_selector:
                    break
        op = [
            {"op": "remove", "path": f"{package.path_prefix}build/noarch"},
            {
                "op": "add",
                "path": f"{package.path_prefix}requirements/host",
                "match": "python",
                "value": ["python"],
            },
            {
                "op": "add",
                "path": f"{package.path_prefix}requirements/run",
                "match": "python",
                "value": ["python"],
            },
            {
                "op": "replace",
                "path": f"{package.path_prefix}test/requires",
                "match": "python",
                "value": ["python"],
            },
        ]
        if skip_selector:
            op.append(
                {
                    "op": "add",
                    "path": f"{package.path_prefix}build/skip",
                    "value": f"True {skip_selector}",
                }
            )
        return recipe.patch(op)


class patch_unnecessary(LintCheck):
    """
    patch should not be in build when source/patches is not set

    Remove patch/m2-patch from ``build``
    """

    def check_recipe(self, recipe: Recipe) -> None:
        if not recipe_has_patches(recipe):
            deps = _utils.get_deps_dict(
                recipe,
            )
            if "patch" in deps or "m2-patch" in deps:
                self.message(section="build")


class patch_must_be_in_build(LintCheck):
    """
    patch must be in build when source/patches is set.

    Add patch to ``build``::

      requirements:
        build:
          - patch       # [not win]
          - m2-patch    # [win]
    """

    def check_recipe(self, recipe: Recipe) -> None:
        if recipe_has_patches(recipe):
            deps = _utils.get_deps_dict(
                recipe,
            )
            if "patch" in deps:
                if any("build" not in location for location in deps["patch"]["paths"]):
                    self.message(section="requirements/build")
            elif "m2-patch" in deps:
                if any("build" not in location for location in deps["m2-patch"]["paths"]):
                    self.message(section="requirements/build")
            else:
                self.message(section="requirements/build")


class has_run_test_and_commands(LintCheck):
    """
    Test commands are not executed when run_test.sh (.bat...) is present.

    Add the test commands to run_test.sh/.bat/.pl
    """

    def check_recipe(self, recipe: Recipe) -> None:
        if outputs := recipe.get("outputs", None):
            for o in range(len(outputs)):
                test_section = f"outputs/{o}/test"
                if recipe.get(f"{test_section}/script", None) and recipe.get(f"{test_section}/commands", None):
                    self.message(section=f"{test_section}/commands", output=o)
        else:
            if recipe.get("test/commands", []) and (
                recipe.get("test/script", None)
                or (
                    recipe.dir
                    and set(os.listdir(recipe.dir)).intersection({"run_test.sh", "run_test.pl", "run_test.bat"})
                )
            ):
                self.message(section="test/commands")


class missing_imports_or_run_test_py(LintCheck):
    """
    Python packages require imports or a python test file in tests.

    Add::
        test:
          imports:
            - <module>

    Or add a run_test.py file into the recipe directory.

    For multi-ouput recipes, add imports or a python test file for each output::
        test:
          script: <test file>
    """

    def check_recipe(self, recipe: Recipe) -> None:
        is_pypi = is_pypi_source(recipe)
        deps = _utils.get_deps_dict(recipe, "host")
        if not is_pypi and "python" not in deps:
            return
        if outputs := recipe.get("outputs", None):
            paths_to_check = []
            if is_pypi:
                paths_to_check = [f"outputs/{o}" for o in range(len(outputs))]
            else:
                paths_to_check = [
                    "/".join(path.split("/")[:2])
                    for path in deps["python"]["paths"]
                    if not path.startswith("requirements")
                ]
            for path in paths_to_check:
                if not recipe.get(f"{path}/test/imports", []) and not recipe.get(f"{path}/test/script", ""):
                    o = int(path.split("/")[1])
                    self.message(section=f"{path}/test", output=o)
        elif (
            (is_pypi or "python" in deps)
            and not recipe.get("test/imports", [])
            and not (recipe.dir and os.path.isfile(os.path.join(recipe.dir, "run_test.py")))
        ):
            self.message(section="test")


class missing_pip_check(LintCheck):
    """
    For pypi packages, pip check should be present in the test commands

    Add pip check to test/commands:

      tests:
        commands:
          - pip check
    """

    def _check_file(self, file: str, recipe: Recipe, package: str) -> None:
        """
        Reads the file for a `pip check` command and outputs a message if not found.
        :param file: The path of the file.
        :param recipe: Recipe instance tied to the file
        :param package: Name of the package of interest
        """
        if os.path.isfile(file):
            with open(file, encoding="utf-8") as test_file:
                for line in test_file:
                    if "pip check" in line:
                        return
        self.message(fname=file, data=(recipe, package))

    def check_recipe(self, recipe: Recipe) -> None:
        is_pypi = is_pypi_source(recipe)

        single_output = True
        if len(recipe.packages) > 1:
            single_output = False

        for package in recipe.packages.values():
            if (
                not single_output
                and not is_pypi
                and not recipe.contains(f"{package.path_prefix}script", "pip install", "")
            ):
                continue
            if (
                single_output
                and not is_pypi
                and not recipe.contains(f"{package.path_prefix}build/script", "pip install", "")
            ):
                continue
            if commands := recipe.get(f"{package.path_prefix}test/commands", None):
                if not any("pip check" in cmd for cmd in commands):
                    self.message(section=f"{package.path_prefix}test/commands", data=(recipe, package))
            elif recipe.dir and (script := recipe.get(f"{package.path_prefix}test/script", None)):
                self._check_file(os.path.join(recipe.dir, script), recipe, package)
            elif not single_output:
                self.message(section=f"{package.path_prefix}test", data=(recipe, package))
            else:
                test_files = (
                    set(os.listdir(recipe.dir)).intersection({"run_test.sh", "run_test.bat"})
                    if os.path.exists(recipe.dir)
                    else set()
                )
                if len(test_files) > 0:
                    for file in test_files:
                        self._check_file(os.path.join(recipe.dir, file), recipe, package)
                else:
                    # In PAT-249, data was not being passed. Take this into consideration if/when this gets reworked to
                    # use the recipe parser.
                    self.message(section=f"{package.path_prefix}test", data=(recipe, package))

    def fix(self, message, data) -> bool:
        (recipe, package) = data
        op = [
            {
                "op": "add",
                "path": f"{package.path_prefix}test/commands",
                "match": "pip check",
                "value": ["pip check"],
            },
        ]
        return recipe.patch(op)


class missing_test_requirement_pip(LintCheck):  #
    """
    pip is required in the test requirements.

    Please add::
        test:
          requires:
            - pip
    """

    def _check_file(self, file: str) -> bool:
        """
        Determines if `pip check` is found in the file
        TODO Future: This `pip check` utility seems to be used in an identically named function that varies slightly.
                     Hopefully both can be de-duplicated.
        :param file: Path to the file to check.
        :returns: True if the file contains `pip check`. False otherwise.
        """
        if not os.path.isfile(file):
            return False
        with open(file, encoding="utf-8") as test_file:
            for line in test_file:
                if "pip check" in line:
                    return True
        return False

    def _has_pip_check(self, recipe: Recipe, output: str = "") -> None:
        """
        Indicates if a feedstock (recipe and script files) contains a `pip check`
        :param recipe: Recipe instance to check against
        :param output: (Optional) Output file to check against
        :returns: True if the feedstock contains `pip check`. False otherwise.
        """
        test_section = f"{output}test"
        if commands := recipe.get(f"{test_section}/commands", None):
            if any("pip check" in cmd for cmd in commands):
                return True
        elif self.recipe.dir:
            if output.startswith("outputs"):
                script = recipe.get(f"{test_section}/script", "")
                return self._check_file(os.path.join(recipe.dir, script))
            else:
                test_files = (
                    set(os.listdir(recipe.dir)).intersection({"run_test.sh", "run_test.bat"})
                    if os.path.exists(recipe.dir)
                    else set()
                )
                for file in test_files:
                    if self._check_file(os.path.join(recipe.dir, file)):
                        return True
        return False

    def check_recipe(self, recipe: Recipe) -> None:
        for package in recipe.packages.values():
            if self._has_pip_check(recipe, output=package.path_prefix) and "pip" not in recipe.get(
                f"{package.path_prefix}test/requires", []
            ):
                self.message(section=f"{package.path_prefix}test/requires", data=(recipe, package))

    def fix(self, message, data) -> bool:
        (recipe, package) = data
        op = [
            {
                "op": "add",
                "path": f"{package.path_prefix}test/requires",
                "match": "pip",
                "value": ["pip"],
            },
        ]
        return recipe.patch(op)


class missing_python(LintCheck):
    """
    For pypi packages, python should be present in the host and run sections. Missing in {}

    Add python:

      requirements:
        host:
          - python
        run:
          - python
    """

    def check_recipe(self, recipe: Recipe) -> None:
        is_pypi = is_pypi_source(recipe)
        for package in recipe.packages.values():
            if (
                is_pypi
                or recipe.contains(f"{package.path_prefix}build/script", "pip install", "")
                or recipe.contains(f"{package.path_prefix}script", "pip install", "")
            ):
                for section in ["host", "run"]:
                    if not package.has_dep(section, "python"):
                        self.message(
                            section=f"{package.path_prefix}requirements/{section}",
                            data=(recipe, package),
                        )

    def fix(self, message, data) -> bool:
        (recipe, package) = data
        op = [
            {
                "op": "add",
                "path": f"{package.path_prefix}requirements/host",
                "match": "python",
                "value": ["python"],
            },
            {
                "op": "add",
                "path": f"{package.path_prefix}requirements/run",
                "match": "python",
                "value": ["python"],
            },
        ]
        return recipe.patch(op)


class remove_python_pinning(LintCheck):
    """
    On arch specific packages, python deps should not be constrained.

    Replace python constraints by a skip directive:

      build:
        skip: True # [py<38]

      requirements:
        host:
          - python
        run:
          - python
    """

    def check_recipe(self, recipe: Recipe) -> None:
        for package in recipe.packages.values():
            if recipe.get(f"{package.path_prefix}build/noarch", "") == "":
                for section in ["host", "run"]:
                    for dep in package.get(section):
                        if dep.pkg == "python" and dep.constraint != "":
                            self.message(section=dep.path, data=(recipe, package, dep))

    def fix(self, message, data) -> bool:
        (recipe, package, dep) = data
        s = dep.split(">=")
        if len(s) > 1:
            skip_selector = f" # [py<{s[1].replace('.','')}]"
            op = [
                {
                    "op": "add",
                    "path": f"{package.path_prefix}build/skip",
                    "value": f"True {skip_selector}",
                }
            ]
            return recipe.patch(op)
        return False


class no_git_on_windows(LintCheck):
    """
    git should not be used as a dependency on Windows.

    git is supplied by the cygwin environment. Installing it may break the build.
    """

    def check_deps(self, deps) -> None:
        if self.recipe.selector_dict.get("win", 0) == 1 and "git" in deps:
            for path in deps["git"]["paths"]:
                output = -1 if not path.startswith("outputs") else int(path.split("/")[1])
                self.message(section=path, output=output, data=path)

    def fix(self, message, data) -> bool:
        # NOTE: The path found in `check_deps()` is a post-selector-rendering
        # path to the dependency. So in order to change the recipe file, we need
        # to relocate `git`, relative to the raw file.
        def _add_git_selector(parser: RecipeParser) -> None:
            paths = parser.find_value("git")
            for path in paths:
                # Attempt to filter-out false-positives
                if "/requirements" not in path:
                    continue
                parser.add_selector(path, "[not win]", SelectorConflictMode.AND)

        return self.recipe.patch_with_parser(_add_git_selector)


class gui_app(LintCheck):
    """
    This may be a GUI application. It is advised to test the GUI.
    """

    guis = (
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
    )

    def check_recipe(self, recipe: Recipe) -> None:
        if set(self.guis).intersection(set(_utils.get_deps(recipe, "run"))):
            self.message(severity=Severity.INFO)
