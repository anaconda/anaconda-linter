"""Completeness

Verify that the recipe is not missing anything essential.
"""

import os

import conda_build.license_family

# from . import ERROR, INFO
from . import WARNING, LintCheck


class missing_section(LintCheck):
    """The {} section is missing.

    Please add this section to the recipe or output
    """

    def check_recipe(self, recipe):
        global_sections = (
            "package",
            "build",
            "about",
        )
        output_sections = ("requirements",)
        for section in global_sections:
            if not recipe.get(section, None):
                self.message(section)
        if outputs := recipe.get("outputs", None):
            for o in range(len(outputs)):
                for section in output_sections:
                    if not recipe.get(f"outputs/{o}/{section}", None):
                        self.message(section, output=o)
        else:
            for section in output_sections:
                if not recipe.get(section, None):
                    self.message(section)


class missing_build_number(LintCheck):
    """The recipe is missing a build number

    Please add::

        build:
            number: 0
    """

    def check_recipe(self, recipe):
        if not recipe.get("build/number", ""):
            self.message(section="build")


class missing_package_name(LintCheck):
    """The recipe is missing a package name

    Please add::

        package:
            name: <package name>
    """

    def check_recipe(self, recipe):
        if not recipe.get("package/name", ""):
            self.message(section="package")


class missing_package_version(LintCheck):
    """The recipe is missing a package version

    Please add::

        package:
            version: <package version>
    """

    def check_recipe(self, recipe):
        if not recipe.get("package/version", ""):
            self.message(section="package")


class missing_home(LintCheck):
    """The recipe is missing a homepage URL

    Please add::

       about:
          home: <URL to homepage>

    """

    def check_recipe(self, recipe):
        if not recipe.get("about/home", ""):
            self.message(section="about")


class missing_summary(LintCheck):
    """The recipe is missing a summary

    Please add::

       about:
         summary: One line briefly describing package

    """

    def check_recipe(self, recipe):
        if not recipe.get("about/summary", ""):
            self.message(section="about")


class missing_license(LintCheck):
    """The recipe is missing the ``about/license`` key.

    Please add::

        about:
           license: <name of license>

    """

    def check_recipe(self, recipe):
        if not recipe.get("about/license", ""):
            self.message(section="about")


class missing_license_file(LintCheck):
    """The recipe is missing the ``about/license_file`` or ``about/license_url`` key.

    Please add::

        about:
           license_file: <license file name>

    or::

        about:
           license_file:
                - <license file name>
                - <license file name>

    or::
        about:
           license_url: <license url>

    """

    def check_recipe(self, recipe):
        if not recipe.get("about/license_file", "") and not recipe.get("about/license_url", ""):
            self.message(section="about", severity=WARNING)


class license_file_overspecified(LintCheck):
    """Using license_file and license_url is overspecified.

    Please remove license_url.
    """

    def check_recipe(self, recipe):
        if recipe.get("about/license_file", "") and recipe.get("about/license_url", ""):
            self.message(section="about", severity=WARNING)


class missing_license_family(LintCheck):
    """The recipe is missing the ``about/license_family`` key.

    Please add::

        about:
           license_family: <license_family>

    """

    def check_recipe(self, recipe):
        if not recipe.get("about/license_family", ""):
            self.message(section="about")


class invalid_license_family(LintCheck):
    """The recipe has an incorrect ``about/license_family`` value.

    Please change::

        about:
           license_family: <license_family>

    """

    def check_recipe(self, recipe):
        license_family = recipe.get("about/license_family", "")
        if license_family and not license_family.lower() in [
            x.lower() for x in conda_build.license_family.allowed_license_families
        ]:
            self.message(section="about")


class missing_tests(LintCheck):
    """No tests were found.

    Please add::

        test:
            commands:
               - some_command

    and/or::

        test:
            imports:
               - some_module


    and/or any file named ``run_test.py`, ``run_test.sh`` or
    ``run_test.pl`` executing tests.

    For multi-output recipes, add:

      test:
        script: <test file>

    to each output

    """

    test_files = ["run_test.py", "run_test.sh", "run_test.pl"]

    def check_output(self, recipe, output=""):
        test_section = f"{output}test"
        if recipe.get(f"{test_section}/commands", "") or recipe.get(f"{test_section}/imports", ""):
            return
        o = -1 if not test_section.startswith("outputs") else int(test_section.split("/")[1])
        if recipe.get(f"{test_section}", False) is not False:
            self.message(section=test_section, output=o)
        else:
            self.message(section=output, output=o)

    def check_recipe(self, recipe):
        if outputs := recipe.get("outputs", None):
            for o in range(len(outputs)):
                if not recipe.get(f"outputs/{o}/test/script", ""):
                    self.check_output(recipe, f"outputs/{o}/")
        # multi-output recipes do not execute test files automatically
        elif not (
            recipe.dir and any(os.path.exists(os.path.join(recipe.dir, f)) for f in self.test_files)
        ):
            self.check_output(recipe)


class missing_hash(LintCheck):
    """The recipe is missing a sha256 checksum for a source file

    Please add::

       source:
         sha256: checksum-value

    Note: md5 and sha1 are deprecated.

    """

    checksum_names = ["sha256"]

    exempt_types = ["git_url", "path"]

    def check_source(self, source, section):
        if not any(source.get(typ, None) for typ in self.exempt_types) and not any(
            source.get(chk, None) for chk in self.checksum_names
        ):
            self.message(section=section)


class missing_source(LintCheck):
    """The recipe is missing a URL for the source

    Please add::

        source:
            url: <URL to source>

    Or::
        source:
            - url: <URL to source>

    """

    source_types = ["url", "git_url", "hg_url", "svn_url", "path"]

    def check_source(self, source, section):
        if not any(source.get(chk, None) for chk in self.source_types):
            self.message(section=section)


class non_url_source(LintCheck):
    """A source of the recipe is not a valid type. Allowed types are url, git_url, and path.

    Please change to::

        source:
            url: <URL to source>

    """

    source_types = ["hg_url", "svn_url"]

    def check_source(self, source, section):
        if any(source.get(chk, None) for chk in self.source_types):
            self.message(section=section, severity=WARNING)


class missing_documentation(LintCheck):
    """The recipe is missing a doc_url or doc_source_url

    Please add::

        about:
            doc_url: some_documentation_url

    Or::

        about:
            doc_source_url: some-documentation-source-url

    """

    def check_recipe(self, recipe):
        if not recipe.get("about/doc_url", "") and not recipe.get("about/doc_source_url", ""):
            self.message(section="about")


class documentation_overspecified(LintCheck):
    """Using doc_url and doc_source_url is overspecified

    Please remove doc_source_url.

    """

    def check_recipe(self, recipe):
        if recipe.get("about/doc_url", "") and recipe.get("about/doc_source_url", ""):
            self.message(section="about", severity=WARNING)


class missing_dev_url(LintCheck):
    """The recipe is missing a dev_url

    Please add::

        about:
            dev_url: some-dev-url

    """

    def check_recipe(self, recipe):
        if not recipe.get("about/dev_url", ""):
            self.message(section="about")


class missing_description(LintCheck):
    """The recipe is missing a description

    Please add::

        about:
            description: some-description

    """

    def check_recipe(self, recipe):
        if not recipe.get("about/description", ""):
            self.message(section="about", severity=WARNING)
