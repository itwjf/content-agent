-- ============================================================
-- 策略引擎建表脚本（手动执行）
-- 说明：这些表不会由应用自动创建，需手动执行本脚本
-- 执行方式：mysql -u <user> -p <database> < 03_strategy_tables.sql
-- ============================================================

-- 1. 策略调整记录表（可审计的优化轨迹）
CREATE TABLE IF NOT EXISTS `strategy_adjustments` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `session_id` INT NOT NULL COMMENT '所属场次ID',
    `rules_hit` JSON COMMENT '命中的规则列表（规则名+原因+指标快照）',
    `reason` VARCHAR(500) COMMENT '调整原因（人类可读汇总）',
    `weights_before` JSON COMMENT '调整前权重快照',
    `weights_after` JSON COMMENT '调整后权重快照',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '调整时间',
    PRIMARY KEY (`id`),
    KEY `idx_strategy_session_id` (`session_id`),
    KEY `idx_strategy_session_time` (`session_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='策略调整记录表';
