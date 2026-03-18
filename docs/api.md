# API 文档

## 基础信息

- Base URL: `http://localhost:8000/api/v1`
- 交互式文档: `http://localhost:8000/docs`

---

## 1. Agent 决策接口

### POST `/agent/decide`

Agent 核心决策，接收直播多模态数据，返回提词建议。

**请求体示例：**
```json
{
  "直播状态": {
    "当前阶段": "产品讲解期",
    "已直播时长": 900,
    "计划总时长": 3600,
    "当前产品": "精华液_sku_12345"
  },
  "弹幕数据": {
    "最近30秒消息": ["油皮能用吗？", "价格太贵了", "油皮能用吗？"],
    "情绪分析": {
      "高频词": {"油皮": 3, "价格": 2},
      "负面反馈": ["价格太贵了"]
    }
  },
  "商品数据": {
    "sku_id": "12345",
    "产品名称": "控油修护精华液",
    "规格": "30ml",
    "价格": 350,
    "成分": ["水杨酸", "烟酰胺", "透明质酸"],
    "功效": ["控油", "修护", "保湿"]
  },
  "后台数据": {
    "在线人数": 1250,
    "购物车点击率": "上升5%",
    "转化率": "2.3%"
  }
}
```

**响应示例：**
```json
{
  "提词指令": {
    "优先级": "高",
    "建议话术": "很多宝宝在问油皮能不能用，这款精华特意添加了水杨酸成分，专门针对油皮设计，控油效果非常好！",
    "动作建议": "拿起产品展示成分表",
    "触发原因": "弹幕高频问题:油皮适用性",
    "合规检查": "通过"
  }
}
```

---

## 2. 商品管理接口

### POST `/products`
新增商品

### GET `/products`
获取商品列表

### GET `/products/{sku_id}`
查询商品详情

### DELETE `/products/{sku_id}`
删除商品

---

## 3. 合规检查接口

### POST `/compliance/check`
检查文本是否合规

### GET `/compliance/word-count`
获取违禁词库数量

---

## 4. RAG 知识库接口

### GET `/rag/collections`
获取所有知识库集合

### GET `/rag/collections/{collection_name}`
获取集合详情

### POST `/rag/documents`
添加文档到知识库

**请求体：**
```json
{
  "collection": "products",
  "text": "文档内容...",
  "metadata": {"type": "product", "sku": "12345"}
}
```

### POST `/rag/search`
语义搜索

**请求体：**
```json
{
  "collection": "products",
  "query": "油皮能用吗",
  "top_k": 3
}
```

### DELETE `/rag/collections/{collection_name}`
删除知识库集合

---

## 5. LLM 测试接口

### POST `/llm/test`
测试 LLM 连接

---

## 6. 健康检查

### GET `/health`
