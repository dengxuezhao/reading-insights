import os
import sqlite3
import asyncio
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.dialects.postgresql import insert

from backend.app.models.user import User
from backend.app.models.book import Book
from backend.app.models.reading_session import ReadingSession
from backend.app.services.webdav_service import WebDAVService


class DataSyncService:
    """数据同步服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.webdav_service = WebDAVService(db)
    
    def _parse_sqlite_file(self, sqlite_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        解析KOReader的SQLite统计文件
        
        Args:
            sqlite_path: SQLite文件路径
            
        Returns:
            解析后的数据，包含books和page_stats两个列表
        """
        try:
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()
            
            # 解析书籍数据
            books_data = []
            try:
                cursor.execute("""
                    SELECT id, title, authors, pages, md5, series, language
                    FROM book
                """)
                for row in cursor.fetchall():
                    books_data.append({
                        'id': row[0],
                        'title': row[1] or 'Unknown Title',
                        'authors': row[2] or 'Unknown Author',
                        'pages': row[3] or 0,
                        'md5': row[4],
                        'series': row[5],
                        'language': row[6]
                    })
            except sqlite3.OperationalError as e:
                print(f"解析book表时出错: {e}")
            
            # 解析阅读统计数据 - 尝试不同的表名和字段名
            page_stats_data = []
            
            # 首先尝试page_stat_data表（真实的KOReader格式）
            try:
                cursor.execute("""
                    SELECT id_book, page, start_time, duration, total_pages
                    FROM page_stat_data
                """)
                for row in cursor.fetchall():
                    page_stats_data.append({
                        'id_book': row[0],
                        'page': row[1],
                        'start_time': row[2],
                        'duration': row[3],  # 真实KOReader使用duration字段
                        'total_pages': row[4]
                    })
                print(f"✅ 从page_stat_data表解析了 {len(page_stats_data)} 条阅读记录")
            except sqlite3.OperationalError:
                # 如果page_stat_data不存在，尝试page_stat表（旧格式或其他格式）
                try:
                    cursor.execute("""
                        SELECT id_book, page, start_time, period, total_pages
                        FROM page_stat
                    """)
                    for row in cursor.fetchall():
                        page_stats_data.append({
                            'id_book': row[0],
                            'page': row[1],
                            'start_time': row[2],
                            'duration': row[3],  # 转换period为duration
                            'total_pages': row[4]
                        })
                    print(f"✅ 从page_stat表解析了 {len(page_stats_data)} 条阅读记录")
                except sqlite3.OperationalError as e:
                    print(f"❌ 解析阅读统计表时出错: {e}")
            
            conn.close()
            
            print(f"📊 解析完成: {len(books_data)} 本书籍, {len(page_stats_data)} 条阅读记录")
            
            return {
                'books': books_data,
                'page_stats': page_stats_data
            }
            
        except Exception as e:
            print(f"解析SQLite文件时出错: {e}")
            return {'books': [], 'page_stats': []}
    
    async def _sync_books(self, user_id: int, books_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        同步书籍数据
        
        Args:
            user_id: 用户ID
            books_data: 书籍数据列表
            
        Returns:
            md5到book_id的映射字典
        """
        md5_to_book_id = {}
        
        for book_data in books_data:
            try:
                # 提取书籍信息
                title = book_data.get('title', 'Unknown Title')
                author = book_data.get('authors', 'Unknown Author')
                md5 = book_data.get('md5')
                total_pages = book_data.get('pages')
                
                if not md5:
                    continue
                
                # 检查书籍是否已存在
                result = await self.db.execute(
                    select(Book).where(
                        and_(Book.user_id == user_id, Book.md5 == md5)
                    )
                )
                existing_book = result.scalar_one_or_none()
                
                if existing_book:
                    # 更新现有书籍信息
                    existing_book.title = title
                    existing_book.author = author
                    if total_pages:
                        existing_book.total_pages = total_pages
                    md5_to_book_id[md5] = existing_book.id
                else:
                    # 创建新书籍
                    new_book = Book(
                        user_id=user_id,
                        title=title,
                        author=author,
                        md5=md5,
                        total_pages=total_pages
                    )
                    self.db.add(new_book)
                    await self.db.flush()  # 获取生成的ID
                    md5_to_book_id[md5] = new_book.id
                    
            except Exception as e:
                print(f"同步书籍数据时出错: {e}")
                continue
        
        await self.db.commit()
        return md5_to_book_id
    
    async def _sync_reading_sessions(
        self, 
        page_stats_data: List[Dict[str, Any]], 
        md5_to_book_id: Dict[str, int]
    ) -> int:
        """
        同步阅读会话数据
        
        Args:
            page_stats_data: 页面统计数据列表
            md5_to_book_id: md5到book_id的映射
            
        Returns:
            新增的阅读会话数量
        """
        new_sessions_count = 0
        
        # 创建book_id映射（KOReader使用数字ID，需要转换）
        # 首先获取所有已同步书籍的信息
        result = await self.db.execute(
            select(Book.id, Book.md5).where(Book.user_id == list(md5_to_book_id.values())[0] // 1000 if md5_to_book_id else 1)
        )
        
        # 重新获取用户ID
        if md5_to_book_id:
            user_id = None
            for book_id in md5_to_book_id.values():
                book_result = await self.db.execute(
                    select(Book.user_id).where(Book.id == book_id)
                )
                book = book_result.scalar_one_or_none()
                if book:
                    user_id = book
                    break
        else:
            return 0
        
        # 获取用户的所有书籍，建立KOReader ID到数据库book_id的映射
        books_result = await self.db.execute(
            select(Book).where(Book.user_id == user_id)
        )
        books = books_result.scalars().all()
        
        # 创建从KOReader book.id到我们数据库book_id的映射
        koreader_id_to_book_id = {}
        for book in books:
            # 由于我们在书籍同步时可能没有保存KOReader的原始ID，
            # 我们需要通过md5匹配来建立关联
            for md5, db_book_id in md5_to_book_id.items():
                if db_book_id == book.id:
                    # 查找对应的KOReader ID
                    for stat in page_stats_data:
                        if stat.get('id_book'):
                            koreader_id_to_book_id[stat['id_book']] = book.id
                            break
        
        print(f"📖 准备同步 {len(page_stats_data)} 条阅读记录")
        processed_count = 0
        
        for stat in page_stats_data:
            try:
                # 提取阅读会话信息
                koreader_book_id = stat.get('id_book')
                page = stat.get('page')
                start_time_timestamp = stat.get('start_time')
                duration = stat.get('duration', 0)  # 真实KOReader使用duration字段
                total_pages_at_time = stat.get('total_pages')
                
                if not all([koreader_book_id is not None, page is not None, start_time_timestamp]):
                    continue
                
                # 查找对应的数据库book_id
                book_id = None
                for book in books:
                    # 通过KOReader book ID匹配
                    # 由于我们无法直接映射，我们使用一个简化的方法：
                    # 假设KOReader的book ID对应我们数据库中的书籍顺序
                    if koreader_book_id <= len(books):
                        # 找到第koreader_book_id本书（按ID排序）
                        sorted_books = sorted(books, key=lambda b: b.id)
                        if koreader_book_id <= len(sorted_books):
                            book_id = sorted_books[koreader_book_id - 1].id
                            break
                
                if not book_id:
                    continue
                
                # 解析时间戳
                try:
                    if isinstance(start_time_timestamp, (int, float)):
                        start_time = datetime.fromtimestamp(start_time_timestamp)
                    else:
                        start_time = datetime.fromisoformat(str(start_time_timestamp).replace('Z', '+00:00'))
                except (ValueError, TypeError, OSError) as e:
                    print(f"时间戳解析失败: {start_time_timestamp}, 错误: {e}")
                    continue
                
                # 检查是否已存在相同的阅读会话（避免重复导入）
                result = await self.db.execute(
                    select(ReadingSession).where(
                        and_(
                            ReadingSession.book_id == book_id,
                            ReadingSession.page == page,
                            ReadingSession.start_time == start_time
                        )
                    )
                )
                existing_session = result.scalar_one_or_none()
                
                if not existing_session:
                    # 创建新的阅读会话
                    new_session = ReadingSession(
                        book_id=book_id,
                        page=page,
                        start_time=start_time,
                        duration=duration,
                        total_pages_at_time=total_pages_at_time
                    )
                    self.db.add(new_session)
                    new_sessions_count += 1
                
                processed_count += 1
                if processed_count % 100 == 0:
                    print(f"  已处理 {processed_count}/{len(page_stats_data)} 条记录")
                    
            except Exception as e:
                print(f"同步阅读会话数据时出错: {e}, 数据: {stat}")
                continue
        
        await self.db.commit()
        print(f"✅ 成功同步 {new_sessions_count} 条新的阅读记录")
        return new_sessions_count
    
    async def sync_user_data(self, user_id: int, remote_path: str = None) -> Dict[str, Any]:
        """
        同步用户的阅读数据
        
        Args:
            user_id: 用户ID
            remote_path: 远程SQLite文件路径，如果为None则自动查找
            
        Returns:
            同步结果统计
        """
        try:
            # 1. 从WebDAV下载统计文件
            if remote_path is None:
                remote_path = await self.webdav_service.find_statistics_file(user_id)
                if not remote_path:
                    return {
                        'success': False,
                        'error': '未找到statistics.sqlite3文件',
                        'books_synced': 0,
                        'sessions_synced': 0
                    }
            
            local_path = await self.webdav_service.download_statistics_file(user_id, remote_path)
            if not local_path:
                return {
                    'success': False,
                    'error': '下载statistics.sqlite3文件失败',
                    'books_synced': 0,
                    'sessions_synced': 0
                }
            
            try:
                # 2. 解析SQLite文件
                parsed_data = self._parse_sqlite_file(local_path)
                
                # 3. 同步书籍数据
                md5_to_book_id = await self._sync_books(user_id, parsed_data['books'])
                books_synced = len(md5_to_book_id)
                
                # 4. 同步阅读会话数据
                sessions_synced = await self._sync_reading_sessions(
                    parsed_data['page_stats'], 
                    md5_to_book_id
                )
                
                return {
                    'success': True,
                    'error': None,
                    'books_synced': books_synced,
                    'sessions_synced': sessions_synced,
                    'remote_path': remote_path
                }
                
            finally:
                # 清理临时文件
                if os.path.exists(local_path):
                    os.remove(local_path)
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'同步数据时出错: {str(e)}',
                'books_synced': 0,
                'sessions_synced': 0
            }
    
    async def get_sync_status(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户的同步状态
        
        Args:
            user_id: 用户ID
            
        Returns:
            同步状态信息
        """
        try:
            # 获取用户的书籍数量 - 使用COUNT查询
            books_count_result = await self.db.execute(
                select(func.count(Book.id)).where(Book.user_id == user_id)
            )
            total_books = books_count_result.scalar() or 0
            
            # 获取用户的阅读会话数量 - 使用COUNT查询
            sessions_count_result = await self.db.execute(
                select(func.count(ReadingSession.id))
                .join(Book)
                .where(Book.user_id == user_id)
            )
            total_sessions = sessions_count_result.scalar() or 0
            
            # 获取最后一次阅读时间
            last_session_result = await self.db.execute(
                select(ReadingSession.start_time)
                .join(Book)
                .where(Book.user_id == user_id)
                .order_by(ReadingSession.start_time.desc())
                .limit(1)
            )
            last_reading_time = last_session_result.scalar_one_or_none()
            
            # 检查WebDAV配置
            has_webdav = await self.webdav_service.get_webdav_config(user_id) is not None
            
            return {
                'total_books': total_books,
                'total_sessions': total_sessions,
                'last_reading_time': last_reading_time.isoformat() if last_reading_time else None,
                'has_webdav_config': has_webdav
            }
            
        except Exception as e:
            print(f"获取同步状态失败: {e}")
            return {
                'total_books': 0,
                'total_sessions': 0,
                'last_reading_time': None,
                'has_webdav_config': False,
                'error': str(e)
            } 