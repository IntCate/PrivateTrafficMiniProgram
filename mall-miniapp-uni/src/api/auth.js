import { useMock, TOKEN_KEY } from './config';
import { request } from './request';

let loginPromise = null;

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

function doLogin() {
  return new Promise((resolve, reject) => {
    uni.login({
      provider: 'weixin',
      success: (res) => {
        if (!res || !res.code) {
          reject({ code: 1001, message: '登录 code 无效' });
          return;
        }
        request({ url: '/api/auth/login', method: 'POST', data: { code: res.code } })
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

export function ensureLogin() {
  if (useMock) {
    return Promise.resolve(getToken());
  }
  if (getToken()) {
    return Promise.resolve(getToken());
  }
  if (!loginPromise) {
    loginPromise = doLogin().finally(() => {
      loginPromise = null;
    });
  }
  return loginPromise;
}
