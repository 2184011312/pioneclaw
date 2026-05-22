#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# PioneClaw Quick Start Script (Linux/macOS)
# ═══════════════════════════════════════════════════════════════

set -e

echo "🚀 PioneClaw Quick Start"
echo "═════════════════════════════════════"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

echo "✅ Python: $(python3 --version)"
echo "✅ Node.js: $(node --version)"
echo ""

# ── Backend Setup ──────────────────────────────────────────────
echo "📦 Setting up backend..."

cd backend

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "  Installing Python dependencies..."
pip install -q -r requirements.txt

# 配置环境
if [ ! -f ".env" ]; then
    echo "  Creating .env from .env.example..."
    cp .env.example .env
fi

# 数据库迁移
echo "  Running database migrations..."
alembic upgrade head 2>/dev/null || echo "  Migrations already applied"

# 初始化数据
echo "  Initializing base data..."
python -m app.init_data 2>/dev/null || echo "  Data already initialized"

echo "✅ Backend ready!"
echo ""

# ── Frontend Setup ─────────────────────────────────────────────
echo "📦 Setting up frontend..."

cd ../frontend

# 安装依赖
if [ ! -d "node_modules" ]; then
    echo "  Installing Node.js dependencies..."
    npm install
fi

echo "✅ Frontend ready!"
echo ""

# ── Done ───────────────────────────────────────────────────────
cd ..

echo "═════════════════════════════════════"
echo "🎉 Setup complete!"
echo ""
echo "To start the servers:"
echo ""
echo "  # Terminal 1 - Backend:"
echo "  cd backend && source venv/bin/activate"
echo "  uvicorn app.main:app --reload --port 8000"
echo ""
echo "  # Terminal 2 - Frontend:"
echo "  cd frontend && npm run dev"
echo ""
echo "Then open http://localhost:5173"
echo "Default login: admin / admin123"
echo "═════════════════════════════════════"
