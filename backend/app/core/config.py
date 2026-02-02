import os
import yaml
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """环境变量配置"""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    anthropic_base_url: Optional[str] = None
    groq_api_key: Optional[str] = None
    database_url: str = "sqlite:///../data/papers.db"

    class Config:
        env_file = ".env"
        extra = "allow"


# 全局设置实例
settings = Settings()


def get_config() -> dict:
    """加载 YAML 配置文件"""
    config_path = Path(__file__).parent.parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


# 全局配置实例
config = get_config()
