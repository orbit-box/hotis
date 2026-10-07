import asyncio
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.config import settings
from app.db import was_sent, mark_sent, save_snapshot, get_snapshot
from app.logic import daily_brief, prealert_message, reaction_message, result_message
from app.providers import fetch_calendar, get_binance_price
from app.telegram import send_message


def utcnow():
    return datetime.now(timezone.utc)


async def today_events():
    tz = ZoneInfo(settings.timezone)
    local_now = datetime.now(tz)
    start = local_now.date().isoformat()
    end = (local_now.date() + timedelta(days=1)).isoformat()
    events = await fetch_calendar(start, end)
    return [e for e in events if e.date_utc.astimezone(tz).date() == local_now.date()]


async def send_daily_brief():
    key = f"daily:{datetime.now(ZoneInfo(settings.timezone)).date().isoformat()}"
    if was_sent(key):
        return
    events = await today_events()
    await send_message(daily_brief(events))
    mark_sent(key)


async def _send_reaction_later(event):
    await asyncio.sleep(settings.btc_reaction_delay_seconds)
    row = get_snapshot(event.calendar_id)
    if not row:
        return
    before = float(row[1])
    try:
        after = await get_binance_price("BTCUSDT")
        await send_message(reaction_message(event, before, after))
        mark_sent(f"reaction:{event.calendar_id}")
    except Exception as e:
        print("reaction error", repr(e))


async def poll_events():
    tz = ZoneInfo(settings.timezone)
    local_now = datetime.now(tz)
    start = (local_now.date() - timedelta(days=1)).isoformat()
    end = (local_now.date() + timedelta(days=1)).isoformat()
    try:
        events = await fetch_calendar(start, end)
    except Exception as e:
        print("calendar fetch error", repr(e))
        return

    now = utcnow()
    for event in events:
        seconds_to = (event.date_utc - now).total_seconds()

        for minutes in settings.pre_alerts:
            if -15 <= seconds_to - (minutes * 60) <= max(settings.poll_seconds + 10, 45):
                key = f"pre:{minutes}:{event.calendar_id}"
                if not was_sent(key):
                    await send_message(prealert_message(event, minutes))
                    mark_sent(key)

        if -10 <= seconds_to <= max(settings.poll_seconds + 10, 45):
            snap_key = f"snapshot:{event.calendar_id}"
            if not was_sent(snap_key):
                try:
                    price = await get_binance_price("BTCUSDT")
                    save_snapshot(event.calendar_id, "BTCUSDT", price)
                    mark_sent(snap_key)
                except Exception as e:
                    print("snapshot error", repr(e))

        result_key = f"result:{event.calendar_id}"
        if event.actual and not was_sent(result_key):
            age = (now - event.date_utc).total_seconds()
            if -300 <= age <= 6 * 3600:
                if not get_snapshot(event.calendar_id):
                    try:
                        price = await get_binance_price("BTCUSDT")
                        save_snapshot(event.calendar_id, "BTCUSDT", price)
                    except Exception:
                        pass
                await send_message(result_message(event))
                mark_sent(result_key)
                if not was_sent(f"reaction:{event.calendar_id}"):
                    asyncio.create_task(_send_reaction_later(event))
