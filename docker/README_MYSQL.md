# ContentAgent MySQL版本部署指南

## 🚀 快速启动（MySQL版本）

### 1. 环境准备
确保已安装：
- Docker & Docker Compose
- Git

### 2. 配置环境变量
```bash
cd docker
cp .env.docker .env
```

编辑 `.env` 文件，填入必要的配置：
```bash
# LLM 配置（必填）
LLM_API_KEY=your_deepseek_api_key_here

# MySQL 配置（可选，使用默认值即可）
MYSQL_ROOT_PASSWORD=root123456
MYSQL_DATABASE=content_agent
MYSQL_USER=content_agent
MYSQL_PASSWORD=content123
```

### 3. 启动服务
```bash
# 使用MySQL版本的docker-compose文件
docker-compose -f docker-compose-mysql.yml up -d
```

### 4. 验证部署
```bash
# 检查服务状态
docker-compose -f docker-compose-mysql.yml ps

# 测试API
curl http://localhost:8000/health

# 测试商品列表
curl http://localhost:8000/api/v1/products
```

## 📊 服务架构

### 数据存储架构
| 服务 | 端口 | 用途 | 持久化 |
|-----|-----|------|--------|
| MySQL | 3307 | 商品数据、用户数据 | ✅ |
| Qdrant | 6333 | 向量知识库 | ✅ |
| Backend API | 8000 | FastAPI服务 | ❌ |
| Frontend | 3000 | Vue.js前端 | ❌ |

### 数据库表结构
- **products**: 商品信息表
- **users**: 用户信息表（预留）
- **live_sessions**: 直播会话表（预留）
- **prompt_suggestions**: 提词建议记录表（预留）

## 🔧 管理命令

### 数据库管理
```bash
# 进入MySQL容器
docker exec -it content-agent-mysql mysql -ucontent_agent -pcontent123 content_agent

# 查看商品数据
SELECT * FROM products LIMIT 10;

# 重置数据库（谨慎操作）
docker-compose -f docker-compose-mysql.yml down -v
docker-compose -f docker-compose-mysql.yml up -d
```

### 服务管理
```bash
# 停止服务
docker-compose -f docker-compose-mysql.yml down

# 重启服务
docker-compose -f docker-compose-mysql.yml restart

# 查看日志
docker-compose -f docker-compose-mysql.yml logs -f backend
docker-compose -f docker-compose-mysql.yml logs -f mysql
```

## 🎯 功能对比

### MySQL版本 vs 内存版本

| 功能 | MySQL版本 | 内存版本 |
|-----|-----------|----------|
| 数据持久化 | ✅ | ❌ |
| 商品管理 | ✅ 完整CRUD | ✅ 基础CRUD |
| 数据查询 | ✅ 支持复杂查询 | ❌ 简单查询 |
| 并发支持 | ✅ 高并发 | ❌ 单实例 |
| 部署复杂度 | 🔶 中等 | ✅ 简单 |
| 数据量支持 | ✅ 大规模 | ❌ 小规模 |

## 🐛 常见问题

### 1. MySQL连接失败
```bash
# 检查MySQL容器状态
docker logs content-agent-mysql

# 检查网络连接
docker exec content-agent-backend ping mysql
```

### 2. 数据库初始化失败
```bash
# 手动初始化数据库
docker exec content-agent-backend python -m app.services.database_init
```

### 3. 端口冲突
如果3307端口被占用，修改docker-compose-mysql.yml中的端口映射：
```yaml
ports:
  - "3308:3306"  # 改为其他端口
```

## 📈 性能优化建议

1. **MySQL优化**:
   - 添加适当的索引
   - 配置连接池参数
   - 定期备份数据

2. **应用优化**:
   - 启用SQLAlchemy连接池
   - 添加Redis缓存层
   - 实现数据分页查询

3. **监控建议**:
   - 添加数据库性能监控
   - 配置日志收集
   - 设置告警机制

## 🔗 访问地址

- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **MySQL**: localhost:3307
- **Qdrant**: localhost:6333

## 📞 技术支持

如遇到问题，请检查：
1. 环境变量是否正确配置
2. 端口是否被占用
3. Docker服务是否正常运行
4. 查看容器日志获取详细错误信息