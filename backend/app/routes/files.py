# -*- coding: utf-8 -*-
"""文件管理路由 - 上传、下载、预览、编辑"""
import os
import mimetypes
import tempfile
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, Query, Request
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, File as DBFile, DownloadLog
from app.schemas.schemas import FileResponse as FileResponseSchema, FileRename, FolderCreate, FileContent
from app.utils.auth import get_current_user
from app.utils.file_utils import (
    get_mime_type, is_text_file, generate_unique_filename,
    get_user_storage_path, get_full_path,
    create_folder, delete_file_or_folder, zip_folder, get_dir_size, format_size
)
from app.config import settings

router = APIRouter(prefix="/api/files", tags=["文件管理"])

# 图片和视频扩展名
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico"}
VIDEO_EXTS = {".mp4", ".webm", ".ogg", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".m4v"}


@router.get("/list")
def list_files(
    path: str = Query(default="/"),
    folder: str = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出目录下文件"""
    target_path = folder if folder is not None else path
    items = db.query(DBFile).filter(
        DBFile.owner_id == current_user.id,
        DBFile.parent_path == target_path
    ).order_by(DBFile.file_type.desc(), DBFile.original_name).all()

    folders = []
    files = []
    for f in items:
        item = {
            "id": f.id, "filename": f.original_name, "original_name": f.original_name,
            "file_size": f.file_size, "file_type": f.file_type, "mime_type": f.mime_type,
            "parent_path": f.parent_path,
            "file_path": f.file_path,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "updated_at": f.updated_at.isoformat() if f.updated_at else None,
        }
        if f.file_type == "folder":
            folders.append(item)
        else:
            files.append(item)

    return {"folders": folders, "files": files}


@router.get("/storage")
def get_storage(current_user: User = Depends(get_current_user)):
    """存储空间信息"""
    quota = current_user.quota
    used = current_user.used_space
    return {
        "quota": quota, "used_space": used,
        "available_space": max(0, quota - used),
        "used_percent": round(used / quota * 100, 2) if quota > 0 else 0,
        "quota_formatted": format_size(quota),
        "used_formatted": format_size(used),
        "available_formatted": format_size(max(0, quota - used)),
    }


@router.get("/logs")
def get_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """下载记录"""
    logs = db.query(DownloadLog).filter(
        DownloadLog.user_id == current_user.id
    ).order_by(DownloadLog.downloaded_at.desc()).limit(100).all()
    return [
        {"id": l.id, "file_id": l.file_id, "ip_address": l.ip_address,
         "downloaded_at": l.downloaded_at.isoformat() if l.downloaded_at else None}
        for l in logs
    ]


@router.post("/upload")
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    path: str = Query(default="/"),
    folder: str = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传文件"""
    target_path = folder if folder is not None else path
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    content = await file.read()
    file_size = len(content)
    if current_user.used_space + file_size > current_user.quota:
        raise HTTPException(status_code=400, detail="存储空间不足")

    user_dir = get_user_storage_path(settings.FILES_DIR, current_user.id)
    storage_path = os.path.join(user_dir, target_path.lstrip("/"))
    os.makedirs(storage_path, exist_ok=True)

    unique_name = generate_unique_filename(file.filename)
    full_path = os.path.join(storage_path, unique_name)
    with open(full_path, "wb") as f:
        f.write(content)

    db_file = DBFile(
        filename=unique_name, original_name=file.filename,
        file_path=f"{target_path}/{unique_name}" if target_path != "/" else f"/{unique_name}",
        file_size=file_size, file_type="file",
        mime_type=get_mime_type(file.filename),
        parent_path=target_path, owner_id=current_user.id
    )
    db.add(db_file)
    current_user.used_space += file_size
    db.commit()
    db.refresh(db_file)
    return {"message": "上传成功", "file_id": db_file.id}


@router.post("/upload/folder")
async def upload_folder(
    files: List[UploadFile] = FastAPIFile(...),
    path: str = Query(default="/"),
    folder: str = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量上传文件/文件夹"""
    target_path = folder if folder is not None else path
    total_size = 0
    uploaded = []
    user_dir = get_user_storage_path(settings.FILES_DIR, current_user.id)
    created_folders = set()

    def ensure_folder_db(folder_path: str):
        """确保文件夹在数据库中有记录"""
        if folder_path in created_folders:
            return
        existing = db.query(DBFile).filter(
            DBFile.owner_id == current_user.id,
            DBFile.file_path == folder_path,
            DBFile.file_type == "folder"
        ).first()
        if not existing:
            folder_name = os.path.basename(folder_path)
            parent = os.path.dirname(folder_path) or "/"
            db_folder = DBFile(
                filename=folder_name, original_name=folder_name,
                file_path=folder_path,
                file_size=0, file_type="folder", mime_type="inode/directory",
                parent_path=parent, owner_id=current_user.id
            )
            db.add(db_folder)
            db.flush()
        created_folders.add(folder_path)

    for file in files:
        if not file.filename:
            continue
        file_content = await file.read()
        file_size = len(file_content)
        total_size += file_size
        if current_user.used_space + total_size > current_user.quota:
            raise HTTPException(status_code=400, detail="存储空间不足")

        relative_path = file.filename.replace("\\", "/")
        if "/" in relative_path:
            # 文件在子目录中，需要确保所有层级的文件夹都有DB记录
            path_parts = relative_path.split("/")
            folder_parts = path_parts[:-1]

            current_parent = target_path
            for part in folder_parts:
                if current_parent == "/":
                    folder_full_path = f"/{part}"
                else:
                    folder_full_path = f"{current_parent}/{part}"

                # 创建物理目录
                phys_dir = os.path.join(user_dir, folder_full_path.lstrip("/"))
                os.makedirs(phys_dir, exist_ok=True)

                # 创建DB记录
                ensure_folder_db(folder_full_path)
                current_parent = folder_full_path

            parent_path = current_parent
            dest_folder = os.path.join(user_dir, parent_path.lstrip("/"))
        else:
            dest_folder = os.path.join(user_dir, target_path.lstrip("/"))
            parent_path = target_path

        os.makedirs(dest_folder, exist_ok=True)
        unique_name = generate_unique_filename(os.path.basename(relative_path))
        full_path = os.path.join(dest_folder, unique_name)
        with open(full_path, "wb") as f:
            f.write(file_content)

        db_file = DBFile(
            filename=unique_name, original_name=os.path.basename(relative_path),
            file_path=f"{parent_path}/{unique_name}".replace("\\", "/"),
            file_size=file_size, file_type="file",
            mime_type=get_mime_type(os.path.basename(relative_path)),
            parent_path=parent_path, owner_id=current_user.id
        )
        db.add(db_file)
        uploaded.append(db_file)

    current_user.used_space += total_size
    db.commit()
    return {"message": f"成功上传 {len(uploaded)} 个文件", "count": len(uploaded)}


@router.post("/folder")
def create_new_folder(
    data: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建文件夹"""
    existing = db.query(DBFile).filter(
        DBFile.owner_id == current_user.id,
        DBFile.parent_path == data.parent_path,
        DBFile.original_name == data.folder_name,
        DBFile.file_type == "folder"
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="文件夹已存在")

    folder_path = get_full_path(
        settings.FILES_DIR, current_user.id,
        f"{data.parent_path}/{data.folder_name}" if data.parent_path != "/" else f"/{data.folder_name}"
    )
    create_folder(folder_path)

    db_folder = DBFile(
        filename=data.folder_name, original_name=data.folder_name,
        file_path=f"{data.parent_path}/{data.folder_name}" if data.parent_path != "/" else f"/{data.folder_name}",
        file_size=0, file_type="folder", mime_type="inode/directory",
        parent_path=data.parent_path, owner_id=current_user.id
    )
    db.add(db_folder)
    db.commit()
    db.refresh(db_folder)
    return {"message": "文件夹创建成功", "folder_id": db_folder.id}


@router.get("/download/{file_id}")
def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """下载文件"""
    db_file = db.query(DBFile).filter(
        DBFile.id == file_id, DBFile.owner_id == current_user.id
    ).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")

    full_path = get_full_path(settings.FILES_DIR, current_user.id, db_file.file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    # 记录下载
    ip = request.client.host if request and request.client else None
    log = DownloadLog(user_id=current_user.id, file_id=file_id, ip_address=ip, download_type="direct")
    db.add(log)
    db.commit()

    if db_file.file_type == "folder":
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"{db_file.original_name}.zip")
        zip_folder(full_path, zip_path)
        return FileResponse(zip_path, filename=f"{db_file.original_name}.zip", media_type="application/zip")

    return FileResponse(full_path, filename=db_file.original_name, media_type=db_file.mime_type)


@router.delete("/folder/{folder_path:path}")
def delete_folder_by_path(
    folder_path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """通过路径删除文件夹"""
    folder_record = db.query(DBFile).filter(
        DBFile.owner_id == current_user.id,
        DBFile.file_path == f"/{folder_path}",
        DBFile.file_type == "folder"
    ).first()

    if not folder_record:
        raise HTTPException(status_code=404, detail="文件夹不存在")

    full_path = get_full_path(settings.FILES_DIR, current_user.id, folder_record.file_path)
    size = get_dir_size(full_path) if os.path.exists(full_path) else 0

    if os.path.exists(full_path):
        delete_file_or_folder(full_path)

    # 递归删除所有子项DB记录
    def delete_sub_items(parent_path: str):
        sub_items = db.query(DBFile).filter(
            DBFile.owner_id == current_user.id,
            DBFile.parent_path == parent_path
        ).all()
        for item in sub_items:
            if item.file_type == "folder":
                delete_sub_items(item.file_path)
            item_full_path = get_full_path(settings.FILES_DIR, current_user.id, item.file_path)
            if os.path.exists(item_full_path):
                delete_file_or_folder(item_full_path)
            db.delete(item)

    delete_sub_items(folder_record.file_path)

    current_user.used_space = max(0, current_user.used_space - size)
    db.delete(folder_record)
    db.commit()
    return {"message": "文件夹删除成功"}


@router.get("/download-folder")
def download_folder(
    folder: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """下载文件夹（打包成ZIP）"""
    folder_record = db.query(DBFile).filter(
        DBFile.owner_id == current_user.id,
        DBFile.file_path == folder,
        DBFile.file_type == "folder"
    ).first()

    if not folder_record:
        raise HTTPException(status_code=404, detail="文件夹不存在")

    full_path = get_full_path(settings.FILES_DIR, current_user.id, folder_record.file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="文件夹不存在")

    ip = request.client.host if request and request.client else None
    log = DownloadLog(user_id=current_user.id, file_id=folder_record.id, ip_address=ip, download_type="folder_zip")
    db.add(log)
    db.commit()

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"{folder_record.original_name}.zip")
    zip_folder(full_path, zip_path)
    return FileResponse(zip_path, filename=f"{folder_record.original_name}.zip", media_type="application/zip")


@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除文件或文件夹"""
    db_file = db.query(DBFile).filter(
        DBFile.id == file_id, DBFile.owner_id == current_user.id
    ).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")

    full_path = get_full_path(settings.FILES_DIR, current_user.id, db_file.file_path)
    if os.path.exists(full_path):
        size = get_dir_size(full_path) if db_file.file_type == "folder" else db_file.file_size
        delete_file_or_folder(full_path)
    else:
        size = db_file.file_size

    current_user.used_space = max(0, current_user.used_space - size)
    db.delete(db_file)
    db.commit()
    return {"message": "删除成功"}


@router.put("/rename/{file_id}")
def rename_file(
    file_id: int,
    data: FileRename,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重命名"""
    db_file = db.query(DBFile).filter(
        DBFile.id == file_id, DBFile.owner_id == current_user.id
    ).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    db_file.original_name = data.new_name
    if db_file.file_type == "file":
        db_file.mime_type = get_mime_type(data.new_name)
    db.commit()
    return {"message": "重命名成功"}


@router.get("/preview/{file_id}")
def preview_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """预览文件 - 支持图片、视频、音频、PDF、文本等"""
    db_file = db.query(DBFile).filter(
        DBFile.id == file_id, DBFile.owner_id == current_user.id, DBFile.file_type == "file"
    ).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    full_path = get_full_path(settings.FILES_DIR, current_user.id, db_file.file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    ext = os.path.splitext(db_file.original_name)[1].lower()

    # 优先根据扩展名判断MIME
    if is_text_file(db_file.original_name):
        mime = "text/plain; charset=utf-8"
    elif ext in IMAGE_EXTS:
        mime = mimetypes.guess_type(db_file.original_name)[0] or "image/png"
    elif ext in VIDEO_EXTS:
        mime = mimetypes.guess_type(db_file.original_name)[0] or "video/mp4"
    else:
        mime = db_file.mime_type or get_mime_type(db_file.original_name)

    with open(full_path, "rb") as f:
        data = f.read()
    return Response(content=data, media_type=mime)


@router.get("/content/{file_id}")
def get_file_content(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取文件内容(编辑用)"""
    db_file = db.query(DBFile).filter(
        DBFile.id == file_id, DBFile.owner_id == current_user.id, DBFile.file_type == "file"
    ).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    if not is_text_file(db_file.original_name):
        raise HTTPException(status_code=400, detail="该文件类型不支持在线编辑")
    full_path = get_full_path(settings.FILES_DIR, current_user.id, db_file.file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(full_path, "r", encoding="gbk", errors="replace") as f:
            content = f.read()
    return {"content": content, "filename": db_file.original_name}


@router.put("/content/{file_id}")
def save_file_content(
    file_id: int,
    data: FileContent,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """保存文件内容"""
    db_file = db.query(DBFile).filter(
        DBFile.id == file_id, DBFile.owner_id == current_user.id, DBFile.file_type == "file"
    ).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    full_path = get_full_path(settings.FILES_DIR, current_user.id, db_file.file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    old_size = db_file.file_size
    new_content = data.content.encode("utf-8")
    new_size = len(new_content)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(data.content)
    db_file.file_size = new_size
    current_user.used_space = max(0, current_user.used_space - old_size + new_size)
    db.commit()
    return {"message": "保存成功"}
