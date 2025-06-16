"""
用户初始化服务
负责自动创建和管理默认用户
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.config import settings
from backend.app.services.auth_service import AuthService
from backend.app.services.webdav_service import WebDAVService
from backend.app.schemas.auth import UserCreate

logger = logging.getLogger(__name__)


class UserInitService:
    """用户初始化服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.auth_service = AuthService(db)
        self.webdav_service = WebDAVService(db)
    
    async def ensure_default_user(self) -> dict:
        """确保默认用户存在"""
        if not settings.DEFAULT_USER_ENABLED:
            logger.info("默认用户功能已禁用")
            return None
        
        try:
            # 检查默认用户是否已存在
            existing_user = await self.auth_service.get_user_by_username(settings.DEFAULT_USERNAME)
            
            if existing_user:
                logger.info(f"✅ 默认用户已存在: {settings.DEFAULT_USERNAME} (ID: {existing_user.id})")
                user_info = {
                    "user_id": existing_user.id,
                    "username": existing_user.username,
                    "created": False
                }
            else:
                # 如果不存在且允许自动创建，则创建默认用户
                if settings.DEFAULT_USER_AUTO_CREATE:
                    logger.info(f"🔧 创建默认用户: {settings.DEFAULT_USERNAME}")
                    
                    user_data = UserCreate(
                        username=settings.DEFAULT_USERNAME,
                        password=settings.DEFAULT_PASSWORD
                    )
                    
                    new_user = await self.auth_service.create_user(user_data)
                    logger.info(f"✅ 默认用户创建成功: {new_user.username} (ID: {new_user.id})")
                    
                    user_info = {
                        "user_id": new_user.id,
                        "username": new_user.username,
                        "created": True
                    }
                else:
                    logger.warning(f"⚠️ 默认用户不存在且自动创建已禁用: {settings.DEFAULT_USERNAME}")
                    return None
            
            # 自动配置WebDAV（如果配置了的话）
            await self._configure_default_user_webdav(user_info["user_id"])
            
            return user_info
                
        except Exception as e:
            logger.error(f"❌ 默认用户初始化失败: {e}")
            raise
    
    async def _configure_default_user_webdav(self, user_id: int) -> bool:
        """为默认用户配置WebDAV设置"""
        try:
            # 检查.env中是否配置了WebDAV
            if not settings.has_webdav_config:
                logger.info("📝 .env中未配置WebDAV，跳过自动配置")
                return False
            
            # 检查用户是否已经配置了WebDAV
            existing_config = await self.webdav_service.get_webdav_config(user_id)
            if existing_config:
                logger.info("🔗 默认用户已配置WebDAV，跳过自动配置")
                return True
            
            # 从.env配置中为默认用户设置WebDAV
            logger.info("🔧 为默认用户配置WebDAV...")
            await self.webdav_service.save_webdav_config(
                user_id=user_id,
                url=settings.WEBDAV_URL,
                username=settings.WEBDAV_USERNAME,
                password=settings.WEBDAV_PASSWORD
            )
            
            logger.info("✅ 默认用户WebDAV配置完成")
            logger.info(f"   URL: {settings.WEBDAV_URL}")
            logger.info(f"   用户名: {settings.WEBDAV_USERNAME}")
            logger.info(f"   基础路径: {settings.WEBDAV_BASE_PATH}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 配置默认用户WebDAV失败: {e}")
            return False
    
    async def get_default_user_token(self) -> str:
        """获取默认用户的访问令牌"""
        if not settings.DEFAULT_USER_ENABLED:
            raise ValueError("默认用户功能已禁用")
        
        # 确保默认用户存在
        user_info = await self.ensure_default_user()
        if not user_info:
            raise ValueError("无法获取默认用户信息")
        
        # 生成访问令牌
        token = self.auth_service.create_access_token(
            data={"sub": user_info["username"]}
        )
        
        logger.info(f"🔑 为默认用户生成访问令牌: {user_info['username']}")
        return token
    
    async def get_default_user_info(self) -> dict:
        """获取默认用户信息"""
        user_info = await self.ensure_default_user()
        if not user_info:
            return None
        
        # 检查WebDAV配置状态
        webdav_configured = await self.webdav_service.get_webdav_config(user_info["user_id"]) is not None
        
        return {
            "user_id": user_info["user_id"],
            "username": user_info["username"],
            "is_default": True,
            "demo_mode": settings.PUBLIC_DEMO_MODE,
            "frontend_title": settings.FRONTEND_TITLE,
            "frontend_description": settings.FRONTEND_DESCRIPTION,
            "webdav_configured": webdav_configured,
            "webdav_url": settings.WEBDAV_URL if settings.has_webdav_config else None
        }
    
    async def test_default_user_webdav(self) -> dict:
        """测试默认用户的WebDAV连接"""
        user_info = await self.ensure_default_user()
        if not user_info:
            return {"success": False, "error": "默认用户不可用"}
        
        try:
            # 测试WebDAV连接
            connection_ok = await self.webdav_service.test_webdav_connection(user_info["user_id"])
            
            if connection_ok:
                return {
                    "success": True,
                    "message": "WebDAV连接测试成功",
                    "user_id": user_info["user_id"],
                    "username": user_info["username"]
                }
            else:
                return {
                    "success": False,
                    "error": "WebDAV连接测试失败",
                    "user_id": user_info["user_id"],
                    "username": user_info["username"]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"WebDAV连接测试异常: {str(e)}",
                "user_id": user_info["user_id"],
                "username": user_info["username"]
            } 