"""Application-level comparable result shape.

Comparable search is currently served by valuation_engine.py; this lightweight
model is for controller/service typing and future persistence if saved comps are needed.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ComparableResult:
    property_type: str
    city: str
    locality: str
    area_sqft: float
    price: Optional[float] = None
    price_per_sqft: Optional[float] = None
