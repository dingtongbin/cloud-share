# -*- coding: utf-8 -*-
"""Pydantic数据模型定义"""
import re
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator


def _validate_password_strength(v: str) -> str:
    """密码强度校验: 至少8位，包含大小写字母和数字"""
    if len(v) < 8:
        raise ValueError("密码至少需要8个字符")
    if len(v) > 128:
        raise ValueError("密码不能超过128个字符")
    if not re.search(r"[a-z]", v):
        raise ValueError("密码需包含小写字母")
    if not re.search(r"[A-Z]", v):
        raise ValueError("密码需包含大写字母")
    if not re.search(r"[0-9]", v):
        raise ValueError("密码需包含数字")
    return v


# ============ 用户相关 ============
class UserCreate(BaseModel):
    """创建用户"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)

    @validator("password")
    def strong_password(cls, v):
        return _validate_password_strength(v)

    email: str = Field(...)
    quota: int = Field(default=10 * 1024 * 1024 * 1024)
    speed_limit: int = Field(default=0)


class UserUpdate(BaseModel):
    """更新用户"""
    email: Optional[str] = None
    quota: Optional[int] = None
    speed_limit: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    is_admin: bool
    is_active: bool
    quota: int
    used_space: int
    speed_limit: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """修改密码"""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator("new_password")
    def strong_password(cls, v):
        return _validate_password_strength(v)


class LoginRequest(BaseModel):
    """登录"""
    username: str
    password: str


class Token(BaseModel):
    """JWT令牌"""
    access_token: str
    token_type: str = "bearer"


# ============ 文件相关 ============
class FileResponse(BaseModel):
    """文件响应"""
    id: int
    filename: str
    original_name: str
    file_size: int
    file_type: str
    mime_type: str
    parent_path: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FileRename(BaseModel):
    """重命名"""
    new_name: str = Field(..., min_length=1, max_length=255)


class FolderCreate(BaseModel):
    """创建文件夹"""
    folder_name: str = Field(..., min_length=1, max_length=255, alias="name")
    parent_path: str = Field(default="/", alias="parent")

    class Config:
        populate_by_name = True


class FileContent(BaseModel):
    """文件内容"""
    content: str


# ============ 分享相关 ============
class ShareCreate(BaseModel):
    """创建分享"""
    file_id: int
    password: Optional[str] = None
    max_downloads: int = Field(default=0)
    expire_hours: int = Field(default=0)
    message: Optional[str] = Field(default=None, max_length=400)


class ShareUpdate(BaseModel):
    """编辑分享"""
    password: Optional[str] = None
    max_downloads: Optional[int] = None
    expire_hours: Optional[int] = None
    message: Optional[str] = Field(default=None, max_length=400)


class ShareAccess(BaseModel):
    """访问分享(验证密码)"""
    password: Optional[str] = None


# ============ 举报相关 ============
class ReportCreate(BaseModel):
    """创建举报"""
    reason: str = Field(..., min_length=1, max_length=500)
    reporter_name: Optional[str] = Field(default=None, max_length=100)
