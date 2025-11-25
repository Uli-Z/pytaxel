"""Extract eBilanz values from XML into CSV rows."""

from __future__ import annotations

import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict

NS_TO_PREFIX: Dict[str, str] = {
    "http://www.elster.de/elsterxml/schema/v11": "",
    "http://rzf.fin-nrw.de/RMS/EBilanz/2016/XMLSchema": "ebilanz",
}


def _prefixed(tag: str) -> str:
    if tag.startswith("{"):
        uri, local = tag[1:].split("}", 1)
        prefix = NS_TO_PREFIX.get(uri, "")
        return f"{prefix}:{local}" if prefix else local
    return tag


def extract_to_csv(xml_path: Path, output_path: Path) -> None:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    rows = []
    for elem in root.iter():
        if elem.text and elem.text.strip():
            tag = _prefixed(elem.tag)
            rows.append({"tag": tag, "value": elem.text.strip(), "context": ""})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["tag", "value", "context"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
