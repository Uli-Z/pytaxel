"""Walking skeleton for ERiC validation using the pytaxel wrapper."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repository root and eric-py checkout are importable when running this example directly.
REPO_ROOT = Path(__file__).resolve().parents[1]
ERIC_PY_ROOT = REPO_ROOT.parent / "eric-py"
for path in (REPO_ROOT, ERIC_PY_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from eric_py.errors import EricError  # noqa: E402
from eric_py.facade import EricClient  # noqa: E402


def main() -> int:
    xml_path = (
        Path(__file__).resolve().parents[1]
        / "taxel"
        / "test_data"
        / "taxonomy"
        / "v6.5"
        / "SteuerbilanzAutoverkaeufer_PersG.xml"
    )
    datenart_version = "Bilanz_6.5"

    xml_text = xml_path.read_text(encoding="utf-8")
    # Replace the placeholder Hersteller-ID with a neutral value for validation-only runs.
    xml_text = xml_text.replace("<HerstellerID>74931</HerstellerID>", "<HerstellerID>00000</HerstellerID>")

    try:
        with EricClient() as client:
            result = client.validate_xml(xml_text, datenart_version=datenart_version)
            print(f"Validation return code: {result.code}")
            print("Validation response:")
            print(result.validation_response)
            if result.server_response:
                print("Server response:")
                print(result.server_response)
        return 0
    except EricError as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
