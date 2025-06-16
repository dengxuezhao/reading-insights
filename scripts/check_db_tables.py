#!/usr/bin/env python3
"""
数据库表检查脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.database import engine
from sqlalchemy import text

async def check_tables():
    """检查数据库表是否存在"""
    print("🔍 检查数据库表...")
    print("=" * 50)
    
    try:
        async with engine.connect() as conn:
            # 检查所有表
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result]
            
            print(f"📊 数据库中的表 ({len(tables)}个):")
            for table in tables:
                print(f"  ✓ {table}")
            
            # 检查期望的表
            expected_tables = ["users", "books", "reading_sessions", "highlights", "alembic_version"]
            missing_tables = [table for table in expected_tables if table not in tables]
            
            if missing_tables:
                print(f"\n❌ 缺少的表:")
                for table in missing_tables:
                    print(f"  ✗ {table}")
                return False
            else:
                print(f"\n✅ 所有期望的表都存在!")
                
                # 检查users表结构
                print(f"\n🔍 检查users表结构:")
                result = await conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'users'
                    ORDER BY ordinal_position;
                """))
                
                for row in result:
                    nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                    print(f"  - {row[0]}: {row[1]} ({nullable})")
                
                return True
                
    except Exception as e:
        print(f"❌ 检查表失败: {e}")
        return False

async def main():
    """主函数"""
    success = await check_tables()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 