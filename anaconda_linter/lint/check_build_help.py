"""Build tool usage

These checks catch errors relating to the use of ``-
{{compiler('xx')}}`` and ``setuptools``.

"""

import os
import re

from . import INFO, WARNING, LintCheck

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
    "flit",
    "flit-core",
    "hatch",
    "hatchling",
    "pdm",
    "pip",
    "poetry",
    "setuptools",
    "setuptools-rust",
    "setuptools_scm",
    "whey",
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


def is_pypi_source(recipe):
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


def recipe_has_patches(recipe):
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
    """Packages in host must have exact version pinnings, except python build tools.

    Specifically, comparison operators must not be used. The version numbers can be
    speficified in a conda_build_config.yaml file.
    """

    def check_recipe(self, recipe):
        deps = recipe.get_deps_dict("host")
        exceptions = (
            "python",
            "toml",
            "wheel",
            *PYTHON_BUILD_TOOLS,
        )
        for package, dep in deps.items():
            if package not in exceptions and not (
                package in recipe.selector_dict and recipe.selector_dict[package]
            ):
                for c, constraint in enumerate(dep["constraints"]):
                    if constraint == "" or re.search("^[<>!]", constraint) is not None:
                        path = dep["paths"][c]
                        output = -1 if not path.startswith("outputs") else int(path.split("/")[1])
                        self.message(section=path, output=output)


