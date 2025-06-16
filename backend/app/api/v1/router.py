from fastapi import APIRouter

from backend.app.api.v1.endpoints import auth, webdav, dashboard, books, highlights, sync, debug, statistics, public

api_router = APIRouter()

# 公共端点 - 无需认证
api_router.include_router(public.router, prefix="/public", tags=["公共接口"])

# 注册各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(webdav.router, prefix="/settings", tags=["设置"])
api_router.include_router(sync.router, prefix="/sync", tags=["数据同步"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["仪表盘"])
api_router.include_router(statistics.router, prefix="/statistics", tags=["统计分析"])
api_router.include_router(books.router, prefix="/books", tags=["书籍"])
api_router.include_router(highlights.router, prefix="/highlights", tags=["标注"])

# 调试端点 - 仅在开发环境中启用
# api_router.include_router(debug.router, prefix="/debug", tags=["调试"]) 