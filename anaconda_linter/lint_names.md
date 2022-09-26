## Names of available lints:

- `avoid_noarch`
- `compilers_must_be_in_build`
- `conda_render_failure`
- `cython_must_be_in_host`
- `cython_needs_compiler`
- `duplicate_key_in_meta_yaml`
- `empty_meta_yaml`
- `http_url`
- `incorrect_license`
- `invalid_license_family`
- `invalid_url`
- `jinja_render_failure`
- `linter_failure`
- `missing_build`
- `missing_build_number`
- `missing_description`
- `missing_dev_url`
- `missing_doc_source_url`
- `missing_doc_url`
- `missing_hash`
- `missing_home`
- `missing_license`
- `missing_license_family`
- `missing_license_file`
- `missing_license_url`
- `missing_meta_yaml`
- `missing_source`
- `missing_summary`
- `missing_tests`
- `missing_version_or_name`
- `non_url_source`
- `patch_must_be_in_build`
- `setup_py_install_args`
- `should_use_compilers`
- `unknown_check`
- `unknown_selector`
- `uses_setuptools`
- `version_constraints_missing_whitespace`


## TODO

- `incorrect_hash_type` (md5, sha1, etc.)
- `missing_pip_check` (in test/requires, for python packages if needed)
- `missing_wheel` (in host, for python packages)
- `incorrect_build_number` (if the same build number already exists on defaults)
- `gui_app` (if the package is a gui application, it requires additional testing)
- `package_in_cbc_yaml` (mainly, we shouldn't build a package if it's mentioned in the global cbc.yaml)
- `has_unreviewed_cves` (for info only, optional; need cvetool to retrieve data)