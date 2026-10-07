from dataclasses import dataclass
from html import escape
from zoneinfo import ZoneInfo

from app.config import settings
from app.models import EconomicEvent


@dataclass
class Surprise:
    label: str
    emoji: str
    diff_text: str


def compare(event: EconomicEvent) -> Surprise:
    a, f = event.actual_value, event.forecast_value
    if a is None or f is None:
        return Surprise("예상치 비교 불가", "⚪️", "")
    diff = a - f
    tol = max(abs(f) * 1e-9, 1e-9)
    if abs(diff) <= tol:
        label, emoji = "예상치 부합", "⚪️"
    elif diff > 0:
        label, emoji = "예상치 상회", "🔴"
    else:
        label, emoji = "예상치 하회", "🔵"
    suffix = "%p" if event.unit == "%" or "%" in (event.actual or "") else ""
    return Surprise(label, emoji, f"{diff:+.2f}{suffix}")


def _event_kind(event: EconomicEvent) -> str:
    t = f"{event.category} {event.event}".lower()
    if "core pce" in t or "pce price" in t:
        return "inflation"
    if "cpi" in t or "inflation" in t or "consumer price" in t or "ppi" in t or "producer price" in t:
        return "inflation"
    if "interest rate" in t or "fed funds" in t or "fomc" in t:
        return "rates"
    if "unemployment rate" in t or "jobless claims" in t:
        return "labor_weakness"
    if "non farm" in t or "nonfarm" in t or "payroll" in t or "adp" in t:
        return "labor_strength"
    if "gdp" in t:
        return "growth"
    if "retail sales" in t or "ism" in t or "pmi" in t:
        return "growth"
    return "generic"


def interpretation(event: EconomicEvent) -> str:
    if event.actual_value is None or event.forecast_value is None:
        return "컨센서스와 직접 비교하기 어려운 발표입니다. 초기 가격 반응과 세부 내용을 함께 확인하세요."
    higher = event.actual_value > event.forecast_value
    equal = event.actual_value == event.forecast_value
    if equal:
        return "시장 예상에 대체로 부합했습니다. 방향성보다 세부 항목과 기존 포지션 정리가 변동성을 만들 수 있습니다."

    kind = _event_kind(event)
    if kind == "inflation":
        return ("물가 압력이 예상보다 강합니다. 일반적으로 금리 인하 기대를 낮추고 달러·미 국채금리 상승 압력을 만들 수 있어 BTC·나스닥에는 단기 부담 요인입니다."
                if higher else
                "물가 압력이 예상보다 약합니다. 일반적으로 금리 인하 기대를 높일 수 있어 위험자산에는 우호적으로 해석될 수 있습니다.")
    if kind == "labor_weakness":
        return ("고용시장 둔화 신호가 예상보다 강합니다. 금리 인하 기대에는 우호적일 수 있지만 경기 우려가 커질 경우 위험자산 반응은 엇갈릴 수 있습니다."
                if higher else
                "고용시장이 예상보다 견조하게 해석될 수 있습니다. 금리 인하 기대가 일부 후퇴할 수 있어 국채금리와 달러 반응을 함께 확인할 필요가 있습니다.")
    if kind == "labor_strength":
        return ("고용이 예상보다 강합니다. 경기 측면에서는 긍정적이지만 금리 인하 기대를 낮출 수 있어 BTC·나스닥에는 단기적으로 혼재된 재료입니다."
                if higher else
                "고용이 예상보다 약합니다. 금리 인하 기대에는 우호적일 수 있으나 경기 둔화 우려가 동시에 커질 수 있습니다.")
    if kind == "growth":
        return ("성장·수요 지표가 예상보다 강합니다. 경기에는 긍정적이지만 금리 기대에는 매파적으로 작용할 수 있어 시장 반응 확인이 중요합니다."
                if higher else
                "성장·수요 지표가 예상보다 약합니다. 금리 인하 기대에는 우호적일 수 있지만 경기 둔화 우려와 함께 해석될 수 있습니다.")
    if kind == "rates":
        return "금리 결정은 숫자 자체보다 성명서 문구, 점도표 및 기자회견의 향후 경로 신호가 시장 변동성을 좌우할 수 있습니다."
    return "예상치와의 차이가 확인됐습니다. 자산별 방향은 금리·달러·주가지수 선물 반응과 함께 판단하는 편이 안전합니다."


def fmt_value(v: str | None) -> str:
    return escape(v) if v else "-"


def event_title(event: EconomicEvent) -> str:
    t = event.event or event.category
    return escape(t)


def result_message(event: EconomicEvent) -> str:
    s = compare(event)
    time_kst = event.date_utc.astimezone(ZoneInfo(settings.timezone)).strftime("%m/%d %H:%M")
    return (
        f"🚨 <b>미국 주요 경제지표 발표</b>\n\n"
        f"🇺🇸 <b>{event_title(event)}</b>\n"
        f"🕘 {time_kst} KST\n\n"
        f"실제  <b>{fmt_value(event.actual)}</b>\n"
        f"예상  {fmt_value(event.forecast)}\n"
        f"이전  {fmt_value(event.previous)}\n\n"
        f"{s.emoji} <b>{s.label}</b>{(' (' + s.diff_text + ')') if s.diff_text else ''}\n\n"
        f"📌 <b>시장 해석</b>\n{escape(interpretation(event))}\n\n"
        f"⚠️ 발표 직후에는 스프레드 확대와 급등락이 나타날 수 있습니다."
    )


def prealert_message(event: EconomicEvent, minutes: int) -> str:
    time_kst = event.date_utc.astimezone(ZoneInfo(settings.timezone)).strftime("%H:%M")
    return (
        f"⏰ <b>주요 지표 발표 {minutes}분 전</b>\n\n"
        f"🇺🇸 <b>{event_title(event)}</b>\n"
        f"발표 예정: <b>{time_kst} KST</b>\n\n"
        f"예상  {fmt_value(event.forecast)}\n"
        f"이전  {fmt_value(event.previous)}\n\n"
        f"BTC·나스닥 등 위험자산 변동성에 주의하세요."
    )


def daily_brief(events: list[EconomicEvent]) -> str:
    tz = ZoneInfo(settings.timezone)
    if not events:
        return "📅 <b>오늘의 주요 미국 경제일정</b>\n\n중요도 높은 예정 지표가 없습니다."
    lines = ["📅 <b>오늘의 주요 미국 경제일정</b>", ""]
    for e in sorted(events, key=lambda x: x.date_utc):
        tm = e.date_utc.astimezone(tz).strftime("%H:%M")
        lines += [f"🔥 <b>{tm}</b>  {event_title(e)}", f"   예상 {fmt_value(e.forecast)} · 이전 {fmt_value(e.previous)}", ""]
    lines.append("발표 결과는 확인되는 즉시 자동 안내합니다.")
    return "\n".join(lines)


def reaction_message(event: EconomicEvent, before: float, after: float) -> str:
    pct = ((after / before) - 1) * 100 if before else 0
    arrow = "📈" if pct > 0 else "📉" if pct < 0 else "➖"
    return (
        f"{arrow} <b>발표 후 BTC 1분 반응</b>\n\n"
        f"기준가: ${before:,.2f}\n"
        f"현재가: <b>${after:,.2f}</b>\n"
        f"변동률: <b>{pct:+.2f}%</b>\n\n"
        f"※ 1분 반응은 초기 변동성일 뿐 추세 확정 신호가 아닙니다."
    )
