import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pytaxel.ebilanz import parse_csv, render_ebilanz  # noqa: E402


def normalize_xml(path: Path) -> str:
    tree = ET.parse(path)
    root = tree.getroot()
    _strip_whitespace(root)
    return ET.tostring(root, encoding="unicode")


def _strip_whitespace(elem: ET.Element) -> None:
    if elem.text:
        elem.text = elem.text.strip()
    if elem.tail:
        elem.tail = elem.tail.strip()
    for child in elem:
        _strip_whitespace(child)


def test_generate_xml_matches_expected(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "taxel" / "test_data" / "taxonomy" / "v6.5" / "sample.csv"
    template_path = repo_root / "taxel" / "templates" / "elster_v11" / "taxonomy_v6.5" / "ebilanz.xml"
    expected_path = repo_root / "taxel" / "test_data" / "taxonomy" / "v6.5" / "sample_expected.xml"

    model = parse_csv(csv_path)
    tree = render_ebilanz(model, template_path)

    output_path = tmp_path / "generated.xml"
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

    generated = normalize_xml(output_path)
    expected = normalize_xml(expected_path)

    assert generated == expected
