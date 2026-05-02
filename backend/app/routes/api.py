# -*- coding: utf-8 -*-
"""通用API - 第三方脚本集成"""
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, File as DBFile
from app.utils.auth import get_current_user
from app.utils.file_utils import get_full_path, get_mime_type, generate_unique_filename
from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["通用API"])


@router.get("/files")
def api_list_files(
    path: str = Query(default="/"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出文件"""
    files = db.query(DBFile).filter(
        DBFile.owner_id == current_user.id, DBFile.parent_path == path
    ).all()
    return [
        {"id": f.id, "name": f.original_name, "type": f.file_type,
         "size": f.file_size, "path": f.file_path, "mime": f.mime_type,
         "created": f.created_at.isoformat() if f.created_at else None}
        for f in files
    ]


@router.post("/files/upload")
async def api_upload(
    file: UploadFile = FastAPIFile(...),
    path: str = Query(default="/"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传文件"""
    content = await file.read()
    file_size = len(content)
    if current_user.used_space + file_size > current_user.quota:
        raise HTTPException(status_code=400, detail="空间不足")

    user_dir = os.path.join(settings.FILES_DIR, str(current_user.id))
    storage_path = os.path.join(user_dir, path.lstrip("/"))
    os.makedirs(storage_path, exist_ok=True)

    unique_name = generate_unique_filename(file.filename)
    full_path = os.path.join(storage_path, unique_name)
    with open(full_path, "wb") as f:
        f.write(content)

    db_file = DBFile(
        filename=unique_name, original_name=file.filename,
        file_path=f"{path}/{unique_name}" if path != "/" else f"/{unique_name}",
        file_size=file_size, file_type="file",
        mime_type=get_mime_type(file.filename),
        parent_path=path, owner_id=current_user.id
    )
    db.add(db_file)
    current_user.used_space += file_size
    db.commit()
    db.refresh(db_file)
    return {"id": db_file.id, "message": "上传成功"}


@router.get("/files/{file_id}/download")
def api_download(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下载文件"""
    f = db.query(DBFile).filter(DBFile.id == file_id, DBFile.owner_id == current_user.id).first()
    if not f:
        raise HTTPException(status_code=404)
    full_path = get_full_path(settings.FILES_DIR, current_user.id, f.file_path)
    return FileResponse(full_path, filename=f.original_name)


@router.delete("/files/{file_id}")
def api_delete(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除文件"""
    f = db.query(DBFile).filter(DBFile.id == file_id, DBFile.owner_id == current_user.id).first()
    if not f:
        raise HTTPException(status_code=404)
    full_path = get_full_path(settings.FILES_DIR, current_user.id, f.file_path)
    if os.path.exists(full_path):
        os.remove(full_path)
        current_user.used_space = max(0, current_user.used_space - f.file_size)
    db.delete(f)
    db.commit()
    return {"message": "删除成功"}
