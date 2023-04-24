# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.

## 0.0.6


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
