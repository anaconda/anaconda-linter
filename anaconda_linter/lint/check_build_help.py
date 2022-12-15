"""Build tool usage

These checks catch errors relating to the use of ``-
{{compiler('xx')}}`` and ``setuptools``.

"""

import os

from . import INFO, WARNING, LintCheck


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


class uses_setuptools(LintCheck):
    """The recipe uses setuptools in run depends

    Most Python packages only need setuptools during installation.
    Check if the package really needs setuptools (e.g. because it uses
    pkg_resources or setuptools console scripts).

    """

    def check_recipe(self, recipe):
        deps = recipe.get_deps_dict("run")
        if "setuptools" in deps:
            for path in deps["setuptools"]["paths"]:
                self.message(severity=WARNING, section=path)


class missing_wheel(LintCheck):
    """For pypi packages, wheel should be present in the host section

    Add wheel to requirements/host:

      requirements:
        host:
          - wheel
    """

    def check_recipe(self, recipe):
        is_pypi = is_pypi_source(recipe)
        if is_pypi or "pip install" in recipe.get("build/script", ""):
            if "wheel" not in recipe.get("requirements/host", []):
                self.message(section="requirements/host")
        if outputs := recipe.get("outputs", None):
            for o in range(len(outputs)):
                if is_pypi or "pip install" in recipe.get(f"outputs/{o}/script", ""):
                    if "wheel" not in recipe.get(f"outputs/{o}/requirements/host", []):
                        self.message(section=f"outputs/{o}/requirements/host", output=o)


class setup_py_install_args(LintCheck):
    """The recipe uses setuptools without required arguments

    Please use::

        $PYTHON setup.py install --single-version-externally-managed --record=record.txt

    The parameters are required to avoid ``setuptools`` trying (and
    failing) to install ``certifi`` when a package this recipe
    requires defines entrypoints in its ``setup.py``.

    """

    @staticmethod
    def _check_line(line: str) -> bool:
        """Check a line for a broken call to setup.py"""
        if "setup.py install" not in line:
            return True
        if "--single-version-externally-managed" in line:
            return True
        return False

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
                            self.message(fname="build.sh", line=num, output=output)
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
        if noarch == "python":
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

    Remove ``test/commands`` or call ``run_test`` from ``test/commands``:

      tests:
        commands:
          - run_test.sh    # [unix]
          - run_test.bat   # [win]

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
                or set(os.listdir(recipe.recipe_dir)).intersection(
                    {"run_test.sh", "run_test.py", "run_test.bat"}
                )
            ):
                self.message(section="test/commands")


class missing_pip_check(LintCheck):
    """For pypi packages, pip check should be present in the test commands

    Add pip check to test/commands:

      tests:
        commands:
          - pip check
    """

    def _check_file(self, file, output=-1):
        with open(file) as test_file:
            for line in test_file:
                if "pip check" in line:
                    return
            self.message(fname=file, output=output)

    def check_output(self, recipe, output="") -> bool:
        # The return value indicates if a test was found
        test_section = f"{output}test"
        o = -1 if not output.startswith("outputs") else int(output.split("/")[1])
        if commands := recipe.get(f"{test_section}/commands", None):
            if not any("pip check" in cmd for cmd in commands):
                self.message(section=f"{test_section}/commands", output=o)
            return True
        elif script := recipe.get(f"{test_section}/script", None):
            test_file = os.path.join(recipe.dir, script)
            if os.path.exists(test_file):
                self._check_file(test_file)
            else:
                self.message(fname=test_file, output=o)
            return True
        return False

    def check_recipe(self, recipe):
        is_pypi = is_pypi_source(recipe)
        if outputs := recipe.get("outputs", None):
            for o in range(len(outputs)):
                if not is_pypi and "pip install" not in recipe.get(f"outputs/{o}/script", ""):
                    continue
                if not self.check_output(recipe, f"outputs/{o}/"):
                    self.message(section=f"outputs/{o}/test", output=o)
        elif is_pypi or "pip install" in self.recipe.get("build/script", ""):
            if not self.check_output(recipe):
                test_files = (
                    set(os.listdir(recipe.recipe_dir)).intersection({"run_test.sh", "run_test.bat"})
                    if os.path.exists(recipe.dir)
                    else set()
                )
                if len(test_files) > 0:
                    for file in test_files:
                        self._check_file(os.path.join(recipe.dir, file))
                else:
                    self.message(section="test")


class missing_python(LintCheck):
    """For pypi packages, python should be present in the host and run sections. Missing in {}

    Add python:

      requirements:
        host:
          - python
        run:
          - python
    """

    def _create_message(self, section, output=-1):
        reset_text = self.__class__.__doc__
        self.__class__.__doc__ = self.__class__.__doc__.format(section)
        self.message(section=section, output=output)
        self.__class__.__doc__ = reset_text

    def check_recipe(self, recipe):
        is_pypi = is_pypi_source(recipe)
        deps = recipe.get_deps_dict(["host", "run"])
        paths = (
            []
            if "python" not in deps
            else ["/".join(path.split("/")[:-1]) for path in deps["python"]["paths"]]
        )
        if outputs := recipe.get("outputs", None):
            for o in range(len(outputs)):
                if is_pypi or "pip install" in self.recipe.get(f"outputs/{o}/script", ""):
                    for section in ["host", "run"]:
                        path_to_section = f"outputs/{o}/requirements/{section}"
                        if path_to_section not in paths:
                            self._create_message(section=path_to_section, output=o)
        elif is_pypi or "pip install" in self.recipe.get("build/script", ""):
            for section in ["host", "run"]:
                path_to_section = f"requirements/{section}"
                if path_to_section not in paths:
                    self._create_message(section=path_to_section)


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
