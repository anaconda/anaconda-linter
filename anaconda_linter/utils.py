"""
Utility Functions and Classes

This module collects small pieces of code used throughout
:py:mod:`anaconda_linter`.
"""

import logging
import os
import re
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Sequence

import requests
from jsonschema import validate

try:
    from ruamel.yaml import YAML
except ModuleNotFoundError:
    from ruamel_yaml import YAML

logger = logging.getLogger(__name__)


yaml = YAML(typ="safe")  # pylint: disable=invalid-name


def validate_config(config):
    """
    Validate config against schema

    Parameters
    ----------
    config : str or dict
        If str, assume it's a path to YAML file and load it. If dict, use it
        directly.
    """
    if not isinstance(config, dict):
        with open(config, encoding="utf-8") as conf:
            config = yaml.load(conf.read())
    fn = os.path.abspath(os.path.dirname(__file__)) + "/config.schema.yaml"
    with open(fn, encoding="utf-8") as f:
        schema = yaml.load(f.read())
    validate(config, schema)


def load_config(path):
    """
    Parses config file, building paths to relevant blocklists

    Parameters
    ----------
    path : str
        Path to YAML config file
    """
    validate_config(path)

    if isinstance(path, dict):

        def relpath(p):
            return p

        config = path
    else:

        def relpath(p):
            return os.path.join(os.path.dirname(path), p)

        with open(path, encoding="utf-8") as conf:
            config = yaml.load(conf.read())

    def get_list(key):
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
    with open(Path(__file__, encoding="utf-8").parent / "data" / "cbc_default.yaml") as text:
        init_arch = yaml.load(text.read())
        data_path = Path(__file__).parent / "data"
        for arch_config_path in data_path.glob("cbc_*.yaml"):
            arch = arch_config_path.stem.split("cbc_")[1]
            if arch != "default":
                with open(arch_config_path, encoding="utf-8") as text:
                    default_config[arch] = deepcopy(init_arch)
                    default_config[arch].update(yaml.load(text.read()))

    return default_config


check_url_cache = {}


def check_url(url):
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
        response_data = {"url": url}
        try:
            response = requests.head(url, allow_redirects=False)
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
        except Exception as e:
            response_data["code"] = -1
            response_data["message"] = str(e)
        check_url_cache[url] = response_data
    return check_url_cache[url]


def generate_correction(pkg_license, compfile=Path(__file__).parent / "data" / "licenses.txt"):
    with open(compfile, encoding="utf-8") as f:
        words = f.readlines()

    words = [w.strip("\n") for w in words]
    WORDS = Counter(words)

    def P(word, N=sum(WORDS.values())):
        "Probability of `word`."
        return WORDS[word] / N

    def correction(word):
        "Most probable spelling correction for word."
        return max(candidates(word), key=P)

    def candidates(word):
        "Generate possible spelling corrections for word."
        return known([word]) or known(edits1(word)) or known(edits2(word)) or [word]

    def known(words):
        "The subset of `words` that appear in the dictionary of WORDS."
        return {w for w in words if w in WORDS}

    def edits1(word):
        "All edits that are one edit away from `word`."
        letters = "abcdefghijklmnopqrstuvwxyz"
        symbols = "-.0123456789"
        letters += letters.upper() + symbols
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
        inserts = [L + c + R for L, R in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)

    def edits2(word):
        "All edits that are two edits away from `word`."
        return (e2 for e1 in edits1(word) for e2 in edits1(e1))

    return correction(pkg_license)


def find_closest_match(string: str) -> str:
    closest_match = generate_correction(string)
    if closest_match == string:
        return None
    return closest_match


def ensure_list(obj):
    """Wraps **obj** in a list if necessary

    >>> ensure_list("one")
    ["one"]
    >>> ensure_list(["one", "two"])
    ["one", "two"]
    """
    if isinstance(obj, Sequence) and not isinstance(obj, str):
        return obj
    return [obj]


def get_dep_path(recipe, dep):
    for n, spec in enumerate(recipe.get(dep.path, [])):
        if spec is None:  # Fixme: lint this
            continue
        if spec == dep.raw_dep:
            return f"{dep.path}/{n}"
    return dep.path


def get_deps_dict(recipe, sections=None, outputs=True):
    if not sections:
        sections = ("build", "run", "host")
    else:
        sections = ensure_list(sections)
    check_paths = []
    for section in sections:
        check_paths.append(f"requirements/{section}")
    if outputs:
        for section in sections:
            for n in range(len(recipe.get("outputs", []))):
                check_paths.append(f"outputs/{n}/requirements/{section}")
    deps = {}
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


def get_deps(recipe, sections=None, output=True):
    return list(get_deps_dict(recipe, sections, output).keys())
