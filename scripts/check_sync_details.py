#!/usr/bin/env python3
"""
详细同步状态检查脚本

检查数据库中的同步数据详情
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from backend.app.database import AsyncSessionLocal
from backend.app.models.book import Book
from backend.app.models.reading_session import ReadingSession
from backend.app.models.user import User
from sqlalchemy import select, func
from datetime import datetime

async def check_sync_details():
    """检查同步数据详情"""
    print("🔍 检查同步数据详情")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        try:
            # 查找最新的WebDAV测试用户
            result = await session.execute(
                select(User).where(User.username.like('webdav_test_%')).order_by(User.id.desc()).limit(1)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ 未找到WebDAV测试用户")
                return
            
            print(f"📧 用户: {user.username} (ID: {user.id})")
            print(f"📅 创建时间: {user.created_at}")
            
            # 检查用户的书籍
            books_result = await session.execute(
                select(Book).where(Book.user_id == user.id)
            )
            books = books_result.scalars().all()
            
            print(f"\n📚 书籍数量: {len(books)}")
            if books:
                print("书籍列表:")
                for i, book in enumerate(books[:10], 1):  # 只显示前10本
                    print(f"  {i}. {book.title} - {book.author} ({book.total_pages}页)")
                if len(books) > 10:
                    print(f"  ... 还有 {len(books) - 10} 本书")
            
            # 检查阅读会话
            sessions_result = await session.execute(
                select(ReadingSession).join(Book).where(Book.user_id == user.id)
            )
            sessions = sessions_result.scalars().all()
            
            print(f"\n📖 阅读记录数量: {len(sessions)}")
            if sessions:
                print("最近的阅读记录:")
                for i, session in enumerate(sessions[:5], 1):  # 显示前5条记录
                    book_result = await session.execute(
                        select(Book).where(Book.id == session.book_id)
                    )
                    book = book_result.scalar_one_or_none()
                    book_title = book.title if book else "未知书籍"
                    
                    print(f"  {i}. {book_title}")
                    print(f"     页码: {session.page}, 时长: {session.duration}秒")
                    print(f"     时间: {session.start_time}")
                
                if len(sessions) > 5:
                    print(f"  ... 还有 {len(sessions) - 5} 条记录")
            
            # 统计信息
            total_duration = await session.scalar(
                select(func.sum(ReadingSession.duration))
                .join(Book)
                .where(Book.user_id == user.id)
            ) or 0
            
            print(f"\n📊 统计信息:")
            print(f"  总阅读时间: {total_duration} 秒 ({total_duration // 60} 分钟)")
            print(f"  平均每本书页数: {sum(book.total_pages or 0 for book in books) // len(books) if books else 0}")
            
        except Exception as e:
            print(f"❌ 检查同步数据时出错: {e}")

if __name__ == "__main__":
    asyncio.run(check_sync_details()) 