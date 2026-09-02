import { store } from './store';

function run(handler, auth, ctx) {
  if (auth) {
    ctx.member = store.ensureAuth(ctx.token);
  }
  return handler(ctx, ctx.match);
}

function wrap(handler, auth) {
  return (ctx) => {
    try {
      const data = run(handler, auth, ctx);
      return { code: 0, message: 'ok', data };
    } catch (e) {
      if (e && e.business) {
        return { code: e.code, message: e.message, data: e.data };
      }
      return { code: 500, message: '系统内部错误', data: null };
    }
  };
}

const routes = [
  {
    method: 'POST',
    pattern: /^\/api\/auth\/login$/,
    handler: (ctx) => store.login(ctx.body || {}),
  },
  {
    method: 'POST',
    pattern: /^\/api\/auth\/logout$/,
    auth: true,
    handler: () => store.logout(),
  },
  {
    method: 'GET',
    pattern: /^\/api\/home\/index$/,
    handler: (ctx) => {
      let member = null;
      try {
        member = store.ensureAuth(ctx.token);
      } catch (e) {
        member = null;
      }
      return store.homeIndex(member);
    },
  },
  {
    method: 'GET',
    pattern: /^\/api\/categories$/,
    handler: () => store.getCategories(),
  },
  {
    method: 'GET',
    pattern: /^\/api\/products$/,
    handler: (ctx) => store.getProducts(ctx.params || {}),
  },
  {
    method: 'GET',
    pattern: /^\/api\/products\/(\d+)$/,
    handler: (ctx, match) => store.getProductDetail(match[1]),
  },
  {
    method: 'GET',
    pattern: /^\/api\/cart$/,
    auth: true,
    handler: () => store.listCart(),
  },
  {
    method: 'POST',
    pattern: /^\/api\/cart\/items$/,
    auth: true,
    handler: (ctx) => store.addCartItem(ctx.body || {}),
  },
  {
    method: 'PUT',
    pattern: /^\/api\/cart\/items\/(\d+)$/,
    auth: true,
    handler: (ctx, match) => store.updateCartItem(match[1], ctx.body || {}),
  },
  {
    method: 'DELETE',
    pattern: /^\/api\/cart\/items\/(\d+)$/,
    auth: true,
    handler: (ctx, match) => store.deleteCartItems([match[1]]),
  },
  {
    method: 'DELETE',
    pattern: /^\/api\/cart\/items$/,
    auth: true,
    handler: (ctx) => store.deleteCartItems((ctx.body && ctx.body.ids) || []),
  },
  {
    method: 'PUT',
    pattern: /^\/api\/cart\/select-all$/,
    auth: true,
    handler: (ctx) => store.selectAll((ctx.body || {}).selected),
  },
  {
    method: 'GET',
    pattern: /^\/api\/addresses$/,
    auth: true,
    handler: () => store.listAddresses(),
  },
  {
    method: 'POST',
    pattern: /^\/api\/addresses$/,
    auth: true,
    handler: (ctx) => store.addAddress(ctx.body || {}),
  },
  {
    method: 'PUT',
    pattern: /^\/api\/addresses\/(\d+)$/,
    auth: true,
    handler: (ctx, match) => store.updateAddress(match[1], ctx.body || {}),
  },
  {
    method: 'DELETE',
    pattern: /^\/api\/addresses\/(\d+)$/,
    auth: true,
    handler: (ctx, match) => store.deleteAddress(match[1]),
  },
  {
    method: 'PUT',
    pattern: /^\/api\/addresses\/(\d+)\/default$/,
    auth: true,
    handler: (ctx, match) => store.setDefaultAddress(match[1]),
  },
  {
    method: 'GET',
    pattern: /^\/api\/orders\/preview$/,
    auth: true,
    handler: (ctx) => store.previewOrder((ctx.params || {}).cartItemIds),
  },
  {
    method: 'GET',
    pattern: /^\/api\/orders\/preview-direct$/,
    auth: true,
    handler: (ctx) => store.previewDirectOrder(ctx.params || {}),
  },
  {
    method: 'POST',
    pattern: /^\/api\/orders\/direct$/,
    auth: true,
    handler: (ctx) => store.createDirectOrder(ctx.body || {}),
  },
  {
    method: 'POST',
    pattern: /^\/api\/orders$/,
    auth: true,
    handler: (ctx) => store.createOrder(ctx.body || {}),
  },
  {
    method: 'GET',
    pattern: /^\/api\/orders\/stats$/,
    auth: true,
    handler: () => store.orderStats(),
  },
  {
    method: 'GET',
    pattern: /^\/api\/orders$/,
    auth: true,
    handler: (ctx) => store.listOrders(ctx.params || {}),
  },
  {
    method: 'GET',
    pattern: /^\/api\/orders\/(\d+)$/,
    auth: true,
    handler: (ctx, match) => store.getOrderDetail(match[1]),
  },
  {
    method: 'POST',
    pattern: /^\/api\/orders\/(\d+)\/pay$/,
    auth: true,
    handler: (ctx, match) => store.payOrder(match[1], ctx.body || {}),
  },
  {
    method: 'POST',
    pattern: /^\/api\/orders\/(\d+)\/cancel$/,
    auth: true,
    handler: (ctx, match) => store.cancelOrder(match[1], ctx.body || {}),
  },
  {
    method: 'POST',
    pattern: /^\/api\/orders\/(\d+)\/refund$/,
    auth: true,
    handler: (ctx, match) => store.refundOrder(match[1], ctx.body || {}),
  },
  {
    method: 'POST',
    pattern: /^\/api\/orders\/(\d+)\/remind$/,
    auth: true,
    handler: (ctx, match) => store.remindOrder(match[1]),
  },
  {
    method: 'POST',
    pattern: /^\/api\/orders\/(\d+)\/confirm$/,
    auth: true,
    handler: (ctx, match) => store.confirmOrder(match[1]),
  },
  {
    method: 'POST',
    pattern: /^\/api\/orders\/(\d+)\/buy-again$/,
    auth: true,
    handler: (ctx, match) => store.buyAgain(match[1]),
  },
  {
    method: 'GET',
    pattern: /^\/api\/favorites$/,
    auth: true,
    handler: (ctx) => store.listFavorites(ctx.params || {}),
  },
  {
    method: 'POST',
    pattern: /^\/api\/favorites\/(\d+)$/,
    auth: true,
    handler: (ctx, match) => store.addFavorite(match[1]),
  },
  {
    method: 'DELETE',
    pattern: /^\/api\/favorites\/(\d+)$/,
    auth: true,
    handler: (ctx, match) => store.removeFavorite(match[1]),
  },
  {
    method: 'GET',
    pattern: /^\/api\/member\/overview$/,
    auth: true,
    handler: () => store.memberOverview(),
  },
  {
    method: 'PUT',
    pattern: /^\/api\/member\/profile$/,
    auth: true,
    handler: (ctx) => store.updateProfile(ctx.body || {}),
  },
];

export function mockRequest({ url, method, data, params, token }) {
  const cleanUrl = String(url || '').split('?')[0];
  const queryString = String(url || '').includes('?') ? String(url).split('?')[1] : '';
  const query = { ...(params || {}) };
  if (queryString) {
    queryString.split('&').forEach((pair) => {
      if (!pair) return;
      const [key, value] = pair.split('=');
      query[decodeURIComponent(key)] = decodeURIComponent(value || '');
    });
  }
  const upperMethod = String(method || 'GET').toUpperCase();

  for (const route of routes) {
    if (route.method !== upperMethod) continue;
    const match = cleanUrl.match(route.pattern);
    if (!match) continue;
    const wrapped = wrap(route.handler, !!route.auth);
    return Promise.resolve(
      wrapped({ url: cleanUrl, method: upperMethod, body: data, params: query, token, match }),
    );
  }

  return Promise.resolve({ code: 404, message: `接口不存在: ${upperMethod} ${cleanUrl}`, data: null });
}