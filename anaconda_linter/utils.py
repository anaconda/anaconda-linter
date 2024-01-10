"""
File:           utils.py
Description:    Utility Functions and Classes
                This module collects small pieces of code used throughout
                :py:mod:`anaconda_linter`.
"""
from __future__ import annotations

import logging
import os
import re
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Final, Optional, Sequence

import requests
from jsonschema import validate
from percy.render.recipe import Recipe
from ruamel.yaml import YAML

HTTP_TIMEOUT: Final[int] = 120

logger = logging.getLogger(__name__)


yaml = YAML(typ="safe")  # pylint: disable=invalid-name

# Shared URL Cache
URLData = dict[str, str | int]
URLCache = dict[str, URLData]
check_url_cache: URLCache = {}


# TODO: Confirm this is correct
# Represents a recipe's "config" or "cbc.yaml" file
RecipeConfigType = dict[str, str | list[str]]


def validate_config(path: str) -> None:
    """
    Validate config against schema
    :param path: Path to the configuration file to validate
    :raises ValidationError: If the configuration file does not match the expected schema.
    """
    with open(path, encoding="utf-8") as conf:
        config = yaml.load(conf.read())
        fn = os.path.abspath(os.path.dirname(__file__)) + "/config.schema.yaml"
        with open(fn, encoding="utf-8") as f:
            schema = yaml.load(f.read())
            validate(config, schema)


# TODO determine type of "value"
def load_config(path: str) -> RecipeConfigType:
    """
    Parses config file, building paths to relevant block-lists.
    TODO Future: determine if this config file is necessary and if we can just get away with constants in this file
    instead.
    :param path: Path to the configuration file to validate
    :raises ValidationError: If the configuration file does not match the expected schema.
    """
    validate_config(path)

    def relpath(p: str) -> str:
        return os.path.join(os.path.dirname(path), p)

    with open(path, encoding="utf-8") as conf:
        config = yaml.load(conf.read())

    def get_list(key: str) -> list:
        # always return empty list, also if NoneType is defined in yaml
        value = config.get(key)
        if value is None:
            return []
        return value

    default_config = {"blocklists": [], "channels": ["defaults"], "requirements": None}
    if "blocklists" in config:
        config["blocklists"] = [relpath(p) for p in get_list("blocklists")]
    if "channels" in config:
        config["channels"] = get_list("channels")

    default_config.update(config)

    # store architecture information
    with open(Path(__file__).parent / "data" / "cbc_default.yaml", encoding="utf-8") as text:
        init_arch = yaml.load(text.read())
        data_path = Path(__file__).parent / "data"
        for arch_config_path in data_path.glob("cbc_*.yaml"):
            arch = arch_config_path.stem.split("cbc_")[1]
            if arch != "default":
                with open(arch_config_path, encoding="utf-8") as text:
                    default_config[arch] = deepcopy(init_arch)
                    default_config[arch].update(yaml.load(text.read()))

    return default_config


def check_url(url: str) -> URLData:
    """
    Validate a URL to see if a response is available

    Parameters
    ----------
    url: str
        URL to validate

    Return
    ------
    response_data: dict
        Limited set of response data
    """

    if url not in check_url_cache:
        response_data: dict[str, str | int] = {"url": url}
        try:
            response = requests.head(url, allow_redirects=False, timeout=HTTP_TIMEOUT)
            if response.status_code >= 200 and response.status_code < 400:
                origin_domain = requests.utils.urlparse(url).netloc
                redirect_domain = origin_domain
                if "Location" in response.headers:
                    redirect_domain = requests.utils.urlparse(response.headers["Location"]).netloc
                if origin_domain != redirect_domain:  # For redirects to other domain
                    response_data["code"] = -1
                    response_data["message"] = f"URL domain redirect {origin_domain} ->  {redirect_domain}"
                    response_data["url"] = response.headers["Location"]
                    response_data["domain_origin"] = origin_domain
                    response_data["domain_redirect"] = redirect_domain
                else:
                    response_data["code"] = response.status_code
                    response_data["message"] = "URL valid"
            else:
                response_data["code"] = response.status_code
                response_data["message"] = f"Not reachable: {response.status_code}"
        except requests.HTTPError as e:
            response_data["code"] = e.response.status_code
            response_data["message"] = e.response.text
        except Exception as e:  # pylint: disable=broad-exception-caught
            response_data["code"] = -1
            response_data["message"] = str(e)
        check_url_cache[url] = response_data
    return check_url_cache[url]


