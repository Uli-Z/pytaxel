"""FFI error handling tests for Eric wrapper."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pytaxel.eric.errors import EricError, check_eric_result  # noqa: E402
from pytaxel.eric.types import EricErrorCode  # noqa: E402


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
