# -*- coding: utf-8 -*-
"""分享路由 - 创建分享、访问分享、下载、举报"""
import os
import io
import base64
import secrets
import string
import tempfile
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, File as DBFile, Share, DownloadLog, Report
from app.schemas.schemas import ShareCreate, ShareAccess, ShareUpdate, ReportCreate
from app.utils.auth import get_current_user
from app.utils.file_utils import zip_folder, generate_qrcode, format_size
from app.config import settings

router = APIRouter(prefix="/api/shares", tags=["分享"])


def generate_share_code(length: int = 8) -> str:
    """生成随机分享码"""
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def _get_base_url(request: Request) -> str:
    """从请求头推断完整的base URL"""
    from urllib.parse import urlparse
    referer = request.headers.get("referer", "")
    if referer:
        parsed = urlparse(referer)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.hostname
    port = request.url.port
    if ":" in host and not host.startswith("["):
        return f"{proto}://{host}"
    if port and port not in (80, 443):
        return f"{proto}://{host}:{port}"
    return f"{proto}://{host}"


def _share_dict(share, file_record):
    """构造分享响应字典"""
    return {
        "id": share.id,
        "share_code": share.share_code,
        "file_id": share.file_id,
        "file_name": file_record.original_name if file_record else "已删除",
        "file_size": file_record.file_size if file_record else 0,
        "file_type": file_record.file_type if file_record else "file",
        "password": share.password,
        "has_password": bool(share.password),
        "max_downloads": share.max_downloads,
        "download_count": share.download_count,
        "expire_at": share.expire_at.isoformat() if share.expire_at else None,
        "is_active": share.is_active,
        "message": share.message or "",
        "created_at": share.created_at.isoformat() if share.created_at else None,
    }


