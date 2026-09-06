import { BASE_URL, useMock, TOKEN_KEY } from './config';
import { mockRequest } from './mock';

let reloginPromise = null;

function getToken() {
  try {
    return uni.getStorageSync(TOKEN_KEY) || '';
  } catch (e) {
    return '';
  }
}

function setToken(token) {
  try {
    uni.setStorageSync(TOKEN_KEY, token);
  } catch (e) {
    /* ignore */
  }
}

function clearToken() {
  try {
    uni.removeStorageSync(TOKEN_KEY);
  } catch (e) {
    /* ignore */
  }
}

function doLogin() {
  return new Promise((resolve, reject) => {
    uni.login({
      provider: 'weixin',
      success: (res) => {
        if (!res || !res.code) {
          reject({ code: 1001, message: '登录 code 无效' });
          return;
        }
        doRequest({ url: '/api/auth/login', method: 'POST', data: { code: res.code } })
          .then((data) => {
            if (data && data.token) {
              setToken(data.token);
            }
            resolve(data);
          })
          .catch(reject);
      },
      fail: (err) => reject({ code: -1, message: '微信登录失败', data: err }),
    });
  });
}

export function relogin() {
  if (useMock) {
    return Promise.resolve(getToken());
  }
  clearToken();
  if (!reloginPromise) {
    reloginPromise = doLogin().finally(() => {
      reloginPromise = null;
    });
  }
  return reloginPromise;
}

function handleAuthError() {
  uni.showToast({ title: '登录状态已失效', icon: 'none' });
}

function cleanParams(params) {
  if (!params || typeof params !== 'object') return params;
  const result = {};
  Object.keys(params).forEach((k) => {
    const v = params[k];
    if (v === null || v === undefined || v === '' || v === 'undefined' || v === 'null') return;
    result[k] = v;
  });
  return result;
}

function doRequest(options) {
  const { url, method = 'GET', data, params } = options;
  const token = getToken();

  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method,
      data: method === 'GET' ? cleanParams(params) : data,
      header: {
        'Content-Type': 'application/json; charset=utf-8',
        Authorization: token ? `Bearer ${token}` : '',
      },
      success: (resp) => {
        if (resp.statusCode === 401) {
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

  return doRequest(options).catch((err) => {
    if (err && err.code === 401) {
      handleAuthError();
      return relogin().then(() => doRequest(options));
    }
    throw err;
  });
}