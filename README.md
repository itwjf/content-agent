# ContentAgent - 智能直播辅助 AI Agent 系统

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Vue](https://img.shields.io/badge/Vue-3.x-brightgreen.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.1xx-orange.svg)
![Docker](https://img.shields.io/badge/Docker-20.10+-important.svg)

## 项目简介

ContentAgent 是一款基于 AI 大模型及 Agent 架构的智能直播辅助系统，专为直播电商场景设计。系统实时接收多模态输入（弹幕、直播阶段、后台指标数据），通过多模块 Agent 协同推理，生成实时、可执行、合规的提词建议，并支持 TTS 语音合成与 2D 数字人形象驱动，构成完整的 **AI 直播辅助闭环**：

```
弹幕接入（多平台） → LLM 互动理解 → 导演脚本 → 合规闸门 → TTS/数字人 → 监场台展示
       ↑                                                              │
       └──────────── 实时指标回流 → 策略引擎动态调权 ←──────────────────┘
```

## 功能特点

### 数据接入
- **多平台弹幕接入网关**：统一消息模型适配多来源——官方开放平台 API（资质就绪后对接）、浏览器端采集（兜底方案，含风控提示）、模拟弹幕源（场景化回放：高频提问/负面刷屏/购买意向）
- **WebSocket 实时通道**：弹幕/决策/指标/阶段/策略调整实时推送，断线自动重连 + `last_event_id` 增量补拉

### 智能决策
- **实时互动理解**：LLM 批量语义分析弹幕（意图/情绪/高频问题聚合），超时/失败自动降级到关键词规则方案
- **导演脚本引擎**：融合剧本阶段规划 + 商品信息 + 互动理解结果，产出面向数字人的结构化脚本（台词/情绪/动作/节奏/商品卡指令），支持 LLM 与规则双模式
- **智能卖点拆解**：商品参数转化为利益点，匹配用户问题生成针对性话术
- **合规约束保障**：内置违禁词库（100+），决策前置修正 + 播出前硬闸门双重防线

### 展示与策略
- **TTS + 2D 数字人**：CosyVoice/商用 API 可配置语音合成；MuseTalk/LivePortrait 口型驱动；无 GPU 自动降级为"语音 + 字幕"形态，支持"AI 生成内容"标识
- **实时策略引擎**：滑动窗口计算人气/弹幕速率/负面占比/转化指标，5 条可配置规则动态调整决策权重，调整过程全程留痕可审计
- **监场台**：弹幕流、导演脚本、阶段进度、指标曲线、策略权重可视化；支持人工接管（暂停自动决策 + 手动话术下发）

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | Vue 3 + Element Plus + Pinia + Vite | Vue 3.3.4+ |
| 后端 | Python + FastAPI + SQLAlchemy + Pydantic v2 | Python 3.11+ |
| 数据库 | MySQL | 8.0+ |
| 向量数据库 | Qdrant | 1.5.0+ |
| 实时通信 | WebSocket | - |
| 部署 | Docker Compose | 2.18+ |

## 系统架构

```
┌──────────────────────────────────────────────────────────────┐
│                    前端 Vue 3                                  │
│     监场台（弹幕流/导演脚本/指标曲线/人工接管）+ 提词 Demo        │
└──────────────┬───────────────────────────┬───────────────────┘
               │ REST                      │ WebSocket（实时推送）
┌──────────────▼───────────────────────────▼───────────────────┐
│                     FastAPI 后端                               │
│                                                              │
│  ┌─────────────┐   ┌──────────────────────────────────────┐  │
│  │ 接入网关     │   │           决策调度器（场次级）          │  │
│  │ 官方API/浏览器│──▶│  弹幕滑动窗口 → LLM互动理解（规则降级） │  │
│  │ /模拟源      │   │       → 导演脚本引擎（LLM/规则）       │  │
│  └─────────────┘   │       → 合规检查修正 → 决策落库        │  │
│                    └──────────────┬───────────────────────┘  │
│  ┌─────────────┐                 │                           │
│  │ 策略引擎     │◀── 实时指标 ────┤                           │
│  │ 滑动窗口+调权 │                 ▼                           │
│  └─────────────┘   ┌──────────────────────────────────────┐  │
│  ┌─────────────┐   │           展示适配层                   │  │
│  │ Agent 模块   │   │  合规硬闸门 → TTS → 字幕/动作指令包     │  │
│  │ 卖点/结构/融合│   │  → （可选）2D 数字人口型驱动           │  │
│  └─────────────┘   └──────────────────────────────────────┘  │
│                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌────────────────────┐  │
│  │ WebSocket Hub│  │ 人工控制     │   │   场次域 CRUD      │  │
│  └─────────────┘   └─────────────┘   └────────────────────┘  │
└──────┬──────────────────┬───────────────────────┬────────────┘
       │                  │                       │
┌──────▼──────┐    ┌──────▼──────┐        ┌───────▼────────┐
│  MySQL 8.0  │    │   Qdrant    │        │    LLM API     │
│ 商品库/场次/ │    │  语义检索    │        │  (大模型调用)   │
│ 决策/指标/策略│    └─────────────┘        └────────────────┘
└─────────────┘
```

## 核心模块

| 模块 | 职责 | 代码位置 |
|------|------|----------|
| 接入网关 | 多平台弹幕归一化接入（官方 API 占位/浏览器采集/模拟源），适配器可热切换 | `backend/app/services/gateway/` |
| WebSocket Hub | 统一事件信封推送、增量补拉、有界历史缓冲 | `backend/app/services/ws_hub.py` |
| 互动理解 | LLM 弹幕语义分析（意图/情绪/高频问题），超时/失败降级规则方案 | `backend/app/services/agent/` |
| 导演引擎 | 融合剧本+商品+互动结果产出导演脚本；消费策略权重 | `backend/app/services/director/` |
| 决策调度器 | 场次级弹幕滑动窗口，驱动"理解→脚本→合规→落库→推送→展示"全链路 | `backend/app/services/director/scheduler.py` |
| 展示适配 | 合规硬闸门 → TTS（CosyVoice/商用 API/mock）→ 字幕/动作包 → 2D 数字人（MuseTalk/LivePortrait，可降级） | `backend/app/services/showcase/` |
| 策略引擎 | 滑动窗口指标计算 + 可配置规则动态调权 + 调整记录留痕 | `backend/app/services/strategy/` |
| Agent 功能模块 | 卖点拆解、内容结构（阶段规划）、决策融合、合规约束 | `backend/app/services/modules/` |
| 监场台前端 | 实时可视化 + 人工接管控制 | `frontend/src/views/Monitor.vue` |

## 项目结构

```
content-agent/
├── backend/                        # Python FastAPI 后端
│   ├── app/
│   │   ├── api/                    # API 路由层
│   │   │   ├── v1/                 #   Agent / 商品 / 场次路由
│   │   │   ├── gateway_admin.py    #   接入网关管理
│   │   │   ├── browser_collect.py  #   浏览器采集回传
│   │   │   ├── strategy_api.py     #   指标注入与策略查询
│   │   │   ├── live_control.py     #   监场台人工控制
│   │   │   ├── showcase.py         #   TTS 展示适配
│   │   │   ├── ws_live.py          #   WebSocket 实时通道
│   │   │   └── ...
│   │   ├── core/                   # 核心配置（config、db、llm）
│   │   ├── models/                 # 数据库模型（商品/场次/弹幕/决策/指标/策略）
│   │   ├── schemas/                # Pydantic 数据模型
│   │   ├── services/
│   │   │   ├── agent/              # Agent 决策中枢（互动理解等）
│   │   │   ├── modules/            # 功能模块（卖点/结构/合规/融合）
│   │   │   ├── gateway/            # 平台接入网关（适配器/浏览器采集脚本）
│   │   │   ├── director/           # 导演脚本引擎 + 决策调度器
│   │   │   ├── showcase/           # TTS / 数字人形象驱动
│   │   │   ├── strategy/           # 策略引擎 / 指标采集
│   │   │   └── ws_hub.py           # WebSocket 推送枢纽
│   │   ├── main.py                 # 入口（内存版，演示用）
│   │   └── main_mysql.py           # 入口（MySQL 版，部署用）
│   ├── sql/                        # 建表脚本（需手动执行）
│   │   ├── 01_*.sql                #   商品库等基础表
│   │   ├── 02_live_tables.sql      #   场次/弹幕/决策/指标四张表
│   │   └── 03_strategy_tables.sql  #   策略调整记录表
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                       # Vue 3 前端
│   ├── src/
│   │   ├── api/                    # 接口请求封装
│   │   ├── composables/            # useLiveSocket（WS 客户端）
│   │   ├── components/             # 公共组件（Sparkline 指标曲线等）
│   │   ├── views/                  # 页面（Monitor 监场台 / Home / Products）
│   │   ├── store/                  # Pinia 状态管理
│   │   └── router/                 # 路由配置
│   ├── package.json
│   └── Dockerfile
├── docker/                         # Docker 配置
│   ├── docker-compose.yml
│   └── backend.env.example
├── docs/                           # 文档目录
│   ├── architecture.md             # 架构设计文档
│   ├── api.md                      # API 文档
│   ├── deployment.md               # 部署说明
│   └── platform-access.md          # 平台弹幕接入说明（官方渠道/浏览器采集风险提示）
└── README.md
```

## 快速开始指南

### 0. 环境要求

- Python >= 3.11 / Node.js >= 18
- Docker >= 20.10，Docker Compose >= 2.18
- MySQL 8.0（本地或 Docker）

### 1. 克隆项目

```bash
git clone git@github.com:itwjf/content-agent.git
cd content-agent
```

### 2. 初始化数据库（手动建表）

```bash
mysql -u <user> -p <库名> < backend/sql/01_*.sql        # 商品库等基础表
mysql -u <user> -p <库名> < backend/sql/02_live_tables.sql   # 场次/弹幕/决策/指标
mysql -u <user> -p <库名> < backend/sql/03_strategy_tables.sql  # 策略调整记录
```

### 3. 配置环境变量

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`，关键配置：

| 配置项 | 必填 | 说明 |
|--------|------|------|
| `LLM_API_KEY` | ✅ | 大模型 API 密钥（后端启动强依赖） |
| `DATABASE_URL` | ✅ | MySQL 连接串，如 `mysql+pymysql://user:pass@localhost:3306/dbname` |
| `SILICONFLOW_API_KEY` | 可选 | RAG 向量生成 |
| `TTS_PROVIDER` / `AVATAR_*` | 可选 | TTS 与数字人（默认 mock 静音 / 纯声音形态） |
| `BROWSER_ADAPTER_ENABLED` / `BROWSER_COLLECT_TOKEN` | 可选 | 浏览器采集（见 `docs/platform-access.md`） |
| `STRATEGY_*` | 可选 | 策略引擎阈值（均有默认值） |

### 4. 启动服务

#### 方式一：Docker Compose（推荐）

```bash
cd docker
docker-compose up -d     # 首次启动会构建镜像，需要几分钟
docker-compose ps
```

#### 方式二：本地开发

```bash
# 后端（MySQL 版，含直播闭环全部功能）
cd backend
pip install -r requirements.txt
python -m uvicorn app.main_mysql:app --reload

# 前端（新终端）
cd frontend
npm install
npm run dev
```

> 注：`app/main.py` 为内存版演示入口（不含 MySQL 持久化），完整功能请使用 `app.main_mysql:app`。

### 5. 访问服务

| 服务 | Docker 部署 | 本地开发 | 说明 |
|------|------------|---------|------|
| 前端 | http://localhost:3000 | http://localhost:5173 | 监场台路径 `/monitor` |
| 后端 API | http://localhost:8000 | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | http://localhost:8000/docs | Swagger 交互式文档 |

### 6. 体验直播闭环（监场台）

1. 打开监场台 → 新建场次 → 开始直播
2. 选择「模拟弹幕源」→ 启动弹幕源，观察弹幕流与自动决策产出
3. 查看 TTS 字幕（可点播放），注入人气/转化指标观察策略权重变化
4. 打开「人工接管」→ 下发手动话术（自动过合规检查）

## 配置清单

| 文件 | 用途 | 是否提交到 GitHub |
|------|------|------------------|
| `backend/.env` | 本地运行配置（包含 API Key）| ❌ 否（已加入 .gitignore）|
| `backend/.env.example` | 配置模板（GitHub 安全版）| ✅ 是 |
| `docker/backend.env` | Docker 部署配置（包含 API Key）| ❌ 否 |
| `docker/backend.env.example` | Docker 配置模板 | ✅ 是 |
| `docker/docker-compose.yml` | Docker 编排配置 | ✅ 是 |

## 核心 API

### 直播闭环

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/v1/live/sessions` | 创建直播场次 |
| POST | `/api/v1/live/sessions/{id}/start` | 场次开始直播 |
| POST | `/api/v1/gateway/sessions/{id}/start` | 启动弹幕源（mock/browser）与决策循环 |
| WS | `/ws/live/{session_id}?last_event_id=` | 实时推送 danmaku/decision/metric/stage/strategy/presentation/alert |
| POST | `/api/v1/live/sessions/{id}/metrics` | 注入实时指标（人气/转化等） |
| GET | `/api/v1/live/sessions/{id}/strategy/weights` | 查询当前决策权重 |
| GET | `/api/v1/live/sessions/{id}/strategy/adjustments` | 策略调整历史（原因+前后权重快照） |
| POST | `/api/v1/live/sessions/{id}/takeover` | 人工接管（暂停自动决策） |
| POST | `/api/v1/live/sessions/{id}/restore` | 恢复自动决策 |
| POST | `/api/v1/live/sessions/{id}/manual-script` | 手动下发话术（过合规检查→TTS） |
| GET | `/api/v1/live/sessions/{id}/replay/danmaku` | 弹幕回放（断线补拉） |

### 基础功能

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/v1/agent/decide` | Agent 核心决策（兼容保留） |
| POST | `/api/v1/products` | 商品信息管理 |
| POST | `/api/v1/compliance/check` | 文本合规检查 |
| POST | `/api/v1/rag/search` | 语义搜索知识库 |
| POST | `/api/v1/showcase/preview` | TTS 展示链路独立预览 |
| GET | `/api/v1/gateway/browser/collector.js` | 下发浏览器采集脚本 |

> 完整接口见 `http://localhost:8000/docs` 与 [docs/api.md](docs/api.md)。

## 弹幕来源接入说明

三种接入方式对比、官方渠道资质要求、浏览器采集的**风控与条款风险提示**，详见 [docs/platform-access.md](docs/platform-access.md)。

> ⚠️ 浏览器端采集未经平台官方授权，仅限学习研究用途；正式商用请申请官方 API 接入。

## 技术文档

- [架构设计文档](docs/architecture.md)：系统架构和模块说明
- [API 文档](docs/api.md)：完整 API 接口说明和示例
- [部署文档](docs/deployment.md)：详细部署步骤和配置说明
- [平台接入说明](docs/platform-access.md)：弹幕来源接入与风险提示

## 注意事项

1. **API 密钥安全**：`.env` 文件包含敏感信息，请勿提交到 GitHub
2. **环境要求**：确保 Docker 版本 >= 20.10，Docker Compose 版本 >= 2.18
3. **资源配置**：建议服务器至少 4GB 内存，以支持所有服务正常运行
4. **建表方式**：项目不自动建表，`backend/sql/` 下脚本需按上文手动执行
5. **合规底线**：所有生成话术必须经过内置合规模块（广告法违禁词库 100+），任何场景不可绕过

## 故障排查

- **后端启动报 `LLM_API_KEY` 校验失败**：未创建/未填写 `backend/.env`
- **本机启动报 `No module named 'fitz'`**：本机 Python 环境缺少依赖，执行 `pip install pymupdf python-docx`（PyMuPDF 在部分新版本 Python 无预编译 wheel，建议 Python 3.11 或 Docker 部署）
- **决策不产出**：确认场次状态为 `liveing`、弹幕源已启动、商品库非空（未绑定商品时取第一个兜底）
- **WebSocket 连不上**：确认使用 `/ws/live/{session_id}` 且场次存在；`4404` 表示场次不存在
- **服务启动失败**：检查 `LLM_API_KEY` 是否正确设置，查看日志：`docker-compose logs backend`
- **前端无法连接后端**：确认后端服务正常运行、代理配置正确
- **Qdrant 搜索失败**：检查 Qdrant 服务状态：`docker-compose ps qdrant`（未启动时 RAG 自动降级内存存储）
- **数据库连接失败**：检查 MySQL 服务状态和 `DATABASE_URL` 连接字符串配置

## 版权声明

Copyright © 2025 itwjf. All Rights Reserved.

本项目**未采用任何开源许可证**，默认保留所有权利：

- 未经作者书面授权，任何人不得复制、修改、分发、二次开发或商用本项目的全部或部分代码
- 查看源码仅限于学习交流目的
- 如需授权使用，请联系作者
