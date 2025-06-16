from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.app.config import settings
from backend.app.api.v1.router import api_router
from backend.app.tasks.scheduler import sync_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("🚀 正在启动应用...")
    
    # 初始化默认用户
    from backend.app.database import AsyncSessionLocal
    from backend.app.services.user_init_service import UserInitService
    
    async with AsyncSessionLocal() as db:
        try:
            user_init_service = UserInitService(db)
            user_info = await user_init_service.ensure_default_user()
            if user_info:
                print(f"👤 默认用户已就绪 (ID: {user_info['user_id']})")
            else:
                print("⚠️ 默认用户功能已禁用")
        except Exception as e:
            print(f"❌ 默认用户初始化失败: {e}")
    
    if not settings.DEBUG:  # 仅在生产环境启动定时任务
        sync_scheduler.start()
    
    print("✅ 应用启动完成")
    yield
    
    # 关闭时执行
    print("🛑 正在关闭应用...")
    sync_scheduler.stop()
    print("✅ 应用已关闭")


# 创建FastAPI应用实例
app = FastAPI(
    title="ReadingInsights API",
    description="ReadingInsights 个人阅读数据分析平台后端API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 添加受信任主机中间件
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# 注册API路由
app.include_router(api_router, prefix="/api/v1")

# 获取前端文件路径
frontend_path = Path(__file__).parent.parent.parent / "frontend"

# 挂载静态文件服务
app.mount("/js", StaticFiles(directory=str(frontend_path / "js")), name="js")
app.mount("/styles", StaticFiles(directory=str(frontend_path / "styles")), name="styles")

# 根路径返回前端页面
@app.get("/")
async def serve_frontend():
    """服务前端页面"""
    return FileResponse(str(frontend_path / "index.html"))

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}

@app.get("/scheduler/status")
async def scheduler_status():
    """调度器状态检查（仅开发环境）"""
    if not settings.DEBUG:
        return {"error": "仅在开发环境可用"}
    
    return {
        "running": sync_scheduler.is_running,
        "jobs": sync_scheduler.get_jobs_status()
    } 