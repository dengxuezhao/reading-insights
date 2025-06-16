from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class User(Base):
    """用户模型"""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 加密存储的WebDAV凭证
    webdav_url_encrypted: Mapped[Optional[str]] = mapped_column(Text)
    webdav_user_encrypted: Mapped[Optional[str]] = mapped_column(String(255))
    webdav_password_encrypted: Mapped[Optional[str]] = mapped_column(String(255))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    # 关系映射
    books: Mapped[List["Book"]] = relationship("Book", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>" 