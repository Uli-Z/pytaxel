"""Render an EBilanz model into XML using ElementTree and provided templates."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict

from .model import EBilanz, Position

NS = {
    "elster": "http://www.elster.de/elsterxml/schema/v11",
    "ebilanz": "http://rzf.fin-nrw.de/RMS/EBilanz/2016/XMLSchema",
}

# Register namespaces for clean output
for prefix, uri in NS.items():
    ET.register_namespace(prefix if prefix != "elster" else "", uri)


def _ns_tag(tag: str) -> str:
    if ":" not in tag:
        return tag
    prefix, local = tag.split(":", 1)
    uri = NS.get(prefix)
    if uri is None:
        raise ValueError(f"Unknown namespace prefix in tag '{tag}'")
    return f"{{{uri}}}{local}"


def render_ebilanz(model: EBilanz, template_path: Path) -> ET.ElementTree:
    """Load the template XML and populate it with model data."""
    tree = ET.parse(template_path)
    root = tree.getroot()

    ebilanz_node = root.find(".//{http://rzf.fin-nrw.de/RMS/EBilanz/2016/XMLSchema}EBilanz")
    if ebilanz_node is None:
        raise ValueError("Template is missing EBilanz element")

    # Set stichtag
    stichtag_node = ebilanz_node.find(_ns_tag("ebilanz:stichtag"))
    if stichtag_node is None:
        stichtag_node = ET.SubElement(ebilanz_node, _ns_tag("ebilanz:stichtag"))
    stichtag_node.text = model.master.stichtag

    # Attach positions
    for pos in model.positions:
        _add_position(ebilanz_node, pos)

    return tree


def _add_position(parent: ET.Element, position: Position) -> None:
    tag = _ns_tag(position.tag)
    node = parent.find(tag)
    if node is None:
        node = ET.SubElement(parent, tag)
    node.text = position.value
