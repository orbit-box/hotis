# Telegram Economic Event Bot

미국 주요 경제지표를 감시해 Telegram 채널로 자동 전송하는 Railway 배포용 봇입니다.

## 비용

경제 캘린더 데이터에 별도 유료 API를 사용하지 않습니다.

- 경제 일정/Actual/Forecast/Previous/Importance: TradingView 경제 캘린더의 공개 웹 엔드포인트
- BTC 가격: Binance 공개 REST API
- Telegram 전송: Telegram Bot API

TradingView 엔드포인트는 공식 개발자 API가 아닌 웹 캘린더용 공개 엔드포인트이므로 향후 구조가 바뀔 수 있습니다. 장애 시 앱 로그에 오류가 남도록 구성되어 있습니다.

## 동작

1. 매일 09:00 KST: 당일 미국 High Impact 경제일정 요약
2. 발표 30분 / 5분 전: 사전 알림
3. 실제값 공개 감지: Actual / Forecast / Previous 비교 및 자동 게시
4. CPI·PCE·고용·성장·금리 등 지표 성격에 따라 시장 해석
5. 발표 직전 BTC 기준가격 저장
6. 발표 1분 후 BTCUSDT 가격 반응 게시
7. SQLite 중복 전송 방지

## Railway 필수 환경변수

- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHANNEL_ID

그 외 기본값은 .env.example 참고.

## Telegram 준비

1. BotFather에서 봇 생성
2. 봇을 채널 관리자로 추가
3. 메시지 게시 권한 부여
4. 공개 채널은 @채널아이디, 비공개 채널은 -100... chat id 사용

## Health check

GET /health

## 테스트 메시지

POST /admin/test-message

헤더:
X-Admin-Secret: <ADMIN_SECRET>
