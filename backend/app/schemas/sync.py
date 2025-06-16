from typing import Optional
from pydantic import BaseModel, Field


class SyncRequest(BaseModel):
    """同步请求模型"""
    remote_path: Optional[str] = Field(None, description="远程文件路径，如果为空则自动查找")


class SyncResponse(BaseModel):
    """同步响应模型"""
    success: bool = Field(..., description="同步是否成功")
    message: str = Field(..., description="同步结果消息")
    books_synced: int = Field(..., description="同步的书籍数量")
    sessions_synced: int = Field(..., description="同步的阅读会话数量")
    remote_path: Optional[str] = Field(None, description="使用的远程文件路径")


class SyncStatusResponse(BaseModel):
    """同步状态响应模型"""
    total_books: int = Field(..., description="总书籍数量")
    total_sessions: int = Field(..., description="总阅读会话数量")
    last_reading_time: Optional[str] = Field(None, description="最后阅读时间")
    has_webdav_config: bool = Field(..., description="是否已配置WebDAV")


class SyncLog(BaseModel):
    """同步日志模型"""
    timestamp: str = Field(..., description="同步时间戳")
    user_id: int = Field(..., description="用户ID")
    success: bool = Field(..., description="同步是否成功")
    books_synced: int = Field(..., description="同步的书籍数量")
    sessions_synced: int = Field(..., description="同步的阅读会话数量")
    error_message: Optional[str] = Field(None, description="错误信息")
    duration_seconds: float = Field(..., description="同步耗时（秒）") 