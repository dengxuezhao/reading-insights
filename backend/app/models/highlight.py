from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, Index, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class Highlight(Base):
    """标注模型"""
    
    __tablename__ = "highlights"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)  # 高亮内容
    note: Mapped[Optional[str]] = mapped_column(Text)  # 笔记内容，可以为空
    chapter: Mapped[Optional[str]] = mapped_column(String(255))
    page: Mapped[Optional[int]] = mapped_column(Integer)
    created_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # 标注创建时间
    
    # 关系映射
    book: Mapped["Book"] = relationship("Book", back_populates="highlights")
    
    # 创建联合唯一索引防止重复导入同一条标注
    __table_args__ = (
        Index('idx_book_page_created', 'book_id', 'page', 'created_time', unique=True),
        Index('idx_highlights_book_id', 'book_id'),
    )
    
    def __repr__(self) -> str:
        return f"<Highlight(id={self.id}, book_id={self.book_id}, chapter='{self.chapter}', page={self.page})>" 