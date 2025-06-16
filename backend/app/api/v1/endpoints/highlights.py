from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.schemas.highlight import HighlightImport, HighlightResponse
from backend.app.services.auth_service import AuthService
from backend.app.services.highlight_service import HighlightService

router = APIRouter()


@router.post("/", response_model=dict, summary="导入标注数据")
async def import_highlights(
    highlight_data: HighlightImport,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """从KOReader导出插件接收标注数据"""
    highlight_service = HighlightService(db)
    try:
        result = await highlight_service.import_highlights(
            user_id=current_user["user_id"],
            book_data=highlight_data.book,
            highlights_data=highlight_data.highlights
        )
        return {
            "message": "标注导入成功",
            "book_id": result["book_id"],
            "imported_count": result["imported_count"],
            "skipped_count": result["skipped_count"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"标注导入失败: {str(e)}"
        )


@router.get("/{book_id}", response_model=list[HighlightResponse], summary="获取书籍标注")
async def get_book_highlights(
    book_id: int,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定书籍的所有标注"""
    highlight_service = HighlightService(db)
    highlights = await highlight_service.get_book_highlights(
        book_id=book_id,
        user_id=current_user["user_id"]
    )
    return highlights


@router.delete("/{highlight_id}", summary="删除标注")
async def delete_highlight(
    highlight_id: int,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除指定的标注"""
    highlight_service = HighlightService(db)
    success = await highlight_service.delete_highlight(
        highlight_id=highlight_id,
        user_id=current_user["user_id"]
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标注不存在或无权删除"
        )
    
    return {"message": "标注删除成功"} 