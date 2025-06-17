"""
公共API端点
提供无需认证的公共接口，包括默认用户认证
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.config import settings
from backend.app.services.user_init_service import UserInitService
from backend.app.services.data_sync_service import DataSyncService

router = APIRouter()


@router.get("/config", summary="获取前端配置信息")
async def get_frontend_config():
    """获取前端配置信息"""
    return {
        "title": settings.FRONTEND_TITLE,
        "description": settings.FRONTEND_DESCRIPTION,
        "demo_mode": settings.PUBLIC_DEMO_MODE,
        "default_user_enabled": settings.DEFAULT_USER_ENABLED,
        "webdav_configured": settings.has_webdav_config,
        "proxy_domain": settings.PROXY_DOMAIN,
        "proxy_ip": settings.PROXY_IP,
        "version": "1.0.0"
    }


@router.get("/default-token", summary="获取默认用户访问令牌")
async def get_default_user_token(db: AsyncSession = Depends(get_db)):
    """
    获取默认用户的访问令牌
    
    用于前端自动认证，无需手动登录
    """
    try:
        user_init_service = UserInitService(db)
        token = await user_init_service.get_default_user_token()
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "username": settings.DEFAULT_USERNAME,
            "is_default": True
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取默认用户令牌失败: {str(e)}"
        )


@router.get("/default-user", summary="获取默认用户信息")
async def get_default_user_info(db: AsyncSession = Depends(get_db)):
    """获取默认用户信息"""
    try:
        user_init_service = UserInitService(db)
        user_info = await user_init_service.get_default_user_info()
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="默认用户不可用"
            )
        
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取默认用户信息失败: {str(e)}"
        )


@router.post("/init-default-user", summary="初始化默认用户")
async def init_default_user(db: AsyncSession = Depends(get_db)):
    """
    手动初始化默认用户
    
    用于确保默认用户存在，通常在应用启动时调用
    """
    try:
        user_init_service = UserInitService(db)
        user_info = await user_init_service.ensure_default_user()
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="默认用户功能已禁用"
            )
        
        return {
            "message": "默认用户初始化成功" if user_info["created"] else "默认用户已存在",
            "user_info": user_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"初始化默认用户失败: {str(e)}"
        )


@router.get("/test-webdav", summary="测试默认用户WebDAV连接")
async def test_default_user_webdav(db: AsyncSession = Depends(get_db)):
    """测试默认用户的WebDAV连接"""
    try:
        user_init_service = UserInitService(db)
        result = await user_init_service.test_default_user_webdav()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"WebDAV连接测试失败: {str(e)}"
        )


@router.post("/sync-data", summary="同步默认用户数据")
async def sync_default_user_data(db: AsyncSession = Depends(get_db)):
    """
    同步默认用户的阅读数据
    
    从WebDAV下载并导入KOReader统计数据
    """
    try:
        user_init_service = UserInitService(db)
        user_info = await user_init_service.ensure_default_user()
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="默认用户不可用"
            )
        
        # 执行数据同步
        sync_service = DataSyncService(db)
        result = await sync_service.sync_user_data(user_info["user_id"])
        
        if result['success']:
            return {
                "success": True,
                "message": "数据同步成功",
                "user_id": user_info["user_id"],
                "username": user_info["username"],
                "books_synced": result['books_synced'],
                "sessions_synced": result['sessions_synced'],
                "remote_path": result.get('remote_path')
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据同步失败: {str(e)}"
        )


@router.get("/sync-status", summary="获取默认用户同步状态")
async def get_default_user_sync_status(db: AsyncSession = Depends(get_db)):
    """获取默认用户的同步状态"""
    try:
        user_init_service = UserInitService(db)
        user_info = await user_init_service.ensure_default_user()
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="默认用户不可用"
            )
        
        # 获取同步状态
        sync_service = DataSyncService(db)
        status_info = await sync_service.get_sync_status(user_info["user_id"])
        
        return {
            "user_id": user_info["user_id"],
            "username": user_info["username"],
            "total_books": status_info['total_books'],
            "total_sessions": status_info['total_sessions'],
            "last_reading_time": status_info['last_reading_time'],
            "has_webdav_config": status_info['has_webdav_config']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取同步状态失败: {str(e)}"
        ) 