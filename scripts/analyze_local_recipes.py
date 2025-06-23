"""
Script to analyze locally downloaded conda recipes and collect parsing failure statistics.

This script reads meta.yaml files from a local directory (downloaded by download_aggregate_recipes.py)
and generates reports and visualizations of RecipeReader success/failure statistics.
"""

import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Final, Tuple

import matplotlib.pyplot as plt
from conda_recipe_manager.parser.recipe_reader import RecipeReader
from matplotlib.patches import Patch


def capture_exception_details(exception: Exception, feedstock_name: str) -> dict[str, str]:
    """
    Capture the root cause file and line number where an exception occurred.

    :param exception: The exception object to analyze
    :param feedstock_name: Name of the feedstock where the exception occurred
    :returns: Dictionary containing exception details with keys:
        - feedstock: Name of the feedstock
        - type: Exception class name
        - message: Exception message
        - root_cause_file: Filename where error occurred
        - root_cause_line: Line number where error occurred
    """
    root_cause_file = None
    root_cause_line = None

    # Find the deepest conda-recipe-manager frame
    tb = exception.__traceback__
    while tb:
        filename = tb.tb_frame.f_code.co_filename
        if "conda_recipe_manager" in filename:
            root_cause_file = os.path.basename(filename)
            root_cause_line = tb.tb_lineno
        tb = tb.tb_next

    return {
        "feedstock": feedstock_name,
        "type": exception.__class__.__name__,
        "message": str(exception),
        "root_cause_file": root_cause_file,
        "root_cause_line": root_cause_line,
    }


def analyze_local_recipes(
    input_dir_path: str,
) -> Tuple[Counter, int, defaultdict]:
    """
    Analyze all locally saved recipes and collect exception statistics.

    :param input_dir_path: Path to directory containing downloaded recipe files
    :returns: A tuple containing:
        - exception_counter (Counter): Counter of exception types
        - success_count (int): Number of successful RecipeReader creations
        - recipe_details (defaultdict): Detailed exception information grouped by type
    """
    recipe_details = defaultdict(list)
    success_count = 0

    # Expand user path
    input_dir: Final = Path(input_dir_path).expanduser()

    if not input_dir.exists():
        print(f"Input directory does not exist: {input_dir}")
        print("Please run download_aggregate_recipes.py first to download the recipes.")
        return Counter(), success_count, recipe_details

    # Find all .yaml files in the directory
    recipe_files: Final[list[Path]] = list(input_dir.glob("*.yaml"))
    total_count: Final[int] = len(recipe_files)

    if total_count == 0:
        print(f"No .yaml files found in {input_dir}")
        return Counter(), success_count, recipe_details

    print(f"Found {total_count} recipe files in {input_dir}")
    print("Starting analysis...")

    # Process each recipe file
    for i, recipe_file in enumerate(recipe_files, 1):
        feedstock_name = recipe_file.stem  # Remove .yaml extension

        if i % 100 == 0:
            print(f"Processed {i}/{total_count}")

        # Try to parse with RecipeReader
        try:
            RecipeReader(recipe_file.read_text())
            success_count += 1
        except Exception as e:  # pylint: disable=broad-exception-caught
            exception_info = capture_exception_details(e, feedstock_name)
            exception_type = exception_info["type"]
            recipe_details[exception_type].append(exception_info)

    print(f"\nCompleted analysis of {total_count} recipes.")
    print(f"Successful: {success_count} ({success_count/total_count*100:.1f}%)")
    print(f"Failed: {total_count - success_count} ({100 - success_count/total_count*100:.1f}%)")

    # Create counter from recipe_details
    exception_counter = Counter({exc_type: len(details) for exc_type, details in recipe_details.items()})

    return exception_counter, success_count, recipe_details


