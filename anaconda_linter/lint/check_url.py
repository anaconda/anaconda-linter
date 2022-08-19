"""
Check URL

Verify that the URLs in the recipe are valid
"""

from utils import check_url

from . import WARNING, LintCheck


class invalid_url(LintCheck):
    """{} : {}

    Please add a valid URL.

    """

    def check_source(self, source, section):
        url = source.get("url", "")
        if url:
            response_data = check_url(url)
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
                response_data = check_url(url)
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
