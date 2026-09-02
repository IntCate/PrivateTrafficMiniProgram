-- =============================================================================
-- 快乐购商城 · 初始化种子数据（前台段）
-- 对齐 docs/database-design.md §4 初始化数据 + 前端 mock（store.js）
--
-- 说明：
--   * 须在 alembic upgrade head（或 schema.sql）建表之后执行
--   * 仅含 C 端前台表（category/product/product_sku/banner），导入不依赖后台表
--   * 后台种子（sys_config/admin_user）见同目录 seed-backend.sql，待后台模块建表后执行
--   * 图片 URL 为前端相对路径占位（/static/...），上线前替换为真实 CDN
-- =============================================================================

SET NAMES utf8mb4;
SET @now = NOW();
SET FOREIGN_KEY_CHECKS = 0;

-- ---------------------------------------------------------------------------
-- 1. 分类（对应前端 categories：鞋服/箱包/数码/美妆/家居）
-- ---------------------------------------------------------------------------
INSERT INTO `category` (`id`, `parent_id`, `name`, `icon`, `sort`, `status`) VALUES
(1, 0, '鞋服', NULL, 1, 1),
(2, 0, '箱包', NULL, 2, 1),
(3, 0, '数码', NULL, 3, 1),
(4, 0, '美妆', NULL, 4, 1),
(5, 0, '家居', NULL, 5, 1);

-- ---------------------------------------------------------------------------
-- 2. 商品（productCatalog 10 条，对齐前端 mock）
--    images = [main_image]；product_no 格式 P20260831 + 3 位序号
-- ---------------------------------------------------------------------------
INSERT INTO `product`
(`id`, `product_no`, `category_id`, `brand`, `name`, `sub_title`, `price`, `original_price`,
 `main_image`, `images`, `detail_html`, `spec`, `sales`, `stock`, `tags`,
 `shipping_from`, `is_free_shipping`, `status`, `views`)
VALUES
( 1, 'P20260831001', 1, NULL, '潮流运动鞋', '透气网面，轻弹缓震', 299.00, 599.00,
 '/static/product-sneakers.jpg', JSON_ARRAY('/static/product-sneakers.jpg'),
 '<p>透气网面，轻弹缓震</p><p>精选优质材料，匠心工艺，品质保证。</p>',
 JSON_OBJECT('材质','织物+TPU','闭合','系带','适用','跑步/休闲','产地','中国'),
 12000, 500, JSON_ARRAY('热销','包邮'), '上海', 1, 1, 0),
( 2, 'P20260831002', 1, NULL, '轻便休闲鞋', '一脚蹬设计，舒适百搭', 199.00, 359.00,
 '/static/product-sneakers.jpg', JSON_ARRAY('/static/product-sneakers.jpg'),
 '<p>一脚蹬设计，舒适百搭</p><p>精选优质材料，匠心工艺，品质保证。</p>',
 JSON_OBJECT('材质','织物面料','闭合','一脚蹬','适用','日常通勤','产地','中国'),
 8600, 500, JSON_ARRAY('新品'), '上海', 1, 1, 0),
( 3, 'P20260831003', 2, NULL, '简约单肩包', '优质皮料，百搭通勤', 159.00, 329.00,
 '/static/product-bag.jpg', JSON_ARRAY('/static/product-bag.jpg'),
 '<p>优质皮料，百搭通勤</p><p>精选优质材料，匠心工艺，品质保证。</p>',
 JSON_OBJECT('材质','头层牛皮','尺寸','中号','适用','通勤/出行','产地','中国'),
 5600, 500, JSON_ARRAY('通勤','包邮'), '上海', 1, 1, 0),
( 4, 'P20260831004', 2, NULL, '复古水桶包', '大容量，时尚有型', 229.00, 459.00,
 '/static/product-bag.jpg', JSON_ARRAY('/static/product-bag.jpg'),
 '<p>大容量，时尚有型</p><p>精选优质材料，匠心工艺，品质保证。</p>',
 JSON_OBJECT('材质','人造皮革','尺寸','大号','适用','通勤/旅行','产地','中国'),
 2300, 500, JSON_ARRAY(), '上海', 1, 1, 0),
( 5, 'P20260831005', 3, NULL, '无线降噪耳机', '主动降噪，40小时续航', 899.00, 1299.00,
 '/static/product-headphones.jpg', JSON_ARRAY('/static/product-headphones.jpg'),
 '<p>主动降噪，40小时续航</p><p>精选优质材料，匠心工艺，品质保证。</p>',
 JSON_OBJECT('续航','40小时','降噪','主动降噪','佩戴','头戴式','产地','中国'),
 4200, 300, JSON_ARRAY('热销','包邮'), '上海', 1, 1, 0),
