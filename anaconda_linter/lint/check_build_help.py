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

    severity = WARNING

    def check_recipe(self, recipe):
        if "setuptools" in recipe.get_deps("run"):
            self.message()


class missing_wheel(LintCheck):
    """For pypi packages, wheel should be present in the host section

    Add wheel to requirements/host:

      requirements:
        host:
          - wheel
    """

    def check_recipe(self, recipe):

        if is_pypi_source(recipe) or "pip install" in self.recipe.get("build/script", ""):
            if "wheel" not in recipe.get_deps("host"):
                self.message(section="requirements/host")


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

        if not self._check_line(self.recipe.get("build/script", "")):
            self.message(section="build/script")

        try:
            with open(os.path.join(self.recipe.dir, "build.sh")) as buildsh:
                for num, line in enumerate(buildsh):
                    if not self._check_line(line):
                        self.message(fname="build.sh", line=num)
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
            if any("host" not in location for location in deps["cython"]["paths"]):
                self.message()


class cython_needs_compiler(LintCheck):
    """Cython generates C code, which will need to be compiled

    Add the compiler to the recipe::

      requirements:
        build:
          - {{ compiler('c') }}

    """

    def check_deps(self, deps):
        if "cython" in deps and "compiler_c" not in deps:
            self.message()


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

    severity = WARNING

    def check_recipe(self, recipe):
        noarch = recipe.get("build/noarch", "")
        if noarch == "python":
            self.message(section="build")


class patch_must_be_in_build(LintCheck):
    """patch must be in build when source/patches is set.

    Add patch to ``build``::

      requirements:
        build:
          - patch       # [not win]
          - m2-patch    # [win]
    """

    has_patches = False

    def check_source(self, source, section):
        if source.get("patches", ""):
            self.has_patches = True

    def check_deps(self, deps):
        if self.has_patches:
            if "patch" in deps:
                if any("build" not in location for location in deps["patch"]["paths"]):
                    self.message(section="build")
            elif "m2-patch" in deps:
                if any("build" not in location for location in deps["m2-patch"]["paths"]):
                    self.message(section="build")
            else:
                self.message(section="build")


class has_run_test_and_commands(LintCheck):
    """Test commands are not executed when run_test.sh (.bat...) is present.

    Remove ``test/commands`` or call ``run_test`` from ``test/commands``:

      tests:
        commands:
          - run_test.sh    # [unix]
          - run_test.bat   # [win]

    """

    def check_recipe(self, recipe):
        if recipe.get("test/commands", []) and set(os.listdir(recipe.recipe_dir)).intersection(
            {"run_test.sh", "run_test.py", "run_test.bat"}
        ):
            self.message(section="test/commands")


class missing_pip_check(LintCheck):
    """For pypi packages, pip check should be present in the test commands

    Add pip check to test/commands:

      tests:
        commands:
          - pip check
    """

    def check_recipe(self, recipe):

        if is_pypi_source(recipe) or "pip install" in self.recipe.get("build/script", ""):
            if not any("pip check" in cmd for cmd in recipe.get("test/commands", [])):
                self.message(section="test/commands")


class missing_python(LintCheck):
    """For pypi packages, python should be present in the host and run sections

    Add python:

      requirements:
        host:
          - python
        run:
          - python
    """

    def check_recipe(self, recipe):

        if is_pypi_source(recipe) or "pip install" in self.recipe.get("build/script", ""):
            if "python" not in recipe.get_deps("host"):
                self.message(section="requirements/host")
            if "python" not in recipe.get_deps("run"):
                self.message(section="requirements/run")


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
            if (
                "python" in recipe.get_deps("host")
                and recipe.get_deps_dict("host")["python"]["constraints"] != []
            ):
                self.message(section=recipe.get_deps_dict("host")["python"]["paths"][0])
            if (
                "python" in recipe.get_deps("run")
                and recipe.get_deps_dict("run")["python"]["constraints"] != []
            ):
                self.message(section=recipe.get_deps_dict("run")["python"]["paths"][0])


class gui_app(LintCheck):
    """This may be a GUI application. It is advised to test the GUI."""

    severity = INFO

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
            self.message()
