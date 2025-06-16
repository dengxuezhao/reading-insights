from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.schemas.webdav import WebDAVConfig, WebDAVConfigResponse
from backend.app.services.auth_service import AuthService
from backend.app.services.webdav_service import WebDAVService

router = APIRouter()


@router.post("/webdav", response_model=WebDAVConfigResponse, summary="配置WebDAV")
async def configure_webdav(
    webdav_data: WebDAVConfig,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """配置用户的WebDAV设置"""
    webdav_service = WebDAVService(db)
    try:
        await webdav_service.save_webdav_config(
            user_id=current_user["user_id"],
            url=webdav_data.url,
            username=webdav_data.username,
            password=webdav_data.password
        )
        return WebDAVConfigResponse(
            message="WebDAV配置保存成功",
            url=str(webdav_data.url),
            username=webdav_data.username
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"WebDAV配置保存失败: {str(e)}"
        )


@router.get("/webdav", response_model=WebDAVConfigResponse, summary="获取WebDAV配置")
async def get_webdav_config(
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的WebDAV配置（不包含密码）"""
    webdav_service = WebDAVService(db)
    config = await webdav_service.get_webdav_config(current_user["user_id"])
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到WebDAV配置"
        )
    
    return WebDAVConfigResponse(
        message="WebDAV配置获取成功",
        url=config.get("url"),
        username=config.get("username")
    )


@router.delete("/webdav", summary="删除WebDAV配置")
async def delete_webdav_config(
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除用户的WebDAV配置"""
    webdav_service = WebDAVService(db)
    await webdav_service.delete_webdav_config(current_user["user_id"])
    return {"message": "WebDAV配置删除成功"}


@router.post("/webdav/test", summary="测试WebDAV连接")
async def test_webdav_connection(
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """测试WebDAV连接是否正常"""
    webdav_service = WebDAVService(db)
    try:
        is_connected = await webdav_service.test_webdav_connection(current_user["user_id"])
        if is_connected:
            return {"message": "WebDAV连接测试成功", "status": "connected"}
        else:
            return {"message": "WebDAV连接测试失败", "status": "failed"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"WebDAV连接测试失败: {str(e)}"
        ) 