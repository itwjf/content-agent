# ContentAgent 部署说明

本文件详细说明如何配置和部署 ContentAgent 项目。

---

## 1. 环境变量配置

### 1.1 后端配置

在 `backend/` 目录下创建 `.env` 文件（从模板复制）：

```bash
# 复制模板
copy .env.example .env
```

然后编辑 `.env` 文件，修改以下配置：

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| `LLM_API_KEY` | **必须** LLM API Key（DeepSeek/OpenAI等） | `sk-xxx` |
| `LLM_BASE_URL` | LLM API 地址 | `https://api.deepseek.com` |
| `LLM_MODEL` | 使用的模型名 | `deepseek-chat` |
| `DEBUG` | 调试模式 | `true` 或 `false` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

**注意：** `.env 文件包含敏感信息，已加入 .gitignore，不会提交到 GitHub**

---

### 1.2 Docker Compose 配置

在 `docker/docker-compose.yml` 中修改：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `MYSQL_ROOT_PASSWORD` | MySQL root 密码 | `root123456` |
| `MYSQL_DATABASE` | 数据库名 | `content_agent` |
| `MYSQL_USER` | 数据库用户 | `content_agent` |
| `MYSQL_PASSWORD` | 数据库密码 | `content123` |
| 环境变量 `LLM_API_KEY` | LLM API Key | `${LLM_API_KEY}` |

**重要：** 生产环境请修改默认密码！

修改方式：
```bash
# 方式1：直接修改 docker-compose.yml 中的值
# 方式2：在启动前设置环境变量
$env:LLM_API_KEY="your_key_here"
docker-compose up -d
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

访问：
- 前端：http://localhost:5173
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/docs

---

## 3. Docker 部署

### 3.1 构建并启动

```bash
cd docker

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 3.2 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:3000 | Nginx 静态服务 |
| 后端 | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger 文档 |
| MySQL | localhost:3306 | 数据库 |
| Qdrant | localhost:6333 | 向量数据库 |

### 3.3 常用命令

```bash
# 重启某个服务
docker-compose restart backend

# 查看容器状态
docker ps

# 进入容器内部
docker exec -it content-agent-backend /bin/bash

# 查看日志
docker-compose logs -f backend
```

---

## 4. 配置清单汇总

| 文件 | 需要修改的配置 | 敏感信息 |
|------|---------------|---------|
| `backend/.env` | LLM_API_KEY | ✅ 是 |
| `docker/docker-compose.yml` | MySQL密码、各服务端口 | ✅ 是 |
| `.env.example` | 无需修改（模板） | ❌ 否 |

---

## 5. 常见问题

**Q: 启动后提示数据库连接失败？**
A: 确保 MySQL 容器已启动：`docker ps` 查看容器状态

**Q: LLM 调用失败？**
A: 检查 `.env` 中的 `LLM_API_KEY` 是否正确

**Q: 前端无法访问后端 API？**
A: 检查 docker-compose.yml 中前端是否正确代理到后端服务

---

## 6. 安全建议

1. **不要** 将包含真实密码的文件提交到 GitHub
2. 生产环境使用**强密码**
3. 定期轮换 API Key
4. 使用 Docker Secrets 或环境变量管理敏感信息
