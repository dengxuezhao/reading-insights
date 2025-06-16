from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class BookData(BaseModel):
    """书籍数据模型（用于标注导入）"""
    title: str = Field(..., description="书名")
    author: Optional[str] = Field(None, description="作者")
    md5: Optional[str] = Field(None, description="MD5标识符")


class HighlightData(BaseModel):
    """标注数据模型（用于标注导入）"""
    text: str = Field(..., description="高亮内容")
    note: Optional[str] = Field(None, description="笔记内容")
    chapter: Optional[str] = Field(None, description="章节")
    page: Optional[int] = Field(None, description="页码")
    created_time: Optional[datetime] = Field(None, description="创建时间")


class HighlightImport(BaseModel):
    """标注导入模型"""
    book: BookData
    highlights: List[HighlightData]


class HighlightResponse(BaseModel):
    """标注响应模型"""
    id: int
    book_id: int
    text: str
    note: Optional[str] = None
    chapter: Optional[str] = None
    page: Optional[int] = None
    created_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class HighlightsByChapter(BaseModel):
    """按章节分组的标注模型"""
    chapter: str
    highlights: List[HighlightResponse]


class BookHighlights(BaseModel):
    """书籍标注模型"""
    book_id: int
    book_title: str
    total_highlights: int
    highlights_by_chapter: List[HighlightsByChapter] 