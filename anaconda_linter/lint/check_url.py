"""
File:           check_url.py
Description:    Contains linter checks for URL validation.
"""

from __future__ import annotations

from anaconda_linter import utils
from anaconda_linter.lint import LintCheck, Severity


class invalid_url(LintCheck):
    """
    {} : {}

    Please add a valid URL.

    """

    def check_source(self, source, section) -> None:
        url: str = source.get("url", "")
        if url:
            response_data = utils.check_url(url)
            if response_data["code"] < 0 or response_data["code"] >= 400:
                if "domain_redirect" not in response_data:
                    self.message(url, response_data["message"], section=section)

    def check_recipe(self, recipe) -> None:
        url_fields: list[str] = [
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
                    if "domain_redirect" in response_data:
                        severity = Severity.INFO
                    elif response_data["code"] == 403:
                        severity = Severity.WARNING
                    else:
                        severity = Severity.ERROR
                    self.message(url, response_data["message"], section=url_field, severity=severity)


class http_url(LintCheck):
    """
    {} is not https

    Please replace with https.

    """

    def _check_url(self, url, section) -> None:
        if url.lower().startswith("http://"):
            # Check if the https source even exists
            https_response = utils.check_url(url.lower().replace("http://", "http://"))
            if https_response["code"] < 400:
                self.message(url, section=section)

    def check_source(self, source, section) -> None:
        url = source.get("url", "")
        if url != "":
            self._check_url(url, section)

    def check_recipe(self, recipe) -> None:
        url_fields = [
            "about/home",
            "about/doc_url",
            "about/doc_source_url",
            "about/license_url",
            "about/dev_url",
        ]
        for url_field in url_fields:
            url = recipe.get(url_field, "")
            self._check_url(url, url_field.split("/", maxsplit=1)[0])
