"""eBilanz data handling and transformation logic."""

from pathlib import Path
from typing import Union

from .model import EBilanz, MasterData, Position
from .extract import extract_to_csv
from .parser import parse_csv
from .renderer import render_ebilanz

PathLike = Union[str, Path]


def generate_xml_from_csv(csv_file: PathLike | None, template_file: PathLike, output_file: PathLike) -> Path:
    """Parse a CSV and render an eBilanz XML using the provided template."""
    model = parse_csv(Path(csv_file)) if csv_file else EBilanz(master=MasterData(stichtag="", identifier=""))
    tree = render_ebilanz(model, Path(template_file))
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    return output_path


__all__ = [
    "EBilanz",
    "MasterData",
    "Position",
    "parse_csv",
    "render_ebilanz",
    "generate_xml_from_csv",
    "extract_to_csv",
]
