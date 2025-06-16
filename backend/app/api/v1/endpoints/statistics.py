from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional

from backend.app.database import get_db
from backend.app.services.auth_service import AuthService
from backend.app.services.statistics_service import StatisticsService
from backend.app.schemas.dashboard import DashboardSummary

router = APIRouter()


@router.get("/dashboard/summary", response_model=DashboardSummary, summary="获取仪表盘摘要")
async def get_dashboard_summary(
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的仪表盘摘要统计"""
    stats_service = StatisticsService(db)
    
    try:
        summary = await stats_service.get_dashboard_summary(current_user["user_id"])
        return DashboardSummary(**summary)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取仪表盘摘要失败: {str(e)}"
        )


@router.get("/calendar", summary="获取日历热力图数据")
async def get_calendar_heatmap(
    year: Optional[int] = Query(None, description="年份，默认为当前年份"),
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取日历热力图数据
    
    返回指定年份每天的阅读时长数据，用于生成热力图
    """
    stats_service = StatisticsService(db)
    
    try:
        calendar_data = await stats_service.get_calendar_heatmap_data(
            current_user["user_id"], 
            year
        )
        return calendar_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取日历数据失败: {str(e)}"
        )


@router.get("/calendar/detailed", summary="获取详细日历数据")
async def get_detailed_calendar_data(
    year: Optional[int] = Query(None, description="年份，默认为当前年份"),
    month: Optional[int] = Query(None, description="月份，1-12，默认为当前月份"),
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取详细日历数据，包含每日的具体书籍信息
    
    返回指定年月每天的详细阅读数据，包括书籍列表和时长
    """
    stats_service = StatisticsService(db)
    
    try:
        detailed_data = await stats_service.get_detailed_calendar_data(
            current_user["user_id"], 
            year,
            month
        )
        return detailed_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取详细日历数据失败: {str(e)}"
        )


@router.get("/book/{book_id}/map", summary="获取书籍阅读地图")
async def get_book_map(
    book_id: int,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定书籍的阅读地图数据
    
    返回该书籍所有已读页码的列表和阅读进度
    """
    stats_service = StatisticsService(db)
    
    try:
        book_map = await stats_service.get_book_map_data(
            current_user["user_id"], 
            book_id
        )
        return book_map
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取书籍地图失败: {str(e)}"
        )


@router.get("/trends", summary="获取阅读趋势数据")
async def get_reading_trends(
    days: int = Query(30, description="统计天数", ge=1, le=365),
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取阅读趋势数据
    
    返回指定天数内每天的阅读统计，用于生成趋势图表
    """
    stats_service = StatisticsService(db)
    
    try:
        trends = await stats_service.get_reading_trends(
            current_user["user_id"], 
            days
        )
        return trends
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取阅读趋势失败: {str(e)}"
        )


@router.get("/range", summary="获取时间范围统计")
async def get_time_range_statistics(
    start_date: datetime = Query(..., description="开始日期"),
    end_date: datetime = Query(..., description="结束日期"),
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定时间范围的统计数据
    
    用于生成周报、月报等自定义时间范围的统计报告
    """
    stats_service = StatisticsService(db)
    
    try:
        # 验证日期范围
        if start_date >= end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="开始日期必须早于结束日期"
            )
        
        # 限制查询范围不超过1年
        if (end_date - start_date).days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="查询范围不能超过365天"
            )
        
        range_stats = await stats_service.get_time_range_statistics(
            current_user["user_id"], 
            start_date, 
            end_date
        )
        return range_stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取时间范围统计失败: {str(e)}"
        )


@router.get("/weekly", summary="获取本周统计")
async def get_weekly_statistics(
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取本周的阅读统计数据"""
    stats_service = StatisticsService(db)
    
    try:
        # 计算本周的开始和结束日期
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        weekly_stats = await stats_service.get_time_range_statistics(
            current_user["user_id"], 
            start_of_week, 
            end_of_week
        )
        
        # 添加周报特有的信息
        weekly_stats["week_number"] = today.isocalendar()[1]
        weekly_stats["year"] = today.year
        
        return weekly_stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取本周统计失败: {str(e)}"
        )


@router.get("/monthly", summary="获取本月统计")
async def get_monthly_statistics(
    year: Optional[int] = Query(None, description="年份，默认为当前年份"),
    month: Optional[int] = Query(None, description="月份，默认为当前月份"),
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定月份的阅读统计数据"""
    stats_service = StatisticsService(db)
    
    try:
        # 默认为当前年月
        now = datetime.now()
        target_year = year or now.year
        target_month = month or now.month
        
        # 验证月份范围
        if not (1 <= target_month <= 12):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="月份必须在1-12之间"
            )
        
        # 计算月份的开始和结束日期
        start_of_month = datetime(target_year, target_month, 1)
        if target_month == 12:
            end_of_month = datetime(target_year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_of_month = datetime(target_year, target_month + 1, 1) - timedelta(seconds=1)
        
        monthly_stats = await stats_service.get_time_range_statistics(
            current_user["user_id"], 
            start_of_month, 
            end_of_month
        )
        
        # 添加月报特有的信息
        monthly_stats["year"] = target_year
        monthly_stats["month"] = target_month
        monthly_stats["month_name"] = start_of_month.strftime("%B")
        
        return monthly_stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取月度统计失败: {str(e)}"
        )


@router.get("/streaks", summary="获取阅读连续天数详情")
async def get_reading_streaks(
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取详细的阅读连续天数信息
    
    包括最长连续天数、当前连续天数等
    """
    stats_service = StatisticsService(db)
    
    try:
        streaks = await stats_service._calculate_reading_streaks(current_user["user_id"])
        
        # 添加额外的连续天数信息
        result = {
            "max_streak": streaks["max_streak"],
            "current_streak": streaks["current_streak"],
            "is_active": streaks["current_streak"] > 0,
            "streak_status": "active" if streaks["current_streak"] > 0 else "broken"
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取连续阅读天数失败: {str(e)}"
        ) 