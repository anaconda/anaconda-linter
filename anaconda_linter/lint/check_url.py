"""
Check URL

Verify that the URLs in the recipe are valid
"""

from utils import check_url

from . import LintCheck


class invalid_source_url(LintCheck):
    """The license_url is not valid.

    Please add a valid URL.

    """

    def check_recipe(self, recipe):
        url = recipe.get("source/url", "")
        if url:
            response_data = check_url(url)
            if response_data["code"] < 0 or response_data["code"] >= 400:
                self.__class__.__doc__ += "HINT: {}".format(response_data["message"])
                self.message(section="source")


class invalid_home(LintCheck):
    """The home URL is not valid.

    Please add a valid URL.

    """

    def check_recipe(self, recipe):
        url = recipe.get("about/home", "")
        if url:
            response_data = check_url(url)
            if response_data["code"] < 0 or response_data["code"] >= 400:
                self.__class__.__doc__ += "HINT: {}".format(response_data["message"])
                self.message(section="about")


class invalid_doc_url(LintCheck):
    """The doc_url is not valid.

    Please add a valid URL.

    """

    def check_recipe(self, recipe):
        url = recipe.get("about/doc_url", "")
        if url:
            response_data = check_url(url)
            if response_data["code"] < 0 or response_data["code"] >= 400:
                self.__class__.__doc__ += "HINT: {}".format(response_data["message"])
                self.message(section="about")


class invalid_doc_source_url(LintCheck):
    """The doc_source_url is not valid.

    Please add a valid URL.

    """

    def check_recipe(self, recipe):
        url = recipe.get("about/doc_source_url", "")
        if url:
            response_data = check_url(url)
            if response_data["code"] < 0 or response_data["code"] >= 400:
                self.__class__.__doc__ += "HINT: {}".format(response_data["message"])
                self.message(section="about")


class invalid_dev_url(LintCheck):
    """The dev_url is not valid.

    Please add a valid URL.

    """

    def check_recipe(self, recipe):
        url = recipe.get("about/dev_url", "")
        if url:
            response_data = check_url(url)
            if response_data["code"] < 0 or response_data["code"] >= 400:
                self.__class__.__doc__ += "HINT: {}".format(response_data["message"])
                self.message(section="about")


class invalid_license_url(LintCheck):
    """The license_url is not valid.

    Please add a valid URL.

    """

    def check_recipe(self, recipe):
        url = recipe.get("about/license_url", "")
        if url:
            response_data = check_url(url)
            if response_data["code"] < 0 or response_data["code"] >= 400:
                self.__class__.__doc__ += "HINT: {}".format(response_data["message"])
                self.message(section="about")
