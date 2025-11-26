"""FFI error handling tests for Eric wrapper."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ERIC_PY_ROOT = REPO_ROOT.parent / "eric-py"
for path in (REPO_ROOT, ERIC_PY_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from eric_py.errors import EricError, check_eric_result  # noqa: E402
from eric_py.types import EricErrorCode  # noqa: E402


def test_check_eric_result_ok_does_not_raise():
    check_eric_result(EricErrorCode.ERIC_OK)


def test_check_eric_result_raises_on_error():
    code = EricErrorCode.ERIC_GLOBAL_UNKNOWN
    try:
        check_eric_result(code, message="boom")
    except EricError as exc:
        assert exc.code == code
        assert "boom" in str(exc)
    else:
        assert False, "EricError was not raised"