def generate_histogram(exception_counter: Counter, success_count: int) -> None:
    """
    Generate and display colorblind-friendly histogram of exceptions.

    :param exception_counter: Counter of exception types and their frequencies
    :param success_count: Number of successful RecipeReader creations
    """
    # Prepare data for histogram
    labels = list(exception_counter.keys()) + ["Success"]
    counts = list(exception_counter.values()) + [success_count]

    # Create histogram with colorblind-friendly design
    plt.figure(figsize=(15, 8))
    bars = plt.bar(range(len(labels)), counts)

    # Use colorblind-friendly colors (based on Paul Tol's palette)
    # These colors are distinguishable for all types of colorblindness
    colorblind_palette = [
        "#1f77b4",  # Blue
        "#ff7f0e",  # Orange
        "#d62728",  # Red
        "#9467bd",  # Purple
        "#8c564b",  # Brown
        "#e377c2",  # Pink
        "#7f7f7f",  # Gray
        "#bcbd22",  # Olive
        "#17becf",  # Cyan
        "#2ca02c",  # Green (reserved for success)
    ]

    # Apply colors to bars
    for i, bar in enumerate(bars[:-1]):  # All except success bar
        color_idx = i % (len(colorblind_palette) - 1)  # Reserve last color for success
        bar.set_color(colorblind_palette[color_idx])
        bar.set_edgecolor("black")
        bar.set_linewidth(0.5)

    # Success bar with distinctive styling
    success_bar = bars[-1]
    success_bar.set_color("#2ca02c")  # Green, but distinguishable
    success_bar.set_edgecolor("black")
    success_bar.set_linewidth(2)  # Thicker border for emphasis
    success_bar.set_hatch("///")  # Add pattern for additional distinction

    # Customize the plot
    plt.xlabel("Exception Types", fontsize=12, fontweight="bold")
    plt.ylabel("Frequency", fontsize=12, fontweight="bold")
    plt.title("RecipeReader Exceptions and Successes", fontsize=14, fontweight="bold")
    plt.xticks(range(len(labels)), labels, rotation=45, ha="right", fontsize=10)
    plt.yticks(fontsize=10)

    # Add value labels on bars with better positioning
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height + (max(counts) * 0.01),  # Dynamic offset based on max value
            str(count),
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=9,
        )

    # Add grid for better readability
    plt.grid(axis="y", alpha=0.3, linestyle="--")

    # Add legend to distinguish success from failures
    legend_elements = [
        Patch(facecolor="#2ca02c", edgecolor="black", linewidth=2, hatch="///", label="Success"),
        Patch(facecolor="lightcoral", edgecolor="black", linewidth=0.5, label="Exceptions"),
    ]
    plt.legend(handles=legend_elements, loc="upper right", fontsize=10)

    plt.tight_layout()

    # Show the plot
    plt.show()


def print_detailed_report(exception_counter: Counter, success_count: int, recipe_details: defaultdict) -> None:
    """
    Print a detailed report of the analysis results.

    :param exception_counter: Counter of exception types and their frequencies
    :param success_count: Number of successful RecipeReader creations
    :param recipe_details: Detailed exception information grouped by exception type
    """
    total = sum(exception_counter.values()) + success_count

    print("\n" + "=" * 50)
    print("RECIPE ANALYSIS REPORT")
    print("=" * 50)
    print(f"Total recipes: {total}")
    print(f"Successful: {success_count} ({success_count/total*100:.1f}%)")
    print(f"Failed: {sum(exception_counter.values())} ({sum(exception_counter.values())/total*100:.1f}%)")

    print("\nException breakdown:")
    print("-" * 30)
    for exception_type, count in exception_counter.most_common():
        print(f"{exception_type:30} {count:6d} ({count/total*100:5.1f}%)")

    print("\nDetailed exception analysis:")
    print("-" * 60)
    for exception_type, exception_details in recipe_details.items():
        print(f"\n{exception_type} ({exception_counter[exception_type]} occurrences):")

        # Group by unique combination of message, root cause file, and root cause line
        groups = defaultdict(list)
        for detail in exception_details:
            key = (detail["message"], detail["root_cause_file"], detail["root_cause_line"])
            groups[key].append(detail)

        # Display each unique combination
        for i, (key, details_list) in enumerate(sorted(groups.items()), 1):
            message, root_cause_file, root_cause_line = key
            count = len(details_list)

            print(f"  {i}. Message: {message}")
            if root_cause_file:
                print(f"     Root cause file: {root_cause_file}")
            if root_cause_line:
                print(f"     Root cause line: {root_cause_line}")
            print(f"     Count: {count}")

            # Show examples
            examples = [d["feedstock"] for d in details_list[:5]]
            examples_str = ", ".join(examples)
            print(f"     Examples: {examples_str}")
            if len(details_list) > 5:
                print(f"     ... and {len(details_list) - 5} more")

            print()


def main():
    """
    Main function to run the recipe analysis.

    This function orchestrates the complete analysis workflow:

    1. Analyzes local recipe files for parsing errors
    2. Prints a detailed report of results
    3. Generates and displays a histogram visualization
    """
    print("Starting analysis of locally downloaded recipes")

    # Analyze recipes
    input_dir_path: Final[str] = "~/.conda-recipe-manager-aggregate-test-data"
    exception_counter, success_count, recipe_details = analyze_local_recipes(input_dir_path)

    if sum(exception_counter.values()) + success_count == 0:
        print("No recipes to analyze. Exiting.")
        return

    # Print detailed report
    print_detailed_report(exception_counter, success_count, recipe_details)

    # Generate histogram
    generate_histogram(exception_counter, success_count)

    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
