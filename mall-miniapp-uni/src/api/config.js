export const useMock = import.meta.env.VITE_USE_MOCK !== 'false';

export const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const TOKEN_KEY = 'mall-token';

// 后端相对路径（/uploads/...）→ 可访问的完整 URL；本地静态资源（/static/...）与绝对 URL 原样返回
export const toAbs = (url) => (url && url.startsWith('/uploads/') ? BASE_URL + url : url);