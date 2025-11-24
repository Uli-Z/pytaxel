"""Domain model for representing eBilanz data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MasterData:
    """Core identifiers and metadata for an eBilanz filing."""

    stichtag: str
    identifier: str
    unit: str = "EUR"


@dataclass
class Position:
    """Single eBilanz position/value entry."""

    tag: str
    value: str
    context: Optional[str] = None


@dataclass
class EBilanz:
    """Aggregate eBilanz data model containing metadata and values."""

    master: MasterData
    positions: List[Position] = field(default_factory=list)
