# -*- coding: utf-8 -*-
"""
Cloud Share - 个人文件分发系统后端主入口
启动时自动创建files目录、检查admin账户

Copyright 2026 dingtongbin

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models.models import User
from app.utils.auth import get_password_hash

from app.routes import auth, files, admin, shares, api


def init_database():
    """初始化数据库和默认数据"""
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.FILES_DIR, exist_ok=True)
    print(f"文件存储目录: {settings.FILES_DIR}")

    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not admin_user:
            admin_user = User(
                username=settings.ADMIN_USERNAME,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                email="admin@cloud-driver.local",
                is_admin=True,
                is_active=True,
                quota=0,
                speed_limit=0
            )
            db.add(admin_user)
            db.commit()
            print(f"管理员账户已创建: {settings.ADMIN_USERNAME} / {settings.ADMIN_PASSWORD}")
        else:
            print(f"管理员账户已存在: {settings.ADMIN_USERNAME}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    print("=" * 50)
    print("Cloud Share 文件分发系统启动中...")
    print(f"监听地址: {settings.HOST}:{settings.PORT}")
    init_database()
    print("系统初始化完成")
    print("=" * 50)
    yield
    print("系统关闭")


app = FastAPI(
    title="Cloud Share API",
    description="个人文件分发系统 - RESTful API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip压缩
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 注册路由
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(admin.router)
app.include_router(shares.router)
app.include_router(api.router)


@app.get("/api/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "service": "Cloud Share", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        workers=1,
        log_level="info"
    )
