export const useMock = import.meta.env.VITE_USE_MOCK !== 'false';

export const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const TOKEN_KEY = 'mall-token';