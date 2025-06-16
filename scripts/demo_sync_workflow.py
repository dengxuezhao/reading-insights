#!/usr/bin/env python3
"""
KOReader数据同步工作流演示

此脚本演示了完整的数据同步流程，包括：
1. 创建模拟的KOReader数据
2. 通过API上传到数据库
3. 验证同步结果

注意：这是演示版本，不需要真实的WebDAV凭据
"""

import requests
import json
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta
import random

API_BASE = "http://localhost:8000/api/v1"

# 演示用户配置
DEMO_USER = {
    "username": "demo_sync_user",
    "password": "demo123456"
}

def create_sample_statistics_file():
    """创建演示用的statistics.sqlite3文件"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3')
    temp_path = temp_file.name
    temp_file.close()
    
    # 连接SQLite数据库
    conn = sqlite3.connect(temp_path)
    cursor = conn.cursor()
    
    # 创建book表（KOReader格式）
    cursor.execute('''
        CREATE TABLE book (
            md5 TEXT PRIMARY KEY,
            title TEXT,
            author TEXT,
            pages INTEGER
        )
    ''')
    
    # 创建page_stat_data表（KOReader格式）
    cursor.execute('''
        CREATE TABLE page_stat_data (
            id_book TEXT,
            page INTEGER,
            start_time INTEGER,
            duration INTEGER,
            total_pages INTEGER,
            FOREIGN KEY (id_book) REFERENCES book (md5)
        )
    ''')
    
    # 插入演示书籍数据
    books = [
        ("demo_book_1_md5", "《深入理解计算机系统》", "Randal E. Bryant", 800),
        ("demo_book_2_md5", "《算法导论》", "Thomas H. Cormen", 1200),
        ("demo_book_3_md5", "《设计模式》", "Gang of Four", 395),
        ("demo_book_4_md5", "《重构：改善既有代码的设计》", "Martin Fowler", 431),
        ("demo_book_5_md5", "《代码大全》", "Steve McConnell", 960),
    ]
    
    cursor.executemany('''
        INSERT INTO book (md5, title, author, pages) VALUES (?, ?, ?, ?)
    ''', books)
    
    # 生成真实的阅读数据
    base_time = int((datetime.now() - timedelta(days=60)).timestamp())
    reading_sessions = []
    
    for i, (md5, title, author, pages) in enumerate(books):
        # 为每本书生成阅读历史
        book_start_day = i * 10  # 每本书间隔10天开始
        reading_days = random.randint(15, 30)  # 每本书阅读15-30天
        
        current_page = 1
        for day in range(reading_days):
            # 每天1-3次阅读会话
            sessions_per_day = random.randint(1, 3)
            
            for session in range(sessions_per_day):
                # 阅读时间：5分钟到2小时
                duration = random.randint(300, 7200)
                
                # 根据阅读时间推进页数
                pages_read = max(1, duration // 180)  # 平均3分钟一页
                current_page = min(current_page + pages_read, pages)
                
                # 计算时间戳
                session_time = base_time + (book_start_day + day) * 86400 + session * 3600 + random.randint(0, 3600)
                
                reading_sessions.append((md5, current_page, session_time, duration, pages))
                
                # 如果读完了就停止
                if current_page >= pages:
                    break
            
            if current_page >= pages:
                break
    
    cursor.executemany('''
        INSERT INTO page_stat_data (id_book, page, start_time, duration, total_pages) 
        VALUES (?, ?, ?, ?, ?)
    ''', reading_sessions)
    
    conn.commit()
    conn.close()
    
    print(f"📚 创建演示数据文件: {os.path.basename(temp_path)}")
    print(f"📖 书籍数量: {len(books)}")
    print(f"📊 阅读记录数量: {len(reading_sessions)}")
    
    # 显示一些统计信息
    total_duration = sum(session[3] for session in reading_sessions)
    total_hours = total_duration / 3600
    print(f"⏱️ 总阅读时间: {total_hours:.1f} 小时")
    
    return temp_path

def analyze_sqlite_file(sqlite_path):
    """分析SQLite文件内容"""
    print("\n🔍 分析SQLite文件内容:")
    
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    
    # 查看书籍信息
    cursor.execute("SELECT * FROM book")
    books = cursor.fetchall()
    print(f"📚 书籍列表:")
    for book in books:
        print(f"  - {book[1]} ({book[2]}) - {book[3]}页")
    
    # 统计阅读数据
    cursor.execute("""
        SELECT id_book, COUNT(*) as sessions, SUM(duration) as total_time, MAX(page) as max_page
        FROM page_stat_data 
        GROUP BY id_book
    """)
    stats = cursor.fetchall()
    
    print(f"\n📊 阅读统计:")
    book_dict = {book[0]: book[1] for book in books}
    for stat in stats:
        book_title = book_dict.get(stat[0], "Unknown")
        sessions = stat[1]
        hours = stat[2] / 3600
        max_page = stat[3]
        print(f"  - {book_title}: {sessions}次会话, {hours:.1f}小时, 读到第{max_page}页")
    
    conn.close()

def create_or_login_user():
    """创建或登录演示用户"""
    print("\n👤 创建/登录演示用户...")
    
    # 尝试注册用户
    try:
        response = requests.post(f"{API_BASE}/auth/register", json=DEMO_USER, timeout=10)
        if response.status_code in [200, 201]:
            print("✅ 演示用户创建成功")
        elif response.status_code == 400:
            print("ℹ️ 演示用户已存在")
        else:
            print(f"⚠️ 用户注册响应: {response.status_code}")
    except Exception as e:
        print(f"❌ 用户注册异常: {e}")
        return None
    
    # 登录获取Token
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=DEMO_USER, timeout=10)
        if response.status_code == 200:
            token = response.json().get("access_token")
            print("✅ 用户登录成功")
            return token
        else:
            print(f"❌ 用户登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 用户登录异常: {e}")
        return None

def simulate_data_sync(token, sqlite_path):
    """模拟数据同步过程"""
    print("\n🔄 模拟数据同步过程...")
    
    # 这里我们直接使用数据同步服务解析SQLite文件
    # 在实际场景中，这个文件会从WebDAV下载
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 模拟从本地文件同步（实际中是从WebDAV下载）
    try:
        # 读取并解析SQLite文件
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        from backend.app.database import AsyncSessionLocal
        from backend.app.services.data_sync_service import DataSyncService
        import asyncio
        
        async def perform_sync():
            async with AsyncSessionLocal() as db:
                sync_service = DataSyncService(db)
                
                # 解析本地SQLite文件
                parsed_data = sync_service._parse_sqlite_file(sqlite_path)
                print(f"📚 解析到 {len(parsed_data['books'])} 本书籍")
                print(f"📊 解析到 {len(parsed_data['page_stats'])} 条阅读记录")
                
                # 获取用户ID（这里我们需要从token中解析，或直接查询）
                from backend.app.services.auth_service import AuthService
                auth_service = AuthService(db)
                user = await auth_service.get_user_by_username(DEMO_USER["username"])
                
                if not user:
                    print("❌ 找不到用户")
                    return None
                
                # 同步书籍数据
                md5_to_book_id = await sync_service._sync_books(user.id, parsed_data['books'])
                books_synced = len(md5_to_book_id)
                
                # 同步阅读会话数据
                sessions_synced = await sync_service._sync_reading_sessions(
                    parsed_data['page_stats'], 
                    md5_to_book_id
                )
                
                return {
                    'success': True,
                    'books_synced': books_synced,
                    'sessions_synced': sessions_synced
                }
        
        # 执行异步同步
        result = asyncio.run(perform_sync())
        
        if result and result['success']:
            print("✅ 数据同步成功!")
            print(f"📚 同步书籍数量: {result['books_synced']}")
            print(f"📊 同步阅读记录数量: {result['sessions_synced']}")
            return result
        else:
            print("❌ 数据同步失败")
            return None
            
    except Exception as e:
        print(f"❌ 数据同步异常: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_sync_status(token):
    """获取同步状态"""
    print("\n📊 获取同步状态...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/sync/status", headers=headers, timeout=10)
        if response.status_code == 200:
            status = response.json()
            print("📈 同步状态:")
            print(f"  📚 总书籍数: {status.get('total_books', 0)}")
            print(f"  📊 总阅读记录数: {status.get('total_sessions', 0)}")
            print(f"  🕒 最后阅读时间: {status.get('last_reading_time', 'N/A')}")
            print(f"  🔗 WebDAV已配置: {status.get('has_webdav_config', False)}")
            return status
        else:
            print(f"❌ 获取同步状态失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 获取同步状态异常: {e}")
        return None

def test_dashboard_apis(token):
    """测试仪表盘API"""
    print("\n📊 测试仪表盘API...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试仪表盘摘要
    try:
        response = requests.get(f"{API_BASE}/dashboard/summary", headers=headers, timeout=10)
        if response.status_code == 200:
            summary = response.json()
            print("📈 仪表盘摘要:")
            print(f"  📚 总书籍数: {summary.get('total_books', 0)}")
            print(f"  📊 总阅读时间: {summary.get('total_reading_time', 0)} 秒")
            print(f"  📖 平均阅读速度: {summary.get('average_reading_speed', 0):.2f} 页/分钟")
        else:
            print(f"❌ 仪表盘摘要失败: {response.text}")
    except Exception as e:
        print(f"❌ 仪表盘摘要异常: {e}")
    
    # 测试日历数据
    try:
        response = requests.get(f"{API_BASE}/dashboard/calendar", headers=headers, timeout=10)
        if response.status_code == 200:
            calendar_data = response.json()
            print(f"📅 日历数据: {len(calendar_data)} 天有阅读记录")
        else:
            print(f"❌ 日历数据失败: {response.text}")
    except Exception as e:
        print(f"❌ 日历数据异常: {e}")

def main():
    """主演示函数"""
    print("🚀 KOReader数据同步工作流演示")
    print("=" * 80)
    
    # 1. 测试服务器连接
    print("\n1. 🔍 测试服务器连接...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器连接正常")
        else:
            print("❌ 服务器响应异常")
            return
    except Exception as e:
        print(f"❌ 服务器无法连接: {e}")
        print("请确保服务器正在运行: uv run python scripts/dev.py")
        return
    
    # 2. 创建演示数据
    print("\n2. 📝 创建演示KOReader数据...")
    sqlite_file = create_sample_statistics_file()
    
    # 3. 分析SQLite文件
    analyze_sqlite_file(sqlite_file)
    
    # 4. 创建/登录用户
    token = create_or_login_user()
    if not token:
        os.remove(sqlite_file)
        return
    
    # 5. 执行数据同步
    sync_result = simulate_data_sync(token, sqlite_file)
    
    # 清理临时文件
    os.remove(sqlite_file)
    
    if not sync_result:
        return
    
    # 6. 获取同步状态
    get_sync_status(token)
    
    # 7. 测试仪表盘API
    test_dashboard_apis(token)
    
    print("\n🎉 演示完成!")
    print("=" * 80)
    print("✅ 成功演示了KOReader数据同步流程")
    print("📚 模拟数据已导入到数据库")
    print("🌐 您可以访问 http://localhost:8000/docs 查看完整API")
    print("📊 您可以通过仪表盘API查看阅读统计")

if __name__ == "__main__":
    main() 