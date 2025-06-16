#!/usr/bin/env python3
"""
服务状态检查脚本
检查前端和后端服务是否正常运行
"""

import requests
import sys

def check_service(name, url, expected_content=None):
    """检查服务状态"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            if expected_content and expected_content not in response.text:
                print(f"⚠️ {name}: 服务运行但内容异常")
                return False
            print(f"✅ {name}: 正常运行 (状态码: {response.status_code})")
            return True
        else:
            print(f"❌ {name}: 服务异常 (状态码: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name}: 连接失败，服务可能未启动")
        return False
    except requests.exceptions.Timeout:
        print(f"⏱️ {name}: 请求超时")
        return False
    except Exception as e:
        print(f"💥 {name}: 检查异常 - {e}")
        return False

def main():
    """主函数"""
    print("🔍 检查服务状态")
    print("=" * 50)
    
    services = [
        ("前端服务 (ReadingInsights)", "http://localhost:3000", "ReadingInsights"),
        ("后端API服务", "http://localhost:8000/docs", "Swagger UI"),
        ("后端配置API", "http://localhost:8000/api/v1/public/config", "KOReader"),
    ]
    
    all_ok = True
    
    for name, url, expected in services:
        if not check_service(name, url, expected):
            all_ok = False
    
    print("\n" + "=" * 50)
    
    if all_ok:
        print("🎉 所有服务正常运行！")
        print("💡 您可以访问:")
        print("   📱 前端页面: http://localhost:3000")
        print("   📚 API文档: http://localhost:8000/docs")
        return True
    else:
        print("⚠️ 部分服务异常，请检查启动状态")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 