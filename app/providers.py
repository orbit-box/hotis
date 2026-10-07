from datetime import datetime
from typing import Any
import httpx

from app.config import settings
from app.models import EconomicEvent


TV_CALENDAR_URL = "https://economic-calendar.tradingview.com/events"
BINANCE_BASE = "https://api.binance.com"


def _parse_dt(value: str) -> datetime:
    value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value)


def _display(value: Any, unit: str | None, scale: str | None) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, float) and value.is_integer():
        base = str(int(value))
    else:
        base = str(value)
    if scale:
        base += scale
    if unit:
        base += unit
    return base


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def fetch_calendar(start_date: str, end_date: str) -> list[EconomicEvent]:
    start = f"{start_date}T00:00:00.000Z"
    end = f"{end_date}T23:59:59.999Z"
    params = {
        "from": start,
        "to": end,
        "countries": settings.country_code,
        "minImportance": settings.min_importance,
    }
    headers = {
        "Origin": "https://www.tradingview.com",
        "User-Agent": "Mozilla/5.0 hotis-economic-bot/1.0",
        "Accept": "application/json,text/plain,*/*",
    }

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        r = await client.get(TV_CALENDAR_URL, params=params, headers=headers)
        r.raise_for_status()
        payload = r.json()

    data = payload.get("result", [])
    events: list[EconomicEvent] = []
    for item in data:
        importance = int(item.get("importance") if item.get("importance") is not None else -1)
        if importance < settings.min_importance:
            continue

        unit = item.get("unit") or ""
        scale = item.get("scale") or ""
        actual_raw = item.get("actual")
        previous_raw = item.get("previous")
        forecast_raw = item.get("forecast")

        events.append(EconomicEvent(
            calendar_id=str(item.get("id", "")),
            date_utc=_parse_dt(item["date"]),
            country=item.get("country", ""),
            category=item.get("indicator", "") or "",
            event=item.get("title", "") or item.get("indicator", ""),
            actual=_display(actual_raw, unit, scale),
            previous=_display(previous_raw, unit, scale),
            forecast=_display(forecast_raw, unit, scale),
            te_forecast=None,
            importance=importance,
            unit=unit,
            source=item.get("source", "") or "TradingView Economic Calendar",
            actual_value=_num(actual_raw),
            previous_value=_num(previous_raw),
            forecast_value=_num(forecast_raw),
        ))
    return events


async def get_binance_price(symbol: str = "BTCUSDT") -> float:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{BINANCE_BASE}/api/v3/ticker/price", params={"symbol": symbol})
        r.raise_for_status()
        return float(r.json()["price"])
