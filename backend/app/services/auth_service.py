from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from backend.app.config import settings
from backend.app.models.user import User
from backend.app.schemas.auth import UserCreate

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """用户认证服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """生成密码哈希"""
        return pwd_context.hash(password)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        try:
            result = await self.db.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"查询用户失败: {e}")
            raise
    
    async def create_user(self, user_data: UserCreate) -> User:
        """创建新用户"""
        try:
            # 检查用户名是否已存在
            existing_user = await self.get_user_by_username(user_data.username)
            if existing_user:
                raise ValueError("用户名已存在")
            
            # 创建新用户
            hashed_password = self.get_password_hash(user_data.password)
            user = User(
                username=user_data.username,
                password_hash=hashed_password
            )
            
            self.db.add(user)
            
            try:
                await self.db.commit()
                await self.db.refresh(user)
                return user
            except SQLAlchemyError as e:
                await self.db.rollback()
                print(f"创建用户失败，已回滚事务: {e}")
                raise
                
        except ValueError:
            # 重新抛出业务逻辑错误
            raise
        except Exception as e:
            print(f"创建用户时发生未知错误: {e}")
            raise
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户身份"""
        try:
            user = await self.get_user_by_username(username)
            if not user:
                return None
            if not self.verify_password(password, user.password_hash):
                return None
            return user
        except Exception as e:
            print(f"用户认证失败: {e}")
            return None
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """获取当前用户（依赖注入）"""
        from backend.app.database import AsyncSessionLocal
        
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(
                credentials.credentials, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        # 查询数据库获取用户信息
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).where(User.username == username)
                )
                user = result.scalar_one_or_none()
                
                if user is None:
                    raise credentials_exception
                
                return {
                    "user_id": user.id,
                    "username": user.username
                }
        except SQLAlchemyError as e:
            print(f"获取当前用户失败: {e}")
            raise credentials_exception 