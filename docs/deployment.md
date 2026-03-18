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
