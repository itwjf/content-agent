-- ============================================================
-- 直播场次域建表脚本（手动执行）
-- 说明：这些表不会由应用自动创建，需手动执行本脚本
-- 执行方式：mysql -u <user> -p <database> < 02_live_tables.sql
-- ============================================================

-- 1. 直播场次表
CREATE TABLE IF NOT EXISTS `live_sessions` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `title` VARCHAR(200) NOT NULL COMMENT '场次标题',
    `platform` VARCHAR(50) NOT NULL DEFAULT 'mock' COMMENT '平台来源：douyin/taobao/kuaishou/mock',
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态：pending待开播/liveing直播中/ended已结束/error异常',
    `current_stage` VARCHAR(50) NOT NULL DEFAULT '预热期' COMMENT '当前直播阶段',
    `script` JSON COMMENT '导入的整场剧本（阶段规划+目标+话术要点）',
    `started_at` DATETIME COMMENT '开始时间',
    `ended_at` DATETIME COMMENT '结束时间',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_live_sessions_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='直播场次表';

-- 2. 弹幕消息表
CREATE TABLE IF NOT EXISTS `danmaku_messages` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `session_id` INT NOT NULL COMMENT '所属场次ID',
    `platform` VARCHAR(50) COMMENT '来源平台',
    `user_id` VARCHAR(64) COMMENT '脱敏后的用户ID',
    `content` VARCHAR(500) NOT NULL COMMENT '弹幕内容',
    `raw` JSON COMMENT '原始消息数据',
    `sent_at` DATETIME NOT NULL COMMENT '弹幕发送时间',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
    PRIMARY KEY (`id`),
    KEY `idx_danmaku_session_id` (`session_id`),
    KEY `idx_danmaku_session_time` (`session_id`, `sent_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='弹幕消息表';

-- 3. 决策记录表
CREATE TABLE IF NOT EXISTS `decision_records` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `session_id` INT NOT NULL COMMENT '所属场次ID',
    `trigger_reason` VARCHAR(200) COMMENT '触发原因',
    `script` JSON COMMENT '导演脚本（lines/emotion/action/pace/show_product_card等）',
    `priority` VARCHAR(20) COMMENT '优先级：高/中/低',
    `compliance_result` JSON COMMENT '合规检查结果',
    `adopted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否被采纳',
    `degraded` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否为LLM降级产出',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_decision_session_id` (`session_id`),
    KEY `idx_decision_session_time` (`session_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='决策记录表';

-- 4. 实时指标表
CREATE TABLE IF NOT EXISTS `live_metrics` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `session_id` INT NOT NULL COMMENT '所属场次ID',
    `metric_type` VARCHAR(50) NOT NULL COMMENT '指标类型：popularity在线人数/danmaku_rate弹幕速率/like点赞/cart_click购物车点击/order下单',
    `value` DOUBLE NOT NULL COMMENT '指标值',
    `source` VARCHAR(20) NOT NULL DEFAULT 'manual' COMMENT '数据来源：api官方接口/manual手动注入/mock模拟',
    `recorded_at` DATETIME NOT NULL COMMENT '指标记录时间',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
    PRIMARY KEY (`id`),
    KEY `idx_metric_session_id` (`session_id`),
    KEY `idx_metric_session_type_time` (`session_id`, `metric_type`, `recorded_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='实时指标表';
