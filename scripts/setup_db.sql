-- ReadingInsights数据库初始化脚本
-- 请在PostgreSQL中以超级用户身份执行

-- 创建数据库
CREATE DATABASE koreader_data;

-- 创建用户（如果不存在）
-- DO $$
-- BEGIN
--    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'postgres') THEN
--       CREATE USER postgres WITH PASSWORD 'your-password-here';
--    END IF;
-- END
-- $$;

-- 授权
GRANT ALL PRIVILEGES ON DATABASE koreader_data TO postgres;

-- 连接到新数据库
\c koreader_data;

-- 确保用户有创建表的权限
GRANT ALL ON SCHEMA public TO postgres;

-- 显示当前数据库信息
SELECT current_database() as database_name, current_user as current_user; 