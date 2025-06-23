"""
Script to download all conda recipes from AnacondaRecipes/aggregate repository.
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Final, Optional

from dotenv import load_dotenv
from github import Github


def fetch_submodules(github_token: Optional[str] = None) -> list[str]:
    """
    Fetch all feedstock submodule paths from AnacondaRecipes/aggregate repository.

    :param github_token: GitHub token for authentication
    :returns: List of feedstock submodule paths
    """
    g = Github(github_token)
    repo = g.get_repo("AnacondaRecipes/aggregate")
    content = repo.get_contents(".gitmodules").decoded_content.decode("utf-8")

    # Extract feedstock paths from .gitmodules
    submodules: list[str] = []
    lines = content.strip().split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not (line.startswith('[submodule "') and line.endswith('-feedstock"]')):
            i += 1
            continue
        # Find the corresponding path line
        for j in range(i + 1, min(i + 3, len(lines))):
            if lines[j].strip().startswith("path = "):
                path = lines[j].strip().split("= ", 1)[1]
                submodules.append(path)
                break
        i += 1

    print(f"Found {len(submodules)} feedstock submodules")
    return submodules


def download_recipe(feedstock_path: str, output_dir: Path, github_token: Optional[str] = None) -> bool:
    """
    Download meta.yaml from a feedstock repository.

    :param feedstock_path: Feedstock repository path
    :param output_dir: Output directory for downloaded files
    :param github_token: GitHub token for authentication
    :returns: Success flag
    """
    output_file = output_dir / f"{feedstock_path}.yaml"

    try:
        g = Github(github_token)
        repo = g.get_repo(f"AnacondaRecipes/{feedstock_path}")
        if repo.visibility != "public":
            print(f"Skipping {feedstock_path} because it is not public")
            return False
        content = repo.get_contents("recipe/meta.yaml").decoded_content.decode("utf-8")
        output_file.write_text(content, encoding="utf-8")
        return True
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error downloading {feedstock_path}: {e}")
        return False


def load_github_token() -> Optional[str]:
    """
    Load GitHub token from environment.

    :returns: GitHub token if found
    """
    env_file = Path("~/.secrets/crm-failure-stats/.env").expanduser()

    if env_file.exists():
        load_dotenv(env_file)

    return os.getenv("CRM_FAIL_STATS_GITHUB_TOKEN")


def main():
    """
    Download all recipes from the aggregate repository.
    """
    output_dir_path: Final[str] = "~/.conda-recipe-manager-aggregate-test-data"
    output_dir = Path(output_dir_path).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    github_token = load_github_token()
    rate_limit = "5000" if github_token else "60"
    auth_str = "authenticated" if github_token else "unauthenticated"
    print(f"Using {auth_str} requests ({rate_limit} req/hour)")

    submodules = fetch_submodules(github_token)
    if not submodules:
        print("No submodules found!")
        return

    print(f"Downloading {len(submodules)} recipes...")

    # Download concurrently
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(download_recipe, path, output_dir, github_token): path for path in submodules}

        for i, future in enumerate(as_completed(futures), 1):
            results.append(future.result())

            if i % 100 == 0:
                print(f"Processed {i}/{len(submodules)}")

    success_count = sum(results)
    print(f"\nComplete! Downloaded {success_count}/{len(submodules)} recipes to {output_dir}")


if __name__ == "__main__":
    main()
