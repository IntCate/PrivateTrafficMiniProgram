import { request } from './request';

export const authApi = {
  login: (code, nickname, avatar) =>
    request({ url: '/api/auth/login', method: 'POST', data: { code, nickname, avatar } }),
  logout: () => request({ url: '/api/auth/logout', method: 'POST' }),
};

export const homeApi = {
  getIndex: () => request({ url: '/api/home/index', method: 'GET' }),
};

export const categoryApi = {
  list: () => request({ url: '/api/categories', method: 'GET' }),
};

export const productApi = {
  list: ({ categoryId, keyword, sort, order, page, pageSize } = {}) =>
    request({
      url: '/api/products',
      method: 'GET',
      params: { categoryId, keyword, sort, order, page, pageSize },
    }),
  detail: (id) => request({ url: `/api/products/${id}`, method: 'GET' }),
};

export const cartApi = {
  list: () => request({ url: '/api/cart', method: 'GET' }),
  addItem: (skuId, quantity = 1, selected = false) =>
    request({ url: '/api/cart/items', method: 'POST', data: { skuId, quantity, selected } }),
  updateItem: (id, { quantity, selected, skuId } = {}) =>
    request({ url: `/api/cart/items/${id}`, method: 'PUT', data: { quantity, selected, skuId } }),
  removeItems: (ids) => request({ url: '/api/cart/items', method: 'DELETE', data: { ids } }),
  selectAll: (selected) => request({ url: '/api/cart/select-all', method: 'PUT', data: { selected } }),
};

export const addressApi = {
  list: () => request({ url: '/api/addresses', method: 'GET' }),
  add: (payload) => request({ url: '/api/addresses', method: 'POST', data: payload }),
  update: (id, payload) => request({ url: `/api/addresses/${id}`, method: 'PUT', data: payload }),
  remove: (id) => request({ url: `/api/addresses/${id}`, method: 'DELETE' }),
  setDefault: (id) => request({ url: `/api/addresses/${id}/default`, method: 'PUT' }),
};

export const orderApi = {
  preview: (cartItemIds) =>
    request({
      url: '/api/orders/preview',
      method: 'GET',
      params: cartItemIds ? { cartItemIds: cartItemIds.join(',') } : {},
    }),
  previewDirect: (skuId, quantity) =>
    request({ url: '/api/orders/preview-direct', method: 'GET', params: { skuId, quantity } }),
  createDirect: (payload) => request({ url: '/api/orders/direct', method: 'POST', data: payload }),
  create: (payload) => request({ url: '/api/orders', method: 'POST', data: payload }),
  list: ({ status, page, pageSize } = {}) =>
    request({ url: '/api/orders', method: 'GET', params: { status, page, pageSize } }),
  detail: (id) => request({ url: `/api/orders/${id}`, method: 'GET' }),
  pay: (id, payType = 'mock') =>
    request({ url: `/api/orders/${id}/pay`, method: 'POST', data: { payType } }),
  cancel: (id, reason) =>
    request({ url: `/api/orders/${id}/cancel`, method: 'POST', data: { reason } }),
  refund: (id, payload) =>
    request({ url: `/api/after-sales`, method: 'POST', data: { orderId: id, ...payload } }),
  remind: (id) => request({ url: `/api/orders/${id}/remind`, method: 'POST' }),
  confirm: (id) => request({ url: `/api/orders/${id}/confirm`, method: 'POST' }),
  buyAgain: (id) => request({ url: `/api/orders/${id}/buy-again`, method: 'POST' }),
  stats: () => request({ url: '/api/orders/stats', method: 'GET' }),
};

export const favoriteApi = {
  list: ({ page, pageSize } = {}) =>
    request({ url: '/api/favorites', method: 'GET', params: { page, pageSize } }),
  add: (productId) => request({ url: `/api/favorites/${productId}`, method: 'POST' }),
  remove: (productId) => request({ url: `/api/favorites/${productId}`, method: 'DELETE' }),
};

export const memberApi = {
  overview: () => request({ url: '/api/member/overview', method: 'GET' }),
  updateProfile: (payload) => request({ url: '/api/member/profile', method: 'PUT', data: payload }),
};

export default {
  authApi,
  homeApi,
  categoryApi,
  productApi,
  cartApi,
  addressApi,
  orderApi,
  favoriteApi,
  memberApi,
};