( 6, 'P20260831006', 3, NULL, '真无线蓝牙耳机', '小巧便携，低延迟', 259.00, 469.00,
 '/static/product-headphones.jpg', JSON_ARRAY('/static/product-headphones.jpg'),
 '<p>小巧便携，低延迟</p><p>精选优质材料，匠心工艺，品质保证。</p>',
 JSON_OBJECT('续航','8小时','蓝牙','5.3','佩戴','入耳式','产地','中国'),
 9800, 500, JSON_ARRAY('新品'), '上海', 1, 1, 0),
( 7, 'P20260831007', 4, NULL, '保湿护肤套装', '补水修护，温和不紧绷', 219.00, 399.00,
 '/static/product-skincare.jpg', JSON_ARRAY('/static/product-skincare.jpg'),
 '<p>补水修护，温和不紧绷</p><p>精选优质材料，匠心工艺，品质保证。</p>',
 JSON_OBJECT('功效','补水修护','适用肤质','所有肤质','规格','水乳套装','产地','中国'),
 3100, 500, JSON_ARRAY('热销'), '上海', 1, 1, 0),
( 8, 'P20260831008', 4, NULL, '焕亮精华面膜', '深层滋养，提亮肤色', 129.00, 259.00,
 '/static/product-skincare.jpg', JSON_ARRAY('/static/product-skincare.jpg'),
 '<p>深层滋养，提亮肤色</p><p>精选优质材料，匠心工艺，品质保证。</p>',
 JSON_OBJECT('功效','提亮肤色','适用肤质','干性/中性','规格','5片/盒','产地','中国'),
 6100, 500, JSON_ARRAY('囤货首选'), '上海', 1, 1, 0),
( 9, 'P20260831009', 5, NULL, '北欧风香薰套装', '清新怡人，舒缓放松', 89.00, 169.00,
 '/static/product-skincare.jpg', JSON_ARRAY('/static/product-skincare.jpg'),
 '<p>清新怡人，舒缓放松</p><p>精选优质材料，匠心工艺，品质保证。</p>',
 JSON_OBJECT('香型','晨雾/森林','材质','陶瓷','适用','卧室/客厅','产地','中国'),
 1500, 500, JSON_ARRAY(), '上海', 1, 1, 0),
(10, 'P20260831010', 5, NULL, '云朵抱枕靠垫', '柔软亲肤，居家好物', 69.00, 129.00,
 '/static/product-skincare.jpg', JSON_ARRAY('/static/product-skincare.jpg'),
 '<p>柔软亲肤，居家好物</p><p>精选优质材料，匠心工艺，品质保证。</p>',
 JSON_OBJECT('材质','短毛绒','填充','PP棉','尺寸','45x45cm','产地','中国'),
 2600, 500, JSON_ARRAY('包邮'), '上海', 1, 0, 0);  -- 商品10 status=0(下架)，对齐前端 onSale:false

