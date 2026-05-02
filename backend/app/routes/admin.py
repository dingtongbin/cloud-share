# -*- coding: utf-8 -*-
"""管理路由 - 用户管理、系统配置"""
import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from app.database import get_db
from app.models.models import User, File, DownloadLog
from app.schemas.schemas import UserCreate, UserUpdate, UserResponse, PasswordChange
from app.utils.auth import get_password_hash, get_admin_user
from app.config import settings
from app.utils.file_utils import format_size

router = APIRouter(prefix="/api/admin", tags=["管理"])


@router.get("/users")
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """用户列表"""
    users = db.query(User).filter(User.is_admin == False).order_by(User.id).all()
    result = []
    for u in users:
        file_count = db.query(File).filter(File.owner_id == u.id).count()
        result.append({
            "id": u.id, "username": u.username, "email": u.email,
            "is_admin": u.is_admin, "is_active": u.is_active,
            "quota": u.quota, "used_space": u.used_space,
            "speed_limit": u.speed_limit, "file_count": file_count,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })
    return result


@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    file_count = db.query(File).filter(File.owner_id == user.id).count()
    return {
        "id": user.id, "username": user.username, "email": user.email,
        "is_admin": user.is_admin, "is_active": user.is_active,
        "quota": user.quota, "used_space": user.used_space,
        "speed_limit": user.speed_limit, "file_count": file_count,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.post("/users")
def create_user(
    data: UserCreate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """创建用户"""
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已注册")

    user = User(
        username=data.username,
        hashed_password=get_password_hash(data.password),
        email=data.email, is_admin=False,
        quota=data.quota, speed_limit=data.speed_limit
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "用户创建成功", "user_id": user.id}


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """更新用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="不能修改管理员")

    if data.email is not None:
        if db.query(User).filter(User.email == data.email, User.id != user_id).first():
            raise HTTPException(status_code=400, detail="邮箱已被使用")
        user.email = data.email
    if data.quota is not None:
        user.quota = data.quota
    if data.speed_limit is not None:
        user.speed_limit = data.speed_limit
    if data.is_active is not None:
        user.is_active = data.is_active

    db.commit()
    return {"message": "更新成功"}


@router.post("/users/{user_id}/change-password")
def admin_change_user_password(
    user_id: int,
    data: dict,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """管理员修改用户密码"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    new_password = data.get("new_password", "")
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="密码至少8位")
    import re
    if not re.search(r"[a-z]", new_password) or not re.search(r"[A-Z]", new_password) or not re.search(r"[0-9]", new_password):
        raise HTTPException(status_code=400, detail="密码需包含大小写字母和数字")
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return {"message": f"用户 {user.username} 密码已重置"}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="不能删除管理员")

    user_dir = os.path.join(settings.FILES_DIR, str(user.id))
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)
    db.delete(user)
    db.commit()
    return {"message": "用户已删除"}


@router.get("/stats")
def get_stats(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """系统统计"""
    total_users = db.query(User).filter(User.is_admin == False).count()
    total_files = db.query(File).count()
    total_size = db.query(sqlfunc.coalesce(sqlfunc.sum(User.used_space), 0)).filter(User.is_admin == False).scalar()
    total_downloads = db.query(DownloadLog).count()
    return {
        "total_users": total_users, "total_files": total_files,
        "total_size": total_size, "total_size_str": format_size(total_size),
        "total_downloads": total_downloads,
    }


@router.get("/download-logs")
def admin_download_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """下载记录"""
    total = db.query(DownloadLog).count()
    logs = db.query(DownloadLog).order_by(
        DownloadLog.downloaded_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first() if log.user_id else None
        file_rec = db.query(File).filter(File.id == log.file_id).first()
        result.append({
            "id": log.id, "user_id": log.user_id,
            "username": user.username if user else "分享下载",
            "file_id": log.file_id,
            "filename": file_rec.original_name if file_rec else "已删除",
            "file_size": file_rec.file_size if file_rec else 0,
            "ip_address": log.ip_address,
            "download_type": log.download_type or "direct",
            "downloaded_at": log.downloaded_at.isoformat() if log.downloaded_at else None,
        })
    return {"items": result, "total": total}
