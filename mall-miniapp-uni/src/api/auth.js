import { TOKEN_KEY } from './config';
import { relogin } from './request';

function getToken() {
  try {
    return uni.getStorageSync(TOKEN_KEY) || '';
  } catch (e) {
    return '';
  }
}

export function ensureLogin() {
  if (getToken()) {
    return Promise.resolve(getToken());
  }
  return relogin();
}
