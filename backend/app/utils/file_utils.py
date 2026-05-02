# -*- coding: utf-8 -*-
"""文件工具模块"""
import os
import io
import uuid
import shutil
import zipfile
import mimetypes
import qrcode
from pathlib import Path
from typing import Optional

# 可预览/编辑的文本类型
TEXT_EXTENSIONS = {
    ".txt", ".html", ".htm", ".css", ".js", ".json", ".xml", ".csv", ".md",
    ".py", ".java", ".c", ".cpp", ".h", ".go", ".rs", ".sh", ".yaml", ".yml",
    ".toml", ".sql", ".log", ".conf", ".cfg", ".ini", ".ts", ".tsx",
    ".jsx", ".vue", ".scss", ".less", ".php", ".rb", ".gitignore"
}


def get_mime_type(filename: str) -> str:
    """获取MIME类型"""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def is_text_file(filename: str) -> bool:
    """判断是否为文本文件"""
    return Path(filename).suffix.lower() in TEXT_EXTENSIONS


def generate_unique_filename(original_name: str) -> str:
    """生成唯一文件名"""
    ext = Path(original_name).suffix
    return f"{uuid.uuid4().hex}{ext}"


def get_user_storage_path(files_dir: str, user_id: int) -> str:
    """用户存储目录"""
    return os.path.join(files_dir, str(user_id))


def get_full_path(files_dir: str, user_id: int, file_path: str) -> str:
    """获取完整物理路径(防路径穿越)"""
    user_dir = get_user_storage_path(files_dir, user_id)
    full_path = os.path.normpath(os.path.join(user_dir, file_path.lstrip("/")))
    if not full_path.startswith(os.path.normpath(user_dir)):
        raise ValueError("非法路径访问")
    return full_path


def create_folder(full_path: str) -> None:
    """创建文件夹"""
    os.makedirs(full_path, exist_ok=True)


def delete_file_or_folder(full_path: str) -> None:
    """删除文件或文件夹"""
    if os.path.isdir(full_path):
        shutil.rmtree(full_path)
    elif os.path.isfile(full_path):
        os.remove(full_path)


def zip_folder(folder_path: str, zip_path: str) -> None:
    """将文件夹打包为ZIP"""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_full = os.path.join(root, file)
                arcname = os.path.relpath(file_full, os.path.dirname(folder_path))
                zipf.write(file_full, arcname)


def get_dir_size(path: str) -> int:
    """获取目录或文件大小"""
    if os.path.isfile(path):
        return os.path.getsize(path)
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total


def generate_qrcode(data: str) -> bytes:
    """生成二维码图片(bytes)"""
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.1f} {units[i]}"
