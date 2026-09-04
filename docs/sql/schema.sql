-- =============================================================================
-- 快乐购商城 · 数据库结构 (schema.sql)
-- 对齐 docs/database-design.md（17 张表），MySQL 8.x，utf8mb4 / utf8mb4_unicode_ci
--
-- 使用方式：
--   mysql -u{user} -p {db} < schema.sql
--   mysql -u{user} -p {db} < seed-data.sql
--
-- 注意：
--   * 图片 URL 为前端相对路径占位（/static/...），部署时替换为真实 CDN 地址
--   * 初始化脚本含 DROP TABLE，仅在空库/重建场景使用
--   * 与 database-design.md §3.3 的索引差异：product 表字段清单无 sort，
--     故 idx_category_status 使用 (category_id, status)，不再含 sort（文档笔误，字段清单为准）
-- =============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 按依赖倒序清理（外键安全）
DROP TABLE IF EXISTS `sys_config`;
DROP TABLE IF EXISTS `member_session`;
DROP TABLE IF EXISTS `admin_user`;
DROP TABLE IF EXISTS `after_sale`;
DROP TABLE IF EXISTS `banner`;
DROP TABLE IF EXISTS `points_log`;
DROP TABLE IF EXISTS `user_coupon`;
DROP TABLE IF EXISTS `coupon`;
DROP TABLE IF EXISTS `favorite`;
DROP TABLE IF EXISTS `order_item`;
DROP TABLE IF EXISTS `orders`;
DROP TABLE IF EXISTS `shipping_address`;
DROP TABLE IF EXISTS `cart`;
DROP TABLE IF EXISTS `product_sku`;
DROP TABLE IF EXISTS `product`;
DROP TABLE IF EXISTS `category`;
DROP TABLE IF EXISTS `member`;

