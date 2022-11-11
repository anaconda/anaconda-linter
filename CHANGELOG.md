# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.

## 0.0.4

- Add test suite
- Update documentation
- Bug fixes for message system
- Add new check: `patch_unnecessary`
- Add `--severity` option to control the severity level of linter messages
- Remove `load_skips` function
- Bug fix: Correct mocks of conda-build jinja functions. PR: #131, Issues: #118
- Bug fix: Correct error line reporting. PR: #131, Issues: #123
- Bug fix: Handle YAML parsing errors. PR: #131, Issues: #126
- Enhancement: Render recipe using cbc files defined variables. PR: #131

## 0.0.3

- Update installation files
- Bug fixes

## 0.0.2

- patch: Additional checks added
- patch: More compilers supported

## 0.0.1

Initial release:
- To support downloading of tarballs like: https://github.com/anaconda-distribution/anaconda-linter/archive/{{ version }}.tar.gz
