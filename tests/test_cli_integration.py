"""CLI integration tests using subprocess."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

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
    pdf_path = tmp_path / "preview.pdf"

    env = dict(os.environ)
    env["PYTHONPATH"] = f"{REPO_ROOT}:{REPO_ROOT.parent / 'eric-py'}"
    eric_home = REPO_ROOT / "ERiC" / "Linux-x86_64"
    if eric_home.exists():
        env["ERIC_HOME"] = str(eric_home)
    else:
        pytest.skip("ERiC distribution not available for CLI validate test")

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
            "--print",
            str(pdf_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert (log_dir / "validation_response.xml").exists()
    assert (log_dir / "server_response.xml").exists()
    assert pdf_path.exists()


def test_eric_check_without_eric_home():
    """eric-check should fail clearly when ERIC_HOME is not set."""
    env = {k: v for k, v in os.environ.items() if k != "ERIC_HOME"}
    env["PYTHONPATH"] = f"{REPO_ROOT}:{REPO_ROOT.parent / 'eric-py'}"

    result = subprocess.run(
        [
            PYTHON,
            "-m",
            "pytaxel.cli.main",
            "eric-check",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode != 0
    assert "ERIC_HOME is not set" in result.stderr
