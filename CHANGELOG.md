# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.

## 0.1.5
- Bug fix: calls to get_read_only_parser result in unhandled errors on some recipes

## 0.1.4
- Make check_url 403 results a warning
- Add python build tools
- Refresh SPDX list

## 0.1.3
- Python 3.11+ will only be supported for now for ease of maintenance
- Improves error and warnings output, loosely following what C compilers tend to with a "report" section
- When the `--fix` option is used, we return the list of rules that have been successfully auto-fixed
- The executable now returns pre-defined POSIX-style return codes
- Adds more unit tests
- Bug fixes

## 0.1.2
- Enforces Python code auto formatting across the project
- Enforces Python code linting across the project
- Significant changes the `Makefile` and `pre-commit` configurations
- Adds fix support for `no_git_on_windows`
- Adds support and unit tests for some auto-fixable rules
- README changes
- `pytest` now runs tests in parallel
- Various bug fixes

## 0.1.1
- Add knowledge of Python build backends to the missing_wheel rule
- Relax host_section_needs_exact_pinnings
- Add cbc_dep_in_run_missing_from_host
- Make uses_setup_py an error
- Add auto-fix for cbc_dep_in_run_missing_from_host, uses_setup_py, pip_install_args
- Update percy to >=0.1.0,<0.2.0
- Add wrong_output_script_key
- Add potentially_bad_ignore_run_exports

## 0.1.0
- Use percy as render backend
- Fix linter parsing bugs
- Shorten file paths in linter messages
- Support lists in `scripts` recipe fields
- Remove `packaging` from python build tools list
- Check for English-specific doc links
- Prohibit license_family: none
- Add `anaconda-lint` entry point

## 0.0.5

- Add fallbacks to all get commands
- Update recipe
- Fix build tools bugs
- Add no_git_on_windows check
- updates licenses and exceptions to latest as of March
- Add license automation
- Enforce use of --no-build-isolation on pip install
- Fix `pip` dependency for linter environment
- Do not require version pin for hatch extensions
- Remove has_imports_and_run_test_py

## 0.0.4

- Add test suite
- Update documentation
- Bug fixes for message system
- Add new check: `patch_unnecessary`
- Add `--severity` option to control the severity level of linter messages
- Remove threading functionality and unused functions
- Use ruamel.yaml through the module and remove pyyaml
- Remove `load_skips` function
- Bug fix: Correct mocks of conda-build jinja functions. PR: #131, Issues: #118
- Bug fix: Correct error line reporting. PR: #131, Issues: #123
- Bug fix: Handle YAML parsing errors. PR: #131, Issues: #126
- Enhancement: Render recipe using cbc files defined variables. PR: #131
- Add multi-output recipe support. PR: #149, #159, Issues: #88
- Fix missing_pip_check for test scripts. PR: #149, Issues: #144
- Implement new Perseverance Recipe Standards. PR: #160, #161, #162, #164, #165
- Code clean-ups. PR: #154, #155, #163.

## 0.0.3

- Update installation files
- Bug fixes

## 0.0.2

- patch: Additional checks added
- patch: More compilers supported

## 0.0.1

Initial release:
- To support downloading of tarballs like: https://github.com/anaconda-distribution/anaconda-linter/archive/{{ version }}.tar.gz
