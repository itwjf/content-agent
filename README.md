# ContentAgent - 智能直播辅助 AI Agent 系统

## 项目简介

基于 AI 大模型及 Agent 架构的智能直播辅助系统，能够实时接收多模态输入（弹幕、直播阶段、后台数据），通过多模块协同推理，生成精准、实时、可执行的提词建议，辅助主播进行结构化、高转化且合规的直播。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Element Plus + Vite |
| 后端 | Python 3.11 + FastAPI |
| 数据库 | MySQL 8.0 |
| 向量数据库 | Qdrant |
| 部署 | Docker Compose |

## 项目结构

```
content-agent/
├── backend/                    # Python FastAPI 后端
│   ├── app/
│   │   ├── api/v1/             # API 路由层
│   │   ├── core/               # 核心配置（config、db、llm）
│   │   ├── models/             # 数据库模型
│   │   ├── schemas/            # Pydantic 数据模型
│   │   ├── services/
│   │   │   ├── agent/          # Agent 决策中枢
│   │   │   └── modules/        # 各功能模块
│   │   └── utils/              # 工具函数
│   ├── tests/                  # 单元测试
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── api/                # 接口请求
│   │   ├── components/         # 公共组件
│   │   ├── views/              # 页面视图
│   │   ├── store/              # Pinia 状态管理
│   │   └── router/             # 路由配置
│   ├── package.json
│   └── Dockerfile
├── docker/                     # Docker 配置
│   └── docker-compose.yml
├── docs/                       # 文档目录
│   ├── architecture.md         # 架构设计文档
│   ├── api.md                  # API 文档
│   └── deployment.md           # 部署说明
├── scripts/                    # 脚本工具
├── DEV_LOG.md                  # 开发日志
└── README.md                   # 项目说明
```

## 核心模块

| 模块 | 职责 |
|------|------|
| 互动理解模块 | 实时弹幕语义分析，识别用户意图、高频问题、情绪 |
| 卖点拆解模块 | 商品参数转化为利益点，匹配用户问题生成话术 |
| 合规约束模块 | 内置违禁词库（100+），实时过滤并提供替代方案 |
| 内容结构引擎 | 管理直播阶段划分，实时提示当前阶段 |
| 决策融合模块 | 多源输入优先级打分，生成最终提词指令 |

## 快速启动

详见 [部署说明](docs/deployment.md)

```bash
# 1. 克隆项目
git clone git@github.com:itwjf/content-agent.git
cd content-agent

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 .env 填入 API Key 等配置

# 3. 启动所有服务
cd docker
docker-compose up -d

# 4. 访问
# 前端: http://localhost:3000
# 后端 API: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

## 开发进度

详见 [开发日志](DEV_LOG.md)
