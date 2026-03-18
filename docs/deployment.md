# ContentAgent 部署说明

本文件详细说明如何配置和部署 ContentAgent 项目。

---

## 1. 环境变量配置

### 1.1 本地开发配置

在 `backend/` 目录下创建 `.env` 文件（从模板复制）：

```bash
# 复制模板
copy backend\.env.example backend\.env
```

然后编辑 `backend/.env` 文件，修改以下配置：

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| `LLM_API_KEY` | **必须** LLM API Key（DeepSeek/OpenAI等） | `sk-xxx` |
| `LLM_BASE_URL` | LLM API 地址 | `https://api.deepseek.com` |
| `LLM_MODEL` | 使用的模型名 | `deepseek-chat` |
| `DEBUG` | 调试模式 | `true` 或 `false` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

### 1.2 Docker 部署配置

在 `docker/` 目录下编辑 `backend.env` 文件：

```bash
# 编辑 Docker 后端配置
notepad docker\backend.env
```

填入你的 API Key：
```
LLM_API_KEY=your_actual_api_key_here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
DEBUG=false
LOG_LEVEL=INFO
```

---

## 2. 本地开发配置

### 2.1 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 2.2 启动服务

```bash
# 后端（终端1）
cd backend
python -m uvicorn app.main:app --reload

# 前端（终端2）
cd frontend
npm run dev
```

### 2.3 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:5173 | Vue 开发服务器 |
| 后端 | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger 文档 |

---

## 3. Docker 部署

### 3.1 快速启动

```bash
# 1. 进入 Docker 配置目录
cd D:\Documents\project\content-agent\docker

# 2. 编辑 backend.env，填入你的 API Key
notepad backend.env

# 3. 启动所有服务（首次启动会构建镜像，需要几分钟）
docker-compose up -d

# 4. 查看服务状态
docker-compose ps
```

### 3.2 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:3000 | Nginx 静态服务 |
| 后端 | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger 文档 |
| MySQL | localhost:3306 | 数据库（可选） |
| Qdrant | localhost:6333 | 向量数据库（可选） |

### 3.3 常用命令

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启某个服务
docker-compose restart backend

# 查看容器状态
docker ps

# 进入容器内部（调试用）
docker exec -it content-agent-backend /bin/bash

# 重新构建镜像
docker-compose build --no-cache
```

---

## 4. 配置文件说明

| 文件 | 用途 | 是否提交到 GitHub |
|------|------|------------------|
| `backend/.env` | 本地运行配置 | ❌ 否（已加入 .gitignore） |
| `backend/.env.example` | 本地配置模板 | ✅ 是 |
| `docker/backend.env` | Docker 后端配置 | ❌ 否 |
| `docker/docker-compose.yml` | Docker 编排配置 | ✅ 是 |
| `.env.docker` | Docker 环境变量模板 | ✅ 是 |

---

## 5. 自定义配置

### 5.1 修改端口

编辑 `docker/docker-compose.yml` 或设置环境变量：

```bash
# 修改前端端口为 8080
set FRONTEND_PORT=8080
docker-compose up -d

# 或直接修改 docker-compose.yml 中的端口映射
```

### 5.2 修改 MySQL 密码

```bash
# 方式1：环境变量
set MYSQL_PASSWORD=your_new_password
docker-compose up -d

