@echo off
chcp 65001 >nul
echo ==============================================
echo   SciAutoFormat - 科研投稿自动化排版助手
echo ==============================================
echo.
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python环境，请先前往 https://www.python.org/ 安装 Python。
    echo [重要] 安装时请务必勾选 "Add Python to PATH"！
    pause
    exit /b
)
echo 正在检查并配置运行环境...
if not exist "venv" (
    echo [初始化] 首次运行，正在为您创建虚拟环境并下载所需依赖（可能需要1-3分钟）...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
    call venv\Scripts\activate.bat
)
if not exist ".env" (
    copy .env.example .env >nul
    echo.
    echo [提示] 尚未检测到API密钥配置。
    echo 已为您生成 .env 文件，请用记事本打开并填入您的 OPENAI_API_KEY。
    echo ^(如果仅使用基础排版功能，不查阅大模型润色，可直接按任意键跳过^)
    pause
)
echo.
echo 正在启动服务，请勿关闭本窗口...
start http://127.0.0.1:8000
python -m uvicorn main:app --host 0.0.0.0 --port 8000
pause
