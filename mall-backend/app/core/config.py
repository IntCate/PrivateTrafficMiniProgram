"""分层配置：pydantic-settings 驱动的环境配置。"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置，由 .env 或环境变量注入。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 环境
    app_env: str = "dev"
    app_name: str = "快乐购商城"
    api_prefix: str = "/api"

    # 数据库
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "mall"

    # 安全
    secret_key: str = "please_change_me"
    token_ttl_days: int = 7
    admin_jwt_ttl_hours: int = 12

    # 微信
    wx_app_id: str = ""
    wx_app_secret: str = ""
    login_mock: bool = True

    # 日志
    log_level: str = "INFO"
    log_dir: str = "logs"

    # 上传
    upload_dir: str = "uploads"

    # CORS（逗号分隔）
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # 支付
    pay_mode: str = "mock"

    @property
    def database_url(self) -> str:
        """MySQL 连接串。"""
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