class should_use_compilers(LintCheck):
    """The recipe requires a compiler directly

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

    def check_deps(self, deps):
        for compiler in self.compilers:
            for location in deps.get(compiler, {}).get("paths", []):
                self.message(section=location)


class compilers_must_be_in_build(LintCheck):
    """The recipe requests a compiler in a section other than build

    Please move the ``{{ compiler('language') }}`` line into the
    ``requirements: build:`` section.

    """

    def check_deps(self, deps):
        for dep in deps:
            if dep.startswith("compiler_"):
                for location in deps[dep]["paths"]:
                    if "run" in location or "host" in location:
                        self.message(section=location)


class build_tools_must_be_in_build(LintCheck):
    """The build tool {} is not in the build section.

    Please add::
        requirements:
          build:
            - {}
    """

    def check_recipe(self, recipe):
        deps = recipe.get_deps_dict(["host", "run"])
        for tool, dep in deps.items():
            if tool.startswith("m2-") or tool in BUILD_TOOLS:
                for path in dep["paths"]:
                    o = -1 if not path.startswith("outputs") else int(path.split("/")[1])
                    self.message(tool, severity=WARNING, section=path, output=o)


class python_build_tool_in_run(LintCheck):
    """The python build tool {} is in run depends

    Most Python packages only need python build tools during installation.
    Check if the package really needs this build tool (e.g. because it uses
    pkg_resources or setuptools console scripts).

    """

    def check_recipe(self, recipe):
        deps = recipe.get_deps_dict("run")
        for tool in PYTHON_BUILD_TOOLS:
            if tool in deps:
                for path in deps[tool]["paths"]:
                    o = -1 if not path.startswith("outputs") else int(path.split("/")[1])
                    self.message(tool, severity=WARNING, section=path, output=o)


class missing_python_build_tool(LintCheck):
    """Python packages require a python build tool such as setuptools.

    Please add the build tool specified by the upstream package to the host section.
    """

    def check_recipe(self, recipe):
        is_pypi = is_pypi_source(recipe)
        if outputs := recipe.get("outputs", None):
            deps = recipe.get_deps_dict("host")
            for o in range(len(outputs)):
                # Create a list of build tool dependencies for each output
                tools = []
                for tool, dep in deps.items():
                    if tool in PYTHON_BUILD_TOOLS and any(
                        path.startswith(f"outputs/{o}") for path in dep["paths"]
                    ):
                        tools.append(tool)
                if (is_pypi or "pip install" in recipe.get(f"outputs/{o}/script", "")) and len(
                    tools
                ) == 0:
                    self.message(section=f"outputs/{o}/requirements/host", output=o)
        elif is_pypi or "pip install" in recipe.get("build/script", ""):
            deps = recipe.get_deps("host")
            if not any(tool in deps for tool in PYTHON_BUILD_TOOLS):
                self.message(section="requirements/host")


class missing_wheel(LintCheck):
    """For pypi packages, wheel should be present in the host section

    Add wheel to requirements/host:

      requirements:
        host:
          - wheel
    """

    def check_recipe(self, recipe):
        # similar algorithm as missing_python
        is_pypi = is_pypi_source(recipe)
        deps = recipe.get_deps_dict("host")
        paths = (
            []
            if "wheel" not in deps
            else ["/".join(path.split("/")[:-1]) for path in deps["wheel"]["paths"]]
        )
        if outputs := recipe.get("outputs", None):
            for o in range(len(outputs)):
                if is_pypi or "pip install" in recipe.get(f"outputs/{o}/script", ""):
                    if f"outputs/{o}/requirements/host" not in paths:
                        self.message(section=f"outputs/{o}/requirements/host", output=o)
        elif is_pypi or "pip install" in recipe.get("build/script", ""):
            if "requirements/host" not in paths:
                self.message(section="requirements/host")


class uses_setup_py(LintCheck):
    """`python setup.py install` is deprecated.

    Please use::

        $PYTHON -m pip install . --no-deps

    Or use another python build tool.
    """

    @staticmethod
    def _check_line(line: str) -> bool:
        """Check a line for a broken call to setup.py"""
        if "setup.py install" in line:
            return False
        return True

    def check_deps(self, deps):
        if "setuptools" not in deps:
            return  # no setuptools, no problem

        for path in deps["setuptools"]["paths"]:
            if path.startswith("output"):
                n = path.split("/")[1]
                script = f"outputs/{n}/script"
                output = int(n)
            else:
                script = "build/script"
                output = -1
            if not self._check_line(self.recipe.get(script, "")):
                self.message(section=script)
                continue
            try:
                if script == "build/script":
                    build_file = "build.sh"
                else:
                    build_file = self.recipe.get(script)
                with open(os.path.join(self.recipe.dir, build_file)) as buildsh:
                    for num, line in enumerate(buildsh):
                        if not self._check_line(line):
                            self.message(fname=build_file, line=num, output=output)
            except FileNotFoundError:
                pass


class pip_install_args(LintCheck):
    """`pip install` should be run with --no-deps.

    Please use::

        $PYTHON -m pip install . --no-deps

    """

    @staticmethod
    def _check_line(line: str) -> bool:
        """Check a line for a broken call to setup.py"""
        if "pip install" in line and "--no-deps" not in line:
            return False
        return True

    def check_deps(self, deps):
        if "pip" not in deps:
            return  # no pip, no problem

        for path in deps["pip"]["paths"]:
            if path.startswith("output"):
                n = path.split("/")[1]
                script = f"outputs/{n}/script"
                output = int(n)
            else:
                script = "build/script"
                output = -1
            if not self._check_line(self.recipe.get(script, "")):
                self.message(section=script)
                continue
            try:
                if script == "build/script":
                    build_file = "build.sh"
                else:
                    build_file = self.recipe.get(script)
                with open(os.path.join(self.recipe.dir, build_file)) as buildsh:
                    for num, line in enumerate(buildsh):
                        if not self._check_line(line):
                            self.message(fname=build_file, line=num, output=output)
            except FileNotFoundError:
                pass


class cython_must_be_in_host(LintCheck):
    """Cython should be in the host section

    Move cython to ``host``::

      requirements:
        host:
          - cython
    """

    def check_deps(self, deps):
        if "cython" in deps:
            for location in deps["cython"]["paths"]:
                if "/host" not in location:
                    self.message(section=location)


class cython_needs_compiler(LintCheck):
    """Cython generates C code, which will need to be compiled

    Add the compiler to the recipe::

      requirements:
        build:
          - {{ compiler('c') }}

    """

    def check_deps(self, deps):
        if "cython" in deps:
            for location in deps["cython"]["paths"]:
                if location.startswith("outputs"):
                    n = location.split("/")[1]
                    section = f"outputs/{n}/requirements/build"
                    output = int(n)
                else:
                    section = "requirements/build"
                    output = -1
                if "compiler_c" not in self.recipe.get(section):
                    self.message(section=section, output=output)


class avoid_noarch(LintCheck):
    """noarch: python packages should be avoided

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

    def check_recipe(self, recipe):
        noarch = recipe.get("build/noarch", "")
        if (
            noarch == "python"
            and recipe.get("build/number", 0) == 0
            and not recipe.get("build/osx_is_app", False)
            and not recipe.get("app", None)
        ):
            self.message(section="build", severity=WARNING)


