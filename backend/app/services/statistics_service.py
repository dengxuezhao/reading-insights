"""
统计服务模块
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, text, distinct, extract
from datetime import datetime, date, timedelta

from backend.app.models.user import User
from backend.app.models.book import Book
from backend.app.models.reading_session import ReadingSession
from backend.app.models.highlight import Highlight


class StatisticsService:
    """统计数据服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_dashboard_summary(self, user_id: int) -> Dict[str, Any]:
        """获取仪表盘摘要统计"""
        try:
            # 1. 总书籍数量
            total_books = await self._get_total_books(user_id)
            
            # 2. 总阅读时长（秒）
            total_reading_time = await self._get_total_reading_time(user_id)
            
            # 3. 总计已读页数（去重）
            total_pages_read = await self._get_total_pages_read(user_id)
            
            # 4. 总标注数量
            total_highlights = await self._get_total_highlights(user_id)
            
            # 5. 平均阅读速度（页/小时）
            avg_reading_speed = await self._calculate_average_reading_speed(
                total_pages_read, total_reading_time
            )
            
            # 6. 连续阅读天数
            reading_streaks = await self._calculate_reading_streaks(user_id)
            
            # 7. 最喜欢的阅读时段
            favorite_reading_hour = await self._get_favorite_reading_hour(user_id)
            
            # 8. 本周阅读时长
            this_week_reading_time = await self._get_period_reading_time(user_id, days=7)
            
            # 9. 本月阅读时长
            this_month_reading_time = await self._get_period_reading_time(user_id, days=30)
            
            return {
                "total_books": total_books,
                "total_reading_time": total_reading_time,
                "total_pages_read": total_pages_read,
                "total_highlights": total_highlights,
                "books_in_progress": total_books,  # 简化：假设所有书都在进行中
                "books_completed": 0,  # TODO: 需要从书籍状态判断
                "avg_reading_speed": avg_reading_speed,
                "reading_streak": reading_streaks["current_streak"],
                "max_reading_streak": reading_streaks["max_streak"],
                "favorite_reading_hour": favorite_reading_hour,
                "this_week_reading_time": this_week_reading_time,
                "this_month_reading_time": this_month_reading_time,
            }
        except Exception as e:
            print(f"获取仪表盘摘要失败: {e}")
            return self._get_empty_dashboard_summary()
    
    async def _get_total_books(self, user_id: int) -> int:
        """获取总书籍数量"""
        result = await self.db.execute(
            select(func.count(Book.id)).where(Book.user_id == user_id)
        )
        return result.scalar() or 0
    
    async def _get_total_reading_time(self, user_id: int) -> int:
        """
        获取总阅读时长
        
        来源: 对 reading_sessions 表中所有记录的 duration 字段求和
        单位: 秒
        """
        result = await self.db.execute(
            select(func.sum(ReadingSession.duration))
            .join(Book, ReadingSession.book_id == Book.id)
            .where(Book.user_id == user_id)
        )
        return int(result.scalar() or 0)
    
    async def _get_total_pages_read(self, user_id: int) -> int:
        """
        获取总计已读页数
        
        来源: 对 reading_sessions 表中所有记录的 page 和 book_id 进行去重计数
        逻辑: COUNT(DISTINCT (book_id, page))
        """
        # 使用子查询来实现 COUNT(DISTINCT book_id, page)
        subquery = select(
            ReadingSession.book_id,
            ReadingSession.page
        ).join(Book, ReadingSession.book_id == Book.id).where(
            Book.user_id == user_id
        ).distinct()
        
        result = await self.db.execute(
            select(func.count()).select_from(subquery.subquery())
        )
        return int(result.scalar() or 0)
    
    async def _get_total_highlights(self, user_id: int) -> int:
        """获取总标注数量"""
        result = await self.db.execute(
            select(func.count(Highlight.id))
            .join(Book, Highlight.book_id == Book.id)
            .where(Book.user_id == user_id)
        )
        return int(result.scalar() or 0)
    
    async def _calculate_average_reading_speed(self, total_pages: int, total_time_seconds: int) -> float:
        """
        计算平均阅读速度
        
        公式: 总计已读页数 / (总阅读时长 / 3600)
        单位: 页/小时
        """
        if total_time_seconds <= 0:
            return 0.0
        
        total_hours = total_time_seconds / 3600.0
        return round(total_pages / total_hours, 2) if total_hours > 0 else 0.0
    
    async def _calculate_reading_streaks(self, user_id: int) -> Dict[str, int]:
        """
        计算连续阅读天数
        
        返回:
            - max_streak: 最长连续天数
            - current_streak: 当前连续天数
        """
        try:
            # 获取所有不重复的阅读日期，按升序排列
            result = await self.db.execute(
                select(func.date(ReadingSession.start_time).label('reading_date'))
                .join(Book, ReadingSession.book_id == Book.id)
                .where(Book.user_id == user_id)
                .group_by(func.date(ReadingSession.start_time))
                .order_by(func.date(ReadingSession.start_time))
            )
            
            reading_dates = [row.reading_date for row in result]
            
            if not reading_dates:
                return {"max_streak": 0, "current_streak": 0}
            
            # 计算最长连续天数和当前连续天数
            max_streak = 1
            current_streak = 1
            
            for i in range(1, len(reading_dates)):
                current_date = reading_dates[i]
                previous_date = reading_dates[i - 1]
                
                # 检查是否连续（相差1天）
                if (current_date - previous_date).days == 1:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 1
            
            # 检查当前连续天数是否有效
            today = date.today()
            yesterday = today - timedelta(days=1)
            last_reading_date = reading_dates[-1]
            
            # 如果最后阅读日期不是今天或昨天，当前连续天数为0
            if last_reading_date not in [today, yesterday]:
                current_streak = 0
            elif last_reading_date == yesterday:
                # 如果最后阅读是昨天，需要重新计算当前连续天数
                current_streak = 1
                for i in range(len(reading_dates) - 2, -1, -1):
                    if (reading_dates[i + 1] - reading_dates[i]).days == 1:
                        current_streak += 1
                    else:
                        break
            
            return {"max_streak": max_streak, "current_streak": current_streak}
            
        except Exception as e:
            print(f"计算连续阅读天数失败: {e}")
            return {"max_streak": 0, "current_streak": 0}
    
    async def _get_favorite_reading_hour(self, user_id: int) -> int:
        """获取最喜欢的阅读时段（小时）"""
        try:
            result = await self.db.execute(
                select(
                    extract('hour', ReadingSession.start_time).label('hour'),
                    func.count(ReadingSession.id).label('count')
                )
                .join(Book, ReadingSession.book_id == Book.id)
                .where(Book.user_id == user_id)
                .group_by(extract('hour', ReadingSession.start_time))
                .order_by(func.count(ReadingSession.id).desc())
                .limit(1)
            )
            
            row = result.first()
            return int(row.hour) if row else 20  # 默认晚上8点
            
        except Exception as e:
            print(f"获取最喜欢阅读时段失败: {e}")
            return 20
    
    async def _get_period_reading_time(self, user_id: int, days: int) -> int:
        """
        获取指定期间的阅读时长
        
        Args:
            user_id: 用户ID
            days: 天数（7=本周，30=本月）
            
        Returns:
            阅读时长（秒）
        """
        start_date = datetime.now() - timedelta(days=days)
        
        result = await self.db.execute(
            select(func.sum(ReadingSession.duration))
            .join(Book, ReadingSession.book_id == Book.id)
            .where(
                Book.user_id == user_id,
                ReadingSession.start_time >= start_date
            )
        )
        return int(result.scalar() or 0)
    

    
    async def get_reading_trends(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取阅读趋势数据"""
        try:
            # 获取最近N天的阅读趋势
            start_date = datetime.now() - timedelta(days=days)
            
            result = await self.db.execute(
                text("""
                    SELECT 
                        DATE(rs.start_time) as reading_date,
                        SUM(rs.duration) as daily_duration,
                        COUNT(rs.id) as session_count,
                        AVG(rs.duration) as avg_session_duration
                    FROM reading_sessions rs
                    JOIN books b ON rs.book_id = b.id
                    WHERE b.user_id = :user_id 
                        AND rs.start_time >= :start_date
                    GROUP BY DATE(rs.start_time)
                    ORDER BY reading_date
                """),
                {"user_id": user_id, "start_date": start_date}
            )
            
            trends = []
            for row in result:
                trends.append({
                    "date": row.reading_date.isoformat() if row.reading_date else None,
                    "duration": int(row.daily_duration or 0),
                    "sessions": int(row.session_count or 0),
                    "avg_duration": int(row.avg_session_duration or 0),
                })
            
            return {
                "period_days": days,
                "trends": trends,
                "avg_daily_duration": sum(t["duration"] for t in trends) // len(trends) if trends else 0,
                "most_active_day": max(trends, key=lambda x: x["duration"]) if trends else None,
            }
        except Exception as e:
            print(f"获取阅读趋势失败: {e}")
            return {
                "period_days": days,
                "trends": [],
                "avg_daily_duration": 0,
                "most_active_day": None,
            }
    
    def _get_empty_dashboard_summary(self) -> Dict[str, Any]:
        """返回空的仪表盘摘要"""
        return {
            "total_books": 0,
            "total_reading_time": 0,
            "total_pages_read": 0,
            "total_highlights": 0,
            "books_in_progress": 0,
            "books_completed": 0,
            "avg_reading_speed": 0.0,
            "reading_streak": 0,
            "max_reading_streak": 0,
            "favorite_reading_hour": 20,
            "this_week_reading_time": 0,
            "this_month_reading_time": 0,
        }
    
    async def get_book_map_data(self, user_id: int, book_id: int) -> Dict[str, Any]:
        """
        获取书籍地图数据
        
        逻辑: 对于给定的 book_id，查询 reading_sessions 表获取所有读过的唯一页码
        输出: 一个包含所有已读页码的数组，例如 [1, 2, 5, 8, ...]
        """
        try:
            # 验证书籍属于该用户
            book_result = await self.db.execute(
                select(Book).where(Book.id == book_id, Book.user_id == user_id)
            )
            book = book_result.scalar_one_or_none()
            
            if not book:
                return {
                    "book_id": book_id,
                    "book_title": "未找到书籍",
                    "total_pages": 0,
                    "read_pages": [],
                    "reading_progress": 0.0
                }
            
            # 获取所有已读页码
            result = await self.db.execute(
                select(distinct(ReadingSession.page))
                .where(ReadingSession.book_id == book_id)
                .order_by(ReadingSession.page)
            )
            
            read_pages = [row[0] for row in result]
            total_pages = book.total_pages or 0
            reading_progress = (len(read_pages) / total_pages * 100) if total_pages > 0 else 0.0
            
            return {
                "book_id": book_id,
                "book_title": book.title,
                "total_pages": total_pages,
                "read_pages": read_pages,
                "read_pages_count": len(read_pages),
                "reading_progress": round(reading_progress, 2)
            }
            
        except Exception as e:
            print(f"获取书籍地图数据失败: {e}")
            return {
                "book_id": book_id,
                "book_title": "获取失败",
                "total_pages": 0,
                "read_pages": [],
                "reading_progress": 0.0
            }
    
    async def get_time_range_statistics(
        self, 
        user_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        获取指定时间范围的统计数据
        
        用于生成周报、月报等
        """
        try:
            # 基础统计
            result = await self.db.execute(
                select(
                    func.sum(ReadingSession.duration).label('total_duration'),
                    func.count(ReadingSession.id).label('total_sessions'),
                    func.count(distinct(ReadingSession.book_id)).label('books_read'),
                    func.count(distinct(ReadingSession.book_id, ReadingSession.page)).label('pages_read'),
                    func.avg(ReadingSession.duration).label('avg_session_duration')
                )
                .join(Book, ReadingSession.book_id == Book.id)
                .where(
                    Book.user_id == user_id,
                    ReadingSession.start_time >= start_date,
                    ReadingSession.start_time <= end_date
                )
            )
            
            row = result.first()
            
            if not row:
                return self._get_empty_time_range_stats(start_date, end_date)
            
            total_duration = int(row.total_duration or 0)
            total_sessions = int(row.total_sessions or 0)
            books_read = int(row.books_read or 0)
            pages_read = int(row.pages_read or 0)
            avg_session_duration = int(row.avg_session_duration or 0)
            
            # 计算阅读速度
            reading_speed = await self._calculate_average_reading_speed(pages_read, total_duration)
            
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_duration": total_duration,
                "total_sessions": total_sessions,
                "books_read": books_read,
                "pages_read": pages_read,
                "avg_session_duration": avg_session_duration,
                "reading_speed": reading_speed,
                "days_with_reading": await self._count_active_days(user_id, start_date, end_date)
            }
            
        except Exception as e:
            print(f"获取时间范围统计失败: {e}")
            return self._get_empty_time_range_stats(start_date, end_date)
    
    async def _count_active_days(self, user_id: int, start_date: datetime, end_date: datetime) -> int:
        """计算指定时间范围内有阅读记录的天数"""
        result = await self.db.execute(
            select(func.count(distinct(func.date(ReadingSession.start_time))))
            .join(Book, ReadingSession.book_id == Book.id)
            .where(
                Book.user_id == user_id,
                ReadingSession.start_time >= start_date,
                ReadingSession.start_time <= end_date
            )
        )
        return int(result.scalar() or 0)
    
    def _get_empty_time_range_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """返回空的时间范围统计"""
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_duration": 0,
            "total_sessions": 0,
            "books_read": 0,
            "pages_read": 0,
            "avg_session_duration": 0,
            "reading_speed": 0.0,
            "days_with_reading": 0
        }
    
    async def get_calendar_heatmap_data(self, user_id: int, year: Optional[int] = None) -> Dict[str, Any]:
        """
        获取日历热力图数据
        
        逻辑: 按日期聚合指定年份的阅读数据，用于生成热力图
        
        Args:
            user_id: 用户ID
            year: 年份，默认为当前年份
            
        Returns:
            包含每日阅读数据和年度统计摘要的字典
        """
        try:
            # 设置年份，默认为当前年份
            if year is None:
                year = datetime.now().year
            
            # 计算年份的开始和结束日期
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31, 23, 59, 59)
            
            # 查询该年份的每日阅读数据
            result = await self.db.execute(
                text("""
                    SELECT 
                        DATE(rs.start_time) as reading_date,
                        SUM(rs.duration) as daily_duration,
                        COUNT(rs.id) as session_count,
                        COUNT(DISTINCT rs.book_id) as books_count,
                        COUNT(DISTINCT CONCAT(rs.book_id, '-', rs.page)) as pages_count
                    FROM reading_sessions rs
                    JOIN books b ON rs.book_id = b.id
                    WHERE b.user_id = :user_id 
                        AND rs.start_time >= :start_date
                        AND rs.start_time <= :end_date
                    GROUP BY DATE(rs.start_time)
                    ORDER BY reading_date
                """),
                {
                    "user_id": user_id, 
                    "start_date": start_date, 
                    "end_date": end_date
                }
            )
            
            # 处理每日数据
            daily_data = []
            total_duration = 0
            max_daily_duration = 0
            
            for row in result:
                daily_duration = int(row.daily_duration or 0)
                daily_entry = {
                    "date": row.reading_date.isoformat() if row.reading_date else None,
                    "reading_time": daily_duration,
                    "sessions": int(row.session_count or 0),
                    "books_read": int(row.books_count or 0),
                    "pages_read": int(row.pages_count or 0)
                }
                daily_data.append(daily_entry)
                total_duration += daily_duration
                max_daily_duration = max(max_daily_duration, daily_duration)
            
            # 计算年度统计摘要
            active_days = len(daily_data)
            total_days = 366 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 365
            
            return {
                "year": year,
                "data": daily_data,
                "total_days": total_days,
                "active_days": active_days,
                "total_reading_time": total_duration,
                "max_reading_time": max_daily_duration,
                "avg_daily_reading_time": total_duration // active_days if active_days > 0 else 0
            }
            
        except Exception as e:
            print(f"获取日历热力图数据失败: {e}")
            # 返回空数据结构
            current_year = year or datetime.now().year
            total_days = 366 if current_year % 4 == 0 and (current_year % 100 != 0 or current_year % 400 == 0) else 365
            return {
                "year": current_year,
                "data": [],
                "total_days": total_days,
                "active_days": 0,
                "total_reading_time": 0,
                "max_reading_time": 0,
                "avg_daily_reading_time": 0
            }

    async def get_detailed_calendar_data(self, user_id: int, year: Optional[int] = None, month: Optional[int] = None) -> Dict[str, Any]:
        """
        获取详细日历数据，包含每日的具体书籍信息
        
        Args:
            user_id: 用户ID
            year: 年份，默认为当前年份
            month: 月份，默认为当前月份
            
        Returns:
            包含每日详细阅读数据的字典，包括书籍列表和时长
        """
        try:
            # 设置年月，默认为当前年月
            if year is None:
                year = datetime.now().year
            if month is None:
                month = datetime.now().month
            
            # 计算月份的开始和结束日期
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
            
            # 查询该月份的每日详细阅读数据
            result = await self.db.execute(
                text("""
                    SELECT 
                        DATE(rs.start_time) as reading_date,
                        b.title as book_title,
                        b.author as book_author,
                        b.id as book_id,
                        SUM(rs.duration) as book_daily_duration,
                        COUNT(rs.id) as book_session_count,
                        COUNT(DISTINCT rs.page) as book_pages_count,
                        MIN(rs.start_time) as first_session,
                        MAX(rs.start_time) as last_session
                    FROM reading_sessions rs
                    JOIN books b ON rs.book_id = b.id
                    WHERE b.user_id = :user_id 
                        AND rs.start_time >= :start_date
                        AND rs.start_time <= :end_date
                    GROUP BY DATE(rs.start_time), b.id, b.title, b.author
                    ORDER BY reading_date, book_daily_duration DESC
                """),
                {
                    "user_id": user_id, 
                    "start_date": start_date, 
                    "end_date": end_date
                }
            )
            
            # 按日期组织数据
            daily_books = {}
            for row in result:
                date_str = row.reading_date.isoformat() if row.reading_date else None
                if date_str not in daily_books:
                    daily_books[date_str] = []
                
                book_info = {
                    "book_id": row.book_id,
                    "title": row.book_title,
                    "author": row.book_author or "未知作者",
                    "reading_time": int(row.book_daily_duration or 0),
                    "session_count": int(row.book_session_count or 0),
                    "pages_read": int(row.book_pages_count or 0),
                    "first_session": row.first_session.isoformat() if row.first_session else None,
                    "last_session": row.last_session.isoformat() if row.last_session else None
                }
                daily_books[date_str].append(book_info)
            
            # 分析连续阅读模式
            daily_data = []
            book_reading_streaks = {}  # 跟踪每本书的连续阅读
            
            # 生成该月所有日期
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                date_str = current_date.isoformat()
                day_books = daily_books.get(date_str, [])
                
                # 更新连续阅读状态
                self._update_book_streaks(book_reading_streaks, day_books, current_date)
                
                # 为每本书添加连续阅读信息
                for book in day_books:
                    book_id = book["book_id"]
                    if book_id in book_reading_streaks:
                        book["continuous_days"] = book_reading_streaks[book_id]["streak"]
                        book["is_streak_start"] = book_reading_streaks[book_id]["is_start"]
                        book["is_streak_end"] = False  # 将在下一天判断
                
                daily_data.append({
                    "date": date_str,
                    "day": current_date.day,
                    "total_reading_time": sum(book["reading_time"] for book in day_books),
                    "total_sessions": sum(book["session_count"] for book in day_books),
                    "books_count": len(day_books),
                    "books": day_books
                })
                
                current_date += timedelta(days=1)
            
            # 标记连续阅读结束
            self._mark_streak_ends(daily_data)
            
            return {
                "year": year,
                "month": month,
                "days_in_month": (end_date.date() - start_date.date()).days + 1,
                "data": daily_data
            }
            
        except Exception as e:
            print(f"获取详细日历数据失败: {e}")
            return {
                "year": year or datetime.now().year,
                "month": month or datetime.now().month,
                "days_in_month": 0,
                "data": []
            }
    
    def _update_book_streaks(self, streaks: Dict, day_books: list, current_date: date):
        """更新书籍连续阅读状态"""
        books_today = {book["book_id"] for book in day_books}
        
        # 重置所有书籍的今日状态
        for book_id in list(streaks.keys()):
            if book_id in books_today:
                # 书籍今天有阅读，连续天数+1
                streaks[book_id]["streak"] += 1
                streaks[book_id]["is_start"] = False
            else:
                # 书籍今天没有阅读，连续中断
                del streaks[book_id]
        
        # 添加新开始阅读的书籍
        for book in day_books:
            book_id = book["book_id"]
            if book_id not in streaks:
                streaks[book_id] = {
                    "streak": 1,
                    "is_start": True,
                    "start_date": current_date
                }
    
    def _mark_streak_ends(self, daily_data: list):
        """标记连续阅读结束"""
        # 获取所有书籍的最后出现日期
        book_last_dates = {}
        for day_data in daily_data:
            for book in day_data["books"]:
                book_last_dates[book["book_id"]] = day_data["date"]
        
        # 标记连续阅读结束
        for day_data in daily_data:
            for book in day_data["books"]:
                book_id = book["book_id"]
                if book_last_dates[book_id] == day_data["date"]:
                    book["is_streak_end"] = True 