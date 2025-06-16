#!/usr/bin/env python3
"""
检查测试数据是否正确插入
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.database import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.models.book import Book
from backend.app.models.reading_session import ReadingSession
from backend.app.models.highlight import Highlight
from sqlalchemy import select, func

async def check_test_data():
    """检查测试数据"""
    async with AsyncSessionLocal() as session:
        # 获取测试用户
        result = await session.execute(
            select(User).where(User.username == "stats_test_user")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ 找不到测试用户")
            return
        
        print(f"✅ 用户: {user.username} (ID: {user.id})")
        
        # 检查书籍数量
        books_count = await session.execute(
            select(func.count(Book.id)).where(Book.user_id == user.id)
        )
        books_total = books_count.scalar()
        print(f"📚 书籍数量: {books_total}")
        
        # 检查阅读会话数量
        sessions_count = await session.execute(
            select(func.count(ReadingSession.id))
            .join(Book, ReadingSession.book_id == Book.id)
            .where(Book.user_id == user.id)
        )
        sessions_total = sessions_count.scalar()
        print(f"📖 阅读会话数量: {sessions_total}")
        
        # 检查标注数量
        highlights_count = await session.execute(
            select(func.count(Highlight.id))
            .join(Book, Highlight.book_id == Book.id)
            .where(Book.user_id == user.id)
        )
        highlights_total = highlights_count.scalar()
        print(f"🏷️ 标注数量: {highlights_total}")
        
        # 检查总阅读时长
        total_duration = await session.execute(
            select(func.sum(ReadingSession.duration))
            .join(Book, ReadingSession.book_id == Book.id)
            .where(Book.user_id == user.id)
        )
        duration_total = total_duration.scalar() or 0
        print(f"⏱️ 总阅读时长: {duration_total} 秒 ({duration_total // 60} 分钟)")
        
        # 检查书籍详情
        books_result = await session.execute(
            select(Book).where(Book.user_id == user.id)
        )
        books = books_result.scalars().all()
        
        print(f"\n📚 书籍详情:")
        for book in books:
            print(f"  - {book.title} (ID: {book.id})")
            
            # 检查每本书的阅读会话
            book_sessions = await session.execute(
                select(func.count(ReadingSession.id))
                .where(ReadingSession.book_id == book.id)
            )
            book_sessions_count = book_sessions.scalar()
            print(f"    阅读会话: {book_sessions_count}")

if __name__ == "__main__":
    asyncio.run(check_test_data()) 