class patch_unnecessary(LintCheck):
    """patch should not be in build when source/patches is not set

    Remove patch/m2-patch from ``build``
    """

    def check_recipe(self, recipe):
        if not recipe_has_patches(recipe):
            deps = recipe.get_deps_dict()
            if "patch" in deps or "m2-patch" in deps:
                self.message(section="build")


class patch_must_be_in_build(LintCheck):
    """patch must be in build when source/patches is set.

    Add patch to ``build``::

      requirements:
        build:
          - patch       # [not win]
          - m2-patch    # [win]
    """

    def check_recipe(self, recipe):
        if recipe_has_patches(recipe):
            deps = recipe.get_deps_dict()
            if "patch" in deps:
                if any("build" not in location for location in deps["patch"]["paths"]):
                    self.message(section="requirements/build")
            elif "m2-patch" in deps:
                if any("build" not in location for location in deps["m2-patch"]["paths"]):
                    self.message(section="requirements/build")
            else:
                self.message(section="requirements/build")


class has_run_test_and_commands(LintCheck):
    """Test commands are not executed when run_test.sh (.bat...) is present.

    Add the test commands to run_test.sh/.bat/.pl
    """

    def check_recipe(self, recipe):
        if outputs := recipe.get("outputs", None):
            for o in range(len(outputs)):
                test_section = f"outputs/{o}/test"
                if recipe.get(f"{test_section}/script", None) and recipe.get(
                    f"{test_section}/commands", None
                ):
                    self.message(section=f"{test_section}/commands", output=o)
        else:
            if recipe.get("test/commands", []) and (
                recipe.get("test/script", None)
                or set(os.listdir(recipe.dir)).intersection(
                    {"run_test.sh", "run_test.pl", "run_test.bat"}
                )
            ):
                self.message(section="test/commands")


class has_imports_and_run_test_py(LintCheck):
    """Imports and python test file cannot coexist.

    Add the imports to the python test file.
    """

    def check_recipe(self, recipe):
        if outputs := recipe.get("outputs", None):
            for o in range(len(outputs)):
                test_section = f"outputs/{o}/test"
                if recipe.get(f"{test_section}/imports", []) and recipe.get(
                    f"{test_section}/script", ""
                ).endswith(".py"):
                    self.message(section=f"{test_section}/imports", output=o)
        else:
            if recipe.get("test/imports", []) and os.path.isfile(
                os.path.join(recipe.dir, "run_test.py")
            ):
                self.message(section="test/imports")


class missing_imports_or_run_test_py(LintCheck):
    """Python packages require imports or a python test file in tests.

    Add::
        test:
          imports:
            - <module>

    Or add a run_test.py file into the recipe directory.

    For multi-ouput recipes, add imports or a python test file for each output::
        test:
          script: <test file>
    """

    def check_recipe(self, recipe):
        is_pypi = is_pypi_source(recipe)
        deps = recipe.get_deps_dict("host")
        if not is_pypi and "python" not in deps:
            return
        if outputs := recipe.get("outputs", None):
            paths_to_check = []
            if is_pypi:
                paths_to_check = [f"outputs/{o}" for o in range(len(outputs))]
            else:
                paths_to_check = ["/".join(path.split("/")[:2]) for path in deps["python"]["paths"]]
            for path in paths_to_check:
                if not recipe.get(f"{path}/test/imports", []) and not recipe.get(
                    f"{path}/test/script", ""
                ):
                    o = int(path.split("/")[1])
                    self.message(section=f"{path}/test", output=o)
        elif (
            (is_pypi or "python" in deps)
            and not recipe.get("test/imports", [])
            and not os.path.isfile(os.path.join(recipe.dir, "run_test.py"))
        ):
            self.message(section="test")


