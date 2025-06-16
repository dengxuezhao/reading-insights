#!/usr/bin/env python3
"""
查询数据库中的真实数据
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import AsyncSessionLocal
from sqlalchemy import text

async def query_books():
    async with AsyncSessionLocal() as db:
        # 查询书籍信息
        result = await db.execute(text('SELECT id, title, author, total_pages FROM books WHERE user_id = 13'))
        books = result.fetchall()
        print('=== 数据库中的书籍列表 ===')
        for book in books:
            print(f'ID: {book.id}, 书名: {book.title}, 作者: {book.author}, 总页数: {book.total_pages}')
        
        # 查询阅读记录统计
        result = await db.execute(text('''
            SELECT b.title, COUNT(rs.id) as session_count, 
                   SUM(rs.duration) as total_duration,
                   MIN(rs.page) as min_page, MAX(rs.page) as max_page
            FROM books b 
            LEFT JOIN reading_sessions rs ON b.id = rs.book_id 
            WHERE b.user_id = 13 
            GROUP BY b.id, b.title 
            ORDER BY total_duration DESC
        '''))
        sessions = result.fetchall()
        print('\n=== 阅读记录统计 ===')
        for session in sessions:
            duration_hours = session.total_duration / 3600 if session.total_duration else 0
            print(f'书名: {session.title}')
            print(f'  阅读会话: {session.session_count}次')
            print(f'  总时长: {duration_hours:.1f}小时')
            print(f'  页码范围: {session.min_page}-{session.max_page}')
            print()

        # 查询最近的阅读记录
        result = await db.execute(text('''
            SELECT b.title, rs.page, rs.start_time, rs.duration
            FROM reading_sessions rs
            JOIN books b ON rs.book_id = b.id
            WHERE b.user_id = 13
            ORDER BY rs.start_time DESC
            LIMIT 10
        '''))
        recent = result.fetchall()
        print('=== 最近10条阅读记录 ===')
        for record in recent:
            print(f'{record.start_time.strftime("%Y-%m-%d %H:%M")} - {record.title} 第{record.page}页 ({record.duration}秒)')

if __name__ == "__main__":
    asyncio.run(query_books()) 