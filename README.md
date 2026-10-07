# Telegram Economic Event Bot

미국 주요 경제지표(CPI, PCE, 고용, GDP, 소매판매, FOMC 계열 등)를 감시해 Telegram 채널로 자동 전송하는 Railway 배포용 봇입니다.

## 동작

1. 매일 09:00 KST: 당일 중요도 3 미국 경제일정 요약
2. 발표 30분 / 5분 전: 사전 알림
3. 실제값 공개 감지: Actual / Forecast / Previous 비교 및 자동 게시
4. CPI·고용·성장지표 성격에 따라 시장 해석 문구 생성
5. 발표 직전 BTC 기준가격 저장
6. 발표 1분 후 BTCUSDT 가격 반응 후속 게시
7. SQLite로 중복 전송 방지

## 데이터

- 경제 일정/실제/예상/이전값: Trading Economics Economic Calendar API
- BTC: Binance public REST API
- Telegram: Telegram Bot API

## Railway 환경변수

`.env.example`의 값을 Railway Variables에 등록합니다.

필수:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHANNEL_ID`
- `TRADING_ECONOMICS_API_KEY`

권장:
- `ADMIN_SECRET`
- `DB_PATH=/data/economic_bot.sqlite3`

## Telegram 준비

1. BotFather에서 봇 생성
2. 봇을 채널 관리자로 추가
3. 메시지 게시 권한 부여
4. 공개 채널은 `@채널아이디`, 비공개 채널은 `-100...` chat id 사용

## Health check

`GET /health`

## 테스트 메시지

`POST /admin/test-message`

헤더:
`X-Admin-Secret: <ADMIN_SECRET>`

## DB 영구 저장

Railway Volume을 `/data`에 연결하는 것을 권장합니다.
