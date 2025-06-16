#!/usr/bin/env python3
"""
为测试用户添加测试数据
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.database import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.models.book import Book
from backend.app.models.reading_session import ReadingSession
from backend.app.models.highlight import Highlight
from sqlalchemy import select

async def add_test_data():
    """为stats_test_user添加测试数据"""
    async with AsyncSessionLocal() as session:
        # 获取测试用户
        result = await session.execute(
            select(User).where(User.username == "stats_test_user")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ 找不到测试用户")
            return
        
        print(f"✅ 找到用户: {user.username} (ID: {user.id})")
        
        # 创建测试书籍
        books_data = [
            {
                "title": "Python编程：从入门到实践",
                "authors": "Eric Matthes",
                "total_pages": 500,
                "md5": "test_book_1_md5"
            },
            {
                "title": "深度学习",
                "authors": "Ian Goodfellow",
                "total_pages": 800,
                "md5": "test_book_2_md5"
            },
            {
                "title": "算法导论",
                "authors": "Thomas H. Cormen",
                "total_pages": 1200,
                "md5": "test_book_3_md5"
            }
        ]
        
        books = []
        for book_data in books_data:
            book = Book(
                user_id=user.id,
                title=book_data["title"],
                author=book_data["authors"],
                total_pages=book_data["total_pages"],
                md5=book_data["md5"]
            )
            session.add(book)
            books.append(book)
        
        await session.flush()  # 获取book ID
        print(f"✅ 创建了 {len(books)} 本书籍")
        
        # 创建阅读会话数据
        sessions_created = 0
        highlights_created = 0
        
        # 为每本书创建阅读记录
        for book in books:
            # 随机生成过去30天的阅读记录
            for day_offset in range(30):
                # 不是每天都阅读
                if random.random() < 0.7:  # 70%的概率有阅读记录
                    continue
                
                reading_date = datetime.now() - timedelta(days=day_offset)
                
                # 每天可能有多个阅读会话
                sessions_per_day = random.randint(1, 3)
                
                for session_num in range(sessions_per_day):
                    # 随机页码和阅读时长
                    page = random.randint(1, min(book.total_pages, 100))
                    duration = random.randint(300, 3600)  # 5分钟到1小时
                    
                    # 添加一些随机时间偏移
                    session_time = reading_date + timedelta(
                        hours=random.randint(8, 22),
                        minutes=random.randint(0, 59)
                    )
                    
                    reading_session = ReadingSession(
                        book_id=book.id,
                        page=page,
                        start_time=session_time,
                        duration=duration,
                        total_pages_at_time=book.total_pages
                    )
                    session.add(reading_session)
                    sessions_created += 1
                    
                    # 有时候添加标注
                    if random.random() < 0.3:  # 30%的概率添加标注
                        highlight = Highlight(
                            book_id=book.id,
                            page=page,
                            text=f"这是第{page}页的重要内容标注",
                            note=f"笔记：关于第{page}页的思考",
                            created_time=session_time
                        )
                        session.add(highlight)
                        highlights_created += 1
        
        await session.commit()
        
        print(f"✅ 创建了 {sessions_created} 个阅读会话")
        print(f"✅ 创建了 {highlights_created} 个标注")
        print("🎉 测试数据添加完成！")

if __name__ == "__main__":
    asyncio.run(add_test_data()) 