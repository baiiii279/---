#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""创建默认管理员账号（用户名: admin, 密码: admin123）"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.core.security import hash_password

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            if existing.role == "admin":
                print(f"管理员账号已存在: {existing.username} (ID={existing.id})")
                return
            else:
                # 已有 admin 用户但角色不是管理员，升级
                existing.role = "admin"
                db.commit()
                print(f"已将用户 {existing.username} 升级为管理员")
                return
        admin = User(
            username="admin",
            email="admin@papercraft.local",
            password_hash=hash_password("admin123"),
            role="admin",
        )
        db.add(admin)
        db.commit()
        print("管理员账号创建成功!")
        print("  用户名: admin")
        print("  密码:   admin123")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
