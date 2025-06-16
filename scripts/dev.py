#!/usr/bin/env python3
"""
开发服务器启动脚本
"""
import subprocess
import sys
from pathlib import Path


def main():
    """启动开发服务器"""
    # 确保在项目根目录
    project_root = Path(__file__).parent.parent
    
    # 启动uvicorn开发服务器
    cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.app.main:app",
        "--reload",
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload-dir", str(project_root / "backend")
    ]
    
    print("🚀 启动ReadingInsights开发服务器...")
    print(f"📁 项目目录: {project_root}")
    print("🌐 访问地址: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("=" * 50)
    
    try:
        subprocess.run(cmd, cwd=project_root, check=True)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 服务器启动失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 