-- -----------------------------------------------------------------------------
-- 3.1 会员
-- -----------------------------------------------------------------------------
CREATE TABLE `member` (
  `id`             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `openid`         VARCHAR(64)     NOT NULL COMMENT '微信小程序 openid',
  `unionid`        VARCHAR(64)     DEFAULT NULL COMMENT '微信 unionid（多端绑定预留）',
  `nickname`       VARCHAR(64)     DEFAULT NULL COMMENT '昵称',
  `avatar`         VARCHAR(512)    DEFAULT NULL COMMENT '头像 URL',
  `phone`          VARCHAR(20)     DEFAULT NULL COMMENT '手机号',
  `gender`         TINYINT         NOT NULL DEFAULT 0 COMMENT '0 未知 / 1 男 / 2 女',
  `member_level`   VARCHAR(20)     NOT NULL DEFAULT 'bronze' COMMENT 'bronze/silver/gold/platinum',
  `points`         INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '当前积分',
  `status`         TINYINT         NOT NULL DEFAULT 1 COMMENT '1 正常 / 0 禁用',
  `last_login_at`  DATETIME        DEFAULT NULL COMMENT '最近登录时间',
  `created_at`     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
  `deleted`        TINYINT         NOT NULL DEFAULT 0 COMMENT '逻辑删除',
  `updated_at`     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_openid` (`openid`),
  KEY `idx_phone` (`phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会员';

-- -----------------------------------------------------------------------------
-- 3.2 商品分类
-- -----------------------------------------------------------------------------
CREATE TABLE `category` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `parent_id`  BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '父分类 ID，0 为顶级',
  `name`       VARCHAR(64)     NOT NULL COMMENT '分类名',
  `icon`       VARCHAR(512)    DEFAULT NULL COMMENT '分类图标',
  `sort`       INT             NOT NULL DEFAULT 0 COMMENT '排序，越小越靠前',
  `status`     TINYINT         NOT NULL DEFAULT 1 COMMENT '1 启用 / 0 停用',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_parent_sort` (`parent_id`, `sort`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品分类';

-- -----------------------------------------------------------------------------
-- 3.3 商品
-- -----------------------------------------------------------------------------
CREATE TABLE `product` (
  `id`              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `product_no`      VARCHAR(32)     NOT NULL COMMENT '商品编号（对外展示/追踪）',
  `category_id`     BIGINT UNSIGNED NOT NULL COMMENT '所属分类',
  `brand`           VARCHAR(64)     DEFAULT NULL COMMENT '品牌',
  `name`            VARCHAR(128)    NOT NULL COMMENT '商品名称',
  `sub_title`       VARCHAR(255)    DEFAULT NULL COMMENT '副标题/卖点',
  `price`           DECIMAL(10,2)   NOT NULL DEFAULT 0.00 COMMENT '销售价',
  `original_price`  DECIMAL(10,2)   DEFAULT NULL COMMENT '划线价/原价',
  `main_image`      VARCHAR(512)    NOT NULL COMMENT '主图',
  `images`          JSON            DEFAULT NULL COMMENT '图片列表',
  `detail_html`     TEXT            DEFAULT NULL COMMENT '详情富文本',
  `spec`            JSON            DEFAULT NULL COMMENT '参数规格',
  `sales`           INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '已售数量',
  `stock`           INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '总库存（兜底，精确以 SKU 为准）',
  `tags`            JSON            DEFAULT NULL COMMENT '标签',
  `shipping_from`   VARCHAR(32)     DEFAULT NULL COMMENT '发货地',
  `is_free_shipping` TINYINT        NOT NULL DEFAULT 1 COMMENT '1 包邮 / 0 不包邮',
  `status`          TINYINT         NOT NULL DEFAULT 1 COMMENT '1 上架 / 0 下架',
  `views`           INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '浏览量',
  `created_at`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `deleted`         TINYINT         NOT NULL DEFAULT 0 COMMENT '逻辑删除',
  `updated_at`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_product_no` (`product_no`),
  KEY `idx_category_status` (`category_id`, `status`),
  KEY `idx_status_sales` (`status`, `sales`),
  CONSTRAINT `fk_product_category` FOREIGN KEY (`category_id`) REFERENCES `category` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品';

-- -----------------------------------------------------------------------------
-- 3.4 SKU
-- -----------------------------------------------------------------------------
CREATE TABLE `product_sku` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `product_id`  BIGINT UNSIGNED NOT NULL COMMENT '商品 ID',
  `sku_code`    VARCHAR(64)     NOT NULL COMMENT 'SKU 编码',
  `attrs`       JSON            NOT NULL COMMENT '属性组数组 [{name,value},...]',
  `sku_text`    VARCHAR(128)    NOT NULL COMMENT '展示文案，如 云雾白；40',
  `price`       DECIMAL(10,2)   NOT NULL DEFAULT 0.00 COMMENT 'SKU 售价',
  `stock`       INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '库存',
  `lock_stock`  INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '锁定库存',
  `image`       VARCHAR(512)    DEFAULT NULL COMMENT 'SKU 专属图',
  `status`      TINYINT         NOT NULL DEFAULT 1 COMMENT '1 可售 / 0 停售',
  `created_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `deleted`     TINYINT         NOT NULL DEFAULT 0 COMMENT '逻辑删除',
  `updated_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sku_code` (`sku_code`),
  KEY `idx_product` (`product_id`),
  CONSTRAINT `fk_sku_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品 SKU';

-- -----------------------------------------------------------------------------
-- 3.5 购物车
-- -----------------------------------------------------------------------------
CREATE TABLE `cart` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    BIGINT UNSIGNED NOT NULL COMMENT '会员 ID',
  `product_id` BIGINT UNSIGNED NOT NULL COMMENT '商品 ID',
  `sku_id`     BIGINT UNSIGNED NOT NULL COMMENT 'SKU ID',
  `quantity`   INT UNSIGNED    NOT NULL DEFAULT 1 COMMENT '数量',
  `selected`   TINYINT         NOT NULL DEFAULT 0 COMMENT '勾选状态 1/0，加购默认不勾选',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_sku` (`user_id`, `sku_id`),
  KEY `idx_user` (`user_id`),
  CONSTRAINT `fk_cart_user`    FOREIGN KEY (`user_id`) REFERENCES `member` (`id`),
  CONSTRAINT `fk_cart_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`),
  CONSTRAINT `fk_cart_sku`     FOREIGN KEY (`sku_id`) REFERENCES `product_sku` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='购物车';

-- -----------------------------------------------------------------------------
-- 3.6 收货地址
-- -----------------------------------------------------------------------------
CREATE TABLE `shipping_address` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    BIGINT UNSIGNED NOT NULL COMMENT '会员 ID',
  `name`       VARCHAR(32)     NOT NULL COMMENT '收货人姓名',
  `phone`      VARCHAR(20)     NOT NULL COMMENT '手机号',
  `province`   VARCHAR(32)     NOT NULL COMMENT '省',
  `city`       VARCHAR(32)     NOT NULL COMMENT '市',
  `district`   VARCHAR(32)     NOT NULL COMMENT '区',
  `detail`     VARCHAR(255)    NOT NULL COMMENT '详细地址',
  `is_default` TINYINT         NOT NULL DEFAULT 0 COMMENT '是否默认 1/0',
  `deleted`    TINYINT         NOT NULL DEFAULT 0 COMMENT '逻辑删除',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_default` (`user_id`, `is_default`),
  KEY `idx_user_deleted` (`user_id`, `deleted`),
  CONSTRAINT `fk_address_user` FOREIGN KEY (`user_id`) REFERENCES `member` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='收货地址';

-- -----------------------------------------------------------------------------
-- 3.7 订单
-- -----------------------------------------------------------------------------
CREATE TABLE `orders` (
  `id`              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `order_no`        VARCHAR(32)     NOT NULL COMMENT '订单号 K+时间戳+3位随机',
  `user_id`         BIGINT UNSIGNED NOT NULL COMMENT '会员 ID',
  `status`          VARCHAR(20)     NOT NULL DEFAULT 'pending' COMMENT 'pending/paid/shipped/completed/refund/cancelled',
  `total_amount`    DECIMAL(10,2)   NOT NULL DEFAULT 0.00 COMMENT '商品总金额',
  `freight`         DECIMAL(10,2)   NOT NULL DEFAULT 0.00 COMMENT '运费',
  `pay_amount`      DECIMAL(10,2)   NOT NULL DEFAULT 0.00 COMMENT '实付金额',
  `coupon_amount`   DECIMAL(10,2)   NOT NULL DEFAULT 0.00 COMMENT '优惠券抵扣',
  `points_used`     INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '积分抵扣',
  `receiver_name`   VARCHAR(32)     NOT NULL COMMENT '收货人快照',
  `receiver_phone`  VARCHAR(20)     NOT NULL COMMENT '收货电话快照',
  `receiver_region` VARCHAR(128)    NOT NULL COMMENT '省市区快照',
  `receiver_detail` VARCHAR(255)    NOT NULL COMMENT '详细地址快照',
  `pay_type`        VARCHAR(20)     DEFAULT NULL COMMENT 'wechat/mock',
  `transaction_id`  VARCHAR(64)     DEFAULT NULL COMMENT '微信支付单号',
  `remark`          VARCHAR(255)    DEFAULT NULL COMMENT '买家备注',
  `cancel_reason`   VARCHAR(255)    DEFAULT NULL COMMENT '取消/关闭原因',
  `refund_reason`   VARCHAR(255)    DEFAULT NULL COMMENT '售后/退款原因',
  `refund_type`     VARCHAR(20)     DEFAULT NULL COMMENT 'refund 仅退款 / return 退货退款',
  `refund_time`     DATETIME        DEFAULT NULL COMMENT '申请售后时间',
  `pay_time`        DATETIME        DEFAULT NULL COMMENT '支付时间',
  `ship_time`       DATETIME        DEFAULT NULL COMMENT '发货时间',
  `finish_time`     DATETIME        DEFAULT NULL COMMENT '完成时间',
  `deleted`         TINYINT         NOT NULL DEFAULT 0 COMMENT '逻辑删除',
  `created_at`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_order_no` (`order_no`),
  KEY `idx_user_status` (`user_id`, `status`, `created_at`),
  KEY `idx_status` (`status`, `created_at`),
  CONSTRAINT `fk_order_user` FOREIGN KEY (`user_id`) REFERENCES `member` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单';

-- -----------------------------------------------------------------------------
-- 3.8 订单明细
-- -----------------------------------------------------------------------------
CREATE TABLE `order_item` (
  `id`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `order_id`     BIGINT UNSIGNED NOT NULL COMMENT '订单 ID',
  `product_id`   BIGINT UNSIGNED NOT NULL COMMENT '商品 ID',
  `sku_id`       BIGINT UNSIGNED NOT NULL COMMENT 'SKU ID',
  `product_name` VARCHAR(128)    NOT NULL COMMENT '商品名快照',
  `sku_text`     VARCHAR(128)    NOT NULL COMMENT 'SKU 文案快照',
  `image`        VARCHAR(512)    NOT NULL COMMENT '主图快照',
  `price`        DECIMAL(10,2)   NOT NULL DEFAULT 0.00 COMMENT '成交单价快照',
  `quantity`     INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '数量',
  `created_at`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_order` (`order_id`),
  KEY `idx_product` (`product_id`),
  CONSTRAINT `fk_orderitem_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单明细';

-- -----------------------------------------------------------------------------
-- 3.9 收藏
-- -----------------------------------------------------------------------------
CREATE TABLE `favorite` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    BIGINT UNSIGNED NOT NULL COMMENT '会员 ID',
  `product_id` BIGINT UNSIGNED NOT NULL COMMENT '商品 ID',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_product` (`user_id`, `product_id`),
  CONSTRAINT `fk_fav_user`    FOREIGN KEY (`user_id`) REFERENCES `member` (`id`),
  CONSTRAINT `fk_fav_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='收藏';

-- -----------------------------------------------------------------------------
-- 3.10 优惠券模板
-- -----------------------------------------------------------------------------
CREATE TABLE `coupon` (
  `id`             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`           VARCHAR(64)     NOT NULL COMMENT '券名称',
  `type`           VARCHAR(20)     NOT NULL DEFAULT 'cash' COMMENT 'cash满减/discount折扣/shipping免邮',
  `amount`         DECIMAL(10,2)   DEFAULT NULL COMMENT '满减金额',
  `discount`       DECIMAL(4,2)    DEFAULT NULL COMMENT '折扣，如 0.85',
  `min_amount`     DECIMAL(10,2)   NOT NULL DEFAULT 0.00 COMMENT '使用门槛',
  `total_count`    INT             NOT NULL DEFAULT 0 COMMENT '发放总量，0 不限',
  `received_count` INT             NOT NULL DEFAULT 0 COMMENT '已领取数量',
  `valid_start`    DATETIME        DEFAULT NULL COMMENT '生效时间',
  `valid_end`      DATETIME        DEFAULT NULL COMMENT '失效时间',
  `status`         TINYINT         NOT NULL DEFAULT 1 COMMENT '1 启用 / 0 停用',
  `created_at`     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='优惠券模板';

-- -----------------------------------------------------------------------------
-- 3.11 用户优惠券
-- -----------------------------------------------------------------------------
CREATE TABLE `user_coupon` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`       BIGINT UNSIGNED NOT NULL COMMENT '会员 ID',
  `coupon_id`     BIGINT UNSIGNED NOT NULL COMMENT '优惠券模板 ID',
  `status`        VARCHAR(20)     NOT NULL DEFAULT 'unused' COMMENT 'unused/used/expired',
  `used_order_no` VARCHAR(32)     DEFAULT NULL COMMENT '核销订单号',
  `used_at`       DATETIME        DEFAULT NULL COMMENT '使用时间',
  `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_status` (`user_id`, `status`),
  CONSTRAINT `fk_usercoupon_user`   FOREIGN KEY (`user_id`) REFERENCES `member` (`id`),
  CONSTRAINT `fk_usercoupon_coupon` FOREIGN KEY (`coupon_id`) REFERENCES `coupon` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户优惠券';

-- -----------------------------------------------------------------------------
-- 3.12 积分明细
-- -----------------------------------------------------------------------------
CREATE TABLE `points_log` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    BIGINT UNSIGNED NOT NULL COMMENT '会员 ID',
  `change`     INT             NOT NULL DEFAULT 0 COMMENT '变动值（正增负减）',
  `balance`    INT             NOT NULL DEFAULT 0 COMMENT '变动后余额',
  `type`       VARCHAR(20)     NOT NULL COMMENT 'earn获得/consume消费/refund退回',
  `biz_type`   VARCHAR(32)     NOT NULL COMMENT '业务场景：order/promotion/admin',
  `remark`     VARCHAR(255)    DEFAULT NULL COMMENT '说明',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user` (`user_id`, `created_at`),
  CONSTRAINT `fk_pointslog_user` FOREIGN KEY (`user_id`) REFERENCES `member` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='积分明细';

-- -----------------------------------------------------------------------------
-- 3.13 运营位
-- -----------------------------------------------------------------------------
CREATE TABLE `banner` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `position`   VARCHAR(20)     NOT NULL COMMENT 'hero 主横幅 / theme 主题精选',
  `title`      VARCHAR(64)     NOT NULL COMMENT '标题',
  `sub_title`  VARCHAR(64)     DEFAULT NULL COMMENT '副标题/描述',
  `image`      VARCHAR(512)    NOT NULL COMMENT '图片',
  `link_type`  VARCHAR(20)     NOT NULL DEFAULT 'none' COMMENT 'none/product/category/page',
  `link_value` VARCHAR(255)    DEFAULT NULL COMMENT '跳转目标',
  `sort`       INT             NOT NULL DEFAULT 0 COMMENT '排序',
  `status`     TINYINT         NOT NULL DEFAULT 1 COMMENT '1 展示 / 0 隐藏',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_position_status` (`position`, `status`, `sort`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='运营位';

-- -----------------------------------------------------------------------------
-- 3.14 售后单
-- -----------------------------------------------------------------------------
CREATE TABLE `after_sale` (
  `id`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `order_id`     BIGINT UNSIGNED NOT NULL COMMENT '订单 ID',
  `user_id`      BIGINT UNSIGNED NOT NULL COMMENT '会员 ID',
  `type`         VARCHAR(20)     NOT NULL COMMENT 'refund仅退款/return退货退款',
  `reason`       VARCHAR(255)    NOT NULL COMMENT '申请原因',
  `amount`       DECIMAL(10,2)   NOT NULL DEFAULT 0.00 COMMENT '申请金额',
  `status`       VARCHAR(20)     NOT NULL DEFAULT 'applying' COMMENT 'applying/approved/rejected/refunded/closed',
  `images`       JSON            DEFAULT NULL COMMENT '凭证图片',
  `audit_remark` VARCHAR(255)    DEFAULT NULL COMMENT '审核意见',
  `created_at`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_order` (`order_id`),
  KEY `idx_user` (`user_id`, `status`),
  CONSTRAINT `fk_aftersale_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`),
  CONSTRAINT `fk_aftersale_user`  FOREIGN KEY (`user_id`) REFERENCES `member` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='售后单';

-- -----------------------------------------------------------------------------
-- 3.15 管理员
-- -----------------------------------------------------------------------------
CREATE TABLE `admin_user` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `username`      VARCHAR(32)     NOT NULL COMMENT '登录名',
  `password`      VARCHAR(128)    NOT NULL COMMENT 'BCrypt 哈希',
  `nickname`      VARCHAR(32)     DEFAULT NULL COMMENT '姓名',
  `role`          VARCHAR(20)     NOT NULL DEFAULT 'admin' COMMENT 'admin/operator/finance',
  `status`        TINYINT         NOT NULL DEFAULT 1 COMMENT '1 启用 / 0 禁用',
  `last_login_at` DATETIME        DEFAULT NULL COMMENT '最近登录',
  `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员';

-- -----------------------------------------------------------------------------
-- 3.16 会员会话
-- -----------------------------------------------------------------------------
CREATE TABLE `member_session` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    BIGINT UNSIGNED NOT NULL COMMENT '会员 ID',
  `token`      VARCHAR(64)     NOT NULL COMMENT '登录态 token',
  `expires_at` DATETIME        NOT NULL COMMENT '过期时间（登录 + 7 天）',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登录时间',
  `deleted`    TINYINT         NOT NULL DEFAULT 0 COMMENT '逻辑删除',
  `updated_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_token` (`token`),
  KEY `idx_user` (`user_id`),
  CONSTRAINT `fk_session_user` FOREIGN KEY (`user_id`) REFERENCES `member` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会员会话';

-- -----------------------------------------------------------------------------
-- 3.17 系统配置
-- -----------------------------------------------------------------------------
CREATE TABLE `sys_config` (
  `id`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `config_key`   VARCHAR(64)     NOT NULL COMMENT '配置键',
  `config_value` TEXT            NOT NULL COMMENT '配置值（JSON 兼容）',
  `remark`       VARCHAR(255)    DEFAULT NULL COMMENT '说明',
  `updated_at`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置';

SET FOREIGN_KEY_CHECKS = 1;
