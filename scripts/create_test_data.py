#!/usr/bin/env python3
"""
创建测试数据脚本
生成测试用户、书籍和阅读记录，用于前端真实数据测试
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone
import random
import hashlib

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.models.book import Book
from backend.app.models.reading_session import ReadingSession
from backend.app.models.highlight import Highlight
from backend.app.services.auth_service import AuthService
from backend.app.schemas.auth import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def create_test_user(db: AsyncSession) -> User:
    """创建测试用户"""
    print("🔧 创建测试用户...")
    
    auth_service = AuthService(db)
    
    # 检查用户是否已存在
    existing_user = await auth_service.get_user_by_username("testuser")
    if existing_user:
        print("✅ 测试用户已存在")
        return existing_user
    
    # 创建新用户
    user_data = UserCreate(
        username="testuser",
        password="testpass123"
    )
    
    user = await auth_service.create_user(user_data)
    print(f"✅ 创建用户成功: {user.username} (ID: {user.id})")
    return user


async def create_test_books(db: AsyncSession, user: User) -> list[Book]:
    """创建测试书籍"""
    print("📚 创建测试书籍...")
    
    books_data = [
        {
            "title": "地下室手记",
            "author": "陀思妥耶夫斯基",
            "total_pages": 156,
        },
        {
            "title": "白控力",
            "author": "凯利·麦格尼格尔",
            "total_pages": 280,
        },
        {
            "title": "毛泽东传",
            "author": "罗斯·特里尔",
            "total_pages": 520,
        },
        {
            "title": "青年希特勒",
            "author": "布里吉特·哈曼",
            "total_pages": 380,
        },
        {
            "title": "人类简史",
            "author": "尤瓦尔·赫拉利",
            "total_pages": 440,
        },
        {
            "title": "三体",
            "author": "刘慈欣",
            "total_pages": 320,
        }
    ]
    
    books = []
    for book_data in books_data:
        # 生成MD5哈希
        md5_hash = hashlib.md5(f"{book_data['title']}{book_data['author']}".encode()).hexdigest()
        
        # 检查书籍是否已存在
        result = await db.execute(
            text("SELECT * FROM books WHERE title = :title AND user_id = :user_id"),
            {"title": book_data["title"], "user_id": user.id}
        )
        existing = result.fetchone()
        
        if existing:
            book = Book(
                id=existing.id,
                user_id=existing.user_id,
                title=existing.title,
                author=existing.author,
                md5=existing.md5,
                total_pages=existing.total_pages,
                cover_image_url=existing.cover_image_url
            )
            books.append(book)
            continue
        
        book = Book(
            user_id=user.id,
            title=book_data["title"],
            author=book_data["author"],
            md5=md5_hash,
            total_pages=book_data["total_pages"]
        )
        
        db.add(book)
        books.append(book)
    
    await db.commit()
    print(f"✅ 创建了 {len(books)} 本书籍")
    return books


async def create_reading_sessions(db: AsyncSession, user: User, books: list[Book]):
    """创建阅读记录"""
    print("📖 创建阅读记录...")
    
    # 生成过去30天的阅读记录
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    
    session_count = 0
    current_date = start_date
    
    while current_date <= end_date:
        # 70%的概率有阅读记录
        if random.random() < 0.7:
            # 每天可能读1-3本书
            daily_books = random.sample(books, random.randint(1, min(3, len(books))))
            
            for book in daily_books:
                # 每本书可能有1-5个阅读会话
                sessions_per_book = random.randint(1, 3)
                
                for _ in range(sessions_per_book):
                    # 随机阅读时长 (5-120分钟)
                    duration = random.randint(300, 7200)  # 5分钟到2小时
                    
                    # 随机页码范围
                    start_page = random.randint(1, max(1, book.total_pages - 20))
                    pages_read = random.randint(1, min(20, book.total_pages - start_page + 1))
                    
                    # 随机时间点
                    session_time = current_date.replace(
                        hour=random.randint(8, 23),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59)
                    )
                    
                    # 为每页创建阅读记录
                    for page in range(start_page, start_page + pages_read):
                        session = ReadingSession(
                            book_id=book.id,
                            page=page,
                            start_time=session_time,
                            duration=duration // pages_read  # 平均分配时间
                        )
                        db.add(session)
                        session_count += 1
        
        current_date += timedelta(days=1)
    
    await db.commit()
    print(f"✅ 创建了 {session_count} 条阅读记录")


async def create_highlights(db: AsyncSession, user: User, books: list[Book]):
    """创建高亮摘抄"""
    print("💡 创建高亮摘抄...")
    
    sample_highlights = [
        "人生的意义在于追求真理和美好。",
        "知识是人类进步的阶梯。",
        "时间是最宝贵的财富。",
        "阅读是与智者对话的过程。",
        "思考比知识更重要。",
        "历史是最好的老师。",
        "科学改变世界，文学改变心灵。",
        "每个人都有自己的使命。"
    ]
    
    highlight_count = 0
    for book in books[:3]:  # 只为前3本书创建高亮
        for _ in range(random.randint(2, 5)):
            highlight = Highlight(
                book_id=book.id,
                page=random.randint(1, book.total_pages),
                text=random.choice(sample_highlights),
                note=f"来自《{book.title}》的精彩片段"
            )
            db.add(highlight)
            highlight_count += 1
    
    await db.commit()
    print(f"✅ 创建了 {highlight_count} 条高亮摘抄")


async def get_access_token(db: AsyncSession, username: str) -> str:
    """获取用户访问令牌"""
    print("🔑 生成访问令牌...")
    
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_username(username)
    if not user:
        raise ValueError(f"用户 {username} 不存在")
    
    token = auth_service.create_access_token(data={"sub": user.username})
    print(f"✅ 访问令牌: {token[:50]}...")
    return token


async def main():
    """主函数"""
    print("🚀 开始创建测试数据...")
    
    try:
        # 获取数据库会话
        async with AsyncSessionLocal() as db:
            # 创建测试用户
            user = await create_test_user(db)
            
            # 创建测试书籍
            books = await create_test_books(db, user)
            
            # 创建阅读记录
            await create_reading_sessions(db, user, books)
            
            # 创建高亮摘抄
            await create_highlights(db, user, books)
            
            # 获取访问令牌
            token = await get_access_token(db, "testuser")
            
            print("\n" + "="*50)
            print("✅ 测试数据创建完成!")
            print(f"👤 用户名: testuser")
            print(f"🔒 密码: testpass123")
            print(f"🔑 访问令牌: {token}")
            print("="*50)
            
            # 保存令牌到文件
            with open("test_token.txt", "w") as f:
                f.write(token)
            print("💾 访问令牌已保存到 test_token.txt")
            
    except Exception as e:
        print(f"❌ 创建测试数据失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 