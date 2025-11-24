"""CSV parsing utilities to populate the eBilanz data model."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, List

from .model import EBilanz, MasterData, Position


def parse_csv(path: Path) -> EBilanz:
    """Read a CSV file and return an EBilanz model.

    Expected columns:
    - tag: XML tag (e.g., ebilanz:stichtag, ebilanz:bilanz.summeAktiva)
    - value: stringified value
    - context (optional): context identifier (e.g., context1/context2)
    """
    positions: List[Position] = []
    master_data_kwargs = {"stichtag": None, "identifier": None, "unit": "EUR"}

    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            tag = (row.get("tag") or "").strip()
            value = (row.get("value") or "").strip()
            context = (row.get("context") or "").strip() or None

            if not tag:
                continue

            if tag == "ebilanz:stichtag":
                master_data_kwargs["stichtag"] = value
                continue
            if tag == "identifier":
                master_data_kwargs["identifier"] = value
                continue
            if tag == "unit":
                master_data_kwargs["unit"] = value
                continue

            positions.append(Position(tag=tag, value=value, context=context))

    if master_data_kwargs["stichtag"] is None:
        raise ValueError("Missing required master data: ebilanz:stichtag")
    if master_data_kwargs["identifier"] is None:
        raise ValueError("Missing required master data: identifier")

    master = MasterData(
        stichtag=master_data_kwargs["stichtag"],
        identifier=master_data_kwargs["identifier"],
        unit=master_data_kwargs["unit"],
    )
    return EBilanz(master=master, positions=positions)
