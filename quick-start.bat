@echo off
REM ═══════════════════════════════════════════════════════════════
REM PioneClaw Quick Start Script (Windows)
REM ═══════════════════════════════════════════════════════════════

echo.
echo 🚀 PioneClaw Quick Start
echo ═════════════════════════════════════════════════════

REM 检查 Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Python is required but not installed.
    pause
    exit /b 1
)

REM 检查 Node.js
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Node.js is required but not installed.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VER=%%i
for /f "tokens=*" %%i in ('node --version') do set NODE_VER=%%i

echo ✅ Python: %PYTHON_VER%
echo ✅ Node.js: %NODE_VER%
echo.

REM ── Backend Setup ──────────────────────────────────────────────
echo 📦 Setting up backend...
echo.

cd backend

REM 创建虚拟环境
if not exist "venv" (
    echo   Creating virtual environment...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate

REM 安装依赖
echo   Installing Python dependencies...
pip install -q -r requirements.txt

REM 配置环境
if not exist ".env" (
    echo   Creating .env from .env.example...
    copy .env.example .env >nul
)

REM 数据库迁移
echo   Running database migrations...
alembic upgrade head 2>nul || echo   Migrations already applied

REM 初始化数据
echo   Initializing base data...
python -m app.init_data 2>nul || echo   Data already initialized

echo.
echo ✅ Backend ready!
echo.

REM ── Frontend Setup ─────────────────────────────────────────────
echo 📦 Setting up frontend...
echo.

cd ..\frontend

REM 安装依赖
if not exist "node_modules" (
    echo   Installing Node.js dependencies...
    call npm install
)

echo.
echo ✅ Frontend ready!
echo.

REM ── Done ───────────────────────────────────────────────────────
cd ..

echo ═════════════════════════════════════════════════════
echo 🎉 Setup complete!
echo.
echo To start the servers:
echo.
echo   # Terminal 1 - Backend:
echo   cd backend
echo   venv\Scripts\activate
echo   uvicorn app.main:app --reload --port 8000
echo.
echo   # Terminal 2 - Frontend:
echo   cd frontend
echo   npm run dev
echo.
echo Then open http://localhost:5173
echo Default login: admin / admin123
echo ═════════════════════════════════════════════════════
echo.

pause
