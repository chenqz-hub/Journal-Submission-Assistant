# SciAutoFormat (科研投稿自动化排版与辅助工具)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

SciAutoFormat 是一款专为科研人员打造的本地化/云端可部署的论文排版与辅助提交平台。它旨在通过一套轻量级的 Web 用户界面与大语言模型 (LLM) 的结合，将科研人员从繁琐的“排版、拆分文件、逐段修缮润色”等缺乏科研价值的机械劳动中解放出来。

## 🌟 核心功能

1. **期刊规则解析网络**：输入目标期刊的《作者指南》(Author Guidelines) 链接/文本，AI 自动进行要点抽提。
2. **智能排版与中英全自动润色**：直接上传原始中文 Word / Markdown / TXT 稿件，自动调用挂载的大模型翻译为地道学术英文，并在底层使用 `python-docx` 原生重建文档格式和样式。
3. **多文件拆分与打包转投**：系统能够对全文的标题、摘要、正文、参考、图注、表格等进行智能切片（Splitter），并按 ScholarOne / Editorial Manager 系统的要求生成相互独立的文档压缩包。
4. **独立表格自动化转换**：完美兼容 Markdown `|---|` 表格格式，直接解析为标准的 Word 三线表（三线、居中对齐）。
5. **一键生成与核对 Cover Letter**：带有关联检测，自动替换所投标红的期刊名和必填声明约束。

## 🚀 快速启动

### 方法 A：Windows 本地一键启动 (推荐个人使用)
项目提供了一个自动化的启动脚本，纯小白也能零配置运行：
1. 确保已安装 Python，并勾选了 `Add Python to PATH`。
2. 双击运行 `start.bat`。
3. 首次启动会自动创建虚拟环境并在后台下载依赖，随后提示输入 LLM API Key 和访问口令。
4. 服务成功启动后，将自动打开浏览器访问：`http://127.0.0.1:8000`。

### 方法 B：公网部署 / 服务器运行 (推荐实验室共享)
工具支持部署到实验室的通用服务器或云服务器上，通过网络共享给课题组的小伙伴：

```bash
git clone https://github.com/your_username/SciAutoFormat.git
cd SciAutoFormat

# 1. 创建并激活虚拟环境
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入您的 LLM API_KEY 及 访问口令 (ACCESS_CODE)
nano .env

# 4. 启动服务 (生产环境推荐使用 systemd 或 supervisor 守护进程)
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🔐 接口安全防御机制

为了防止部署到云端后，您的大模型 API Token 被全网抓取或未授权的访问者随意消耗，内置了**访问口令防御（Authorization）**：
- 通过在 `.env` 中配置 `ACCESS_CODE=您的密码` 进行保护。
- 服务启动后，前端页面顶部会出现“🔐 访问口令”输入框，未提供正确密码的 API 调用请求均会被后端拦截并抛出 `403 Forbidden`。
- 全局使用依赖注入结构：保护了 `/api/v1/*` 所有的关键路径，实现轻量却绝对安全。

## 📁 目录结构与架构

```text
SciAutoFormat/
├── api/                # FastAPI 路由请求及校验中间件 (auth.py)
├── core/               # 项目全局配置管理模块
├── static/             # 纯原生 HTML/JS/CSS，已注入全局 Auth fetch 拦截器
├── temp/               # 自动化文件分片缓存/排版输出路径 (已添加入 .gitignore)
├── utils/              # 通用的独立工具函数集合 (例如文件读写)
├── .env.example        # 敏感信息及环境变量防泄漏模板
├── main.py             # FastAPI App 入口文件 (含跨域及依赖装载)
├── requirements.txt    # 核心依赖清单，保证版本可重现性
└── start.bat           # Windows 批处理流程（自动装载 venv）
```

## 📄 授权协议

本项目基于 **MIT License** 开源。
欢迎各类前沿交叉学科的同学进行探索、Fork 并拓展为新的生产力工具！如果这个小项目能帮助到你们组顺利发表几篇 Top Journal，将是我们莫大的荣幸！
