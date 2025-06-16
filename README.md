# ReadingInsights - 个人阅读数据分析平台

ReadingInsights 是一个现代化的Web应用，专注于个人阅读数据的深度分析和可视化。支持从KOReader等阅读设备同步数据，为用户提供全面的阅读习惯洞察。

> 📖 **完整使用指南请查看 [用户指南.md](用户指南.md)**

## 项目特性

- 📊 **阅读统计仪表盘**: 全面的阅读数据可视化
- 📚 **书籍管理**: 书籍列表、详情查看和阅读进度跟踪
- ☁️ **WebDAV同步**: 从坚果云等WebDAV服务自动同步阅读数据
- 📝 **标注管理**: 导入和管理KOReader的高亮标注
- 📅 **日历热力图**: 直观展示每日阅读活动
- 🔐 **用户认证**: 安全的JWT认证系统

## 技术栈

### 后端
- **FastAPI**: 现代、高性能的Python Web框架
- **SQLAlchemy 2.0**: 现代Python ORM
- **PostgreSQL**: 主数据库
- **Alembic**: 数据库迁移工具
- **APScheduler**: 定时任务调度
- **Pydantic**: 数据验证和序列化

### 前端 (计划中)
- **Vue.js 3**: 现代前端框架
- **TypeScript**: 类型安全的JavaScript
- **Vite**: 快速构建工具

## 快速开始

### 环境要求
- Python 3.11+
- PostgreSQL 12+
- uv (推荐的Python包管理器)

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd reading-insights
   ```

2. **安装依赖**
   ```bash
   uv sync
   ```

3. **配置环境变量**
   ```bash
   cp env.example .env
   # 编辑 .env 文件，填入你的数据库配置等信息
   ```

4. **创建数据库**
   ```bash
   # 在PostgreSQL中创建数据库
   createdb koreader_data
   ```

5. **运行数据库迁移**
   ```bash
   uv run alembic upgrade head
   ```

6. **启动开发服务器**
   ```bash
   # 推荐方式：使用开发脚本
   uv run python scripts/dev.py
   
   # 或者直接使用uvicorn
   uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **访问应用**
   - API文档: http://localhost:8000/docs
   - 健康检查: http://localhost:8000/health

## 项目结构

```
reading-insights/
├── backend/                    # 后端应用
│   ├── app/
│   │   ├── api/               # API路由
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # Pydantic模型
│   │   ├── services/          # 业务逻辑层
│   │   ├── utils/             # 工具函数
│   │   └── tasks/             # 定时任务
│   ├── alembic/               # 数据库迁移
│   └── tests/                 # 测试
├── frontend/                   # 前端应用 (待开发)
├── docker/                     # Docker配置
├── docs/                       # 文档
├── pyproject.toml             # 项目配置
└── README.md                  # 项目说明
```

## API 端点

### 认证
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户信息

### WebDAV配置
- `POST /api/v1/settings/webdav` - 配置WebDAV
- `GET /api/v1/settings/webdav` - 获取WebDAV配置
- `POST /api/v1/settings/webdav/test` - 测试WebDAV连接

### 仪表盘
- `GET /api/v1/dashboard/summary` - 获取统计摘要
- `GET /api/v1/dashboard/calendar` - 获取日历热力图数据

### 书籍管理
- `GET /api/v1/books/` - 获取书籍列表
- `GET /api/v1/books/{book_id}` - 获取书籍详情

### 标注管理
- `POST /api/v1/highlights/` - 导入标注数据
- `GET /api/v1/highlights/{book_id}` - 获取书籍标注

### 数据同步
- `POST /api/v1/sync/manual` - 手动同步数据
- `POST /api/v1/sync/background` - 后台同步数据
- `GET /api/v1/sync/status` - 获取同步状态
- `GET /api/v1/sync/files` - 列出远程文件
- `GET /api/v1/sync/find-statistics` - 查找统计文件

## 开发指南

### 代码规范
- 使用 `black` 进行代码格式化
- 使用 `isort` 进行导入排序
- 使用 `mypy` 进行类型检查
- 使用 `flake8` 进行代码检查

### 运行代码检查
```bash
uv run black backend/
uv run isort backend/
uv run mypy backend/
uv run flake8 backend/
```

### 运行测试
```bash
uv run pytest
```

### 数据库迁移
```bash
# 创建新的迁移文件
uv run alembic revision --autogenerate -m "描述信息"

# 应用迁移
uv run alembic upgrade head

# 回滚迁移
uv run alembic downgrade -1
```

## 部署

### Docker部署
```bash
docker-compose up -d
```

### 生产环境配置
1. 设置 `DEBUG=False`
2. 配置强密码和密钥
3. 使用HTTPS
4. 配置数据库连接池
5. 设置反向代理

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系我们

- 项目链接: [https://github.com/yourusername/reading-insights](https://github.com/yourusername/reading-insights)
- 问题反馈: [Issues](https://github.com/yourusername/reading-insights/issues)

## 致谢

- [KOReader](https://github.com/koreader/koreader) - 优秀的电子书阅读器
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python Web框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL工具包 