#!/usr/bin/env python3
"""
开发服务器启动脚本
"""
import argparse
import subprocess
import sys
import socket
from pathlib import Path


def get_local_ip():
    """获取本机IP地址"""
    try:
        # 连接到一个外部地址来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "localhost"


def main():
    """启动开发服务器"""
    # 添加命令行参数解析
    parser = argparse.ArgumentParser(description="启动ReadingInsights开发服务器")
    parser.add_argument("--port", "-p", type=int, default=8083, help="服务器端口 (默认: 8083)")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机 (默认: 0.0.0.0)")
    args = parser.parse_args()
    
    # 确保在项目根目录
    project_root = Path(__file__).parent.parent
    
    # 获取本机IP
    local_ip = get_local_ip()
    
    # 启动uvicorn开发服务器
    cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.app.main:app",
        "--reload",
        "--host", args.host, 
        "--port", str(args.port),
        "--reload-dir", str(project_root / "backend")
    ]
    
    print("🚀 启动ReadingInsights开发服务器...")
    print(f"📁 项目目录: {project_root}")
    print("=" * 50)
    print("📍 访问地址:")
    print(f"   本地访问: http://localhost:{args.port}")
    if local_ip != "localhost":
        print(f"   内网访问: http://{local_ip}:{args.port}")
        print(f"   外网访问: http://[您的VPS公网IP]:{args.port}")
    print("=" * 50)
    print(f"📚 API文档: http://localhost:{args.port}/docs")
    print("💡 提示: 如遇到'Invalid host header'错误，请确认ALLOWED_HOSTS配置包含您的访问域名")
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