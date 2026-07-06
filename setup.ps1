# PaperCraft 一键安装脚本 (Windows PowerShell)
# 右键 -> 使用 PowerShell 运行

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  PaperCraft 依赖安装脚本" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# 检查 Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "[错误] 未检测到 Python，请先安装 Python 3.11+" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Python: $(& python --version)" -ForegroundColor Green

# 检查 Node.js
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Host "[错误] 未检测到 Node.js，请先安装 Node.js 18+" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Node.js: $(& node --version)" -ForegroundColor Green

# 检查 MySQL
$mysql = Get-Command mysql -ErrorAction SilentlyContinue
if ($mysql) {
    Write-Host "[OK] 已检测到 MySQL CLI" -ForegroundColor Green
} else {
    Write-Host "[警告] 未检测到 MySQL CLI，请确保 MySQL 服务已安装并运行" -ForegroundColor Yellow
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "`n>>> 安装后端依赖..." -ForegroundColor Yellow
Set-Location "$root\backend"

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "[提示] 已从 .env.example 创建 .env 文件，请修改其中的数据库密码和 API Key" -ForegroundColor Yellow
}

pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 后端依赖安装失败" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] 后端依赖安装完成" -ForegroundColor Green

Write-Host "`n>>> 安装前端依赖..." -ForegroundColor Yellow
Set-Location "$root\frontend"
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 前端依赖安装失败" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] 前端依赖安装完成" -ForegroundColor Green

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "  安装完成!" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host @"

下一步：
  1. 编辑 backend\.env，填入你的数据库密码和 DeepSeek API Key
  2. 确保 MySQL 已运行，并创建数据库:
     mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS papercraft DEFAULT CHARACTER SET utf8mb4;"
  3. 启动后端:  cd backend; uvicorn app.main:app --reload --port 8004
  4. 启动前端:  cd frontend; npm run dev

  管理员账号将在后端首次启动时自动创建: admin / admin123

"@
