-- =============================================================================
-- 快乐购商城 · 初始化种子数据（后台段）
-- 依赖后台模块建表（sys_config / admin_user），由 alembic 迁移 c3d4e5f6a7b8 创建
--
-- 说明：
--   * 须在 alembic upgrade head 建表之后执行
--   * 与 docs/sql/seed-data.sql（前台段）拆分，避免前台初始化被后台表缺失中断
--   * 管理员初始密码占位（BCrypt），上线前必须修改
-- =============================================================================

SET NAMES utf8mb4;
SET @now = NOW();
SET FOREIGN_KEY_CHECKS = 0;

-- ---------------------------------------------------------------------------
-- 1. 系统配置（预留键）
-- ---------------------------------------------------------------------------
INSERT INTO `sys_config` (`config_key`, `config_value`, `remark`) VALUES
('service_hotline',         '400-800-8888', '客服热线'),
('free_shipping_threshold', '0',           '包邮门槛（0 表示全包邮）'),
('app_version',             '1.0.0',       'APP 版本');

-- ---------------------------------------------------------------------------
-- 2. 管理员（初始账号，上线前必须修改密码）
--    password 为 Admin@123456 的 BCrypt 哈希（passlib 生成）
-- ---------------------------------------------------------------------------
INSERT INTO `admin_user` (`username`, `password`, `nickname`, `role`, `status`) VALUES
('admin', '$2b$12$SXWTlGg7Y9UORKYSnCmlK.ipclECAA0kc5kcQgVER2KOSodQA60fu', '超级管理员', 'admin', 1);

SET FOREIGN_KEY_CHECKS = 1;
