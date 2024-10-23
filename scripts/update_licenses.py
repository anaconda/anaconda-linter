"""
File:           update_licenses.py
Description:    Stand-alone script
"""

from __future__ import annotations

import os
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import Final, List

import requests

from anaconda_linter.utils import HTTP_TIMEOUT

LICENSES: Final[str] = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json"
EXCEPTIONS: Final[str] = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/exceptions.json"


def write_to_file(dest_file: Path or str, data: List[str]) -> bool:
    with open(dest_file, "w+", encoding="utf-8") as f:
        f.write("\n".join(data))
        f.write("\n")
    return os.path.getsize(dest_file) > 0


if __name__ == "__main__":
    lic_resp = requests.get(LICENSES, timeout=HTTP_TIMEOUT)
    exc_resp = requests.get(EXCEPTIONS, timeout=HTTP_TIMEOUT)
    try:
        licenses = [l.get("licenseId") for l in lic_resp.json()["licenses"]]
        exceptions = [e.get("licenseExceptionId") for e in exc_resp.json()["exceptions"]]
    except JSONDecodeError as e:
        raise ConnectionError("There was an error with the license source address.") from e

    lic = write_to_file(Path("anaconda_linter", "data", "licenses.txt"), licenses)
    exc = write_to_file(Path("anaconda_linter", "data", "license_exceptions.txt"), exceptions)
    if all([lic, exc]):
        print("Files updated!")
    else:
        print("Problem fetching data")
