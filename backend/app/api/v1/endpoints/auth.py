from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.schemas.auth import UserCreate, UserLogin, Token, UserResponse
from backend.app.services.auth_service import AuthService

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """用户注册接口"""
    auth_service = AuthService(db)
    try:
        user = await auth_service.create_user(user_data)
        return UserResponse(
            id=user.id,
            username=user.username,
            created_at=user.created_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # 捕获所有其他异常并记录
        print(f"用户注册发生异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )


@router.post("/login", response_model=Token, summary="用户登录")
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """用户登录接口"""
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前登录用户的信息"""
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_username(current_user["username"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        created_at=user.created_at
    ) 