-- ---------------------------------------------------------------------------
-- 3. SKU（按商品属性组笛卡尔积；sku_code = P{商品id}-S{序号}）
-- ---------------------------------------------------------------------------
INSERT INTO `product_sku`
(`id`, `product_id`, `sku_code`, `attrs`, `sku_text`, `price`, `stock`, `lock_stock`, `image`, `status`)
VALUES
-- 商品1 潮流运动鞋：颜色 x 尺码 = 3 x 4
( 101, 1, 'P1-S001', JSON_ARRAY(JSON_OBJECT('name','颜色','value','云雾白'),JSON_OBJECT('name','尺码','value','39')), '云雾白；39', 299.00, 88, 0, NULL, 1),
( 102, 1, 'P1-S002', JSON_ARRAY(JSON_OBJECT('name','颜色','value','云雾白'),JSON_OBJECT('name','尺码','value','40')), '云雾白；40', 299.00, 88, 0, NULL, 1),
( 103, 1, 'P1-S003', JSON_ARRAY(JSON_OBJECT('name','颜色','value','云雾白'),JSON_OBJECT('name','尺码','value','41')), '云雾白；41', 299.00, 88, 0, NULL, 1),
( 104, 1, 'P1-S004', JSON_ARRAY(JSON_OBJECT('name','颜色','value','云雾白'),JSON_OBJECT('name','尺码','value','42')), '云雾白；42', 299.00, 88, 0, NULL, 1),
( 105, 1, 'P1-S005', JSON_ARRAY(JSON_OBJECT('name','颜色','value','碳素黑'),JSON_OBJECT('name','尺码','value','39')), '碳素黑；39', 299.00, 88, 0, NULL, 1),
( 106, 1, 'P1-S006', JSON_ARRAY(JSON_OBJECT('name','颜色','value','碳素黑'),JSON_OBJECT('name','尺码','value','40')), '碳素黑；40', 299.00, 88, 0, NULL, 1),
( 107, 1, 'P1-S007', JSON_ARRAY(JSON_OBJECT('name','颜色','value','碳素黑'),JSON_OBJECT('name','尺码','value','41')), '碳素黑；41', 299.00, 88, 0, NULL, 1),
( 108, 1, 'P1-S008', JSON_ARRAY(JSON_OBJECT('name','颜色','value','碳素黑'),JSON_OBJECT('name','尺码','value','42')), '碳素黑；42', 299.00, 88, 0, NULL, 1),
( 109, 1, 'P1-S009', JSON_ARRAY(JSON_OBJECT('name','颜色','value','珊瑚粉'),JSON_OBJECT('name','尺码','value','39')), '珊瑚粉；39', 299.00, 2, 0, NULL, 1),  -- 低库存测试项
( 110, 1, 'P1-S010', JSON_ARRAY(JSON_OBJECT('name','颜色','value','珊瑚粉'),JSON_OBJECT('name','尺码','value','40')), '珊瑚粉；40', 299.00, 88, 0, NULL, 1),
( 111, 1, 'P1-S011', JSON_ARRAY(JSON_OBJECT('name','颜色','value','珊瑚粉'),JSON_OBJECT('name','尺码','value','41')), '珊瑚粉；41', 299.00, 88, 0, NULL, 1),
( 112, 1, 'P1-S012', JSON_ARRAY(JSON_OBJECT('name','颜色','value','珊瑚粉'),JSON_OBJECT('name','尺码','value','42')), '珊瑚粉；42', 299.00, 88, 0, NULL, 1),
-- 商品2 轻便休闲鞋：颜色 x 尺码 = 2 x 3
( 201, 2, 'P2-S001', JSON_ARRAY(JSON_OBJECT('name','颜色','value','云雾白'),JSON_OBJECT('name','尺码','value','40')), '云雾白；40', 199.00, 88, 0, NULL, 1),
( 202, 2, 'P2-S002', JSON_ARRAY(JSON_OBJECT('name','颜色','value','云雾白'),JSON_OBJECT('name','尺码','value','41')), '云雾白；41', 199.00, 88, 0, NULL, 1),
( 203, 2, 'P2-S003', JSON_ARRAY(JSON_OBJECT('name','颜色','value','云雾白'),JSON_OBJECT('name','尺码','value','42')), '云雾白；42', 199.00, 88, 0, NULL, 1),
( 204, 2, 'P2-S004', JSON_ARRAY(JSON_OBJECT('name','颜色','value','碳素黑'),JSON_OBJECT('name','尺码','value','40')), '碳素黑；40', 199.00, 88, 0, NULL, 1),
( 205, 2, 'P2-S005', JSON_ARRAY(JSON_OBJECT('name','颜色','value','碳素黑'),JSON_OBJECT('name','尺码','value','41')), '碳素黑；41', 199.00, 88, 0, NULL, 1),
( 206, 2, 'P2-S006', JSON_ARRAY(JSON_OBJECT('name','颜色','value','碳素黑'),JSON_OBJECT('name','尺码','value','42')), '碳素黑；42', 199.00, 88, 0, NULL, 1),
-- 商品3 简约单肩包：颜色 x 均码
( 301, 3, 'P3-S001', JSON_ARRAY(JSON_OBJECT('name','颜色','value','黑色'),JSON_OBJECT('name','尺码','value','均码')), '黑色；均码', 159.00, 88, 0, NULL, 1),
( 302, 3, 'P3-S002', JSON_ARRAY(JSON_OBJECT('name','颜色','value','棕色'),JSON_OBJECT('name','尺码','value','均码')), '棕色；均码', 159.00, 88, 0, NULL, 1),
-- 商品4 复古水桶包
( 401, 4, 'P4-S001', JSON_ARRAY(JSON_OBJECT('name','颜色','value','米白'),JSON_OBJECT('name','尺码','value','均码')), '米白；均码', 229.00, 88, 0, NULL, 1),
( 402, 4, 'P4-S002', JSON_ARRAY(JSON_OBJECT('name','颜色','value','焦糖'),JSON_OBJECT('name','尺码','value','均码')), '焦糖；均码', 229.00, 88, 0, NULL, 1),
-- 商品5 无线降噪耳机：颜色 x 版本
( 501, 5, 'P5-S001', JSON_ARRAY(JSON_OBJECT('name','颜色','value','曜石黑'),JSON_OBJECT('name','版本','value','标准版')), '曜石黑；标准版', 899.00, 88, 0, NULL, 1),
-- 商品6 真无线蓝牙耳机
( 601, 6, 'P6-S001', JSON_ARRAY(JSON_OBJECT('name','颜色','value','云雾白'),JSON_OBJECT('name','版本','value','标准版')), '云雾白；标准版', 259.00, 88, 0, NULL, 1),
( 602, 6, 'P6-S002', JSON_ARRAY(JSON_OBJECT('name','颜色','value','深海蓝'),JSON_OBJECT('name','版本','value','标准版')), '深海蓝；标准版', 259.00, 88, 0, NULL, 1),
-- 商品7 保湿护肤套装：包装 x 规格
( 701, 7, 'P7-S001', JSON_ARRAY(JSON_OBJECT('name','包装','value','礼盒装'),JSON_OBJECT('name','规格','value','标准装')), '礼盒装；标准装', 219.00, 88, 0, NULL, 1),
-- 商品8 焕亮精华面膜
( 801, 8, 'P8-S001', JSON_ARRAY(JSON_OBJECT('name','包装','value','单盒装'),JSON_OBJECT('name','规格','value','标准装')), '单盒装；标准装', 129.00, 88, 0, NULL, 1),
( 802, 8, 'P8-S002', JSON_ARRAY(JSON_OBJECT('name','包装','value','三盒装'),JSON_OBJECT('name','规格','value','标准装')), '三盒装；标准装', 129.00, 88, 0, NULL, 1),
-- 商品9 北欧风香薰套装：香型 x 规格
( 901, 9, 'P9-S001', JSON_ARRAY(JSON_OBJECT('name','香型','value','晨雾'),JSON_OBJECT('name','规格','value','均码')), '晨雾；均码', 89.00, 88, 0, NULL, 1),
( 902, 9, 'P9-S002', JSON_ARRAY(JSON_OBJECT('name','香型','value','森林'),JSON_OBJECT('name','规格','value','均码')), '森林；均码', 89.00, 88, 0, NULL, 1),
-- 商品10 云朵抱枕靠垫：颜色 x 规格
(1001, 10, 'P10-S001', JSON_ARRAY(JSON_OBJECT('name','颜色','value','云朵白'),JSON_OBJECT('name','规格','value','均码')), '云朵白；均码', 69.00, 88, 0, NULL, 1),
(1002, 10, 'P10-S002', JSON_ARRAY(JSON_OBJECT('name','颜色','value','迷雾灰'),JSON_OBJECT('name','规格','value','均码')), '迷雾灰；均码', 69.00, 88, 0, NULL, 1);

