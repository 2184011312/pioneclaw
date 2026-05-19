# PioneClaw 快速启动说明

> 解压 pioneclaw.zip 后，按以下步骤启动系统

---

## 1. 环境要求

- **Python 3.10+**
- **Node.js 18+**
- npm 或 pnpm

---

## 2. 后端启动

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

# 创建环境配置
cp .env.example .env
# 首次启动可以不修改 .env，使用默认配置

# 初始化数据库
alembic upgrade head

# 初始化基础数据（创建管理员账号等）
python -m app.init_data

# 启动后端服务
uvicorn app.main:app --reload --port 8000
```

后端启动成功后访问：
- API 文档：http://localhost:8000/docs
- 默认账号：`admin` / `admin123`

---

## 3. 前端启动

**新开一个终端窗口**

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端启动成功后访问：
- http://localhost:5173

---

## 4. 一键启动脚本

### Windows
双击运行 `quick-start.bat`

### Linux/macOS
```bash
chmod +x quick-start.sh
./quick-start.sh
```

脚本会自动：
1. 创建虚拟环境
2. 安装后端依赖
3. 初始化数据库
4. 安装前端依赖

完成后按提示分别启动后端和前端。

---

## 5. 常见问题

### Q: 端口被占用怎么办？

```bash
# 后端改用其他端口
uvicorn app.main:app --reload --port 8001

# 前端会自动使用 5174 等可用端口
```

### Q: 数据库初始化失败？

```bash
# 删除旧数据库重新初始化
rm -f pioneclaw.db
alembic downgrade base
alembic upgrade head
python -m app.init_data
```

### Q: npm install 很慢？

```bash
# 使用国内镜像
npm config set registry https://registry.npmmirror.com
npm install
```

### Q: pip install 很慢？

```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 6. 生产环境部署

如需生产环境部署，请参考 `docs/DEPLOYMENT.md`。

---

**祝使用顺利！**