def generate_correction(pkg_license: str, compfile: Path = Path(__file__).parent / "data" / "licenses.txt") -> str:
    """
    Uses a probabilistic model to generate corrections on a license file
    TODO: Evaluate if this is the best method to use
    :param pkg_license: Contents of the license file to correct, as a string.
    :param compfile: Path to a license file to compare/diff against.
    :returns: Modified version of the original license file string.
    """
    with open(compfile, encoding="utf-8") as f:
        words = f.readlines()

    words: list[str] = [w.strip("\n") for w in words]
    words_cntr: Final[Counter] = Counter(words)

    def probability(word: str, n: int = sum(words_cntr.values())) -> float:
        """
        Probability of `word`.
        """
        return words_cntr[word] / n

    def correction(word: str) -> str:
        """
        Most probable spelling correction for word.
        """
        return max(candidates(word), key=probability)

    def candidates(word: str) -> set[str]:
        """
        Generate possible spelling corrections for word.
        """
        return known([word]) or known(edits1(word)) or known(edits2(word)) or {word}

    def known(words: list[str]) -> set[str]:
        """
        The subset of `words` that appear in the dictionary of `words_cntr`.
        """
        return {w for w in words if w in words_cntr}

    def edits1(word: str) -> set[str]:
        """
        All edits that are one edit away from `word`.
        """
        letters = "abcdefghijklmnopqrstuvwxyz"
        symbols = "-.0123456789"
        letters += letters.upper() + symbols
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [l + r[1:] for l, r in splits if r]
        transposes = [l + r[1] + r[0] + r[2:] for l, r in splits if len(r) > 1]
        replaces = [l + c + r[1:] for l, r in splits if r for c in letters]
        inserts = [l + c + r for l, r in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)

    def edits2(word: str) -> set[str]:
        """
        All edits that are two edits away from `word`.
        """
        return {e2 for e1 in edits1(word) for e2 in edits1(e1)}

    return correction(pkg_license)


def find_closest_match(string: str) -> Optional[str]:
    closest_match = generate_correction(string)
    if closest_match == string:
        return None
    return closest_match


def ensure_list(obj: Any) -> list:
    """
    Wraps **obj** in a list if necessary

    >>> ensure_list("one")
    ["one"]
    >>> ensure_list(["one", "two"])
    ["one", "two"]
    """
    if isinstance(obj, Sequence) and not isinstance(obj, str):
        return obj
    return [obj]


def get_dep_path(recipe: Recipe, dep):
    for n, spec in enumerate(recipe.get(dep.path, [])):
        if spec is None:  # Fixme: lint this
            continue
        if spec == dep.raw_dep:
            return f"{dep.path}/{n}"
    return dep.path


def get_deps_dict(recipe: Recipe, sections: Optional[list[str]] = None, outputs: bool = True) -> dict[str, list[str]]:
    """
    Returns a dictionary containing lists of recipe dependencies.
    TODO Future: Look into removing the `outputs` flag and query `recipe` if it has an outputs section.
    :param recipe: Target recipe instance
    :param sections: (Optional)  List of strings
    :param outputs: (Optional) Set to True for recipes that have an `outputs` section
    """
    if sections is None:
        sections = ["build", "run", "host"]
    else:
        sections = ensure_list(sections)
    check_paths = []
    for section in sections:
        check_paths.append(f"requirements/{section}")
    if outputs:
        for section in sections:
            for n in range(len(recipe.get("outputs", []))):
                check_paths.append(f"outputs/{n}/requirements/{section}")
    deps: dict[str : list[str]] = {}
    for path in check_paths:
        for n, spec in enumerate(recipe.get(path, [])):
            if spec is None:  # Fixme: lint this
                continue
            splits = re.split(r"[\s<=>]", spec, 1)
            d = deps.setdefault(splits[0], {"paths": [], "constraints": []})
            d["paths"].append(f"{path}/{n}")
            if len(splits) > 1:
                d["constraints"].append(splits[1])
            else:
                d["constraints"].append("")
    return deps


def get_deps(recipe: Recipe, sections: Optional[list[str]] = None, outputs: bool = True) -> list[str]:
    """
    Returns a list of dependencies of a recipe
    :param recipe: Target recipe instance
    :param sections: (Optional)  List of strings
    :param outputs: (Optional) Set to True for recipes that have an `outputs` section
    """
    return list(get_deps_dict(recipe, sections, outputs).keys())
