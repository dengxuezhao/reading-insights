from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class Book(Base):
    """书籍模型"""
    
    __tablename__ = "books"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(255))
    md5: Mapped[Optional[str]] = mapped_column(String(32))  # 用于唯一识别书籍
    total_pages: Mapped[Optional[int]] = mapped_column(Integer)
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(255))
    
    # 关系映射
    user: Mapped["User"] = relationship("User", back_populates="books")
    reading_sessions: Mapped[List["ReadingSession"]] = relationship(
        "ReadingSession", back_populates="book", cascade="all, delete-orphan"
    )
    highlights: Mapped[List["Highlight"]] = relationship(
        "Highlight", back_populates="book", cascade="all, delete-orphan"
    )
    
    # 创建联合唯一索引来防止同一用户重复添加同一本书
    __table_args__ = (
        Index('idx_user_md5', 'user_id', 'md5', unique=True),
        Index('idx_books_user_id', 'user_id'),
    )
    
    def __repr__(self) -> str:
        return f"<Book(id={self.id}, title='{self.title}', author='{self.author}')>" 