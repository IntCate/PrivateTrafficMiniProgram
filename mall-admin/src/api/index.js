import request from '@/utils/request'

export const login = (data) => request.post('/login', data)

export const listAdmins = (params) => request.get('/admins', { params })
export const createAdmin = (data) => request.post('/admins', data)
export const updateAdminStatus = (id, data) => request.put(`/admins/${id}/status`, data)

export const listProducts = (params) => request.get('/products', { params })
export const getProduct = (id) => request.get(`/products/${id}`)
export const createProduct = (data) => request.post('/products', data)
export const updateProduct = (id, data) => request.put(`/products/${id}`, data)
export const updateProductStatus = (id, data) => request.put(`/products/${id}/status`, data)
export const deleteProduct = (id) => request.delete(`/products/${id}`)

export const listProductSkus = (productId) => request.get(`/products/${productId}/skus`)
export const createProductSku = (productId, data) => request.post(`/products/${productId}/skus`, data)
export const updateProductSku = (productId, skuId, data) => request.put(`/products/${productId}/skus/${skuId}`, data)
export const deleteProductSku = (productId, skuId) => request.delete(`/products/${productId}/skus/${skuId}`)

export const listCategories = () => request.get('/categories')
export const createCategory = (data) => request.post('/categories', data)
export const updateCategory = (id, data) => request.put(`/categories/${id}`, data)
export const deleteCategory = (id) => request.delete(`/categories/${id}`)

export const listOrders = (params) => request.get('/orders', { params })
export const getOrder = (id) => request.get(`/orders/${id}`)
export const shipOrder = (id, data) => request.put(`/orders/${id}/ship`, data)

export const listMembers = (params) => request.get('/members', { params })
export const updateMemberStatus = (id, data) => request.put(`/members/${id}/status`, data)

export const listBanners = () => request.get('/banners')
export const createBanner = (data) => request.post('/banners', data)
export const updateBanner = (id, data) => request.put(`/banners/${id}`, data)
export const deleteBanner = (id) => request.delete(`/banners/${id}`)

// 通用图片上传：POST /admin/api/upload，category 支持 banner/product/category，返回可用 URL
export const uploadImage = (file, category = 'banner') => {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('category', category)
  return request.post('/upload', fd)
}

export const listCoupons = () => request.get('/coupons')
export const createCoupon = (data) => request.post('/coupons', data)
export const updateCoupon = (id, data) => request.put(`/coupons/${id}`, data)
export const grantCoupon = (id, data) => request.post(`/coupons/${id}/grant`, data)

export const listAfterSales = (params) => request.get('/after-sales', { params })
export const auditAfterSale = (id, data) => request.put(`/after-sales/${id}/audit`, data)

export const getDashboardSummary = () => request.get('/dashboard/summary')
export const getDashboardTrend = () => request.get('/dashboard/trend')

export const listConfigs = () => request.get('/configs')
export const updateConfig = (key, data) => request.put(`/configs/${key}`, data)
