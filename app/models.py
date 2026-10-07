from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class EconomicEvent:
    calendar_id: str
    date_utc: datetime
    country: str
    category: str
    event: str
    actual: Optional[str]
    previous: Optional[str]
    forecast: Optional[str]
    te_forecast: Optional[str]
    importance: int
    unit: str
    source: str
    actual_value: Optional[float] = None
    previous_value: Optional[float] = None
    forecast_value: Optional[float] = None
