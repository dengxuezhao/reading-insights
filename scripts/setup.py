#!/usr/bin/env python
"""
ReadingInsights项目设置脚本

该脚本用于：
1. 检查环境配置
2. 初始化数据库
3. 创建初始数据
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.config import settings
from backend.app.database import engine, Base


async def create_tables():
    """创建数据库表"""
    print("正在创建数据库表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表创建完成！")


async def check_database_connection():
    """检查数据库连接"""
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        print("✓ 数据库连接正常")
        return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False


def check_environment():
    """检查环境配置"""
    print("检查环境配置...")
    
    # 检查必要的环境变量
    required_vars = [
        "SECRET_KEY",
        "JWT_SECRET_KEY",
        "DB_HOST",
        "DB_USER",
        "DB_PASSWORD",
        "DB_NAME"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"✗ 缺少必要的环境变量: {', '.join(missing_vars)}")
        print("请检查 .env 文件并确保所有必要的配置项都已设置")
        return False
    
    print("✓ 环境配置检查通过")
    return True


async def main():
    """主函数"""
    print("=== ReadingInsights项目设置 ===\n")
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 检查数据库连接
    if not await check_database_connection():
        print("\n请确保：")
        print("1. PostgreSQL服务已启动")
        print("2. 数据库配置正确")
        print("3. 数据库用户有相应权限")
        sys.exit(1)
    
    # 创建数据库表
    await create_tables()
    
    print("\n=== 设置完成 ===")
    print("你现在可以运行以下命令启动服务：")
    print("  uv run dev")
    print("或者：")
    print("  uv run uvicorn backend.app.main:app --reload")


if __name__ == "__main__":
    asyncio.run(main()) 