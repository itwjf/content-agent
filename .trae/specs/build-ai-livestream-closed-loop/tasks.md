# Tasks

- [x] Task 1: 数据模型与场次域（LiveSession / DanmakuMessage / DecisionRecord / LiveMetric）
  - [x] SubTask 1.1: 在 `backend/app/models/` 新增四张表的 SQLAlchemy 模型（字段定义见 spec Requirement 2）
  - [x] SubTask 1.2: 建表 SQL 提供于 `backend/sql/02_live_tables.sql`（按用户要求由用户手动执行，应用不做自动建表）
  - [x] SubTask 1.3: 新增场次 CRUD 服务与路由（创建/开始/结束/查询回放），同步更新 `main_mysql.py` 注册
- [x] Task 2: 统一消息模型与平台接入网关骨架
  - [x] SubTask 2.1: 定义统一弹幕消息模型与实时指标模型（Pydantic + 内部协议）
  - [x] SubTask 2.2: 抽象 `BasePlatformAdapter` 接口（connect/reconnect/消息缓冲/归一化）
  - [x] SubTask 2.3: 实现模拟弹幕源适配器（支持场景化弹幕序列回放：高频提问/负面刷屏/购买意向）
  - [x] SubTask 2.4: 网关管理路由（查询/切换适配器状态，官方适配器保持禁用占位与配置开关）
- [x] Task 3: WebSocket 实时通道
  - [x] SubTask 3.1: 实现 `/ws/live/{session_id}` 端点，推送 danmaku/decision/metric/stage 四类消息
  - [x] SubTask 3.2: 断线重连与 last_event_id 增量补拉机制
  - [x] SubTask 3.3: 保留 REST `POST /agent/decide` 兼容（未改动现有端点，回归验证在 Task 10 执行）
- [x] Task 4: 决策中枢升级——LLM 互动理解（含规则降级）
  - [x] SubTask 4.1: LLM 批量弹幕语义分析（意图/情绪/高频问题聚合），输出结构化结果
  - [x] SubTask 4.2: 超时/失败自动降级到现有关键词规则方案，标记 `degraded=true` 并记录日志
- [x] Task 5: 导演脚本与剧本融合
  - [x] SubTask 5.1: 定义导演脚本 JSON 格式（lines/emotion/action/pace/show_product_card/priority/trigger_reason）
  - [x] SubTask 5.2: `director/` 服务：融合剧本（阶段规划导入）+ 商品信息 + 互动理解结果，产出导演脚本
  - [x] SubTask 5.3: 决策记录（DecisionRecord）自动落库
- [x] Task 6: 展示适配层（TTS + 2D 数字人形象驱动）
  - [x] SubTask 6.1: TTS 适配器抽象 + CosyVoice/商用 API 可配置实现
  - [x] SubTask 6.2: 合规闸门前置：台词过合规模块（复用现有违禁词库），不通过则拦截并告警
  - [x] SubTask 6.3: 输出音频 + 字幕 JSON + 动作指令包
  - [x] SubTask 6.4: 2D 形象驱动适配器：底版素材管理（真人录制/照片/AI 生成三种来源，3~5 套轮换）+ MuseTalk/LivePortrait 实时口型驱动 + 画面合成（商品特写贴片/字幕/商品卡叠加）（推理服务接口约定 + 适配器就绪，底版素材管理与画面合成贴片由推理服务侧承载）
  - [x] SubTask 6.5: 降级机制：无 GPU/驱动模型未就绪时自动降级为"TTS + 字幕"纯声音形态；"AI 生成内容"标识叠加配置
- [x] Task 7: 浏览器采集适配器（官方渠道兜底方案）
  - [x] SubTask 7.1: 实现浏览器端采集脚本与回传接口，归一化进统一消息模型
  - [x] SubTask 7.2: 在 `docs/` 补充平台接入说明：官方渠道资质要求、浏览器采集的风控与条款风险提示
- [x] Task 8: 实时指标采集与策略引擎
  - [x] SubTask 8.1: LiveMetric 采集入库（官方 API 拉取占位 + 监场台/模拟源手动注入）
  - [x] SubTask 8.2: `strategy/` 策略引擎：滑动窗口指标计算 + 3~5 条可配置基础策略规则（权重动态调整）
  - [x] SubTask 8.3: 策略调整记录（原因 + 前后权重快照）落库与查询接口（建表 SQL：`backend/sql/03_strategy_tables.sql`，需手动执行）
