from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.app.database import get_db
from backend.app.services.auth_service import AuthService
from backend.app.services.data_sync_service import DataSyncService
from backend.app.schemas.sync import SyncRequest, SyncResponse, SyncStatusResponse

router = APIRouter()


@router.post("/manual", response_model=SyncResponse, summary="手动同步数据")
async def manual_sync(
    sync_request: SyncRequest = None,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """手动触发数据同步"""
    sync_service = DataSyncService(db)
    
    remote_path = sync_request.remote_path if sync_request else None
    
    try:
        result = await sync_service.sync_user_data(
            user_id=current_user["user_id"],
            remote_path=remote_path
        )
        
        if result['success']:
            return SyncResponse(
                success=True,
                message="数据同步成功",
                books_synced=result['books_synced'],
                sessions_synced=result['sessions_synced'],
                remote_path=result.get('remote_path')
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"同步过程中发生错误: {str(e)}"
        )


@router.post("/background", summary="后台同步数据")
async def background_sync(
    background_tasks: BackgroundTasks,
    sync_request: SyncRequest = None,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """在后台异步执行数据同步"""
    async def sync_task():
        sync_service = DataSyncService(db)
        remote_path = sync_request.remote_path if sync_request else None
        result = await sync_service.sync_user_data(
            user_id=current_user["user_id"],
            remote_path=remote_path
        )
        # TODO: 可以在这里记录同步日志或发送通知
        print(f"后台同步完成: {result}")
    
    background_tasks.add_task(sync_task)
    return {"message": "后台同步任务已启动"}


@router.get("/status", response_model=SyncStatusResponse, summary="获取同步状态")
async def get_sync_status(
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的数据同步状态"""
    sync_service = DataSyncService(db)
    
    try:
        status_info = await sync_service.get_sync_status(current_user["user_id"])
        
        return SyncStatusResponse(
            total_books=status_info['total_books'],
            total_sessions=status_info['total_sessions'],
            last_reading_time=status_info['last_reading_time'],
            has_webdav_config=status_info['has_webdav_config']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取同步状态失败: {str(e)}"
        )


@router.get("/files", summary="列出远程文件")
async def list_remote_files(
    path: str = "/",
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """列出WebDAV远程目录中的文件"""
    sync_service = DataSyncService(db)
    
    try:
        files = await sync_service.webdav_service.list_remote_files(
            user_id=current_user["user_id"],
            remote_path=path
        )
        
        return {
            "path": path,
            "files": files
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出远程文件失败: {str(e)}"
        )


@router.get("/find-statistics", summary="查找统计文件")
async def find_statistics_file(
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """自动查找statistics.sqlite3文件的路径"""
    sync_service = DataSyncService(db)
    
    try:
        file_path = await sync_service.webdav_service.find_statistics_file(
            current_user["user_id"]
        )
        
        if file_path:
            return {
                "found": True,
                "path": file_path,
                "message": "找到statistics.sqlite3文件"
            }
        else:
            return {
                "found": False,
                "path": None,
                "message": "未找到statistics.sqlite3文件"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查找统计文件失败: {str(e)}"
        ) 