from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class BookResponse(BaseModel):
    """书籍基础信息响应模型"""
    id: int = Field(..., description="书籍ID")
    title: str = Field(..., description="书籍标题")
    author: Optional[str] = Field(None, description="作者")
    total_pages: Optional[int] = Field(None, description="总页数")
    cover_image_url: Optional[str] = Field(None, description="封面图片URL")
    reading_progress: float = Field(0.0, description="阅读进度百分比", ge=0, le=100)
    total_reading_time: int = Field(0, description="总阅读时长（秒）", ge=0)
    last_read_time: Optional[datetime] = Field(None, description="最后阅读时间")
    md5: Optional[str] = Field(None, description="文件MD5标识符")


class BookDetail(BookResponse):
    """书籍详情模型"""
    read_pages: List[int] = Field(default=[], description="已读页码数组")
    read_pages_count: int = Field(0, description="已读页数", ge=0)
    reading_sessions_count: int = Field(0, description="阅读会话数量", ge=0)
    highlights_count: int = Field(0, description="标注数量", ge=0)
    created_at: Optional[datetime] = Field(None, description="创建时间")


class BookList(BaseModel):
    """书籍列表响应模型"""
    books: List[BookResponse] = Field(default=[], description="书籍列表")
    total: int = Field(0, description="总数量", ge=0)
    page: int = Field(1, description="当前页码", ge=1)
    page_size: int = Field(10, description="每页数量", ge=1)
    total_pages: int = Field(0, description="总页数", ge=0)


class BookCreate(BaseModel):
    """书籍创建模型"""
    title: str = Field(..., description="书籍标题", min_length=1, max_length=255)
    author: Optional[str] = Field(None, description="作者", max_length=255)
    total_pages: Optional[int] = Field(None, description="总页数", gt=0)
    cover_image_url: Optional[str] = Field(None, description="封面图片URL")
    md5: Optional[str] = Field(None, description="文件MD5标识符", max_length=32)


class BookUpdate(BaseModel):
    """书籍更新模型"""
    title: Optional[str] = Field(None, description="书籍标题", min_length=1, max_length=255)
    author: Optional[str] = Field(None, description="作者", max_length=255)
    total_pages: Optional[int] = Field(None, description="总页数", gt=0)
    cover_image_url: Optional[str] = Field(None, description="封面图片URL") 