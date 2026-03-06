import io
readme_content = """# SciAutoFormat (科研投稿自动化排版与辅助工具 / AI Journal Submission Assistant)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

🇨🇳 **SciAutoFormat** 是一款专为科研人员打造的本地化/云端可部署的论文排版与辅助提交平台。它旨在通过一套轻量级的 Web 用户界面与大语言模型 (LLM) 的结合，将科研人员从繁琐的“排版、拆分文件、逐段修缮润色”等缺乏科研价值的机械劳动中解放出来。

🇬🇧 **SciAutoFormat** is a locally/cloud-deployable formatting and submission assistant designed specifically for academic researchers. By combining a lightweight Web UI with Large Language Models (LLMs), it aims to free researchers from the tedious, low-value mechanical labor of "formatting, file splitting, and paragraph-by-paragraph polishing."

---

## 🌟 核心功能 / Core Features

**1. 期刊规则解析网络 / Journal Guidelines Parser**
- 🇨🇳 输入目标期刊的《作者指南》(Author Guidelines) 链接/文本，AI 自动进行要点抽提。
- 🇬🇧 Input the URL or text of the target journal's "Author Guidelines", and the AI will automatically extract key formatting rules.

**2. 智能排版与中英全自动润色 / Smart Formatting & Translation**
- 🇨🇳 直接上传原始中文 Word / Markdown / TXT 稿件，自动调用挂载的大模型翻译为地道学术英文，并在底层使用 python-docx 原生重建文档格式和样式。
- 🇬🇧 Upload your original Word/Markdown/TXT drafts to automatically translate them into authentic academic English. The system natively rebuilds document formats and styles using python-docx.

**3. 多文件拆分与打包转投 / Multi-file Splitting & Bundling**
- 🇨🇳 系统能够对全文的标题、摘要、正文、参考、图注、表格等进行智能切片（Splitter），并按 ScholarOne / Editorial Manager 系统的要求生成相互独立的文档压缩包。
- 🇬🇧 Intelligently split the full text (Title, Abstract, Main Text, References, Figure Captions, Tables) into separate file bundles required by ScholarOne or Editorial Manager submission systems.

**4. 独立表格自动化转换 / Automated Table Conversion**
- 🇨🇳 完美兼容 Markdown |---| 表格格式，直接解析为标准的 Word 三线表（三线、居中对齐）。
- 🇬🇧 Perfectly compatible with Markdown |---| tables, parsing them directly into standard academic Word three-line tables (all centered).

**5. 一键生成与核对 Cover Letter / Cover Letter Generation**
- 🇨🇳 带有关联检测，自动替换所投标红的期刊名和必填声明约束。
- 🇬🇧 Detects relationships, automatically replaces targeted journal names, and smartly appends missing mandatory declarations (e.g., Data Availability, Conflicts of Interest).

---

## 🚀 快速启动 / Quick Start

### 方法 A：Windows 本地一键启动 (推荐个人使用) / Method A: Windows Local 1-Click Start

🇨🇳 项目提供了一个自动化的启动脚本，纯小白也能零配置运行：
🇬🇧 The project provides an automated startup script for zero-configuration execution:

- 🇨🇳 1. 确保已安装 Python，并勾选了 Add Python to PATH。
- 🇬🇧 1. Ensure Python is installed and check Add Python to PATH.
- 🇨🇳 2. 双击运行 start.bat。
- 🇬🇧 2. Double-click to run start.bat.
- 🇨🇳 3. 首次启动会自动创建虚拟环境并在后台下载依赖，随后提示输入 LLM API Key 和访问口令。
- 🇬🇧 3. It will auto-create a virtual environment, install dependencies, and prompt for your LLM API Key & Access Code on the first run.
- 🇨🇳 4. 服务成功启动后，将自动打开浏览器访问：http://127.0.0.1:8000
- 🇬🇧 4. Once started, the browser will auto-open to: http://127.0.0.1:8000

### 方法 B：公网部署 / 服务器运行 (推荐实验室共享) / Method B: Server Deployment

🇨🇳 工具支持部署到实验室的通用服务器或云服务器上，通过网络共享给课题组小伙伴：
🇬🇧 You can also deploy this tool on lab or cloud servers to share with your research group:

\\\ash
git clone https://github.com/chenqz-hub/Journal-Submission-Assistant.git
cd Journal-Submission-Assistant

# 🇨🇳 1. 创建并激活虚拟环境
# 🇬🇧 1. Create and activate virtual environment
python -m venv venv
# Windows: venv\\Scripts\\activate
# Linux/Mac: source venv/bin/activate

# 🇨🇳 2. 安装依赖
# 🇬🇧 2. Install dependencies
pip install -r requirements.txt

# 🇨🇳 3. 配置环境变量 (将模板复制并填入您的 API Key)
# 🇬🇧 3. Configure environment variables (copy template and enter API key)
cp .env.example .env
nano .env

# 🇨🇳 4. 启动服务 (生产环境推荐使用 systemd 或 supervisor)
# 🇬🇧 4. Start the server (systemd or supervisor is recommended for production)
uvicorn main:app --host 0.0.0.0 --port 8000
\\\

---

## 🔐 接口安全防御机制 / Security & Authorization

🇨🇳 为了防止部署到云端后，您的大模型 API Token 被全网抓取或未授权的访问者随意消耗，内置了**访问口令防御（Authorization）**：
🇬🇧 To prevent unauthorized consumption of your LLM API tokens when deployed publicly, a lightweight token defense mechanism is built-in:

- 🇨🇳 通过在 .env 中配置 ACCESS_CODE=您的密码 进行保护。
- 🇬🇧 It is protected by configuring ACCESS_CODE=your_password in .env.
- 🇨🇳 服务启动后，前端页面顶部会出现“🔐 访问口令”输入框，未提供正确密码的 API 调用请求均会被后端拦截并抛出 403 Forbidden。
- 🇬🇧 The frontend includes a "🔐 Access Code" input. API requests without the correct code will be intercepted with a 403 Forbidden error.

---

## 📁 目录结构与架构 / Project Structure

\\\	ext
SciAutoFormat/
├── api/                # 🇨🇳 FastAPI 路由请求及校验中间件  | 🇬🇧 API routes and auth middleware
├── core/               # 🇨🇳 项目全局配置管理模块          | 🇬🇧 Global configurations
├── static/             # 🇨🇳 前端资源(已注入拦截器)        | 🇬🇧 Static assets with fetch wrapper
├── temp/               # 🇨🇳 自动化排版缓存输出路径        | 🇬🇧 Temp cache for document splitting
├── utils/              # 🇨🇳 通用的独立工具函数集合        | 🇬🇧 Utility functions
├── .env.example        # 🇨🇳 环境变量防泄漏模板            | 🇬🇧 Environment variables template
├── main.py             # 🇨🇳 FastAPI App 入口文件          | 🇬🇧 FastAPI entry point
├── requirements.txt    # 🇨🇳 核心依赖清单                  | 🇬🇧 Dependencies list
└── start.bat           # 🇨🇳 Windows 批处理一键启动脚本    | 🇬🇧 Windows startup batch script
\\\

---

## 📄 授权协议 / License

🇨🇳 本项目基于 **MIT License** 开源。欢迎各类前沿交叉学科的同学进行探索、Fork 并拓展为新的生产力工具！如果这个小项目能帮助到你们组顺利发表几篇 Top Journal，将是我们莫大的荣幸！

🇬🇧 This project is licensed under the **MIT License**. We welcome researchers from all disciplines to explore, fork, and expand this tool! If this project helps your group publish a few Top Journals, it will be our greatest honor!
"""

with io.open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme_content)