-- ---------------------------------------------------------------------------
-- 4. 运营位：hero 主横幅 3 条 + theme 主题精选 4 条（对齐前端 banners/themes）
-- ---------------------------------------------------------------------------
INSERT INTO `banner`
(`position`, `title`, `sub_title`, `image`, `link_type`, `link_value`, `sort`, `status`)
VALUES
('hero',  '夏季新品 火热开售', '限时特惠', '/static/hero-banner.jpg', 'page',     '/pages/products/products', 1, 1),
('hero',  '会员日 积分翻倍',   '会员专享', '/static/hero-banner.jpg', 'page',     '/pages/me/me',             2, 1),
('hero',  '通勤好物 一站购齐', '每日精选', '/static/hero-banner.jpg', 'category', '2',                      3, 1),
('theme', '夏季焕新',          '轻盈出行', '/static/hero-banner.jpg', 'category', '1',                      1, 1),
('theme', '会员专享',          '积分抵现', '/static/hero-banner.jpg', 'page',     '/pages/me/me',            2, 1),
('theme', '通勤百搭',          '精致搭配', '/static/hero-banner.jpg', 'category', '2',                      3, 1),
('theme', '影音数码',          '沉浸体验', '/static/hero-banner.jpg', 'category', '3',                      4, 1);

SET FOREIGN_KEY_CHECKS = 1;
