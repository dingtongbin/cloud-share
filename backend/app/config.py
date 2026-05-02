# -*- coding: utf-8 -*-
"""应用配置模块"""
import os


class Settings:
    """应用配置"""
    # 数据库
    DATABASE_URL: str = "sqlite:///./database/cloud.db"

    # JWT配置
    SECRET_KEY: str = "cloud-driver-secret-key-2024-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # 文件存储目录
    FILES_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "files")

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 29000

    # 默认管理员
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"

    # 默认用户配额 (10GB)
    DEFAULT_QUOTA: int = 10 * 1024 * 1024 * 1024


settings = Settings()