@router.post("")
def create_share(
    data: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建分享链接"""
    file_record = db.query(DBFile).filter(
        DBFile.id == data.file_id, DBFile.owner_id == current_user.id
    ).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")

    expire_at = None
    if data.expire_hours and data.expire_hours > 0:
        expire_at = datetime.utcnow() + timedelta(hours=data.expire_hours)

    message = data.message[:400] if data.message else None

    share = Share(
        share_code=generate_share_code(),
        file_id=data.file_id,
        owner_id=current_user.id,
        password=data.password,
        max_downloads=data.max_downloads or 0,
        expire_at=expire_at,
        message=message,
    )
    db.add(share)
    db.commit()
    db.refresh(share)

    return _share_dict(share, file_record)


@router.get("/my")
def my_shares(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """我的分享列表"""
    shares = db.query(Share).filter(
        Share.owner_id == current_user.id
    ).order_by(Share.created_at.desc()).all()

    result = []
    for s in shares:
        f = db.query(DBFile).filter(DBFile.id == s.file_id).first()
        result.append(_share_dict(s, f))
    return result


@router.put("/{share_id}")
def update_share(
    share_id: int,
    data: ShareUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """编辑分享信息（编辑者可再次编辑）"""
    share = db.query(Share).filter(
        Share.id == share_id, Share.owner_id == current_user.id
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享不存在")

    if not share.is_active:
        raise HTTPException(status_code=400, detail="已取消的分享无法编辑")

    if data.password is not None:
        share.password = data.password
    if data.max_downloads is not None:
        share.max_downloads = data.max_downloads
    if data.expire_hours is not None:
        if data.expire_hours > 0:
            share.expire_at = datetime.utcnow() + timedelta(hours=data.expire_hours)
        else:
            share.expire_at = None
    if data.message is not None:
        share.message = data.message[:400] if data.message else None

    db.commit()
    db.refresh(share)

    file_record = db.query(DBFile).filter(DBFile.id == share.file_id).first()
    return _share_dict(share, file_record)


@router.patch("/{share_id}/cancel")
def cancel_share(
    share_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消分享（分享只能取消，不能删除）"""
    share = db.query(Share).filter(
        Share.id == share_id, Share.owner_id == current_user.id
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享不存在")

    if not share.is_active:
        raise HTTPException(status_code=400, detail="分享已经取消了")

    share.is_active = False
    db.commit()
    return {"message": "分享已取消"}


@router.delete("/{share_id}")
def delete_share(
    share_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消分享（兼容旧接口，实际为取消而非删除）"""
    share = db.query(Share).filter(
        Share.id == share_id, Share.owner_id == current_user.id
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享不存在")
    share.is_active = False
    db.commit()
    return {"message": "分享已取消"}


@router.get("/access/{share_code}")
def get_share_info(share_code: str, db: Session = Depends(get_db)):
    """获取分享信息(无需登录)"""
    share = db.query(Share).filter(
        Share.share_code == share_code, Share.is_active == True
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享链接不存在或已失效")

    if share.expire_at and share.expire_at < datetime.utcnow():
        share.is_active = False
        db.commit()
        raise HTTPException(status_code=410, detail="分享链接已过期")

    if share.max_downloads > 0 and share.download_count >= share.max_downloads:
        share.is_active = False
        db.commit()
        raise HTTPException(status_code=410, detail="下载次数已达上限")

    file_record = db.query(DBFile).filter(DBFile.id == share.file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="源文件已被删除")

    # 获取分享者信息
    owner = db.query(User).filter(User.id == share.owner_id).first()

    # 如果是文件夹分享，获取文件夹内的文件列表
    children = []
    if file_record.file_type == "folder":
        children_raw = db.query(DBFile).filter(
            DBFile.owner_id == share.owner_id,
            DBFile.parent_path == file_record.file_path
        ).order_by(DBFile.file_type.desc(), DBFile.original_name).all()
        children = [
            {
                "id": f.id,
                "original_name": f.original_name,
                "file_size": f.file_size,
                "file_type": f.file_type,
                "mime_type": f.mime_type,
                "file_path": f.file_path,
            }
            for f in children_raw
        ]

    return {
        "share_code": share.share_code,
        "file_name": file_record.original_name,
        "file_type": file_record.file_type,
        "file_size": file_record.file_size,
        "file_path": file_record.file_path,
        "need_password": bool(share.password),
        "has_password": bool(share.password),
        "max_downloads": share.max_downloads,
        "download_count": share.download_count,
        "expire_at": share.expire_at.isoformat() if share.expire_at else None,
        "message": share.message or "",
        "sharer_name": owner.username if owner else "匿名用户",
        "children": children,
    }


@router.get("/access/{share_code}/folder")
def get_folder_contents(share_code: str, path: str = Query("/"), db: Session = Depends(get_db)):
    """获取分享文件夹内的子目录内容"""
    share = db.query(Share).filter(
        Share.share_code == share_code, Share.is_active == True
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享不存在")

    file_record = db.query(DBFile).filter(DBFile.id == share.file_id).first()
    if not file_record or file_record.file_type != "folder":
        raise HTTPException(status_code=400, detail="不是文件夹分享")

    # 确定要查询的目录路径
    if path == "/":
        target_path = file_record.file_path
    else:
        # path 是相对于分享文件夹的路径
        target_path = file_record.file_path + "/" + path.strip("/")

    children = db.query(DBFile).filter(
        DBFile.owner_id == share.owner_id,
        DBFile.parent_path == target_path
    ).order_by(DBFile.file_type.desc(), DBFile.original_name).all()

    return {
        "current_path": path,
        "items": [
            {
                "id": f.id,
                "original_name": f.original_name,
                "file_size": f.file_size,
                "file_type": f.file_type,
                "mime_type": f.mime_type,
                "file_path": f.file_path,
            }
            for f in children
        ]
    }


@router.post("/verify/{share_code}")
def verify_password(share_code: str, data: ShareAccess, db: Session = Depends(get_db)):
    """验证分享密码"""
    share = db.query(Share).filter(
        Share.share_code == share_code, Share.is_active == True
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享不存在")
    if share.password and data.password != share.password:
        raise HTTPException(status_code=403, detail="提取密码错误")
    return {"message": "验证通过"}


@router.get("/download/{share_code}")
def download_shared(
    share_code: str,
    password: Optional[str] = Query(default=None),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """下载分享文件(支持直接HTTP链接)"""
    share = db.query(Share).filter(
        Share.share_code == share_code, Share.is_active == True
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享不存在")

    if share.expire_at and share.expire_at < datetime.utcnow():
        share.is_active = False
        db.commit()
        raise HTTPException(status_code=410, detail="分享已过期")

    if share.max_downloads > 0 and share.download_count >= share.max_downloads:
        share.is_active = False
        db.commit()
        raise HTTPException(status_code=410, detail="下载次数已满")

    if share.password and password != share.password:
        raise HTTPException(status_code=403, detail="提取密码错误")

    file_record = db.query(DBFile).filter(DBFile.id == share.file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="源文件不存在")

    owner = db.query(User).filter(User.id == share.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="文件所有者不存在")

    # 记录下载
    ip = request.client.host if request and request.client else None
    log = DownloadLog(user_id=None, file_id=file_record.id, ip_address=ip, download_type="share")
    db.add(log)
    share.download_count += 1
    db.commit()

    if file_record.file_type == "folder":
        folder_path = os.path.join(settings.FILES_DIR, str(owner.id), file_record.file_path.lstrip("/"))
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=404, detail="文件夹已丢失")
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"{file_record.original_name}.zip")
        zip_folder(folder_path, zip_path)
        return FileResponse(zip_path, filename=f"{file_record.original_name}.zip", media_type="application/zip")
    else:
        real_path = os.path.join(settings.FILES_DIR, str(owner.id), file_record.file_path.lstrip("/"))
        if not os.path.exists(real_path):
            raise HTTPException(status_code=404, detail="文件已丢失")
        return FileResponse(real_path, filename=file_record.original_name, media_type=file_record.mime_type)


@router.get("/download-file/{share_code}/{file_id}")
def download_shared_file(
    share_code: str,
    file_id: int,
    password: Optional[str] = Query(default=None),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """下载分享文件夹中的单个文件"""
    share = db.query(Share).filter(
        Share.share_code == share_code, Share.is_active == True
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享不存在")

    if share.password and password != share.password:
        raise HTTPException(status_code=403, detail="提取密码错误")

    file_record = db.query(DBFile).filter(DBFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 验证文件属于分享的文件夹
    shared_file = db.query(DBFile).filter(DBFile.id == share.file_id).first()
    if not shared_file:
        raise HTTPException(status_code=404, detail="源文件不存在")

    if not file_record.file_path.startswith(shared_file.file_path):
        raise HTTPException(status_code=403, detail="无权访问此文件")

    owner = db.query(User).filter(User.id == share.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="文件所有者不存在")

    # 记录下载
    ip = request.client.host if request and request.client else None
    log = DownloadLog(user_id=None, file_id=file_record.id, ip_address=ip, download_type="share")
    db.add(log)
    share.download_count += 1
    db.commit()

    if file_record.file_type == "folder":
        folder_path = os.path.join(settings.FILES_DIR, str(owner.id), file_record.file_path.lstrip("/"))
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=404, detail="文件夹已丢失")
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"{file_record.original_name}.zip")
        zip_folder(folder_path, zip_path)
        return FileResponse(zip_path, filename=f"{file_record.original_name}.zip", media_type="application/zip")
    else:
        real_path = os.path.join(settings.FILES_DIR, str(owner.id), file_record.file_path.lstrip("/"))
        if not os.path.exists(real_path):
            raise HTTPException(status_code=404, detail="文件已丢失")
        return FileResponse(real_path, filename=file_record.original_name, media_type=file_record.mime_type)


@router.post("/report/{share_code}")
def report_share(
    share_code: str,
    data: ReportCreate,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """举报分享"""
    share = db.query(Share).filter(
        Share.share_code == share_code, Share.is_active == True
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享不存在")

    ip = request.client.host if request and request.client else None

    report = Report(
        share_id=share.id,
        reporter_name=data.reporter_name,
        reason=data.reason[:500],
        ip_address=ip,
    )
    db.add(report)
    db.commit()

    return {"message": "举报已提交，感谢反馈"}


@router.get("/qrcode-img/{share_code}")
def get_share_qrcode_img(share_code: str, request: Request, db: Session = Depends(get_db)):
    """获取分享二维码图片（直接返回PNG）"""
    share = db.query(Share).filter(Share.share_code == share_code).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享不存在")

    base_url = _get_base_url(request)
    share_url = f"{base_url}/share/{share_code}"
    img_bytes = generate_qrcode(share_url)
    return Response(content=img_bytes, media_type="image/png")


@router.get("/qrcode/{share_code}")
@router.get("/qr/{share_code}")
def get_share_qrcode(share_code: str, request: Request, db: Session = Depends(get_db)):
    """获取分享二维码(Base64)"""
    share = db.query(Share).filter(Share.share_code == share_code).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享不存在")

    base_url = _get_base_url(request)
    share_url = f"{base_url}/share/{share_code}"
    img_bytes = generate_qrcode(share_url)
    qr_base64 = base64.b64encode(img_bytes).decode()
    return {"share_code": share_code, "qr_code": f"data:image/png;base64,{qr_base64}", "share_url": share_url}
