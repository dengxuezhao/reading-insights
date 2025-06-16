"""
调试端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

from backend.app.database import get_db
from backend.app.models.user import User

router = APIRouter()


@router.get("/test-db")
async def test_database_connection(db: AsyncSession = Depends(get_db)):
    """测试数据库连接"""
    try:
        # 简单查询测试
        result = await db.execute(text("SELECT 1 as test"))
        test_value = result.scalar()
        
        # 查询用户数量
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        return {
            "success": True,
            "test_query": test_value,
            "user_count": len(users),
            "message": "数据库连接正常"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "数据库连接失败"
        }


@router.post("/test-user-creation")
async def test_user_creation(db: AsyncSession = Depends(get_db)):
    """测试用户创建"""
    try:
        from backend.app.services.auth_service import AuthService
        from backend.app.schemas.auth import UserCreate
        
        auth_service = AuthService(db)
        
        # 创建测试用户
        user_data = UserCreate(
            username="api_test_user",
            password="test123456"
        )
        
        # 检查用户是否已存在
        existing_user = await auth_service.get_user_by_username(user_data.username)
        if existing_user:
            return {
                "success": True,
                "message": f"用户已存在: {existing_user.username}",
                "user_id": existing_user.id
            }
        
        # 创建新用户
        user = await auth_service.create_user(user_data)
        
        return {
            "success": True,
            "message": "用户创建成功",
            "user_id": user.id,
            "username": user.username
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "message": "用户创建失败"
        } 