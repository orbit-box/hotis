from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str
    telegram_channel_id: str
    timezone: str = "Asia/Seoul"
    country_code: str = "US"
    min_importance: int = 1
    poll_seconds: int = 30
    pre_alert_minutes: str = "30,5"
    daily_brief_hour: int = 9
    daily_brief_minute: int = 0
    btc_reaction_delay_seconds: int = 60
    admin_secret: str = ""
    db_path: str = "/tmp/economic_bot.sqlite3"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def pre_alerts(self) -> list[int]:
        return sorted({int(x.strip()) for x in self.pre_alert_minutes.split(",") if x.strip()}, reverse=True)


settings = Settings()
