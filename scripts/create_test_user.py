#!/usr/bin/env python3
"""
创建测试用户
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.database import AsyncSessionLocal
from backend.app.services.auth_service import AuthService
from backend.app.schemas.auth import UserCreate

async def create_test_user():
    """创建测试用户"""
    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session)
        
        username = "stats_test_user"
        password = "test123"
        
        try:
            user_data = UserCreate(username=username, password=password)
            user = await auth_service.create_user(user_data)
            print(f"✅ 创建用户成功:")
            print(f"   用户名: {user.username}")
            print(f"   ID: {user.id}")
            print(f"   密码: {password}")
            return True
        except Exception as e:
            print(f"❌ 创建用户失败: {e}")
            return False

if __name__ == "__main__":
    asyncio.run(create_test_user()) 