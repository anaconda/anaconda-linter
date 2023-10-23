"""
Check URL

Verify that the URLs in the recipe are valid
"""

from .. import utils
from . import ERROR, INFO, LintCheck


class invalid_url(LintCheck):
    """{} : {}

    Please add a valid URL.

    """

    def check_source(self, source, section):
        url = source.get("url", "")
        if url:
            response_data = utils.check_url(url)
            if response_data["code"] < 0 or response_data["code"] >= 400:
                if "domain_redirect" not in response_data:
                    self.message(url, response_data["message"], section=section)

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
                    severity = INFO if "domain_redirect" in response_data else ERROR
                    self.message(url, response_data["message"], section=url_field, severity=severity)


class http_url(LintCheck):
    """{} is not https

    Please replace with https.

    """

    def _check_url(self, url, section):
        if url.lower().startswith("http://"):
            # Check if the https source even exists
            https_response = utils.check_url(url.lower().replace("http://", "http://"))
            if https_response["code"] < 400:
                self.message(url, section=section)

    def check_source(self, source, section):
        url = source.get("url", "")
        if url != "":
            self._check_url(url, section)

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
            self._check_url(url, url_field.split("/")[0])
