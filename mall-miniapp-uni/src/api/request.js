import { BASE_URL, useMock, TOKEN_KEY } from './config';
import { mockRequest } from './mock';

function getToken() {
  try {
    return uni.getStorageSync(TOKEN_KEY) || '';
  } catch (e) {
    return '';
  }
}

function handleAuthError() {
  uni.showToast({ title: '登录状态已失效', icon: 'none' });
}

export function request(options) {
  const { url, method = 'GET', data, params } = options;
  const token = getToken();

  if (useMock) {
    return mockRequest({ url, method, data, params, token }).then((res) => {
      if (res.code === 401) {
        handleAuthError();
        return Promise.reject(res);
      }
      if (res.code !== 0) {
        return Promise.reject(res);
      }
      return res.data;
    });
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method,
      data: method === 'GET' ? params : data,
      header: {
        'Content-Type': 'application/json; charset=utf-8',
        Authorization: token ? `Bearer ${token}` : '',
      },
      success: (resp) => {
        if (resp.statusCode === 401) {
          handleAuthError();
          reject({ code: 401, message: '未登录或登录过期', data: null });
          return;
        }
        const body = resp.data || {};
        if (body.code === 0) {
          resolve(body.data);
          return;
        }
        reject(body);
      },
      fail: (err) => {
        reject({ code: -1, message: '网络异常，请稍后重试', data: err });
      },
    });
  });
}