# 方式2：直接编辑 docker-compose.yml
```

---

## 6. 常见问题

**Q: 启动后提示数据库连接失败？**
A: 确保 MySQL 容器已启动：`docker ps` 查看容器状态

**Q: LLM 调用失败？**
A: 检查 `docker/backend.env` 中的 `LLM_API_KEY` 是否正确

**Q: 前端无法访问后端 API？**
A: 检查 nginx.conf 中是否正确代理到后端服务

**Q: 容器启动失败？**
A: 查看日志排查：`docker-compose logs backend`

---

## 7. 安全建议

1. **不要** 将包含真实密码的文件提交到 GitHub
2. 生产环境使用**强密码**
3. 定期轮换 API Key
4. 使用 Docker Secrets 管理敏感信息
5. 生产环境建议配置 HTTPS

## 8. 依赖清单

### 8.1 后端依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| fastapi | ^0.104.1 | Web框架 |
| uvicorn[standard] | ^0.24.0 | ASGI服务器 |
| pydantic | ^2.5.0 | 数据验证 |
| pydantic-settings | ^2.1.0 | 配置管理 |
| qdrant-client | ^1.7.4 | 向量数据库客户端 |
| mysql-connector-python | ^8.2.0 | MySQL驱动 |
| transformers | ^4.35.0 | 文本处理 |
| sentence-transformers | ^2.2.2 | 文本向量化 |
| requests | ^2.31.0 | HTTP客户端 |
| python-dotenv | ^1.0.0 | 环境变量管理 |
| loguru | ^0.7.2 | 日志管理 |

### 8.2 前端依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| vue | ^3.3.4 | 前端框架 |
| element-plus | ^2.3.12 | UI组件库 |
| axios | ^1.6.0 | HTTP客户端 |
| pinia | ^2.1.7 | 状态管理 |
| vue-router | ^4.2.5 | 路由管理 |

## 9. 环境配置详细说明

### 9.1 后端环境变量

| 环境变量 | 类型 | 默认值 | 说明 |
|---------|------|--------|------|
| `LLM_API_KEY` | 字符串 | - | LLM API密钥（必填） |
| `LLM_BASE_URL` | 字符串 | `https://api.deepseek.com` | LLM API地址 |
| `LLM_MODEL` | 字符串 | `deepseek-chat` | 使用的模型名称 |
| `DEBUG` | 布尔值 | `false` | 调试模式 |
| `LOG_LEVEL` | 字符串 | `INFO` | 日志级别 |
| `DATABASE_URL` | 字符串 | `mysql://root:password@localhost:3306/content_agent` | 数据库连接字符串 |
| `QDRANT_URL` | 字符串 | `http://localhost:6333` | Qdrant向量数据库地址 |
| `QDRANT_API_KEY` | 字符串 | - | Qdrant API密钥（如启用） |
| `SECRET_KEY` | 字符串 | - | 应用密钥 |

### 9.2 前端环境变量

| 环境变量 | 类型 | 默认值 | 说明 |
|---------|------|--------|------|
| `VITE_API_BASE_URL` | 字符串 | `http://localhost:8000/api/v1` | 后端API基础地址 |
| `VITE_APP_TITLE` | 字符串 | `ContentAgent` | 应用标题 |
| `VITE_DEBUG` | 布尔值 | `false` | 调试模式 |

## 10. 开发与生产环境差异

| 配置项 | 开发环境 | 生产环境 |
|--------|---------|----------|
| `DEBUG` | `true` | `false` |
| `LOG_LEVEL` | `DEBUG` | `INFO` |
| `前端服务` | Vite开发服务器 | Nginx静态服务 |
| `后端服务` | 热重载模式 | 生产模式 |
| `数据库` | 本地或Docker容器 | 独立数据库服务 |
| `Qdrant` | 本地或Docker容器 | 独立向量数据库服务 |

## 11. 监控与维护

### 11.1 日志管理

- **后端日志**：存储在 `backend/logs/` 目录
- **Docker日志**：使用 `docker-compose logs` 查看
- **前端日志**：浏览器控制台和Nginx日志

### 11.2 常见问题排查

**Q: 后端服务启动失败？**
A: 检查 `LLM_API_KEY` 是否正确设置，查看日志：`docker-compose logs backend`

**Q: 前端无法连接后端？**
A: 检查 `VITE_API_BASE_URL` 配置，确保后端服务正常运行

**Q: Qdrant搜索失败？**
A: 检查 Qdrant 服务状态：`docker-compose ps qdrant`，查看日志：`docker-compose logs qdrant`

**Q: 数据库连接失败？**
A: 检查 MySQL 服务状态和连接字符串配置

### 11.3 性能监控

- 使用 FastAPI 内置的 `/metrics` 端点监控服务性能
- 配置 Prometheus 和 Grafana 进行更详细的监控
- 定期检查 Qdrant 向量库大小和查询性能
