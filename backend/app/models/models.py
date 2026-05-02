# -*- coding: utf-8 -*-
"""数据库模型定义"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    quota = Column(BigInteger, default=10 * 1024 * 1024 * 1024)  # 10GB
    used_space = Column(BigInteger, default=0)
    speed_limit = Column(Integer, default=0)  # KB/s, 0=不限速
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")
    shares = relationship("Share", back_populates="owner", cascade="all, delete-orphan")


class File(Base):
    """文件模型"""
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)  # 存储名(UUID)
    original_name = Column(String(255), nullable=False)  # 原始文件名
    file_path = Column(String(500), nullable=False)  # 相对路径
    file_size = Column(BigInteger, default=0)
    file_type = Column(String(50), default="file")  # file / folder
    mime_type = Column(String(200), default="application/octet-stream")
    parent_path = Column(String(500), default="/")  # 父目录
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="files")


class Share(Base):
    """分享链接模型"""
    __tablename__ = "shares"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    share_code = Column(String(32), unique=True, index=True, nullable=False)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    password = Column(String(50), nullable=True)
    max_downloads = Column(Integer, default=0)  # 0=不限
    download_count = Column(Integer, default=0)
    expire_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    message = Column(String(400), nullable=True)  # 分享留言，最多400字
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="shares")


class DownloadLog(Base):
    """下载记录"""
    __tablename__ = "download_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    ip_address = Column(String(50), nullable=True)
    download_type = Column(String(20), default="direct")  # direct / share / zip
    downloaded_at = Column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    """举报记录"""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    share_id = Column(Integer, ForeignKey("shares.id"), nullable=False)
    reporter_name = Column(String(100), nullable=True)  # 举报人昵称（可匿名）
    reason = Column(Text, nullable=False)  # 举报原因
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