- [x] Task 9: 前端监场台改版
  - [x] SubTask 9.1: WebSocket 客户端（自动重连 + 增量补拉）
  - [x] SubTask 9.2: 监场台页面：弹幕流、导演脚本展示、阶段进度、指标曲线
  - [x] SubTask 9.3: 人工接管/恢复：暂停自动决策、手动话术输入（过合规检查）、TTS 音频播放
- [ ] Task 10: 端到端联调与验收 ⚠️【依赖 backend/.env 配置：LLM_API_KEY 必填 + DATABASE_URL 指向已建表的本机 MySQL；可选 SILICONFLOW/TTS/浏览器采集配置见 .env.example】
  - [ ] SubTask 10.1: 模拟源全链路验证：弹幕注入 → LLM 决策 → 导演脚本 → 合规 → TTS → 前端监场台（需 LLM_API_KEY）
  - [ ] SubTask 10.2: 指标回流验证：注入人气/转化数据 → 策略引擎调权 → 决策行为变化可观测
  - [ ] SubTask 10.3: 降级与异常场景验证：LLM 超时降级、WebSocket 断线重连、合规拦截

# Task Dependencies

- Task 1 为基础，所有任务依赖 Task 1
- Task 2 → Task 3（通道推送依赖统一消息模型）
- Task 4、Task 5 依赖 Task 1，可并行；Task 5 依赖 Task 4 的互动理解输出
- Task 6 依赖 Task 5；Task 7 依赖 Task 2（可与 Task 4/5/6 并行）
- Task 8 依赖 Task 1、Task 3；Task 9 依赖 Task 3、Task 6
- Task 10 依赖全部任务完成

# 环境配置依赖说明

- Task 1~9 的开发与代码级验证（单元冒烟测试）不需要 `.env`，用临时环境变量绕过启动校验即可
- **Task 10 端到端联调必须先配置 `backend/.env`**：最少需 `LLM_API_KEY`（启动强依赖）与 `DATABASE_URL`（指向用户手动建表的本机 MySQL，本机运行时不能用默认的 docker 主机名 mysql:3306）
- 其余配置（SILICONFLOW_API_KEY / TTS_* / AVATAR_* / BROWSER_*)按联调范围可选，详见 `backend/.env.example` 与 `docs/platform-access.md`

# 用户手动待办（Task 10 联调前完成）

- [ ] 【必须】执行建表 SQL：`mysql -u <user> -p <库名> < backend/sql/03_strategy_tables.sql`（Task 8 新增的 `strategy_adjustments` 策略调整记录表）
- [ ] 【必须】创建 `backend/.env`（复制 `backend/.env.example`），至少填写：
  - `LLM_API_KEY`（后端启动强依赖，缺失时应用无法启动）
  - `DATABASE_URL=mysql+pymysql://<用户>:<密码>@localhost:3306/<库名>`（本机运行必须用 localhost，不能用默认的 docker 主机名）
- [ ] 【可选·按需】`.env` 可选项：
  - `SILICONFLOW_API_KEY`（RAG 语义检索用）
  - `BROWSER_ADAPTER_ENABLED=true` + `BROWSER_COLLECT_TOKEN=<随机串>`（Task 7 浏览器采集；不配可用运行时接口代替启用）
  - `TTS_PROVIDER` / `AVATAR_*`（Task 6 TTS 与数字人；默认 mock 静音 + 纯声音形态，联调可先不配）
- [ ] 【本机运行时】修复本机 Python 环境缺失依赖：`pip install pymupdf python-docx`（requirements 已声明但本机未装；PyMuPDF 在 Python 3.13 下无预编译 wheel 会源码编译失败，建议用 Python 3.11 环境或直接走 Docker 部署，Docker 不受影响）。影响范围：商品上传模块（`product_upload.py`）导入失败 → 本机启动 `main_mysql` 失败
- [ ] 【联调时确认】MySQL 已建好 `02_live_tables.sql`（Task 1 四张表）与 `03_strategy_tables.sql`（Task 8 一张表）共五张表
