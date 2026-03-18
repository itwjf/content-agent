-- MySQL初始化脚本
-- 创建数据库和表结构

-- 使用指定的数据库
USE content_agent;

-- 创建商品表（如果不存在）
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sku_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    brand VARCHAR(100),
    spec VARCHAR(100),
    price FLOAT NOT NULL,
    original_price FLOAT,
    ingredients JSON,
    effects JSON,
    description TEXT,
    selling_points JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_sku_id (sku_id),
    INDEX idx_category (category),
    INDEX idx_brand (brand)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入示例数据
INSERT INTO products (sku_id, name, category, brand, spec, price, original_price, ingredients, effects, description, selling_points) VALUES
('12345', '控油修护精华液', '护肤品', '品牌A', '30ml', 350, 499, '["水杨酸", "烟酰胺", "透明质酸"]', '["控油", "修护", "保湿"]', '专为油皮设计的控油修护精华，温和不刺激', '["油皮亲妈", "持久控油", "温和不刺激"]'),
('67890', '氨基酸洁面乳', '护肤品', '品牌A', '100ml', 129, 199, '["氨基酸", "神经酰胺", "甘草酸二钾"]', '["温和清洁", "补水", "舒缓"]', '氨基酸温和洁面，敏感肌可用', '["温和不刺激", "敏感肌适用", "泡沫丰富"]'),
('11111', '美白淡斑精华液', '护肤品', '品牌B', '50ml', 299, 399, '["维生素C", "烟酰胺", "熊果苷"]', '["美白", "淡斑", "提亮"]', '高浓度VC美白精华，28天提亮肤色', '["28天见效", "高浓度VC", "淡化色斑"]'),
('22222', '抗皱紧致面霜', '护肤品', '品牌B', '50g', 458, 598, '["视黄醇", "胶原蛋白", "神经酰胺"]', '["抗皱", "紧致", "滋润"]', '视黄醇抗皱面霜，淡化细纹紧致肌肤', '["淡化细纹", "紧致提拉", "滋润不油腻"]'),
('33333', '玻尿酸补水面膜', '护肤品', '品牌C', '10片/盒', 89, 129, '["玻尿酸", "透明质酸", "甘油"]', '["补水", "保湿", "滋润"]', '玻尿酸深层补水面膜，一片水润一整天', '["深层补水", "一片见效", "平价好用"]'),
('44444', '防晒隔离霜 SPF50+', '彩妆', '品牌C', '40ml', 168, 218, '["二氧化钛", "氧化锌", "维生素E"]', '["防晒", "隔离", "修饰肤色"]', '高倍防晒隔离霜，轻薄不油腻', '["SPF50+", "轻薄透气", "防晒隔离二合一"]'),
('55555', '修复护发精油', '洗护', '品牌D', '100ml', 79, 99, '["摩洛哥坚果油", "荷荷巴油", "维生素E"]', '["修复", "柔顺", "光泽"]', '修复干枯受损发质，一抹顺滑', '["修复分叉", "一抹顺滑", "不油腻"]'),
('66666', '眼部按摩仪', '美容仪器', '品牌E', '1台', 299, 399, '[]', '["淡化黑眼圈", "缓解眼疲劳", "促进吸收"]', '微电流眼部按摩仪，淡化黑眼圈眼袋', '["微电流按摩", "淡化黑眼圈", "便携易用"]');

-- 创建用户表（可选，用于后续扩展）
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建直播记录表（可选，用于后续扩展）
CREATE TABLE IF NOT EXISTS live_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id INT,
    product_sku VARCHAR(50),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    duration_seconds INT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建提词记录表（可选，用于后续扩展）
CREATE TABLE IF NOT EXISTS prompt_suggestions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    priority VARCHAR(10) NOT NULL,
    trigger_reason TEXT,
    suggestion_text TEXT NOT NULL,
    action_advice VARCHAR(200),
    compliance_status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES live_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_priority (priority),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;