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
        
        # 事务管理由调用方统一处理，这里不进行提交
        return md5_to_book_id
    
    async def _clear_user_data(self, user_id: int) -> Dict[str, int]:
        """
        清理用户的所有阅读数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            清理统计信息
        """
        try:
            # 统计清理前的数据量
            books_count_result = await self.db.execute(
                select(func.count(Book.id)).where(Book.user_id == user_id)
            )
            books_count = books_count_result.scalar() or 0
            
            sessions_count_result = await self.db.execute(
                select(func.count(ReadingSession.id))
                .join(Book)
                .where(Book.user_id == user_id)
            )
            sessions_count = sessions_count_result.scalar() or 0
            
            # 删除用户的所有书籍（reading_sessions会通过外键级联删除）
            books_to_delete = await self.db.execute(
                select(Book).where(Book.user_id == user_id)
            )
            books = books_to_delete.scalars().all()
            
            for book in books:
                await self.db.delete(book)
            
            print(f"🗑️ 清理用户数据: {books_count} 本书籍, {sessions_count} 条阅读记录")
            
            return {
                'books_cleared': books_count,
                'sessions_cleared': sessions_count
            }
            
        except Exception as e:
            print(f"清理用户数据时出错: {e}")
            raise
    
    async def _sync_reading_sessions(
        self, 
        user_id: int,
        page_stats_data: List[Dict[str, Any]], 
        books_data: List[Dict[str, Any]]
    ) -> int:
        """
        同步阅读会话数据（全量替换）
        
        Args:
            user_id: 用户ID
            page_stats_data: 页面统计数据列表
            books_data: 书籍数据列表（包含KOReader原始ID和md5）
            
        Returns:
            新增的阅读会话数量
        """
        new_sessions_count = 0
        
        # 创建KOReader book_id到md5的映射
        koreader_id_to_md5 = {}
        for book_data in books_data:
            koreader_id = book_data.get('id')
            md5 = book_data.get('md5')
            if koreader_id and md5:
                koreader_id_to_md5[koreader_id] = md5
        
        # 获取用户当前的所有书籍（新同步的），建立md5到database_book_id的映射
        books_result = await self.db.execute(
            select(Book).where(Book.user_id == user_id)
        )
        books = books_result.scalars().all()
        
        md5_to_book_id = {}
        for book in books:
            if book.md5:
                md5_to_book_id[book.md5] = book.id
        
        print(f"📖 准备同步 {len(page_stats_data)} 条阅读记录")
        processed_count = 0
        
        for stat in page_stats_data:
            try:
                # 提取阅读会话信息
                koreader_book_id = stat.get('id_book')
                page = stat.get('page')
                start_time_timestamp = stat.get('start_time')
                duration = stat.get('duration', 0)
                total_pages_at_time = stat.get('total_pages')
                
                if not all([koreader_book_id is not None, page is not None, start_time_timestamp]):
                    continue
                
                # 通过KOReader book_id找到对应的数据库book_id
                md5 = koreader_id_to_md5.get(koreader_book_id)
                if not md5:
                    continue
                    
                book_id = md5_to_book_id.get(md5)
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
                
                # 创建新的阅读会话（全量替换，不检查重复）
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
                
                try:
                    # 3. 开始全量替换同步（在单个事务中完成）
                    print(f"🔄 开始全量同步用户数据 (用户ID: {user_id})")
                    
                    # 3.1 清理现有数据
                    clear_stats = await self._clear_user_data(user_id)
                    
                    # 3.2 同步书籍数据
                    md5_to_book_id = await self._sync_books(user_id, parsed_data['books'])
                    books_synced = len(md5_to_book_id)
                    
                    # 3.3 同步阅读会话数据
                    sessions_synced = await self._sync_reading_sessions(
                        user_id,
                        parsed_data['page_stats'], 
                        parsed_data['books']
                    )
                    
                    # 3.4 提交所有更改
                    await self.db.commit()
                    
                    print(f"✅ 全量同步完成!")
                    print(f"📚 清理书籍: {clear_stats['books_cleared']} → 新增书籍: {books_synced}")
                    print(f"📊 清理阅读记录: {clear_stats['sessions_cleared']} → 新增阅读记录: {sessions_synced}")
                    
                    return {
                        'success': True,
                        'error': None,
                        'books_synced': books_synced,
                        'sessions_synced': sessions_synced,
                        'books_cleared': clear_stats['books_cleared'],
                        'sessions_cleared': clear_stats['sessions_cleared'],
                        'remote_path': remote_path
                    }
                    
                except Exception as sync_error:
                    # 同步过程中出错，回滚事务
                    await self.db.rollback()
                    print(f"❌ 同步过程中出错，已回滚所有更改: {sync_error}")
                    raise sync_error
                
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