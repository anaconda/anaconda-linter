"""
Check URL

Verify that the URLs in the recipe are valid
"""

from .. import utils
from . import WARNING, LintCheck


class invalid_url(LintCheck):
    """{} : {}

    Please add a valid URL.

    """

    def check_source(self, source, section):
        url = source.get("url", "")
        if url:
            response_data = utils.check_url(url)
            acceptable_redirects = [
                ("pypi.io", "pypi.org"),
                ("github.com", "objects.githubusercontent.com"),
            ]
            if response_data["code"] < 0 and "domain_redirect" in response_data:
                for redir in acceptable_redirects:
                    if (
                        response_data["domain_origin"] == redir[0]
                        and response_data["domain_redirect"] == redir[1]
                    ):
                        return
            if response_data["code"] < 0 or response_data["code"] >= 400:
                self.__class__.__doc__ = self.__class__.__doc__.format(
                    url, response_data["message"]
                )
                self.message(section=section)

    def check_recipe(self, recipe):
        url_fields = [
            "about/home",
            "about/doc_url",
            "about/doc_source_url",
            "about/license_url",
            "about/dev_url",
        ]
        for url_field in url_fields:
            url = recipe.get(url_field, "")
            if url:
                response_data = utils.check_url(url)
                if response_data["code"] < 0 or response_data["code"] >= 400:
                    self.__class__.__doc__ = self.__class__.__doc__.format(
                        url, response_data["message"]
                    )
                    self.message(section=url_field)


class http_url(LintCheck):
    """{} is not https

    Please replace with https if possible.

    """

    severity = WARNING

    def check_source(self, source, section):
        url = source.get("url", "")
        if url.lower().startswith("http://"):
            self.__class__.__doc__ = self.__class__.__doc__.format(url)
            self.message(section=section)

    def check_recipe(self, recipe):
        url_fields = [
            "about/home",
            "about/doc_url",
            "about/doc_source_url",
            "about/license_url",
            "about/dev_url",
        ]
        for url_field in url_fields:
            url = recipe.get(url_field, "")
            if url.lower().startswith("http://"):
                self.__class__.__doc__ = self.__class__.__doc__.format(url)
                self.message(section=url_field.split("/")[0])
