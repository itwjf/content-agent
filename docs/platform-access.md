# 平台接入说明（弹幕来源接入指南）

本文档说明 ContentAgent 如何接入直播平台弹幕：三种接入方式的适用条件、启用步骤，以及各自的风险与合规提示。

## 一、接入方式总览

| 方式 | 适配器名 | 前提条件 | 合规性 | 适用场景 |
|------|----------|----------|--------|----------|
| 官方开放平台 API | `douyin` / `taobao` / `kuaishou` | 企业资质 + 平台审批 | ✅ 官方授权 | 正式商用部署 |
| 浏览器端采集 | `browser` | 仅需浏览器 | ⚠️ 非官方授权，有风险 | 无官方渠道时的兜底/个人演示 |
| 模拟弹幕源 | `mock` | 无 | ✅ 自产数据 | 开发调试、功能演示 |

三种方式输出统一的弹幕消息模型（`session_id / platform / user_id(脱敏) / content / timestamp / raw`），对决策中枢与前端完全透明，可随时通过网关管理接口切换。

## 二、官方渠道接入（推荐商用路径）

### 2.1 资质要求

| 平台 | 资质要求 | 说明 |
|------|----------|------|
| 抖音 | 抖音开放平台企业账号 + 直播互动相关权限审批 | 需提交应用场景说明，弹幕（直播评论）能力通常面向自播/服务商场景开放 |
| 淘宝 | 淘宝开放平台 ISV 资质 + 淘宝直播开放接口权限 | 需商家授权（session 授权），直播弹幕接口审批较严格 |
| 快手 | 快手开放平台企业账号 + 直播相关权限 | 需报备使用场景 |

> 具体资质要求以各平台开放平台官方文档的最新政策为准，审批周期一般为数个工作日至数周。

### 2.2 启用步骤（资质获批后）

1. 在 `backend/.env` 中打开对应开关：

   ```env
   DOUYIN_API_ENABLED=true
   # TAOBAO_API_ENABLED=true
   # KUAISHOU_API_ENABLED=true
   ```

2. 在对应适配器（`backend/app/services/gateway/official_adapters.py`）中完成平台接口对接实现——当前为禁用占位，`_run()` 直接抛出 `NotImplementedError`，未对接时即使开关打开也无法启动。
3. 通过网关管理接口为场次启动：

   ```bash
   POST /api/v1/gateway/sessions/{session_id}/start
   {"adapter_name": "douyin", "options": {}}
   ```

## 三、浏览器端采集（兜底方案）

### 3.1 ⚠️ 风险提示（使用前必读）

- **条款风险**：浏览器端脚本采集直播评论**未经平台官方授权**，可能违反各平台《用户服务协议》《开发者协议》中关于"禁止以非官方方式抓取/获取平台数据"的条款。
- **风控风险**：平台可能识别自动化采集行为，导致**账号限流、警告、封禁直播间或账号**等处罚。采集频率越高、时长越长，风险越大。
- **合规义务**：采集到的弹幕内容含观众发言，仅应用于本系统内部的直播辅助决策，**不得对外存储、转售、公开展示**；请遵守《个人信息保护法》等法规，系统已对用户标识做脱敏处理（昵称哈希化，不落原始昵称）。
- **责任声明**：浏览器采集能力仅供学习研究和个人辅助使用，因使用本功能产生的账号处罚、法律纠纷由使用者自行承担。
- **建议**：正式商用请优先申请官方 API 接入（见第二节）。

### 3.2 技术局限

- 依赖页面 DOM 结构，**平台改版可能失效**，需按 3.4 节调整选择器；
- 部分直播间的弹幕区使用 Canvas 渲染（如某些大促直播间），DOM 方案采集不到；
- 部分弹幕（付费留言、粉丝团专属）可能需要手动展开后才出现在 DOM 中。

### 3.3 使用步骤

1. **启用适配器**（二选一）：
   - 配置 `backend/.env`：`BROWSER_ADAPTER_ENABLED=true` 后重启后端；
   - 或调用运行时开关：`POST /api/v1/gateway/adapters/browser/enable`。

2. **为场次启动采集源**（同时联动决策循环）：

   ```bash
   POST /api/v1/gateway/sessions/{session_id}/start
   {"adapter_name": "browser", "options": {}}
   ```

3. **获取采集脚本**：浏览器访问

   ```
   http://localhost:8000/api/v1/gateway/browser/collector.js?session_id={session_id}
   ```

   服务地址、场次ID、令牌已自动注入脚本中，直接全选复制。

4. **注入直播间页面**（二选一）：
   - **控制台方式**：打开直播间页面 → F12 控制台 → 粘贴脚本执行（页面刷新后需重新注入）；
   - **油猴方式**：安装 Tampermonkey 扩展 → 新建脚本 → 粘贴内容保存 → 打开直播间自动运行（推荐，刷新免重注）。

5. **验证**：控制台出现 `[CA采集] 已启动`，弹幕出现后看到 `回传成功`；监场台（WebSocket `/ws/live/{session_id}`）应实时收到 `platform=browser` 的弹幕。

### 3.4 脚本自定义（平台改版时）

脚本头部 `CONFIG` 可修改：

```js
var CONFIG = {
  itemSelector: '',   // 弹幕条目选择器，如 '.webcast-chatroom___item'（抖音网页版示例）
  textSelector: '',   // 条目内文本选择器，留空取条目 innerText
  flushInterval: 2000, // 回传间隔(ms)，调小会增加风控风险
  debug: true
};
```

脚本内置通用解析（`昵称：内容` / 整行为内容）与系统提示过滤，绝大多数场景无需修改。

### 3.5 安全建议

- **配置回传令牌**：在 `backend/.env` 设置 `BROWSER_COLLECT_TOKEN=自定义随机串`，未配置时回传接口不校验令牌，**仅限本机/内网使用**；
- 采集脚本通过 `GET /api/v1/gateway/browser/collector.js` 下发时令牌随之注入，请勿将带令牌的脚本外传；
- 降低 `flushInterval`（如 5s）可减小风控触发概率，代价是弹幕延迟升高。

## 四、相关接口速查

| 接口 | 说明 |
|------|------|
| `GET /api/v1/gateway/adapters` | 查询全部适配器状态 |
| `POST /api/v1/gateway/adapters/{name}/enable` / `disable` | 运行时启用/禁用 |
| `POST /api/v1/gateway/sessions/{id}/start` | 为场次启动弹幕源（body: `adapter_name` + `options`） |
| `POST /api/v1/gateway/sessions/{id}/stop` | 停止场次弹幕源与决策循环 |
| `POST /api/v1/gateway/browser/ingest/{session_id}` | 采集脚本回传弹幕（body: `token`/`items[]`） |
| `GET /api/v1/gateway/browser/collector.js` | 下发采集脚本（query: `session_id`/`server`/`token`） |
| `WS /ws/live/{session_id}` | 实时接收 danmaku/decision/metric/stage 推送 |
