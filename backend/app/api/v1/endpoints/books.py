from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.schemas.book import BookResponse, BookDetail, BookList
from backend.app.services.auth_service import AuthService
from backend.app.services.book_service import BookService

router = APIRouter()


@router.get("/", response_model=BookList, summary="获取书籍列表")
async def get_books(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的书籍列表，支持搜索和分页"""
    book_service = BookService(db)
    books_data = await book_service.get_user_books(
        user_id=current_user["user_id"],
        skip=skip,
        limit=limit,
        search=search
    )
    return books_data


@router.get("/{book_id}", response_model=BookDetail, summary="获取书籍详情")
async def get_book_detail(
    book_id: int,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单本书籍的详细信息，包括阅读进度和已读页码"""
    book_service = BookService(db)
    book_detail = await book_service.get_book_detail(
        book_id=book_id,
        user_id=current_user["user_id"]
    )
    
    if not book_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="书籍不存在"
        )
    
    return book_detail


@router.delete("/{book_id}", summary="删除书籍")
async def delete_book(
    book_id: int,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除指定的书籍及其相关数据"""
    book_service = BookService(db)
    success = await book_service.delete_book(
        book_id=book_id,
        user_id=current_user["user_id"]
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="书籍不存在或无权删除"
        )
    
    return {"message": "书籍删除成功"} 