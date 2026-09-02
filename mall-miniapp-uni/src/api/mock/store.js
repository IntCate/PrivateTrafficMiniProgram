import { TOKEN_KEY, useMock } from '../config';

const pad = (n) => (n < 10 ? '0' + n : '' + n);

const formatDateTime = (date) =>
  `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;

const nowText = () => formatDateTime(new Date());

class BusinessError {
  constructor(code, message, data = null) {
    this.code = code;
    this.message = message;
    this.data = data;
    this.business = true;
  }
}

const error = (code, message, data = null) => new BusinessError(code, message, data);

const STATUS_TEXT = {
  pending: '待付款',
  paid: '待发货',
  shipped: '待收货',
  completed: '已完成',
  refund: '售后中',
  cancelled: '已取消',
};

const STATUS_DESC = {
  pending: '订单已提交，请尽快完成支付',
  paid: '商家正在打包，请耐心等待发货',
  shipped: '商品已发货，请注意查收',
  completed: '交易已完成，感谢您的信任',
  refund: '售后处理中，请耐心等待',
  cancelled: '订单已取消，期待再次光临',
};

const PRODUCT_ATTRS = [
  { attrs: [{ name: '颜色', values: ['云雾白', '碳素黑', '珊瑚粉'] }, { name: '尺码', values: ['39', '40', '41', '42'] }] },
  { attrs: [{ name: '颜色', values: ['云雾白', '碳素黑'] }, { name: '尺码', values: ['40', '41', '42'] }] },
  { attrs: [{ name: '颜色', values: ['黑色', '棕色'] }, { name: '尺码', values: ['均码'] }] },
  { attrs: [{ name: '颜色', values: ['米白', '焦糖'] }, { name: '尺码', values: ['均码'] }] },
  { attrs: [{ name: '颜色', values: ['曜石黑'] }, { name: '版本', values: ['标准版'] }] },
  { attrs: [{ name: '颜色', values: ['云雾白', '深海蓝'] }, { name: '版本', values: ['标准版'] }] },
  { attrs: [{ name: '包装', values: ['礼盒装'] }, { name: '规格', values: ['标准装'] }] },
  { attrs: [{ name: '包装', values: ['单盒装', '三盒装'] }, { name: '规格', values: ['标准装'] }] },
  { attrs: [{ name: '香型', values: ['晨雾', '森林'] }, { name: '规格', values: ['均码'] }] },
  { attrs: [{ name: '颜色', values: ['云朵白', '迷雾灰'] }, { name: '规格', values: ['均码'] }] },
];

const PRODUCT_SEEDS = [
  { categoryId: 1, name: '潮流运动鞋', subTitle: '透气网面，轻弹缓震', price: 299, originalPrice: 599, image: '/static/product-sneakers.jpg', sales: 12000, tags: ['热销', '包邮'], spec: { '材质': '织物+TPU', '闭合': '系带', '适用': '跑步/休闲', '产地': '中国' } },
  { categoryId: 1, name: '轻便休闲鞋', subTitle: '一脚蹬设计，舒适百搭', price: 199, originalPrice: 359, image: '/static/product-sneakers.jpg', sales: 8600, tags: ['新品'], spec: { '材质': '织物面料', '闭合': '一脚蹬', '适用': '日常通勤', '产地': '中国' } },
  { categoryId: 2, name: '简约单肩包', subTitle: '优质皮料，百搭通勤', price: 159, originalPrice: 329, image: '/static/product-bag.jpg', sales: 5600, tags: ['通勤', '包邮'], spec: { '材质': '头层牛皮', '尺寸': '中号', '适用': '通勤/出行', '产地': '中国' } },
  { categoryId: 2, name: '复古水桶包', subTitle: '大容量，时尚有型', price: 229, originalPrice: 459, image: '/static/product-bag.jpg', sales: 2300, tags: [], spec: { '材质': '人造皮革', '尺寸': '大号', '适用': '通勤/旅行', '产地': '中国' } },
  { categoryId: 3, name: '无线降噪耳机', subTitle: '主动降噪，40小时续航', price: 899, originalPrice: 1299, image: '/static/product-headphones.jpg', sales: 4200, tags: ['热销', '包邮'], spec: { '续航': '40小时', '降噪': '主动降噪', '佩戴': '头戴式', '产地': '中国' } },
  { categoryId: 3, name: '真无线蓝牙耳机', subTitle: '小巧便携，低延迟', price: 259, originalPrice: 469, image: '/static/product-headphones.jpg', sales: 9800, tags: ['新品'], spec: { '续航': '8小时', '蓝牙': '5.3', '佩戴': '入耳式', '产地': '中国' } },
  { categoryId: 4, name: '保湿护肤套装', subTitle: '补水修护，温和不紧绷', price: 219, originalPrice: 399, image: '/static/product-skincare.jpg', sales: 3100, tags: ['热销'], spec: { '功效': '补水修护', '适用肤质': '所有肤质', '规格': '水乳套装', '产地': '中国' } },
  { categoryId: 4, name: '焕亮精华面膜', subTitle: '深层滋养，提亮肤色', price: 129, originalPrice: 259, image: '/static/product-skincare.jpg', sales: 6100, tags: ['囤货首选'], spec: { '功效': '提亮肤色', '适用肤质': '干性/中性', '规格': '5片/盒', '产地': '中国' } },
  { categoryId: 5, name: '北欧风香薰套装', subTitle: '清新怡人，舒缓放松', price: 89, originalPrice: 169, image: '/static/product-skincare.jpg', sales: 1500, tags: [], spec: { '香型': '晨雾/森林', '材质': '陶瓷', '适用': '卧室/客厅', '产地': '中国' } },
  { categoryId: 5, name: '云朵抱枕靠垫', subTitle: '柔软亲肤，居家好物', price: 69, originalPrice: 129, image: '/static/product-skincare.jpg', sales: 2600, tags: ['包邮'], spec: { '材质': '短毛绒', '填充': 'PP棉', '尺寸': '45x45cm', '产地': '中国' }, onSale: false },
];

const CATEGORY_SEEDS = [
  { id: 1, name: '鞋服', sort: 1 },
  { id: 2, name: '箱包', sort: 2 },
  { id: 3, name: '数码', sort: 3 },
  { id: 4, name: '美妆', sort: 4 },
  { id: 5, name: '家居', sort: 5 },
];

let skuSeq = 10000;
let productSeq = 0;
let cartSeq = 0;
let addressSeq = 0;
let orderSeq = 10000;
let favoriteSeq = 0;
let orderItemSeq = 9000;

const state = {
  member: null,
  products: [],
  cartItems: [],
  addresses: [],
  orders: [],
  favorites: [],
  categories: CATEGORY_SEEDS,
  banners: [],
  themes: [],
  promises: ['正品保障', '7天无理由', '极速发货'],
};

function buildSku(productId, attrs, price) {
  skuSeq += 1;
  const skuText = attrs.map((a) => a.value).join('；');
  const stock = productId === 1 && attrs.some((a) => a.name === '颜色' && a.value === '珊瑚粉') && attrs.some((a) => a.name === '尺码' && a.value === '39') ? 2 : 50 + ((skuSeq * 7) % 150);
  return { id: skuSeq, attrs, skuText, price, stock, image: '', lockStock: 0 };
}

function buildSkus(productId, attrGroups, price) {
  const combos = attrGroups.reduce(
    (acc, group) => acc.flatMap((combo) => group.values.map((v) => [...combo, { name: group.name, value: v }])),
    [[]]
  );
  return combos.map((attrs) => buildSku(productId, attrs, price));
}

function buildProducts() {
  productSeq = 0;
  skuSeq = 10000;
  state.products = PRODUCT_SEEDS.map((seed, index) => {
    productSeq += 1;
    const { categoryId, name, subTitle, price, originalPrice, image, sales, tags, spec } = seed;
    const skus = buildSkus(productSeq, PRODUCT_ATTRS[index].attrs, price);
    return {
      id: productSeq,
      productNo: `P20260831${String(productSeq).padStart(3, '0')}`,
      categoryId,
      name,
      subTitle,
      price,
      originalPrice,
      mainImage: image,
      images: [image],
      detailHtml: `<p>${subTitle}</p><p>精选优质材料，匠心工艺，品质保证。</p>`,
      spec,
      sales,
      shippingFrom: '上海',
      isFreeShipping: true,
      tags,
      skus,
      onSale: seed.onSale !== false,
    };
  });
}

const addressDto = (a) => ({
  id: a.id,
  name: a.name,
  phone: a.phone,
  province: a.province,
  city: a.city,
  district: a.district,
  detail: a.detail,
  isDefault: a.isDefault,
  regionText: a.regionText,
});

function receiverDto(a) {
  return { name: a.name, phone: a.phone, regionText: a.regionText, detail: a.detail };
}

const cartItemDto = (item) => {
  const product = state.products.find((p) => p.id === item.productId);
  const cart = {
    id: item.id,
    productId: item.productId,
    skuId: item.skuId,
    name: item.name,
    skuText: item.skuText,
    price: item.price,
    quantity: item.quantity,
    image: item.image,
    selected: item.selected,
    stock: item.stock,
    onSale: product ? product.onSale !== false : false,
  };
  return cart;
};

function findSku(skuId) {
  for (const p of state.products) {
    const sku = p.skus.find((s) => s.id === skuId);
    if (sku) return { product: p, sku };
  }
  return null;
}

const availableStock = (sku) => Math.max(0, sku.stock - sku.lockStock);

function guardQuantity(skuId, quantity) {
  if (!Number.isFinite(quantity) || quantity < 1) {
    throw error(400, 'quantity 必须为不小于 1 的整数');
  }
  const found = findSku(skuId);
  if (!found) throw error(404, 'SKU 不存在');
  const { product, sku } = found;
  if (!product.onSale) throw error(1102, '商品已下架');
  if (quantity > 99) throw error(1201, '数量超出单次限购（最大 99）', { maxQuantity: 99 });
  const avail = availableStock(sku);
  if (quantity > avail) throw error(1104, '库存不足', { skuId, availableStock: avail });
}

function ensureAuth(token) {
  if (!token || token !== state.member.token) {
    throw error(401, '未登录或登录过期');
  }
  return state.member;
}

function cartItemAvailable(item) {
  const found = findSku(item.skuId);
  return !!found && found.product.onSale !== false && availableStock(found.sku) > 0;
}

function calcCartTotals() {
  const selected = state.cartItems.filter((item) => item.selected && cartItemAvailable(item));
  return {
    totalPrice: Math.round(selected.reduce((sum, item) => sum + item.price * item.quantity, 0) * 100) / 100,
    totalQuantity: selected.reduce((sum, item) => sum + item.quantity, 0),
  };
}

function refreshCartStock() {
  state.cartItems.forEach((item) => {
    const found = findSku(item.skuId);
    item.stock = found ? availableStock(found.sku) : 0;
  });
}

const orderDto = (order, { detail = false } = {}) => {
  const dto = {
    id: order.id,
    orderNo: order.orderNo,
    status: order.status,
    statusText: STATUS_TEXT[order.status],
    totalAmount: order.totalAmount,
    freight: order.freight,
    payAmount: order.payAmount,
    receiver: order.receiver,
    items: order.items.map((item) => ({
      id: item.id,
      productName: item.productName,
      skuText: item.skuText,
      price: item.price,
      quantity: item.quantity,
      image: item.image,
    })),
    createTime: order.createTime,
  };
  if (detail) {
    dto.statusDesc = STATUS_DESC[order.status];
    dto.payType = order.payType;
    dto.payTime = order.payTime;
    dto.shipTime = order.shipTime;
    dto.finishTime = order.finishTime;
  }
  dto.availableActions = computeActions(order.status);
  return dto;
};

function computeActions(status) {
  if (status === 'pending') return ['pay', 'cancel', 'buyAgain'];
  if (status === 'paid') return ['remind', 'refund', 'buyAgain'];
  if (status === 'shipped') return ['confirm', 'refund', 'buyAgain'];
  if (status === 'completed') return ['refund', 'buyAgain'];
  if (status === 'cancelled') return ['buyAgain'];
  if (status === 'refund') return ['buyAgain'];
  return [];
}

function calcOrderAmounts(skus) {
  const totalAmount = skus.reduce((sum, s) => sum + s.price * s.quantity, 0);
  const freight = 0; // P0 阶段统一免邮，P1 接入真实运费规则
  return {
    totalAmount: Math.round(totalAmount * 100) / 100,
    freight,
    payAmount: Math.round((totalAmount + freight) * 100) / 100,
  };
}

function generateOrderNo(date) {
  const n = date.getFullYear() + pad(date.getMonth() + 1) + pad(date.getDate()) + pad(date.getHours()) + pad(date.getMinutes()) + pad(date.getSeconds());
  const rand = String(Math.floor(Math.random() * 900) + 100);
  return 'K' + n + rand;
}

function buildOrderFromItems({ address, productItems }) {
  orderSeq += 1;
  const now = new Date();
  const amounts = calcOrderAmounts(productItems);
  const itemSkus = productItems.map((p) => p.skuId);
  const order = {
    id: orderSeq,
    orderNo: generateOrderNo(now),
    status: 'pending',
    items: productItems.map((productItem) => {
      orderItemSeq += 1;
      return {
        id: orderItemSeq,
        productName: productItem.name,
        skuText: productItem.skuText,
        price: productItem.price,
        quantity: productItem.quantity,
        image: productItem.image,
      };
    }),
    itemSkus,
    totalAmount: amounts.totalAmount,
    freight: amounts.freight,
    payAmount: amounts.payAmount,
    receiver: receiverDto(address),
    payType: null,
    payTime: null,
    shipTime: null,
    finishTime: null,
    createTime: nowText(),
  };
  state.orders.unshift(order);
  return order;
}

function preoccupyStock(productItems) {
  productItems.forEach((productItem) => {
    const found = findSku(productItem.skuId);
    if (found) found.sku.lockStock += productItem.quantity;
  });
}

function releaseStock(order) {
  order.items.forEach((item, index) => {
    const skuId = order.itemSkus ? order.itemSkus[index] : null;
    if (!skuId) return;
    const found = findSku(skuId);
    if (found) found.sku.lockStock = Math.max(0, found.sku.lockStock - item.quantity);
  });
}

function reset() {
  buildProducts();
  cartSeq = 0;
  addressSeq = 0;
  orderSeq = 10000;
  orderItemSeq = 9000;
  favoriteSeq = 0;

  state.member = {
    id: 1,
    nickname: '快乐购物家',
    avatar: '',
    memberLevel: 'gold',
    memberLevelText: '黄金会员',
    points: 2680,
    couponCount: 5,
    phone: '13812345678',
    token: generateToken(),
  };

  state.cartItems = [
    { id: ++cartSeq, productId: 1, skuId: findSkuByText(1, [{ name: '颜色', value: '云雾白' }, { name: '尺码', value: '40' }]), name: '潮流运动鞋', skuText: '云雾白；40', price: 299, quantity: 1, image: '/static/product-sneakers.jpg', selected: false, stock: 88 },
    { id: ++cartSeq, productId: 3, skuId: findSkuByText(3, [{ name: '颜色', value: '棕色' }, { name: '尺码', value: '均码' }]), name: '简约单肩包', skuText: '棕色', price: 159, quantity: 2, image: '/static/product-bag.jpg', selected: false, stock: 88 },
    { id: ++cartSeq, productId: 7, skuId: findSkuByText(7, [{ name: '包装', value: '礼盒装' }, { name: '规格', value: '标准装' }]), name: '保湿护肤套装', skuText: '礼盒装', price: 219, quantity: 1, image: '/static/product-skincare.jpg', selected: false, stock: 88 },
    { id: ++cartSeq, productId: 10, skuId: findSkuByText(10, [{ name: '颜色', value: '云朵白' }, { name: '规格', value: '均码' }]), name: '云朵抱枕靠垫', skuText: '云朵白', price: 69, quantity: 1, image: '/static/product-skincare.jpg', selected: false, stock: 88 },
  ];
  refreshCartStock();

  state.addresses = [
    { id: ++addressSeq, name: '王小悦', phone: '13812345678', province: '上海市', city: '上海市', district: '浦东新区', detail: '张江高科技园区 1 号楼 501 室', isDefault: true, regionText: '上海市 上海市 浦东新区', createdAt: '2026-08-20 10:00:00' },
  ];
  for (let i = 2; i <= 19; i += 1) {
    const district = i % 2 ? '徐汇区' : '静安区';
    state.addresses.push({
      id: ++addressSeq,
      name: '测试用户' + i,
      phone: '139' + String(10000000 + i * 7),
      province: '上海市',
      city: '上海市',
      district,
      detail: '测试地址 ' + i + ' 号',
      isDefault: false,
      regionText: '上海市 上海市 ' + district,
      createdAt: '2026-08-19 00:' + String(i).padStart(2, '0') + ':00',
    });
  }

  const defaultAddress = state.addresses[0];
  state.orders = [
    {
      id: ++orderSeq,
      orderNo: 'K20260830142003001',
      status: 'pending',
      items: [{ id: ++orderItemSeq, productName: '潮流运动鞋', skuText: '云雾白；40', price: 299, quantity: 1, image: '/static/product-sneakers.jpg' }],
      itemSkus: [findSkuByText(1, [{ name: '颜色', value: '云雾白' }, { name: '尺码', value: '40' }])],
      totalAmount: 299, freight: 0, payAmount: 299,
      receiver: receiverDto(defaultAddress),
      payType: null, payTime: null, shipTime: null, finishTime: null,
      createTime: '2026-08-30 14:20:03',
    },
    {
      id: ++orderSeq,
      orderNo: 'K20260829100512999',
      status: 'paid',
      items: [{ id: ++orderItemSeq, productName: '简约单肩包', skuText: '棕色', price: 159, quantity: 2, image: '/static/product-bag.jpg' }],
      itemSkus: [findSkuByText(3, [{ name: '颜色', value: '棕色' }, { name: '尺码', value: '均码' }])],
      totalAmount: 318, freight: 0, payAmount: 318,
      receiver: receiverDto(defaultAddress),
      payType: 'mock', payTime: '2026-08-29 10:05:30', shipTime: null, finishTime: null,
      createTime: '2026-08-29 10:05:12',
    },
    {
      id: ++orderSeq,
      orderNo: 'K20260827093022066',
      status: 'shipped',
      items: [{ id: ++orderItemSeq, productName: '保湿护肤套装', skuText: '礼盒装', price: 219, quantity: 1, image: '/static/product-skincare.jpg' }],
      itemSkus: [findSkuByText(7, [{ name: '包装', value: '礼盒装' }, { name: '规格', value: '标准装' }])],
      totalAmount: 219, freight: 0, payAmount: 219,
      receiver: receiverDto(defaultAddress),
      payType: 'mock', payTime: '2026-08-27 09:30:45', shipTime: '2026-08-28 11:00:00', finishTime: null,
      createTime: '2026-08-27 09:30:22',
    },
    {
      id: ++orderSeq,
      orderNo: 'K20260825081507088',
      status: 'completed',
      items: [{ id: ++orderItemSeq, productName: '真无线蓝牙耳机', skuText: '云雾白', price: 259, quantity: 1, image: '/static/product-headphones.jpg' }],
      itemSkus: [findSkuByText(6, [{ name: '颜色', value: '云雾白' }, { name: '版本', value: '标准版' }])],
      totalAmount: 259, freight: 0, payAmount: 259,
      receiver: receiverDto(defaultAddress),
      payType: 'mock', payTime: '2026-08-25 08:15:20', shipTime: '2026-08-25 14:00:00', finishTime: '2026-08-28 09:00:00',
      createTime: '2026-08-25 08:15:07',
    },
    {
      id: ++orderSeq,
      orderNo: 'K20260822173011321',
      status: 'cancelled',
      items: [{ id: ++orderItemSeq, productName: '北欧风香薰套装', skuText: '森林', price: 89, quantity: 1, image: '/static/product-skincare.jpg' }],
      itemSkus: [findSkuByText(9, [{ name: '香型', value: '森林' }, { name: '规格', value: '均码' }])],
      totalAmount: 89, freight: 0, payAmount: 89,
      receiver: receiverDto(defaultAddress),
      payType: null, payTime: null, shipTime: null, finishTime: null,
      createTime: '2026-08-22 17:30:11',
    },
  ];

  state.favorites = [
    { id: ++favoriteSeq, productId: findProductByName('潮流运动鞋').id },
    { id: ++favoriteSeq, productId: findProductByName('简约单肩包').id },
    { id: ++favoriteSeq, productId: findProductByName('保湿护肤套装').id },
  ];

  state.banners = [
    { id: 1, title: '夏季新品 火热开售', tag: '限时特惠', image: '/static/hero-banner.jpg', linkType: 'page', linkValue: '/pages/products/products' },
    { id: 2, title: '会员日 积分翻倍', tag: '会员专享', image: '/static/hero-banner.jpg', linkType: 'page', linkValue: '/pages/me/me' },
    { id: 3, title: '通勤好物 一站购齐', tag: '每日精选', image: '/static/hero-banner.jpg', linkType: 'category', linkValue: '2' },
  ];

  state.themes = [
    { id: 1, name: '夏季焕新', desc: '轻盈出行', image: '/static/hero-banner.jpg', linkType: 'category', linkValue: '1' },
    { id: 2, name: '会员专享', desc: '积分抵现', image: '/static/hero-banner.jpg', linkType: 'page', linkValue: '/pages/me/me' },
    { id: 3, name: '通勤百搭', desc: '精致搭配', image: '/static/hero-banner.jpg', linkType: 'category', linkValue: '2' },
    { id: 4, name: '影音数码', desc: '沉浸体验', image: '/static/hero-banner.jpg', linkType: 'category', linkValue: '3' },
  ];
}

function findSkuByText(productId, attrs) {
  const product = state.products.find((p) => p.id === productId);
  const sku = product && product.skus.find((s) => attrs.every((a) => s.attrs.some((sa) => sa.name === a.name && sa.value === a.value)));
  return sku ? sku.id : null;
}

function findProductByName(name) {
  return state.products.find((p) => p.name === name);
}

function findOrder(id) {
  const order = state.orders.find((o) => o.id === Number(id));
  if (!order) throw error(404, '订单不存在');
  return order;
}

function paginate(list, { page = 1, pageSize = 10 } = {}) {
  const pageNum = Number(page) || 1;
  const size = Math.min(Number(pageSize) || 10, 50);
  const total = list.length;
  const items = list.slice((pageNum - 1) * size, pageNum * size);
  return { list: items, total, page: pageNum, pageSize: size, hasMore: pageNum * size < total };
}

function validateAddress({ name, phone, province, city, district, detail }) {
  if (!name || !String(name).trim()) throw error(400, '姓名不能为空');
  if (!/^1\d{10}$/.test(phone || '')) throw error(400, '手机号格式不正确');
  if (!province || !city || !district) throw error(400, '省市区不能为空');
  if (!detail || !String(detail).trim()) throw error(400, '详细地址不能为空');
}

function sortAddresses(list) {
  return [...list].sort((a, b) => {
    if (a.isDefault !== b.isDefault) return a.isDefault ? -1 : 1;
    return b.createdAt.localeCompare(a.createdAt);
  });
}

function generateToken() {
  return 'mock-token-' + Date.now() + '-' + Math.floor(Math.random() * 100000);
}

function toPersistToken() {
  if (!useMock) return;
  try {
    uni.setStorageSync(TOKEN_KEY, state.member.token);
  } catch (e) {
    return;
  }
}

reset();
if (useMock) toPersistToken();

export const store = {
  ensureAuth,
  toPersistToken,

  getCategories() {
    return { list: state.categories.map((c) => ({ id: c.id, name: c.name, sort: c.sort })) };
  },

  getProducts({ categoryId, keyword, sort, order, page, pageSize }) {
    let list = state.products.filter((p) => {
      if (!p.onSale) return false;
      if (categoryId && p.categoryId !== Number(categoryId)) return false;
      if (keyword) {
        const kw = String(keyword).trim().toLowerCase();
        if (!kw) return true;
        if (!(p.name.toLowerCase().includes(kw) || p.subTitle.toLowerCase().includes(kw))) return false;
      }
      return true;
    });
    const sortKey = sort === 'sales' ? 'sales' : sort === 'price' ? 'price' : null;
    if (sortKey) {
      const dir = order === 'asc' ? 1 : -1;
      list = [...list].sort((a, b) => (a[sortKey] - b[sortKey]) * dir);
    }
    const paged = paginate(list, { page, pageSize });
    return {
      list: paged.list.map((p) => ({
        id: p.id,
        productNo: p.productNo,
        name: p.name,
        subTitle: p.subTitle,
        price: p.price,
        originalPrice: p.originalPrice,
        mainImage: p.mainImage,
        sales: p.sales,
        tags: p.tags,
      })),
      total: paged.total,
      page: paged.page,
      pageSize: paged.pageSize,
      hasMore: paged.hasMore,
    };
  },

  getProductDetail(id) {
    const product = state.products.find((p) => p.id === Number(id));
    if (!product) throw error(404, '商品不存在');
    if (!product.onSale) throw error(1102, '商品已下架');
    return {
      id: product.id,
      productNo: product.productNo,
      categoryId: product.categoryId,
      name: product.name,
      subTitle: product.subTitle,
      price: product.price,
      originalPrice: product.originalPrice,
      mainImage: product.mainImage,
      images: product.images,
      detailHtml: product.detailHtml,
      spec: product.spec,
      sales: product.sales,
      shippingFrom: product.shippingFrom,
      isFreeShipping: product.isFreeShipping,
      tags: product.tags,
      skus: product.skus.map((s) => ({
        id: s.id,
        attrs: s.attrs,
        skuText: s.skuText,
        price: s.price,
        stock: availableStock(s),
        image: s.image,
      })),
      promises: state.promises,
    };
  },

  homeIndex(authedMember) {
    return {
      member: authedMember
        ? { points: authedMember.points, couponCount: authedMember.couponCount, nickname: authedMember.nickname }
        : null,
      banners: state.banners,
      themes: state.themes,
      promises: state.promises,
    };
  },

  listCart() {
    refreshCartStock();
    return { list: state.cartItems.map(cartItemDto), ...calcCartTotals() };
  },

  addCartItem({ skuId, quantity = 1, selected = false }) {
    guardQuantity(skuId, quantity);
    const existing = state.cartItems.find((item) => item.skuId === skuId);
    if (existing) {
      const nextQuantity = existing.quantity + quantity;
      guardQuantity(skuId, nextQuantity);
      existing.quantity = nextQuantity;
      existing.selected = selected;
    } else {
      const found = findSku(skuId);
      cartSeq += 1;
      state.cartItems.unshift({
        id: cartSeq,
        productId: found.product.id,
        skuId,
        name: found.product.name,
        skuText: found.sku.skuText,
        price: found.sku.price,
        quantity,
        image: found.product.mainImage,
        selected,
        stock: availableStock(found.sku),
      });
    }
    refreshCartStock();
    return { list: state.cartItems.map(cartItemDto), ...calcCartTotals() };
  },

  updateCartItem(id, { quantity, selected, skuId }) {
    const item = state.cartItems.find((i) => i.id === Number(id));
    if (!item) throw error(404, '购物车项不存在');
    if (skuId !== undefined) {
      const found = findSku(Number(skuId));
      if (!found) throw error(404, 'SKU 不存在');
      if (found.product.id !== item.productId) throw error(400, '不能切换到其他商品的规格');
      if (Number(skuId) === item.skuId) {
        item.skuId = Number(skuId);
      } else {
        const existing = state.cartItems.find((i) => i.skuId === Number(skuId));
        if (existing) {
          const nextQuantity = existing.quantity + item.quantity;
          guardQuantity(Number(skuId), nextQuantity);
          existing.quantity = nextQuantity;
          existing.selected = item.selected;
          state.cartItems = state.cartItems.filter((i) => i.id !== item.id);
        } else {
          guardQuantity(Number(skuId), item.quantity);
          item.skuId = Number(skuId);
          item.skuText = found.sku.skuText;
          item.price = found.sku.price;
          item.stock = availableStock(found.sku);
        }
      }
    }
    if (quantity !== undefined) {
      if (Number(quantity) === 0) {
        state.cartItems = state.cartItems.filter((i) => i.id !== Number(id));
        return { list: state.cartItems.map(cartItemDto), ...calcCartTotals() };
      }
      guardQuantity(item.skuId, Number(quantity));
      item.quantity = Number(quantity);
    }
    if (selected !== undefined) {
      item.selected = !!selected;
    }
    refreshCartStock();
    return { list: state.cartItems.map(cartItemDto), ...calcCartTotals() };
  },

  deleteCartItems(ids) {
    const idList = Array.isArray(ids) ? ids.map(Number) : [];
    if (!idList.length) throw error(400, 'ids 不能为空');
    state.cartItems = state.cartItems.filter((i) => !idList.includes(i.id));
    return { list: state.cartItems.map(cartItemDto), ...calcCartTotals() };
  },

  selectAll(selected) {
    state.cartItems.forEach((i) => {
      if (!selected) {
        i.selected = false;
        return;
      }
      if (!cartItemAvailable(i)) return;
      i.selected = true;
    });
    return { list: state.cartItems.map(cartItemDto), ...calcCartTotals() };
  },

  listAddresses() {
    return { list: sortAddresses(state.addresses).map(addressDto) };
  },

  addAddress(payload) {
    const { name, phone, province, city, district, detail, isDefault } = payload;
    validateAddress({ name, phone, province, city, district, detail });
    if (state.addresses.length >= 20) throw error(1301, '地址数量已达上限（20 条）', { maxCount: 20 });
    const first = state.addresses.length === 0;
    addressSeq += 1;
    const address = {
      id: addressSeq,
      name: String(name).trim(),
      phone,
      province,
      city,
      district,
      detail: String(detail).trim(),
      isDefault: !!(isDefault || first),
      regionText: `${province} ${city} ${district}`,
      createdAt: nowText(),
    };
    if (address.isDefault) {
      state.addresses.forEach((a) => {
        a.isDefault = false;
      });
    }
    state.addresses.push(address);
    return addressDto(address);
  },

  updateAddress(id, payload) {
    const address = state.addresses.find((a) => a.id === Number(id));
    if (!address) throw error(404, '地址不存在');
    const { name, phone, province, city, district, detail, isDefault } = payload;
    validateAddress({ name, phone, province, city, district, detail });
    address.name = String(name).trim();
    address.phone = phone;
    address.province = province;
    address.city = city;
    address.district = district;
    address.detail = String(detail).trim();
    address.regionText = `${province} ${city} ${district}`;
    if (isDefault) {
      state.addresses.forEach((a) => {
        a.isDefault = a.id === Number(id);
      });
    }
    return addressDto(address);
  },

  deleteAddress(id) {
    const target = state.addresses.find((a) => a.id === Number(id));
    if (!target) throw error(404, '地址不存在');
    state.addresses = state.addresses.filter((a) => a.id !== Number(id));
    if (target.isDefault && state.addresses.length) {
      const latest = [...state.addresses].sort((a, b) => b.createdAt.localeCompare(a.createdAt))[0];
      latest.isDefault = true;
    }
    return { list: state.addresses.map(addressDto) };
  },

  setDefaultAddress(id) {
    const address = state.addresses.find((a) => a.id === Number(id));
    if (!address) throw error(404, '地址不存在');
    state.addresses.forEach((a) => {
      a.isDefault = a.id === Number(id);
    });
    return { list: state.addresses.map(addressDto) };
  },

  listAddressesForPreview() {
    return sortAddresses(state.addresses).map((a) => ({
      id: a.id,
      name: a.name,
      phone: a.phone,
      regionText: a.regionText,
      detail: a.detail,
      isDefault: a.isDefault,
    }));
  },

  previewOrder(cartItemIds) {
    const ids = cartItemIds ? String(cartItemIds).split(',').map(Number) : null;
    let selectedItems = ids ? state.cartItems.filter((i) => ids.includes(i.id)) : state.cartItems.filter((i) => i.selected);
    if (!selectedItems.length) throw error(400, '请先选择要结算的商品');
    const unavailables = [];
    for (const item of selectedItems) {
      const found = findSku(item.skuId);
      if (!found || !found.product.onSale || availableStock(found.sku) <= 0) {
        unavailables.push({ cartItemId: item.id, productId: item.productId, skuId: item.skuId, name: item.name, skuText: item.skuText });
      }
    }
    if (unavailables.length) throw error(1203, '部分商品已下架或库存不足', { unavailables });
    for (const item of selectedItems) {
      const found = findSku(item.skuId);
      if (availableStock(found.sku) < item.quantity) {
        throw error(1104, '库存不足', { skuId: found.sku.id, availableStock: availableStock(found.sku) });
      }
    }
    const items = selectedItems.map((item) => ({
      cartItemId: item.id,
      productId: item.productId,
      skuId: item.skuId,
      name: item.name,
      skuText: item.skuText,
      price: item.price,
      quantity: item.quantity,
      image: item.image,
      stock: item.stock,
    }));
    const amounts = calcOrderAmounts(items);
    return {
      items,
      totalAmount: amounts.totalAmount,
      freight: amounts.freight,
      payAmount: amounts.payAmount,
      addresses: this.listAddressesForPreview(),
    };
  },

  createOrder({ addressId, items }) {
    if (!Array.isArray(items) || !items.length) throw error(400, '订单商品不能为空');
    const address = state.addresses.find((a) => a.id === Number(addressId));
    if (!address) throw error(404, '地址不存在');
    const productItems = [];
    for (const req of items) {
      const quantity = Number(req.quantity);
      guardQuantity(req.skuId, quantity);
      const found = findSku(req.skuId);
      const cartItem = state.cartItems.find((c) => c.skuId === req.skuId);
      productItems.push({
        skuId: req.skuId,
        name: found.product.name,
        skuText: found.sku.skuText,
        price: found.sku.price,
        quantity,
        image: found.product.mainImage,
      });
      if (cartItem) {
        state.cartItems = state.cartItems.filter((c) => c.skuId !== req.skuId);
      }
    }
    preoccupyStock(productItems);
    const order = buildOrderFromItems({ address, productItems });
    return orderDto(order, { detail: true });
  },

  previewDirectOrder({ skuId, quantity }) {
    const qty = Number(quantity);
    guardQuantity(skuId, qty);
    const found = findSku(skuId);
    const item = {
      cartItemId: 0,
      productId: found.product.id,
      skuId: found.sku.id,
      name: found.product.name,
      skuText: found.sku.skuText,
      price: found.sku.price,
      quantity: qty,
      image: found.product.mainImage,
      stock: availableStock(found.sku),
    };
    const amounts = calcOrderAmounts([item]);
    return {
      items: [item],
      totalAmount: amounts.totalAmount,
      freight: amounts.freight,
      payAmount: amounts.payAmount,
      addresses: this.listAddressesForPreview(),
    };
  },

  createDirectOrder({ addressId, skuId, quantity }) {
    const qty = Number(quantity);
    guardQuantity(skuId, qty);
    const address = state.addresses.find((a) => a.id === Number(addressId));
    if (!address) throw error(404, '地址不存在');
    const found = findSku(skuId);
    const productItems = [
      {
        skuId: found.sku.id,
        name: found.product.name,
        skuText: found.sku.skuText,
        price: found.sku.price,
        quantity: qty,
        image: found.product.mainImage,
      },
    ];
    preoccupyStock(productItems);
    const order = buildOrderFromItems({ address, productItems });
    return orderDto(order, { detail: true });
  },

  listOrders({ status, page, pageSize }) {
    let list = state.orders;
    if (status) {
      list = list.filter((o) => o.status === status);
    }
    const paged = paginate(list, { page, pageSize });
    return {
      list: paged.list.map((o) => orderDto(o)),
      total: paged.total,
      page: paged.page,
      pageSize: paged.pageSize,
      hasMore: paged.hasMore,
    };
  },

  getOrderDetail(id) {
    return orderDto(findOrder(id), { detail: true });
  },

  payOrder(id, { payType }) {
    const order = findOrder(id);
    if (order.status !== 'pending') throw error(409, '订单已支付，请勿重复支付');
    if (payType === 'wechat') {
      return { payParams: { timeStamp: '1', nonceStr: 'mock', package: 'mock', signType: 'RSA', paySign: 'mock' } };
    }
    order.status = 'paid';
    order.payType = 'mock';
    order.payTime = nowText();
    return orderDto(order, { detail: true });
  },

  cancelOrder(id, { reason }) {
    const order = findOrder(id);
    if (order.status !== 'pending') throw error(1402, '订单状态不允许该操作');
    order.status = 'cancelled';
    releaseStock(order);
    return orderDto(order, { detail: true });
  },

  refundOrder(id, { reason, type }) {
    const order = findOrder(id);
    if (!['paid', 'shipped', 'completed'].includes(order.status)) {
      throw error(1402, '订单状态不允许申请售后');
    }
    order.refundReason = reason || '不符合预期';
    order.refundType = type || (order.status === 'paid' ? 'refund' : 'return');
    order.refundTime = nowText();
    order.status = 'refund';
    releaseStock(order);
    return orderDto(order, { detail: true });
  },

  remindOrder(id) {
    const order = findOrder(id);
    if (order.status !== 'paid') throw error(1402, '订单状态不允许该操作');
    return { reminded: true };
  },

  confirmOrder(id) {
    const order = findOrder(id);
    if (order.status !== 'shipped') throw error(1402, '订单状态不允许该操作');
    order.status = 'completed';
    order.finishTime = nowText();
    if (state.member) state.member.points += Math.floor(order.payAmount);
    return orderDto(order, { detail: true });
  },

  buyAgain(id) {
    const order = findOrder(id);
    const defaultAddress = state.addresses.find((a) => a.isDefault) || state.addresses[0];
    if (!defaultAddress) throw error(400, '暂无收货地址，请先添加');
    const productItems = [];
    order.items.forEach((item, index) => {
      const skuId = order.itemSkus ? order.itemSkus[index] : null;
      guardQuantity(skuId, item.quantity);
      const found = findSku(skuId);
      productItems.push({
        skuId,
        name: found.product.name,
        skuText: found.sku.skuText,
        price: found.sku.price,
        quantity: item.quantity,
        image: found.product.mainImage,
      });
    });
    preoccupyStock(productItems);
    const newOrder = buildOrderFromItems({ address: defaultAddress, productItems });
    return orderDto(newOrder, { detail: true });
  },

  orderStats() {
    const stats = { pending: 0, paid: 0, shipped: 0, refund: 0 };
    state.orders.forEach((o) => {
      if (stats[o.status] !== undefined) stats[o.status] += 1;
    });
    return stats;
  },

  listFavorites({ page, pageSize }) {
    const paged = paginate(state.favorites, { page, pageSize });
    return {
      list: paged.list.map((f) => {
        const product = state.products.find((p) => p.id === f.productId);
        return {
          id: f.id,
          productId: f.productId,
          name: product ? product.name : '',
          price: product ? product.price : 0,
          image: product ? product.mainImage : '',
        };
      }),
      total: paged.total,
      page: paged.page,
      pageSize: paged.pageSize,
      hasMore: paged.hasMore,
    };
  },

  addFavorite(productId) {
    const product = state.products.find((p) => p.id === Number(productId));
    if (!product || !product.onSale) throw error(1102, '商品已下架');
    const exists = state.favorites.find((f) => f.productId === Number(productId));
    if (exists) return { favorited: true, existed: true };
    favoriteSeq += 1;
    state.favorites.unshift({ id: favoriteSeq, productId: Number(productId) });
    return { favorited: true, existed: false };
  },

  removeFavorite(productId) {
    state.favorites = state.favorites.filter((f) => f.productId !== Number(productId));
    return { favorited: false };
  },

  memberOverview() {
    return {
      member: {
        id: state.member.id,
        nickname: state.member.nickname,
        avatar: state.member.avatar,
        memberLevel: state.member.memberLevel,
        memberLevelText: state.member.memberLevelText,
        points: state.member.points,
        couponCount: state.member.couponCount,
      },
      orderStats: this.orderStats(),
    };
  },

  updateProfile({ nickname, avatar }) {
    if (!nickname || String(nickname).trim().length < 1 || String(nickname).trim().length > 20) {
      throw error(1003, '昵称长度需为 1-20 字');
    }
    if (avatar && !/^https?:\/\//.test(avatar)) {
      throw error(1003, '头像必须为有效的 URL');
    }
    state.member.nickname = String(nickname).trim();
    if (avatar) state.member.avatar = avatar;
    return { nickname: state.member.nickname, avatar: state.member.avatar };
  },

  login({ code, nickname, avatar, phone } = {}) {
    if (!code || !String(code).trim()) {
      throw error(1001, '登录 code 无效');
    }
    if (nickname) state.member.nickname = String(nickname).trim();
    if (avatar) state.member.avatar = avatar;
    if (phone) state.member.phone = phone;
    state.member.token = generateToken();
    this.toPersistToken();
    return {
      token: state.member.token,
      expiresIn: 604800,
      member: {
        id: state.member.id,
        nickname: state.member.nickname,
        avatar: state.member.avatar,
        memberLevel: state.member.memberLevel,
        points: state.member.points,
        phone: state.member.phone,
      },
    };
  },

  logout() {
    state.member.token = '';
    try {
      uni.removeStorageSync(TOKEN_KEY);
    } catch (e) {
      return;
    }
    return { loggedOut: true };
  },
};