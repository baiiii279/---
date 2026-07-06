#!/bin/bash
# PaperCraft 一键安装脚本
# 适用于 Linux / macOS / Windows (Git Bash)
set -e

echo "================================"
echo "  PaperCraft 依赖安装脚本"
echo "================================"

# 检查 Python
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "[错误] 未检测到 Python，请先安装 Python 3.11+"
    exit 1
fi
PYTHON=$(command -v python3 || command -v python)
echo "[OK] Python: $($PYTHON --version)"

# 检查 Node.js
if ! command -v node &>/dev/null; then
    echo "[错误] 未检测到 Node.js，请先安装 Node.js 18+"
    exit 1
fi
echo "[OK] Node.js: $(node --version)"

# 检查 MySQL
if command -v mysql &>/dev/null; then
    echo "[OK] MySQL: $(mysql --version 2>&1 | head -1)"
else
    echo "[警告] 未检测到 MySQL CLI，请确保 MySQL 服务已安装并运行"
fi

echo ""
echo ">>> 安装后端依赖..."
cd "$(dirname "$0")/backend"

# 创建 .env（如果不存在）
if [ ! -f .env ]; then
    cp .env.example .env
    echo "[提示] 已从 .env.example 创建 .env 文件，请修改其中的数据库密码和 API Key"
fi

pip install -r requirements.txt
echo "[OK] 后端依赖安装完成"

echo ""
echo ">>> 安装前端依赖..."
cd ../frontend
npm install
echo "[OK] 前端依赖安装完成"

echo ""
echo "================================"
echo "  安装完成!"
echo "================================"
echo ""
echo "下一步："
echo "  1. 编辑 backend/.env，填入你的数据库密码和 DeepSeek API Key"
echo "  2. 确保 MySQL 已运行，并创建数据库:"
echo "     mysql -u root -p -e \"CREATE DATABASE IF NOT EXISTS papercraft DEFAULT CHARACTER SET utf8mb4;\""
echo "  3. 启动后端:  cd backend && uvicorn app.main:app --reload --port 8004"
echo "  4. 启动前端:  cd frontend && npm run dev"
echo ""
echo "  管理员账号将在后端首次启动时自动创建: admin / admin123"
echo ""
