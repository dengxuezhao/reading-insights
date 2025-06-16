from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    """仪表盘摘要统计模型"""
    total_books: int = Field(..., description="总书籍数量")
    total_reading_time: int = Field(..., description="总阅读时长（秒）")
    total_pages_read: int = Field(..., description="总阅读页数（去重）")
    total_highlights: int = Field(..., description="总标注数量")
    books_in_progress: int = Field(..., description="正在阅读的书籍数量")
    books_completed: int = Field(..., description="已完成的书籍数量")
    avg_reading_speed: float = Field(..., description="平均阅读速度（页/小时）")
    reading_streak: int = Field(..., description="当前连续阅读天数")
    max_reading_streak: int = Field(..., description="最长连续阅读天数")
    favorite_reading_hour: int = Field(..., description="最喜欢的阅读时段")
    this_week_reading_time: int = Field(..., description="本周阅读时长（秒）")
    this_month_reading_time: int = Field(..., description="本月阅读时长（秒）")


class CalendarEntry(BaseModel):
    """日历条目模型"""
    date: str = Field(..., description="日期（YYYY-MM-DD）")
    reading_time: int = Field(..., description="阅读时长（秒）")
    pages_read: int = Field(..., description="阅读页数")
    books_read: int = Field(..., description="阅读书籍数量")


class CalendarHeatmapData(BaseModel):
    """日历热力图数据模型"""
    year: int = Field(..., description="年份")
    data: List[Dict] = Field(..., description="每日阅读数据")
    total_days: int = Field(..., description="总天数")
    active_days: int = Field(..., description="有阅读记录的天数")
    max_reading_time: int = Field(..., description="单日最大阅读时长")


class BookMapData(BaseModel):
    """书籍阅读地图数据模型"""
    book_id: int = Field(..., description="书籍ID")
    book_title: str = Field(..., description="书籍标题")
    total_pages: int = Field(..., description="总页数")
    read_pages: List[int] = Field(..., description="已读页码列表")
    read_pages_count: int = Field(..., description="已读页数")
    reading_progress: float = Field(..., description="阅读进度百分比")


class ReadingTrends(BaseModel):
    """阅读趋势数据模型"""
    period_days: int = Field(..., description="统计天数")
    trends: List[Dict] = Field(..., description="每日趋势数据")
    total_duration: int = Field(..., description="总阅读时长")
    avg_daily_duration: int = Field(..., description="平均每日阅读时长")
    most_active_day: Dict = Field(None, description="最活跃的一天")


class TimeRangeStatistics(BaseModel):
    """时间范围统计数据模型"""
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    total_duration: int = Field(..., description="总阅读时长（秒）")
    total_sessions: int = Field(..., description="总阅读会话数")
    books_read: int = Field(..., description="阅读的书籍数")
    pages_read: int = Field(..., description="阅读的页数")
    avg_session_duration: int = Field(..., description="平均会话时长（秒）")
    reading_speed: float = Field(..., description="阅读速度（页/小时）")
    days_with_reading: int = Field(..., description="有阅读记录的天数")


class ReadingStreaks(BaseModel):
    """阅读连续天数模型"""
    max_streak: int = Field(..., description="最长连续天数")
    current_streak: int = Field(..., description="当前连续天数")
    is_active: bool = Field(..., description="当前是否在连续阅读中")
    streak_status: str = Field(..., description="连续状态：active/broken") 