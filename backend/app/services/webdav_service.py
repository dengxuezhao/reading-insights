import os
import tempfile
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from webdav3.client import Client
import asyncio
from concurrent.futures import ThreadPoolExecutor

from backend.app.config import settings
from backend.app.models.user import User
from backend.app.utils.encryption import encrypt_data, decrypt_data


class WebDAVService:
    """WebDAV服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def save_webdav_config(
        self, 
        user_id: int, 
        url: str, 
        username: str, 
        password: str
    ) -> None:
        """保存用户的WebDAV配置"""
        # 获取用户
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("用户不存在")
        
        # 确保URL是字符串类型（处理HttpUrl对象）
        url_str = str(url) if hasattr(url, '__str__') else url
        
        # 加密存储WebDAV凭证
        user.webdav_url_encrypted = encrypt_data(url_str)
        user.webdav_user_encrypted = encrypt_data(username)
        user.webdav_password_encrypted = encrypt_data(password)
        
        await self.db.commit()
    
    async def get_webdav_config(self, user_id: int) -> Optional[Dict[str, str]]:
        """获取用户的WebDAV配置（解密）"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user or not user.webdav_url_encrypted:
            return None
        
        try:
            return {
                "url": decrypt_data(user.webdav_url_encrypted),
                "username": decrypt_data(user.webdav_user_encrypted),
                "password": decrypt_data(user.webdav_password_encrypted)
            }
        except Exception:
            return None
    
    async def delete_webdav_config(self, user_id: int) -> None:
        """删除用户的WebDAV配置"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.webdav_url_encrypted = None
            user.webdav_user_encrypted = None
            user.webdav_password_encrypted = None
            await self.db.commit()
    
    def _create_webdav_client(self, config: Dict[str, str]) -> Client:
        """创建WebDAV客户端"""
        webdav_options = {
            'webdav_hostname': config['url'],
            'webdav_login': config['username'],
            'webdav_password': config['password'],
            'webdav_timeout': 30,
            'disable_check': True,  # 禁用验证检查，解决坚果云连接问题
        }
        return Client(webdav_options)
    
    def _test_connection_sync(self, config: Dict[str, str]) -> bool:
        """同步测试WebDAV连接"""
        try:
            client = self._create_webdav_client(config)
            # 测试连接：尝试列出根目录
            return client.check()
        except Exception as e:
            print(f"WebDAV连接测试失败: {e}")
            return False
    
    async def test_webdav_connection(self, user_id: int) -> bool:
        """测试WebDAV连接"""
        config = await self.get_webdav_config(user_id)
        if not config:
            return False
        
        # 在线程池中执行同步的WebDAV操作
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                self.executor, 
                self._test_connection_sync, 
                config
            )
            return result
        except Exception as e:
            print(f"WebDAV连接测试异常: {e}")
            return False
    
    def _download_file_sync(self, config: Dict[str, str], remote_path: str, local_path: str) -> bool:
        """同步下载文件"""
        try:
            client = self._create_webdav_client(config)
            
            # 检查远程文件是否存在
            if not client.check(remote_path):
                print(f"远程文件不存在: {remote_path}")
                return False
            
            # 下载文件
            client.download_sync(remote_path=remote_path, local_path=local_path)
            
            # 检查本地文件是否下载成功
            if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                return True
            else:
                print(f"文件下载失败或文件为空: {local_path}")
                return False
                
        except Exception as e:
            print(f"下载文件时出错: {e}")
            return False
    
    async def download_statistics_file(self, user_id: int, remote_path: str = None) -> Optional[str]:
        """
        从WebDAV下载statistics.sqlite3文件
        
        Args:
            user_id: 用户ID
            remote_path: 远程文件路径，如果为None则使用默认路径
            
        Returns:
            本地临时文件路径，如果下载失败则返回None
        """
        config = await self.get_webdav_config(user_id)
        if not config:
            return None
        
        # 如果没有指定远程路径，使用常见的KOReader统计文件路径
        if remote_path is None:
            remote_path = "/statistics.sqlite3"  # 可能需要根据实际情况调整
        
        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        local_filename = f"statistics_{user_id}_{int(asyncio.get_event_loop().time())}.sqlite3"
        local_path = os.path.join(temp_dir, local_filename)
        
        # 在线程池中执行下载
        loop = asyncio.get_event_loop()
        try:
            success = await loop.run_in_executor(
                self.executor,
                self._download_file_sync,
                config,
                remote_path,
                local_path
            )
            
            if success:
                return local_path
            else:
                # 清理失败的文件
                if os.path.exists(local_path):
                    os.remove(local_path)
                return None
                
        except Exception as e:
            print(f"异步下载文件异常: {e}")
            # 清理可能的临时文件
            if os.path.exists(local_path):
                os.remove(local_path)
            return None
    
    def _list_files_sync(self, config: Dict[str, str], remote_path: str = "/") -> list:
        """同步列出远程目录文件"""
        try:
            client = self._create_webdav_client(config)
            return client.list(remote_path)
        except Exception as e:
            print(f"列出文件时出错: {e}")
            return []
    
    async def list_remote_files(self, user_id: int, remote_path: str = "/") -> list:
        """列出远程目录中的文件"""
        config = await self.get_webdav_config(user_id)
        if not config:
            return []
        
        loop = asyncio.get_event_loop()
        try:
            files = await loop.run_in_executor(
                self.executor,
                self._list_files_sync,
                config,
                remote_path
            )
            return files
        except Exception as e:
            print(f"异步列出文件异常: {e}")
            return []
    
    async def find_statistics_file(self, user_id: int) -> Optional[str]:
        """查找statistics.sqlite3文件的路径"""
        config = await self.get_webdav_config(user_id)
        if not config:
            return None
        
        # 从配置中获取基础路径
        from backend.app.config import settings
        base_path = settings.WEBDAV_BASE_PATH.rstrip('/')
        
        # 常见的KOReader统计文件路径
        possible_paths = [
            f"{base_path}/statistics.sqlite3",  # 使用配置的路径
            f"{base_path}/statistics.sqlite",   # 可能没有.3后缀
            "/koreader/statistics.sqlite3", 
            "/statistics.sqlite3",
            "/statistics/statistics.sqlite3",
            "/.adds/koreader/statistics.sqlite3",
            "/Documents/statistics.sqlite3",
            f"{base_path}/Documents/statistics.sqlite3",
        ]
        
        loop = asyncio.get_event_loop()
        
        print(f"正在查找statistics.sqlite3文件，尝试以下路径:")
        for path in possible_paths:
            print(f"  检查路径: {path}")
            try:
                # 在线程池中检查文件是否存在
                exists = await loop.run_in_executor(
                    self.executor,
                    lambda p=path: self._create_webdav_client(config).check(p)
                )
                if exists:
                    print(f"  ✅ 找到文件: {path}")
                    return path
                else:
                    print(f"  ❌ 文件不存在: {path}")
            except Exception as e:
                print(f"  ❌ 检查路径 {path} 时出错: {e}")
                continue
        
        print("❌ 未找到statistics.sqlite3文件")
        return None 