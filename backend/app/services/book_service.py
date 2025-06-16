from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import joinedload

from backend.app.models.book import Book
from backend.app.models.reading_session import ReadingSession
from backend.app.models.highlight import Highlight
from backend.app.schemas.book import BookResponse, BookDetail, BookList


class BookService:
    """书籍服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_books(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> BookList:
        """获取用户书籍列表"""
        try:
            # 构建查询条件
            query = select(Book).where(Book.user_id == user_id)
            
            # 添加搜索条件
            if search and search.strip():
                search_term = f"%{search.strip()}%"
                query = query.where(
                    (Book.title.ilike(search_term)) | 
                    (Book.author.ilike(search_term))
                )
            
            # 获取总数
            count_query = select(func.count(Book.id)).where(Book.user_id == user_id)
            if search and search.strip():
                search_term = f"%{search.strip()}%"
                count_query = count_query.where(
                    (Book.title.ilike(search_term)) | 
                    (Book.author.ilike(search_term))
                )
            
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0
            
            # 添加排序、分页
            query = query.order_by(desc(Book.id)).offset(skip).limit(limit)
            
            # 执行查询
            result = await self.db.execute(query)
            books = result.scalars().all()
            
            # 为每本书计算统计信息
            book_responses = []
            for book in books:
                # 计算阅读进度和统计信息
                stats = await self._calculate_book_stats(book.id, user_id)
                
                book_response = BookResponse(
                    id=book.id,
                    title=book.title,
                    author=book.author,
                    total_pages=book.total_pages,
                    cover_image_url=book.cover_image_url,
                    md5=book.md5,
                    reading_progress=stats["reading_progress"],
                    total_reading_time=stats["total_reading_time"],
                    last_read_time=stats["last_read_time"]
                )
                book_responses.append(book_response)
            
            # 计算分页信息
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return BookList(
                books=book_responses,
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except Exception as e:
            print(f"获取用户书籍列表失败: {e}")
            return BookList(
                books=[],
                total=0,
                page=1,
                page_size=limit,
                total_pages=0
            )
    
    async def get_book_detail(self, book_id: int, user_id: int) -> Optional[BookDetail]:
        """获取书籍详情"""
        try:
            # 查询书籍信息并验证权限
            result = await self.db.execute(
                select(Book).where(Book.id == book_id, Book.user_id == user_id)
            )
            book = result.scalar_one_or_none()
            
            if not book:
                return None
            
            # 获取已读页码数组（去重并排序）
            pages_result = await self.db.execute(
                select(ReadingSession.page)
                .where(ReadingSession.book_id == book_id)
                .distinct()
                .order_by(ReadingSession.page)
            )
            read_pages = [row.page for row in pages_result]
            
            # 计算基础统计信息
            stats = await self._calculate_book_stats(book_id, user_id)
            
            # 获取阅读会话数量
            sessions_result = await self.db.execute(
                select(func.count(ReadingSession.id))
                .where(ReadingSession.book_id == book_id)
            )
            sessions_count = sessions_result.scalar() or 0
            
            # 获取标注数量
            highlights_result = await self.db.execute(
                select(func.count(Highlight.id))
                .where(Highlight.book_id == book_id)
            )
            highlights_count = highlights_result.scalar() or 0
            
            return BookDetail(
                id=book.id,
                title=book.title,
                author=book.author,
                total_pages=book.total_pages,
                cover_image_url=book.cover_image_url,
                md5=book.md5,
                reading_progress=stats["reading_progress"],
                total_reading_time=stats["total_reading_time"],
                last_read_time=stats["last_read_time"],
                read_pages=read_pages,
                read_pages_count=len(read_pages),
                reading_sessions_count=sessions_count,
                highlights_count=highlights_count,
                created_at=book.created_at
            )
            
        except Exception as e:
            print(f"获取书籍详情失败: {e}")
            return None
    
    async def delete_book(self, book_id: int, user_id: int) -> bool:
        """删除书籍及其相关数据"""
        try:
            # 验证书籍存在且属于当前用户
            result = await self.db.execute(
                select(Book).where(Book.id == book_id, Book.user_id == user_id)
            )
            book = result.scalar_one_or_none()
            
            if not book:
                return False
            
            # 开始事务删除操作
            # 1. 删除相关的标注记录
            await self.db.execute(
                select(Highlight).where(Highlight.book_id == book_id)
            )
            highlights_to_delete = await self.db.execute(
                select(Highlight).where(Highlight.book_id == book_id)
            )
            for highlight in highlights_to_delete.scalars():
                await self.db.delete(highlight)
            
            # 2. 删除相关的阅读会话记录
            sessions_to_delete = await self.db.execute(
                select(ReadingSession).where(ReadingSession.book_id == book_id)
            )
            for session in sessions_to_delete.scalars():
                await self.db.delete(session)
            
            # 3. 删除书籍记录
            await self.db.delete(book)
            
            # 提交事务
            await self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"删除书籍失败: {e}")
            await self.db.rollback()
            return False
    
    async def _calculate_book_stats(self, book_id: int, user_id: int) -> dict:
        """计算单本书籍的统计信息"""
        try:
            # 计算总阅读时长
            duration_result = await self.db.execute(
                select(func.sum(ReadingSession.duration))
                .where(ReadingSession.book_id == book_id)
            )
            total_reading_time = int(duration_result.scalar() or 0)
            
            # 计算已读页数（去重）
            pages_result = await self.db.execute(
                select(func.count(func.distinct(ReadingSession.page)))
                .where(ReadingSession.book_id == book_id)
            )
            read_pages_count = int(pages_result.scalar() or 0)
            
            # 获取总页数计算进度
            book_result = await self.db.execute(
                select(Book.total_pages).where(Book.id == book_id)
            )
            total_pages = book_result.scalar() or 0
            
            # 计算阅读进度
            reading_progress = 0.0
            if total_pages and total_pages > 0:
                reading_progress = (read_pages_count / total_pages) * 100
                reading_progress = min(100.0, max(0.0, reading_progress))  # 限制在0-100之间
            
            # 获取最后阅读时间
            last_read_result = await self.db.execute(
                select(func.max(ReadingSession.start_time))
                .where(ReadingSession.book_id == book_id)
            )
            last_read_time = last_read_result.scalar()
            
            return {
                "total_reading_time": total_reading_time,
                "reading_progress": round(reading_progress, 2),
                "last_read_time": last_read_time
            }
            
        except Exception as e:
            print(f"计算书籍统计信息失败: {e}")
            return {
                "total_reading_time": 0,
                "reading_progress": 0.0,
                "last_read_time": None
            } 