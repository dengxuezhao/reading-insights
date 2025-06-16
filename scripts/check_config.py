#!/usr/bin/env python3
"""
配置检查脚本
验证.env文件配置是否正确读取
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.config import settings

def check_config():
    """检查配置"""
    print("🔍 检查应用配置")
    print("=" * 60)
    
    # 基础配置
    print("📋 基础配置:")
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   SECRET_KEY: {settings.SECRET_KEY[:20]}...")
    
    # 默认用户配置
    print("\n👤 默认用户配置:")
    print(f"   DEFAULT_USER_ENABLED: {settings.DEFAULT_USER_ENABLED}")
    print(f"   DEFAULT_USERNAME: {settings.DEFAULT_USERNAME}")
    print(f"   DEFAULT_USER_AUTO_CREATE: {settings.DEFAULT_USER_AUTO_CREATE}")
    
    # WebDAV配置
    print("\n🔗 WebDAV配置:")
    print(f"   WEBDAV_URL: {settings.WEBDAV_URL}")
    print(f"   WEBDAV_USERNAME: {settings.WEBDAV_USERNAME}")
    print(f"   WEBDAV_PASSWORD: {'已配置' if settings.WEBDAV_PASSWORD else '未配置'}")
    print(f"   WEBDAV_BASE_PATH: {settings.WEBDAV_BASE_PATH}")
    print(f"   has_webdav_config: {settings.has_webdav_config}")
    
    # 数据库配置
    print("\n🗄️ 数据库配置:")
    print(f"   DB_HOST: {settings.DB_HOST}")
    print(f"   DB_PORT: {settings.DB_PORT}")
    print(f"   DB_USER: {settings.DB_USER}")
    print(f"   DB_NAME: {settings.DB_NAME}")
    print(f"   DATABASE_URL: {settings.database_url}")
    
    # JWT配置
    print("\n🔑 JWT配置:")
    print(f"   JWT_SECRET_KEY: {settings.JWT_SECRET_KEY[:20]}...")
    print(f"   JWT_ALGORITHM: {settings.JWT_ALGORITHM}")
    print(f"   JWT_ACCESS_TOKEN_EXPIRE_MINUTES: {settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES}")
    
    # 前端配置
    print("\n🌐 前端配置:")
    print(f"   FRONTEND_TITLE: {settings.FRONTEND_TITLE}")
    print(f"   FRONTEND_DESCRIPTION: {settings.FRONTEND_DESCRIPTION}")
    print(f"   PUBLIC_DEMO_MODE: {settings.PUBLIC_DEMO_MODE}")
    
    print("\n" + "=" * 60)
    
    # 检查关键配置
    issues = []
    
    if not settings.DEFAULT_USER_ENABLED:
        issues.append("默认用户功能已禁用")
    
    if not settings.has_webdav_config:
        issues.append("WebDAV配置不完整")
        if not settings.WEBDAV_URL:
            issues.append("  - WEBDAV_URL 未配置")
        if not settings.WEBDAV_USERNAME:
            issues.append("  - WEBDAV_USERNAME 未配置")
        if not settings.WEBDAV_PASSWORD:
            issues.append("  - WEBDAV_PASSWORD 未配置")
    
    if issues:
        print("❌ 配置问题:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print("✅ 配置检查通过")
        return True

if __name__ == "__main__":
    success = check_config()
    sys.exit(0 if success else 1) 