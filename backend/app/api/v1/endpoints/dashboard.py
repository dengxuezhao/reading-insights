from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.schemas.dashboard import DashboardSummary, CalendarHeatmapData
from backend.app.services.auth_service import AuthService
from backend.app.services.statistics_service import StatisticsService

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary, summary="获取仪表盘摘要")
async def get_dashboard_summary(
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的阅读统计摘要"""
    statistics_service = StatisticsService(db)
    summary = await statistics_service.get_dashboard_summary(current_user["user_id"])
    return summary


@router.get("/calendar", response_model=CalendarHeatmapData, summary="获取日历热力图数据")
async def get_calendar_data(
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用于生成日历热力图的数据"""
    statistics_service = StatisticsService(db)
    calendar_data = await statistics_service.get_calendar_heatmap_data(current_user["user_id"])
    return calendar_data 