from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, ForeignKey, DateTime, Index, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class ReadingSession(Base):
    """阅读会话模型"""
    
    __tablename__ = "reading_sessions"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    page: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)  # 阅读持续时长（秒）
    total_pages_at_time: Mapped[Optional[int]] = mapped_column(Integer)  # 阅读时书籍的总页数
    
    # 关系映射
    book: Mapped["Book"] = relationship("Book", back_populates="reading_sessions")
    
    # 创建联合唯一索引防止重复记录
    __table_args__ = (
        Index('idx_book_page_time', 'book_id', 'page', 'start_time', unique=True),
        Index('idx_sessions_book_id', 'book_id'),
        Index('idx_sessions_start_time', 'start_time'),
    )
    
    def __repr__(self) -> str:
        return f"<ReadingSession(id={self.id}, book_id={self.book_id}, page={self.page}, duration={self.duration})>" 