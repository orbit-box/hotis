import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Header, HTTPException

from app.config import settings
from app.db import init_db
from app.service import poll_events, send_daily_brief, today_events
from app.logic import daily_brief
from app.telegram import send_message

scheduler = AsyncIOScheduler(timezone=settings.timezone)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.add_job(
        poll_events,
        "interval",
        seconds=settings.poll_seconds,
        id="poll-events",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        send_daily_brief,
        "cron",
        hour=settings.daily_brief_hour,
        minute=settings.daily_brief_minute,
        id="daily-brief",
        max_instances=1,
    )
    scheduler.start()
    asyncio.create_task(poll_events())
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Economic Telegram Bot", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {
        "ok": True,
        "time": datetime.now(ZoneInfo(settings.timezone)).isoformat(),
        "country": settings.country,
        "min_importance": settings.min_importance,
    }


def _admin(x_admin_secret: str | None):
    if settings.admin_secret and x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/preview/today")
async def preview_today(x_admin_secret: str | None = Header(default=None)):
    _admin(x_admin_secret)
    events = await today_events()
    return {"message": daily_brief(events), "events": [e.__dict__ for e in events]}


@app.post("/admin/test-message")
async def test_message(x_admin_secret: str | None = Header(default=None)):
    _admin(x_admin_secret)
    return await send_message("✅ <b>경제지표 알림봇 연결 테스트 완료</b>\n\n텔레그램 채널 전송이 정상 작동합니다.")


@app.post("/admin/run-poll")
async def run_poll(x_admin_secret: str | None = Header(default=None)):
    _admin(x_admin_secret)
    await poll_events()
    return {"ok": True}
