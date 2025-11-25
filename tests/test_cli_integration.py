"""CLI integration tests using subprocess."""

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def test_generate_cli(tmp_path: Path):
    csv_file = REPO_ROOT / "taxel" / "test_data" / "taxonomy" / "v6.5" / "sample.csv"
    template = (
        REPO_ROOT
        / "taxel"
        / "templates"
        / "elster_v11"
        / "taxonomy_v6.5"
        / "ebilanz.xml"
    )
    output = tmp_path / "out.xml"

    result = subprocess.run(
        [
            PYTHON,
            "-m",
            "pytaxel.cli.main",
            "generate",
            "--csv-file",
            str(csv_file),
            "--template-file",
            str(template),
            "--output-file",
            str(output),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(REPO_ROOT), **os.environ},
    )

    assert result.returncode == 0, result.stderr
    assert output.exists()

def test_extract_cli(tmp_path: Path):
    xml_file = (
        REPO_ROOT
        / "taxel"
        / "test_data"
        / "taxonomy"
        / "v6.5"
        / "sample_expected.xml"
    )
    output = tmp_path / "out.csv"

    result = subprocess.run(
        [
            PYTHON,
            "-m",
            "pytaxel.cli.main",
            "extract",
            "--xml-file",
            str(xml_file),
            "--output-file",
            str(output),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(REPO_ROOT), **os.environ},
    )

    assert result.returncode == 0, result.stderr
    assert output.exists()


def test_validate_cli_success(tmp_path: Path):
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
    log_dir = tmp_path / "logs"

    result = subprocess.run(
        [
            PYTHON,
            "-m",
            "pytaxel.cli.main",
            "validate",
            "--xml-file",
            str(xml),
            "--tax-type",
            "Bilanz",
            "--tax-version",
            "6.5",
            "--log-dir",
            str(log_dir),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(REPO_ROOT), **os.environ},
    )

    assert result.returncode == 0, result.stderr
    assert (log_dir / "validation_response.xml").exists()
    assert (log_dir / "server_response.xml").exists()
