import os
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import List

import requests

LICENSES = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json"
EXCEPTIONS = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/exceptions.json"


def write_to_file(dest_file: Path or str, data: List[str]):
    with open(dest_file, "w+") as f:
        f.write("\n".join(data))
        f.write("\n")
    return os.path.getsize(dest_file) > 0


if __name__ == "__main__":
    lic_resp = requests.get(LICENSES)
    exc_resp = requests.get(EXCEPTIONS)
    try:
        licenses = [l.get("licenseId") for l in lic_resp.json()["licenses"]]  # noqa: E741
        exceptions = [
            e.get("licenseExceptionId") for e in exc_resp.json()["exceptions"]
        ]  # noqa: E741
    except JSONDecodeError:
        raise ConnectionError("There was an error with the license source address.")

    lic = write_to_file(Path("anaconda_linter", "data", "licenses.txt"), licenses)
    exc = write_to_file(Path("anaconda_linter", "data", "license_exceptions.txt"), exceptions)
    print("Problem fetching data") if not all([lic, exc]) else print("Files updated!")
