#!/usr/bin/env python3
"""
WebDAV配置修复脚本
修复坚果云WebDAV连接问题，将disable_check选项设置为True
"""

import sys
from pathlib import Path
import traceback
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.config import settings
from webdav3.client import Client

def test_webdav_connection(disable_check=False):
    """测试WebDAV连接，可选择是否禁用验证检查"""
    print(f"\n🔍 WebDAV配置信息:")
    print(f"URL: {settings.WEBDAV_URL}")
    print(f"用户名: {settings.WEBDAV_USERNAME}")
    print(f"密码长度: {len(settings.WEBDAV_PASSWORD) if settings.WEBDAV_PASSWORD else 0}")
    print(f"基础路径: {settings.WEBDAV_BASE_PATH}")
    print(f"禁用验证检查: {disable_check}")
    
    try:
        webdav_options = {
            'webdav_hostname': settings.WEBDAV_URL,
            'webdav_login': settings.WEBDAV_USERNAME,
            'webdav_password': settings.WEBDAV_PASSWORD,
            'webdav_timeout': 30,
            'disable_check': disable_check,
        }
        
        print("创建WebDAV客户端...")
        client = Client(webdav_options)
        
        print("测试连接...")
        result = client.check()
        print(f"连接结果: {result}")
        
        if result:
            print("✅ WebDAV连接测试成功!")
            
            # 尝试列出根目录
            print("\n📁 列出根目录...")
            try:
                files = client.list("/")
                print(f"✅ 根目录包含 {len(files)} 个项目:")
                for file in files[:10]:
                    print(f"   - {file}")
                if len(files) > 10:
                    print(f"   ... 还有 {len(files) - 10} 个项目")
                
                # 尝试列出基础路径
                if settings.WEBDAV_BASE_PATH:
                    base_path = settings.WEBDAV_BASE_PATH
                    print(f"\n📁 列出基础路径 {base_path}...")
                    try:
                        base_files = client.list(base_path)
                        print(f"✅ 基础路径包含 {len(base_files)} 个项目:")
                        for file in base_files[:10]:
                            print(f"   - {file}")
                        if len(base_files) > 10:
                            print(f"   ... 还有 {len(base_files) - 10} 个项目")
                    except Exception as e:
                        print(f"❌ 列出基础路径失败: {e}")
                
            except Exception as e:
                print(f"❌ 列出文件失败: {e}")
                print("详细错误信息:")
                traceback.print_exc()
            
            return True
        else:
            print("❌ WebDAV连接测试失败")
            return False
    except Exception as e:
        print(f"❌ WebDAV客户端异常: {e}")
        print("详细错误信息:")
        traceback.print_exc()
        return False

def print_fix_instructions():
    """打印修复说明"""
    print("\n🔧 WebDAV配置修复说明:")
    print("=" * 60)
    print("要修复坚果云WebDAV连接问题，请在以下文件中修改WebDAV客户端配置:")
    print("文件: backend/app/services/webdav_service.py")
    print("修改: 将 _create_webdav_client 方法中的 'disable_check': False 改为 'disable_check': True")
    print("\n修改前:")
    print("```python")
    print("webdav_options = {")
    print("    'webdav_hostname': config['url'],")
    print("    'webdav_login': config['username'],")
    print("    'webdav_password': config['password'],")
    print("    'webdav_timeout': 30,")
    print("    'disable_check': False,  # 启用SSL证书检查")
    print("}")
    print("```")
    print("\n修改后:")
    print("```python")
    print("webdav_options = {")
    print("    'webdav_hostname': config['url'],")
    print("    'webdav_login': config['username'],")
    print("    'webdav_password': config['password'],")
    print("    'webdav_timeout': 30,")
    print("    'disable_check': True,  # 禁用验证检查，解决坚果云连接问题")
    print("}")
    print("```")

if __name__ == "__main__":
    print("🔧 WebDAV配置修复工具")
    print("=" * 60)
    
    print("\n1️⃣ 测试当前配置 (disable_check=False)...")
    current_success = test_webdav_connection(disable_check=False)
    
    print("\n2️⃣ 测试修复配置 (disable_check=True)...")
    fixed_success = test_webdav_connection(disable_check=True)
    
    print("\n📊 测试结果:")
    print("=" * 60)
    print(f"当前配置 (disable_check=False): {'✅ 成功' if current_success else '❌ 失败'}")
    print(f"修复配置 (disable_check=True): {'✅ 成功' if fixed_success else '❌ 失败'}")
    
    if not current_success and fixed_success:
        print("\n✅ 确认问题: 需要设置 disable_check=True 才能正常连接坚果云WebDAV服务")
        print_fix_instructions()
    elif current_success:
        print("\n✅ 当前配置已可正常连接，无需修复")
    else:
        print("\n❌ 两种配置都无法连接，可能存在其他问题")
        print("请检查:")
        print("1. WebDAV URL是否正确")
        print("2. 用户名和密码是否正确")
        print("3. 网络连接是否正常")
        print("4. 坚果云WebDAV服务是否可用") 