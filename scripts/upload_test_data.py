#!/usr/bin/env python3
"""
上传测试数据到WebDAV脚本

创建模拟的KOReader statistics.sqlite3文件并上传到WebDAV服务器
用于测试真实的同步流程
"""

import sqlite3
import tempfile
import os
import sys
from datetime import datetime, timedelta
import random
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.config import settings
from backend.app.services.webdav_service import WebDAVService
from backend.app.database import AsyncSessionLocal

def create_test_sqlite_file():
    """创建测试用的statistics.sqlite3文件"""
    print("📝 创建测试SQLite文件")
    print("=" * 50)
    
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3')
    temp_path = temp_file.name
    temp_file.close()
    
    # 连接SQLite数据库
    conn = sqlite3.connect(temp_path)
    cursor = conn.cursor()
    
    # 创建book表（KOReader格式）
    cursor.execute('''
        CREATE TABLE book (
            id INTEGER PRIMARY KEY,
            title TEXT,
            authors TEXT,
            language TEXT,
            series TEXT,
            series_index INTEGER,
            md5 TEXT UNIQUE,
            pages INTEGER
        )
    ''')
    
    # 创建page_stat表（KOReader阅读统计）
    cursor.execute('''
        CREATE TABLE page_stat (
            id_book INTEGER,
            page INTEGER,
            start_time INTEGER,
            period INTEGER,
            total_pages INTEGER,
            FOREIGN KEY (id_book) REFERENCES book (id)
        )
    ''')
    
    # 插入测试书籍数据
    books_data = [
        ("Python编程：从入门到实践", "Eric Matthes", "zh", None, None, "abc123def456", 624),
        ("深度学习", "Ian Goodfellow,Yoshua Bengio,Aaron Courville", "zh", None, None, "def456ghi789", 787),
        ("机器学习实战", "Peter Harrington", "zh", None, None, "ghi789jkl012", 336),
        ("算法导论", "Thomas H. Cormen", "zh", None, None, "jkl012mno345", 1292),
        ("代码大全", "Steve McConnell", "zh", None, None, "mno345pqr678", 914)
    ]
    
    book_ids = []
    for i, (title, authors, language, series, series_index, md5, pages) in enumerate(books_data, 1):
        cursor.execute('''
            INSERT INTO book (id, title, authors, language, series, series_index, md5, pages)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (i, title, authors, language, series, series_index, md5, pages))
        book_ids.append(i)
    
    # 插入阅读记录数据
    base_time = int((datetime.now() - timedelta(days=30)).timestamp())
    
    for book_id in book_ids:
        # 每本书生成20-50条阅读记录
        num_sessions = random.randint(20, 50)
        current_page = 1
        
        for _ in range(num_sessions):
            # 每次阅读1-10页
            pages_read = random.randint(1, 10)
            
            # 阅读时长：5-45分钟
            reading_duration = random.randint(300, 2700)
            
            # 时间间隔：几小时到几天
            time_offset = random.randint(3600, 86400 * 3)
            base_time += time_offset
            
            cursor.execute('''
                INSERT INTO page_stat (id_book, page, start_time, period, total_pages)
                VALUES (?, ?, ?, ?, ?)
            ''', (book_id, current_page, base_time, reading_duration, books_data[book_id-1][6]))
            
            current_page += pages_read
    
    conn.commit()
    conn.close()
    
    print(f"✅ 测试SQLite文件创建完成: {temp_path}")
    return temp_path

async def upload_to_webdav(sqlite_file_path):
    """上传文件到WebDAV"""
    print("\n📤 上传文件到WebDAV")
    print("=" * 50)
    
    if not settings.has_webdav_config:
        print("❌ WebDAV配置不完整，无法上传")
        return False
    
    try:
        async with AsyncSessionLocal() as session:
            webdav_service = WebDAVService(session)
            
            # 读取SQLite文件内容
            with open(sqlite_file_path, 'rb') as f:
                file_content = f.read()
            
            print(f"📄 文件大小: {len(file_content)} bytes")
            
            # 上传到WebDAV
            remote_path = f"{settings.WEBDAV_BASE_PATH}/statistics.sqlite3"
            
            success = await webdav_service.upload_file_content(
                url=settings.WEBDAV_URL,
                username=settings.WEBDAV_USERNAME,
                password=settings.WEBDAV_PASSWORD,
                remote_file_path=remote_path,
                file_content=file_content
            )
            
            if success:
                print(f"✅ 文件上传成功: {remote_path}")
                return True
            else:
                print("❌ 文件上传失败")
                return False
                
    except Exception as e:
        print(f"❌ 上传过程中发生错误: {e}")
        return False

async def main():
    """主函数"""
    print("🚀 上传测试数据到WebDAV")
    print("=" * 50)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 检查WebDAV配置
    if not settings.has_webdav_config:
        print("❌ WebDAV配置不完整！")
        print("请在 .env 文件中配置WebDAV参数")
        return False
    
    print(f"WebDAV服务器: {settings.WEBDAV_URL}")
    print(f"用户名: {settings.WEBDAV_USERNAME}")
    print(f"上传路径: {settings.WEBDAV_BASE_PATH}/statistics.sqlite3")
    print()
    
    # 创建测试SQLite文件
    sqlite_file = create_test_sqlite_file()
    
    try:
        # 上传到WebDAV
        success = await upload_to_webdav(sqlite_file)
        
        if success:
            print("\n" + "=" * 50)
            print("🎉 测试数据上传完成！")
            print("现在可以运行真实同步测试:")
            print("uv run python scripts/test_real_webdav_sync.py")
        else:
            print("\n❌ 上传失败，请检查WebDAV配置和网络连接")
            
        return success
        
    finally:
        # 清理临时文件
        try:
            os.unlink(sqlite_file)
            print(f"🗑️ 清理临时文件: {sqlite_file}")
        except:
            pass

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 