class missing_pip_check(LintCheck):
    """For pypi packages, pip check should be present in the test commands

    Add pip check to test/commands:

      tests:
        commands:
          - pip check
    """

    def _check_file(self, file, output=-1):
        """Reads the file for a `pip check` command and outputs a message if not found.

        Args:
          file: The path of the file.
          output: The output number for multi-output recipes.
        """
        if os.path.isfile(file):
            with open(file) as test_file:
                for line in test_file:
                    if "pip check" in line:
                        return
        self.message(fname=file, output=output)

    def check_recipe(self, recipe):
        is_pypi = is_pypi_source(recipe)
        if outputs := recipe.get("outputs", None):
            for o in range(len(outputs)):
                if not is_pypi and "pip install" not in recipe.get(f"outputs/{o}/script", ""):
                    continue
                test_section = f"outputs/{o}/test"
                if commands := recipe.get(f"{test_section}/commands", None):
                    if not any("pip check" in cmd for cmd in commands):
                        self.message(section=f"{test_section}/commands", output=o)
                elif script := recipe.get(f"{test_section}/script", None):
                    self._check_file(os.path.join(recipe.dir, script))
                else:
                    self.message(section=test_section, output=o)
        elif is_pypi or "pip install" in recipe.get("build/script", ""):
            if commands := recipe.get("test/commands", None):
                if not any("pip check" in cmd for cmd in commands):
                    self.message(section="test/commands")
            else:
                test_files = (
                    set(os.listdir(recipe.dir)).intersection({"run_test.sh", "run_test.bat"})
                    if os.path.exists(recipe.dir)
                    else set()
                )
                if len(test_files) > 0:
                    for file in test_files:
                        self._check_file(os.path.join(recipe.dir, file))
                else:
                    self.message(section="test")


class missing_test_requirement_pip(LintCheck):
    """pip is required in the test requirements.

    Please add::
        test:
          requires:
            - pip
    """

    def _check_file(self, file):
        if not os.path.isfile(file):
            return False
        with open(file) as test_file:
            for line in test_file:
                if "pip check" in line:
                    return True
        return False

    def _has_pip_check(self, recipe, output=""):
        test_section = f"{output}test"
        if commands := recipe.get(f"{test_section}/commands", None):
            if any("pip check" in cmd for cmd in commands):
                return True
        elif output.startswith("outputs"):
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

    def check_recipe(self, recipe):
        if outputs := recipe.get("outputs", None):
            for o in range(len(outputs)):
                if self._has_pip_check(recipe, output=f"outputs/{o}/") and "pip" not in recipe.get(
                    f"outputs/{o}/test/requires", []
                ):
                    self.message(section=f"outputs/{o}/test/requires/", output=o)
        elif self._has_pip_check(recipe) and "pip" not in recipe.get("test/requires", []):
            self.message(section="test/requires")


class missing_python(LintCheck):
    """For pypi packages, python should be present in the host and run sections. Missing in {}

    Add python:

      requirements:
        host:
          - python
        run:
          - python
    """

    def check_recipe(self, recipe):
        # To check for a missing python, find the paths that require python
        # and compare with the existing dependency dictionary.
        # Since this dictionary has everything parsed already, there is no need for regex.
        is_pypi = is_pypi_source(recipe)
        deps = recipe.get_deps_dict(["host", "run"])
        # The `paths` dictionary stores dependencies as, e.g., `requirements/host/{n}/`
        # with the list index n. For multi-output recipes, it the paths are of the form
        # `outputs/{o}/requirements/host/{n}`. To compare, the list index needs to be stripped.
        paths = (
            []
            if "python" not in deps
            else ["/".join(path.split("/")[:-1]) for path in deps["python"]["paths"]]
        )
        if outputs := recipe.get("outputs", None):
            for o in range(len(outputs)):
                if is_pypi or "pip install" in recipe.get(f"outputs/{o}/script", ""):
                    for section in ["host", "run"]:
                        path_to_section = f"outputs/{o}/requirements/{section}"
                        if path_to_section not in paths:
                            self.message(section, section=path_to_section, output=o)
        elif is_pypi or "pip install" in recipe.get("build/script", ""):
            for section in ["host", "run"]:
                path_to_section = f"requirements/{section}"
                if path_to_section not in paths:
                    self.message(section, section=path_to_section)


class remove_python_pinning(LintCheck):
    """On arch specific packages, python deps should not be constrained.

    Replace python constraints by a skip directive:

      build:
        skip: True # [py<38]

      requirements:
        host:
          - python
        run:
          - python
    """

    def check_recipe(self, recipe):
        if recipe.get("build/noarch", "") == "":
            sections = ["host", "run"]
            deps = recipe.get_deps_dict(sections=sections)
            if "python" in deps:
                for c, constraint in enumerate(deps["python"]["constraints"]):
                    if constraint != "":
                        path = deps["python"]["paths"][c]
                        output = -1 if not path.startswith("outputs") else int(path.split("/")[1])
                        self.message(section=path, output=output)


class gui_app(LintCheck):
    """This may be a GUI application. It is advised to test the GUI."""

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

    def check_recipe(self, recipe):
        if set(self.guis).intersection(set(recipe.get_deps("run"))):
            self.message(severity=INFO)
