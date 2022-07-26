import pytest

from conda_lint.linters import SBOMLinter

@pytest.mark.parametrize("good_metafile", [
    "tests/good-feedstock-meta.yaml",
    ])
def test_clean_lint_license(good_metafile):
    s = SBOMLinter()
    result = s.lint_license(good_metafile)
    assert result == [] 

@pytest.mark.parametrize("bad_metafile", [
    "tests/bad-feedstock-meta.yaml",
    ])
def test_dirty_lint_license(bad_metafile):
    s = SBOMLinter()
    result = s.lint_license(bad_metafile)
    lints = [s for s in result if "ERROR: License" in s]
    assert len(lints) > 0

@pytest.mark.parametrize("bad_path", [
    "numpy-meta.yaml",
    "",
    ])
def test_bad_path_lint_license(bad_path):
    s = SBOMLinter()
    with pytest.raises(FileNotFoundError) as exc_info:
        s.lint_license(bad_path)
    assert exc_info.type is FileNotFoundError

