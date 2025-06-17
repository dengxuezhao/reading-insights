from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # 基础配置
    DEBUG: bool = Field(default=True, description="调试模式")
    SECRET_KEY: str = Field(default="your-secret-key-change-this", description="密钥")
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="允许的主机")
    
    # 数据库配置
    DB_HOST: str = Field(default="localhost", description="数据库主机")
    DB_PORT: int = Field(default=5432, description="数据库端口")
    DB_USER: str = Field(default="postgres", description="数据库用户")
    DB_PASSWORD: str = Field(default="postgres", description="数据库密码")
    DB_NAME: str = Field(default="koreader", description="数据库名称")
    DATABASE_URL: Optional[str] = Field(default=None, description="完整数据库URL")
    
    # JWT配置
    JWT_SECRET_KEY: str = Field(default="jwt-secret-key-change-this", description="JWT密钥")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT算法")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="访问令牌过期时间(分钟)")
    
    # 默认用户配置
    DEFAULT_USER_ENABLED: bool = Field(default=True, description="是否启用默认用户")
    DEFAULT_USERNAME: str = Field(default="koreader_user", description="默认用户名")
    DEFAULT_PASSWORD: str = Field(default="koreader123", description="默认用户密码")
    DEFAULT_USER_AUTO_CREATE: bool = Field(default=True, description="是否自动创建默认用户")
    
    # 前端展示配置
    FRONTEND_TITLE: str = Field(default="KOReader 阅读统计", description="前端页面标题")
    FRONTEND_DESCRIPTION: str = Field(default="个人阅读数据可视化平台", description="前端页面描述")
    PUBLIC_DEMO_MODE: bool = Field(default=False, description="是否为公开演示模式")
    
    # WebDAV配置
    WEBDAV_URL: Optional[str] = Field(default=None, description="WebDAV服务器URL")
    WEBDAV_USERNAME: Optional[str] = Field(default=None, description="WebDAV用户名")
    WEBDAV_PASSWORD: Optional[str] = Field(default=None, description="WebDAV密码")
    WEBDAV_BASE_PATH: str = Field(default="/koreader", description="WebDAV基础路径")
    
    # 文件存储配置
    UPLOAD_DIR: str = Field(default="./uploads", description="上传目录")
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, description="最大文件大小(字节)")
    
    # 数据同步配置
    SYNC_INTERVAL_MINUTES: int = Field(default=60, description="同步间隔(分钟)")
    SYNC_INTERVAL_HOURS: int = Field(default=6, description="同步间隔(小时)")
    AUTO_SYNC_ENABLED: bool = Field(default=True, description="是否启用自动同步")
    
    # 加密配置
    ENCRYPTION_KEY: str = Field(default="encryption-key-32-bytes-long!!!", description="加密密钥")
    
    # 代理和域名配置
    PROXY_DOMAIN: Optional[str] = Field(default=None, description="代理域名")
    PROXY_IP: Optional[str] = Field(default=None, description="代理IP地址")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FILE: str = Field(default="logs/app.log", description="日志文件路径")
    
    @property
    def database_url(self) -> str:
        """获取数据库连接URL"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def has_webdav_config(self) -> bool:
        """检查是否配置了WebDAV"""
        return all([self.WEBDAV_URL, self.WEBDAV_USERNAME, self.WEBDAV_PASSWORD])


# 创建全局配置实例
settings = Settings() 