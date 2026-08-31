# CLAUDE.md

本文件在每次对话开始时自动加载，为 LLM 提供项目上下文与行为约束。

## 项目简介

ContentAgent — 智能直播辅助 AI Agent 系统，面向直播电商场景。实时接收多模态输入（弹幕、直播阶段、后台数据），通过多模块 Agent 协同推理，生成实时、可执行、合规的提词建议。

本项目基于根目录下的 `ContentAgent面试题.md` 自研开发。该文档只是首次开发的思路点拨（原始需求），**并非项目的最终目标**，实际功能已在其基础上扩展（MySQL 商品库、Qdrant RAG 知识库、Docker 一键部署等），后续开发不必受限于该文档。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3、Element Plus、Pinia、Vue Router、Axios、Vite（Node.js >= 18） |
| 后端 | Python 3.11、FastAPI、SQLAlchemy、Pydantic v2、OpenAI SDK |
| 数据库 | MySQL 8.0（商品库/日志） |
| 向量库 | Qdrant 1.5.0+（RAG 语义检索） |
| 部署 | Docker >= 20.10、Docker Compose >= 2.18 |

## 环境说明

- **后端环境**：Python 3.11+，依赖见 `backend/requirements.txt`（已锁定版本，勿随意升级）
- **前端环境**：Node.js（支持 Vite 6），依赖见 `frontend/package.json`
- **环境变量**：后端配置通过 `backend/.env` 提供（模板见 `backend/.env.example`），含 `LLM_API_KEY`、`SILICONFLOW_API_KEY` 等；Docker 部署配置见 `docker/backend.env`（模板见 `docker/backend.env.example`）
- **服务端口**：前端 3000，后端 8000
- 项目结构、启动方式、部署步骤详见根目录 `README.md`，此处不再重复

## LLM 行为约束（必须遵守）

### 可以做

- 阅读、理解、修改 `backend/` 与 `frontend/` 中的代码
- 编写或修改 API 路由、服务层、数据模型、前端页面与组件
- 更新 `docs/` 下的文档，以及与本功能直接相关的 README 内容
- 运行本地命令进行调试、测试、验证（启动服务、安装依赖等）
- 修复 bug、重构代码时保持现有架构风格（分层：路由 → 服务 → 模型）

### 不可以做

- **严禁将 `.env`、`docker/backend.env` 等任何包含密钥/敏感信息的文件提交或推送到远程仓库**（`.gitignore` 已配置，不得移除相关规则）
- 不得在代码、注释、日志中硬编码 API Key、密码等敏感信息，一律通过环境变量读取
- 不得修改或绕过安全相关配置（违禁词库、合规过滤逻辑）除非任务明确要求
- 不得擅自删除或覆盖数据库初始化脚本（`docker/mysql-init/`）与已有迁移逻辑
- 未经用户确认，不得执行破坏性 git 操作（force push、reset --hard、删除分支等）
- 不得引入与现有技术栈冲突的重型依赖；新依赖需先向用户说明理由

## 注意事项

- 后端有两个入口：`app/main.py`（内存版，演示用）与 `app/main_mysql.py`（MySQL 版，部署用），修改时注意区分
- 合规模块内置广告法违禁词库（100+），任何生成话术输出前必须经过合规检查
- LLM 相关配置通过 `backend/.env` 提供（参考 `.env.example`）
