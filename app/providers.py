from datetime import datetime, timezone
from typing import Any
import httpx

from app.config import settings
from app.models import EconomicEvent


TE_BASE = "https://api.tradingeconomics.com"
BINANCE_BASE = "https://api.binance.com"


def _parse_dt(value: str) -> datetime:
    value = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _num(item: dict[str, Any], numeric_name: str, text_name: str):
    v = item.get(numeric_name)
    if isinstance(v, (int, float)):
        return float(v)
    raw = item.get(text_name)
    if raw is None or raw == "":
        return None
    s = str(raw).replace(",", "").replace("%", "").strip().upper()
    mult = 1.0
    if s.endswith("K"):
        mult, s = 1_000.0, s[:-1]
    elif s.endswith("M"):
        mult, s = 1_000_000.0, s[:-1]
    elif s.endswith("B"):
        mult, s = 1_000_000_000.0, s[:-1]
    try:
        return float(s) * mult
    except ValueError:
        return None


async def fetch_calendar(start_date: str, end_date: str) -> list[EconomicEvent]:
    country = settings.country.lower().replace(" ", "%20")
    url = f"{TE_BASE}/calendar/country/{country}/{start_date}/{end_date}"
    params = {
        "c": settings.trading_economics_api_key,
        "importance": settings.min_importance,
        "values": "true",
        "f": "json",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()

    events: list[EconomicEvent] = []
    for item in data:
        importance = int(item.get("Importance") or 0)
        if importance < settings.min_importance:
            continue
        events.append(EconomicEvent(
            calendar_id=str(item.get("CalendarId", "")),
            date_utc=_parse_dt(item["Date"]),
            country=item.get("Country", ""),
            category=item.get("Category", ""),
            event=item.get("Event", ""),
            actual=item.get("Actual") or None,
            previous=item.get("Previous") or None,
            forecast=item.get("Forecast") or None,
            te_forecast=item.get("TEForecast") or None,
            importance=importance,
            unit=item.get("Unit", "") or "",
            source=item.get("Source", "") or "",
            actual_value=_num(item, "ActualValue", "Actual"),
            previous_value=_num(item, "PreviousValue", "Previous"),
            forecast_value=_num(item, "ForecastValue", "Forecast"),
        ))
    return events


async def get_binance_price(symbol: str = "BTCUSDT") -> float:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{BINANCE_BASE}/api/v3/ticker/price", params={"symbol": symbol})
        r.raise_for_status()
        return float(r.json()["price"])
