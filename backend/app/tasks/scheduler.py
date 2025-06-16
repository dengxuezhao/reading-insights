import asyncio
import logging
from datetime import datetime
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.config import settings
from backend.app.database import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.services.data_sync_service import DataSyncService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncScheduler:
    """数据同步调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def sync_all_users(self):
        """同步所有用户的数据"""
        logger.info("开始自动同步所有用户数据")
        
        async with AsyncSessionLocal() as session:
            try:
                # 获取所有有WebDAV配置的用户
                result = await session.execute(
                    select(User).where(User.webdav_url_encrypted.isnot(None))
                )
                users = result.scalars().all()
                
                sync_results = []
                
                for user in users:
                    try:
                        sync_service = DataSyncService(session)
                        result = await sync_service.sync_user_data(user.id)
                        
                        sync_results.append({
                            'user_id': user.id,
                            'username': user.username,
                            'success': result['success'],
                            'books_synced': result['books_synced'],
                            'sessions_synced': result['sessions_synced'],
                            'error': result.get('error')
                        })
                        
                        if result['success']:
                            logger.info(f"用户 {user.username} 同步成功: "
                                      f"书籍 {result['books_synced']}, "
                                      f"会话 {result['sessions_synced']}")
                        else:
                            logger.warning(f"用户 {user.username} 同步失败: {result['error']}")
                            
                    except Exception as e:
                        logger.error(f"同步用户 {user.username} 数据时出错: {e}")
                        sync_results.append({
                            'user_id': user.id,
                            'username': user.username,
                            'success': False,
                            'books_synced': 0,
                            'sessions_synced': 0,
                            'error': str(e)
                        })
                
                # 记录同步统计
                successful_syncs = sum(1 for r in sync_results if r['success'])
                total_books = sum(r['books_synced'] for r in sync_results)
                total_sessions = sum(r['sessions_synced'] for r in sync_results)
                
                logger.info(f"自动同步完成: {successful_syncs}/{len(sync_results)} 用户同步成功, "
                          f"总计同步 {total_books} 本书籍, {total_sessions} 个会话")
                
            except Exception as e:
                logger.error(f"自动同步过程中发生错误: {e}")
    
    async def sync_single_user(self, user_id: int):
        """同步单个用户的数据"""
        async with AsyncSessionLocal() as session:
            try:
                sync_service = DataSyncService(session)
                result = await sync_service.sync_user_data(user_id)
                
                if result['success']:
                    logger.info(f"用户 {user_id} 定时同步成功: "
                              f"书籍 {result['books_synced']}, "
                              f"会话 {result['sessions_synced']}")
                else:
                    logger.warning(f"用户 {user_id} 定时同步失败: {result['error']}")
                    
            except Exception as e:
                logger.error(f"同步用户 {user_id} 数据时出错: {e}")
    
    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已经在运行")
            return
        
        # 添加定时任务：每隔指定分钟同步一次所有用户数据
        self.scheduler.add_job(
            self.sync_all_users,
            trigger=IntervalTrigger(minutes=settings.SYNC_INTERVAL_MINUTES),
            id='sync_all_users',
            name='同步所有用户数据',
            max_instances=1,  # 防止重复执行
            coalesce=True,   # 合并多个待执行的任务
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info(f"定时同步调度器已启动，同步间隔: {settings.SYNC_INTERVAL_MINUTES} 分钟")
    
    def stop(self):
        """停止调度器"""
        if not self.is_running:
            return
            
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("定时同步调度器已停止")
    
    def add_user_sync_job(self, user_id: int, interval_minutes: int = None):
        """为特定用户添加定时同步任务"""
        if interval_minutes is None:
            interval_minutes = settings.SYNC_INTERVAL_MINUTES
        
        job_id = f'sync_user_{user_id}'
        
        self.scheduler.add_job(
            self.sync_single_user,
            trigger=IntervalTrigger(minutes=interval_minutes),
            args=[user_id],
            id=job_id,
            name=f'同步用户 {user_id} 数据',
            max_instances=1,
            coalesce=True,
            replace_existing=True
        )
        
        logger.info(f"为用户 {user_id} 添加定时同步任务，间隔: {interval_minutes} 分钟")
    
    def remove_user_sync_job(self, user_id: int):
        """移除特定用户的定时同步任务"""
        job_id = f'sync_user_{user_id}'
        
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"移除用户 {user_id} 的定时同步任务")
        except Exception as e:
            logger.warning(f"移除用户 {user_id} 定时同步任务失败: {e}")
    
    def get_jobs_status(self) -> List[dict]:
        """获取当前所有任务状态"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs


# 全局调度器实例
sync_scheduler = SyncScheduler() 