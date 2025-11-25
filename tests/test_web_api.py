import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pytaxel.web.app import app  # noqa: E402

client = TestClient(app)


def test_web_generate_and_extract(tmp_path: Path):
    csv_path = REPO_ROOT / "taxel" / "test_data" / "taxonomy" / "v6.5" / "sample.csv"
    template_path = (
        REPO_ROOT
        / "taxel"
        / "templates"
        / "elster_v11"
        / "taxonomy_v6.5"
        / "ebilanz.xml"
    )

    with csv_path.open("rb") as f:
        resp = client.post(
            "/generate",
            files={"csv_file": ("sample.csv", f, "text/csv")},
            data={"template_path": str(template_path), "output_path": str(tmp_path / "gen.xml")},
        )
    assert resp.status_code == 200

    with (tmp_path / "gen.xml").open("wb") as outf:
        outf.write(resp.content)

    with (tmp_path / "gen.xml").open("rb") as f:
        resp_ext = client.post(
            "/extract",
            files={"xml_file": ("gen.xml", f, "application/xml")},
            data={"output_path": str(tmp_path / "out.csv")},
        )
    assert resp_ext.status_code == 200


def test_web_validate_logs(tmp_path: Path):
    src = (
        REPO_ROOT
        / "taxel"
        / "test_data"
        / "taxonomy"
        / "v6.5"
        / "SteuerbilanzAutoverkaeufer_PersG.xml"
    )
    xml = tmp_path / "input.xml"
    text = src.read_text(encoding="utf-8").replace(
        "<HerstellerID>74931</HerstellerID>", "<HerstellerID>00000</HerstellerID>"
    )
    xml.write_text(text, encoding="utf-8")

    with xml.open("rb") as f:
        resp = client.post(
            "/validate",
            files={"xml_file": ("input.xml", f, "application/xml")},
            data={"tax_type": "Bilanz", "tax_version": "6.5", "log_dir": str(tmp_path)},
        )
    assert resp.status_code == 200
    assert (tmp_path / "validation_response.xml").exists()
    assert (tmp_path / "server_response.xml").exists()
