#!/usr/bin/env python3
"""
分析真实的statistics.sqlite3文件内容

这个脚本将从坚果云下载真实的statistics.sqlite3文件，
并分析其中的表结构和数据内容
"""

import sqlite3
import sys
import tempfile
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.config import settings
from backend.app.services.webdav_service import WebDAVService
from backend.app.database import AsyncSessionLocal

async def download_and_analyze_sqlite():
    """下载并分析真实的SQLite文件"""
    print("🔍 分析真实的statistics.sqlite3文件")
    print("=" * 60)
    
    if not settings.has_webdav_config:
        print("❌ WebDAV配置不完整")
        return False
    
    async with AsyncSessionLocal() as session:
        webdav_service = WebDAVService(session)
        
        # 创建一个虚拟用户ID（用于WebDAV操作）
        config = {
            "url": settings.WEBDAV_URL,
            "username": settings.WEBDAV_USERNAME,
            "password": settings.WEBDAV_PASSWORD
        }
        
        # 手动创建WebDAV客户端并下载文件
        from webdav3.client import Client
        import asyncio
        
        client = Client({
            'webdav_hostname': config['url'],
            'webdav_login': config['username'],
            'webdav_password': config['password'],
            'webdav_timeout': 30,
            'disable_check': False,
        })
        
        # 尝试不同的路径
        base_path = settings.WEBDAV_BASE_PATH.rstrip('/')
        possible_paths = [
            f"{base_path}/statistics.sqlite3",
            f"{base_path}/statistics.sqlite",
            f"{base_path}/Documents/statistics.sqlite3",
        ]
        
        downloaded_file = None
        found_path = None
        
        for remote_path in possible_paths:
            print(f"📁 尝试路径: {remote_path}")
            try:
                if client.check(remote_path):
                    print(f"✅ 找到文件: {remote_path}")
                    
                    # 下载文件
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3')
                    local_path = temp_file.name
                    temp_file.close()
                    
                    client.download_sync(remote_path=remote_path, local_path=local_path)
                    
                    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                        downloaded_file = local_path
                        found_path = remote_path
                        print(f"✅ 文件下载成功: {local_path}")
                        print(f"📊 文件大小: {os.path.getsize(local_path)} bytes")
                        break
                else:
                    print(f"❌ 文件不存在: {remote_path}")
            except Exception as e:
                print(f"❌ 检查路径 {remote_path} 时出错: {e}")
        
        if not downloaded_file:
            print("❌ 未找到statistics.sqlite3文件")
            return False
        
        try:
            # 分析SQLite文件
            analyze_sqlite_content(downloaded_file, found_path)
            return True
        finally:
            # 清理临时文件
            if os.path.exists(downloaded_file):
                os.unlink(downloaded_file)

def analyze_sqlite_content(sqlite_path: str, remote_path: str):
    """分析SQLite文件内容"""
    print(f"\n📖 分析文件内容")
    print("=" * 60)
    print(f"远程路径: {remote_path}")
    print(f"本地路径: {sqlite_path}")
    
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # 1. 列出所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\n📋 数据库中的表 ({len(tables)} 个):")
        for table in tables:
            print(f"  • {table[0]}")
        
        # 2. 分析每个表的结构和数据
        for table_name, in tables:
            print(f"\n🗂️ 表: {table_name}")
            print("-" * 40)
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print("字段结构:")
            for col in columns:
                print(f"  {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")
            
            # 获取数据行数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"数据行数: {count}")
            
            # 如果有数据，显示前几行
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                rows = cursor.fetchall()
                print("示例数据:")
                for i, row in enumerate(rows):
                    print(f"  行{i+1}: {row}")
                    
                if count > 3:
                    print(f"  ... 还有 {count - 3} 行数据")
        
        # 3. 特别关注KOReader相关的表
        print(f"\n🔍 KOReader数据分析")
        print("=" * 60)
        
        # 检查book表
        try:
            cursor.execute("SELECT COUNT(*) FROM book;")
            book_count = cursor.fetchone()[0]
            print(f"📚 书籍数量: {book_count}")
            
            if book_count > 0:
                cursor.execute("SELECT title, authors, pages FROM book LIMIT 5;")
                books = cursor.fetchall()
                print("书籍示例:")
                for book in books:
                    print(f"  • {book[0]} - {book[1]} ({book[2]} 页)")
        except sqlite3.OperationalError:
            print("❌ book表不存在或结构不匹配")
        
        # 检查page_stat表
        try:
            cursor.execute("SELECT COUNT(*) FROM page_stat;")
            stat_count = cursor.fetchone()[0]
            print(f"\n📊 阅读统计记录: {stat_count}")
            
            if stat_count > 0:
                cursor.execute("""
                    SELECT id_book, page, start_time, period 
                    FROM page_stat 
                    ORDER BY start_time DESC 
                    LIMIT 5
                """)
                stats = cursor.fetchall()
                print("最近阅读记录:")
                for stat in stats:
                    timestamp = datetime.fromtimestamp(stat[2]) if stat[2] else "未知时间"
                    duration_min = (stat[3] // 60) if stat[3] else 0
                    print(f"  • 书籍ID: {stat[0]}, 页面: {stat[1]}, 时间: {timestamp}, 时长: {duration_min}分钟")
        except sqlite3.OperationalError as e:
            print(f"❌ page_stat表分析失败: {e}")
        
        # 检查其他可能的统计表
        for possible_table in ['reading_sessions', 'statistics', 'page_stats']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {possible_table};")
                count = cursor.fetchone()[0]
                print(f"📈 {possible_table}表: {count} 条记录")
            except sqlite3.OperationalError:
                pass
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 分析SQLite文件时出错: {e}")

async def main():
    """主函数"""
    print("🚀 KOReader真实数据分析")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = await download_and_analyze_sqlite()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 分析完成！")
    else:
        print("❌ 分析失败")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 