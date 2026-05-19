# PioneClaw 快速部署指南

PioneClaw 是一个企业级智能协作平台，包含前端（Vue 3 + Element Plus）和后端（FastAPI + SQLAlchemy）。

---

## 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [Docker 部署](#docker-部署)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

---

## 环境要求

### 后端
- Python 3.10+
- SQLite（开发）或 PostgreSQL（生产）

### 前端
- Node.js 18+
- npm 9+ 或 pnpm 8+

---

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd pioneclaw
```

### 2. 后端部署

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，修改必要配置

# 初始化数据库
alembic upgrade head

# 初始化基础数据（管理员、角色等）
python -m app.init_data

# 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端部署

```bash
# 新开终端，进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 访问系统

- 前端地址：http://localhost:5173
- 后端 API：http://localhost:8000/docs
- 默认管理员账号：`admin` / `admin123`

---

## 开发环境部署

### 后端开发环境

```bash
cd backend

# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖（包含开发工具）
pip install -r requirements.txt

# 配置环境
cp .env.example .env

# 数据库迁移
alembic upgrade head

# 初始化数据
python -m app.init_data

# 启动开发服务器（热重载）
uvicorn app.main:app --reload --port 8000
```

### 前端开发环境

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

---

## 生产环境部署

### 后端生产部署

#### 1. 使用 Gunicorn + Uvicorn

```bash
cd backend

# 安装生产依赖
pip install -r requirements.txt

# 使用 Gunicorn 启动（多进程）
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

#### 2. 使用 Systemd 服务（Linux）

创建服务文件 `/etc/systemd/system/pioneclaw.service`：

```ini
[Unit]
Description=PioneClaw Backend
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/pioneclaw/backend
Environment="PATH=/opt/pioneclaw/backend/venv/bin"
ExecStart=/opt/pioneclaw/backend/venv/bin/gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable pioneclaw
sudo systemctl start pioneclaw
```

### 前端生产部署

#### 1. 构建静态文件

```bash
cd frontend
npm install
npm run build
```

构建产物在 `dist/` 目录。

#### 2. Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /opt/pioneclaw/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 支持
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Docker 部署

### 使用 Docker Compose（推荐）

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://pioneclaw:password@db:5432/pioneclaw
      - SECRET_KEY=your-production-secret-key
      - CORS_ORIGINS=["http://localhost","http://localhost:80"]
    depends_on:
      - db
    volumes:
      - ./backend/.env:/app/.env

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=pioneclaw
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=pioneclaw
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

启动：

```bash
docker-compose up -d
```

### 单独构建镜像

#### 后端镜像

```bash
cd backend
docker build -t pioneclaw-backend .
docker run -p 8000:8000 -e DATABASE_URL=sqlite+aiosqlite:///./pioneclaw.db pioneclaw-backend
```

#### 前端镜像

```bash
cd frontend
docker build -t pioneclaw-frontend .
docker run -p 80:80 pioneclaw-frontend
```

---

## 配置说明

### 环境变量配置（.env）

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `APP_NAME` | 应用名称 | PioneClaw | 否 |
| `DEBUG` | 调试模式 | true | 否 |
| `DATABASE_URL` | 数据库连接串 | sqlite+aiosqlite:///./pioneclaw.db | 是 |
| `SECRET_KEY` | JWT 密钥 | - | **是** |
| `REFRESH_SECRET_KEY` | 刷新令牌密钥 | - | **是** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 访问令牌过期时间(分钟) | 10080 | 否 |
| `CORS_ORIGINS` | 允许的跨域来源 | ["http://localhost:5173"] | 否 |

### 数据库配置

#### SQLite（开发环境）

```env
DATABASE_URL=sqlite+aiosqlite:///./pioneclaw.db
```

#### PostgreSQL（生产环境）

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/pioneclaw
```

需要额外安装：

```bash
pip install asyncpg
```

---

## 依赖清单

### 后端依赖 (requirements.txt)

```
# Web 框架
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6

# 数据库
sqlalchemy>=2.0.25
aiosqlite>=0.19.0
asyncpg>=0.29.0      # PostgreSQL 支持
alembic>=1.13.0

# 数据验证
pydantic>=2.5.0
pydantic-settings>=2.1.0
email-validator>=2.1.0

# 认证
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# 工具
python-dotenv>=1.0.0
httpx>=0.26.0
PyYAML>=6.0

# CLI
typer>=0.9.0
rich>=13.0

# 测试
pytest>=8.0.0
pytest-asyncio>=0.23.0

# AI (可选)
litellm>=1.20.0
```

### 前端依赖 (package.json)

```json
{
  "dependencies": {
    "@element-plus/icons-vue": "^2.3.1",
    "axios": "^1.6.8",
    "element-plus": "^2.6.1",
    "marked": "^18.0.2",
    "pinia": "^2.1.7",
    "vue": "^3.4.21",
    "vue-i18n": "^9.14.5",
    "vue-router": "^4.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.4",
    "sass": "^1.72.0",
    "typescript": "^5.4.2",
    "vite": "^5.1.6",
    "vue-tsc": "^2.0.6"
  }
}
```

---

## 常见问题

### 1. 数据库迁移失败

```bash
# 重置数据库
rm -f pioneclaw.db
alembic downgrade base
alembic upgrade head
python -m app.init_data
```

### 2. 前端构建失败

```bash
# 清除缓存重新安装
rm -rf node_modules package-lock.json
npm install
npm run build
```

### 3. CORS 跨域问题

确保后端 `.env` 中的 `CORS_ORIGINS` 包含前端地址：

```env
CORS_ORIGINS=["http://localhost:5173","http://your-domain.com"]
```

### 4. JWT 密钥安全

**生产环境必须修改默认密钥！**

```bash
# 生成安全密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 项目结构

```
pioneclaw/
├── backend/
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── core/         # 核心配置
│   │   ├── models/       # 数据模型
│   │   ├── schemas/      # Pydantic 模型
│   │   ├── modules/      # 功能模块
│   │   └── main.py       # 入口文件
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/        # 页面组件
│   │   ├── api/          # API 调用
│   │   ├── stores/       # Pinia 状态
│   │   ├── router/       # 路由配置
│   │   └── locales/      # 国际化
│   ├── package.json
│   └── Dockerfile
└── docs/
    └── DEPLOYMENT.md
```

---

## 技术支持

- 问题反馈：提交 GitHub Issue
- 文档更新：查看 `docs/` 目录

---

**祝部署顺利！**
