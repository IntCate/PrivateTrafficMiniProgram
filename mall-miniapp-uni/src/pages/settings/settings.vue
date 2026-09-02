<template>
  <view class="page">
    <view class="container">
      <view class="group-card">
        <view class="group-item" @click="comingSoon">
          <uni-icons type="locked" size="18" color="#1C1C1E" />
          <text class="group-text">账号与安全</text>
          <uni-icons type="right" size="14" color="#8A8A8A" />
        </view>
        <view class="group-divider"></view>
        <view class="group-item" @click="comingSoon">
          <uni-icons type="notification" size="18" color="#1C1C1E" />
          <text class="group-text">消息通知</text>
          <uni-icons type="right" size="14" color="#8A8A8A" />
        </view>
        <view class="group-divider"></view>
        <view class="group-item" @click="clearCache">
          <uni-icons type="trash" size="18" color="#1C1C1E" />
          <text class="group-text">清除缓存</text>
          <text class="group-value">12.5MB</text>
        </view>
      </view>

      <view class="group-card">
        <view class="group-item" @click="about">
          <uni-icons type="info" size="18" color="#1C1C1E" />
          <text class="group-text">关于我们</text>
          <uni-icons type="right" size="14" color="#8A8A8A" />
        </view>
        <view class="group-divider"></view>
        <view class="group-item" @click="contactService">
          <uni-icons type="headphones" size="18" color="#1C1C1E" />
          <text class="group-text">联系客服</text>
          <uni-icons type="right" size="14" color="#8A8A8A" />
        </view>
      </view>

      <view class="logout-btn" @click="logout">退出登录</view>

      <text class="version-text">快乐购商城 v1.0.0</text>
    </view>
  </view>
</template>

<script setup>
import { authApi } from '@/api';

const comingSoon = () => {
  uni.showToast({ title: '功能开发中，敬请期待', icon: 'none' });
};

const clearCache = () => {
  uni.showModal({
    title: '清除缓存',
    content: '确定要清除本地缓存数据吗？',
    confirmColor: '#F54949',
    success: (res) => {
      if (res.confirm) {
        uni.showToast({ title: '缓存已清除', icon: 'none' });
      }
    }
  });
};

const about = () => {
  uni.showModal({
    title: '关于我们',
    content: '快乐购商城\n让每一次购物都更快乐\n服务热线：400-800-8888',
    showCancel: false,
    confirmText: '知道了'
  });
};

const contactService = () => {
  uni.showModal({
    title: '联系客服',
    content: '客服热线：400-800-8888\n服务时间：9:00-21:00',
    confirmText: '拨打',
    cancelText: '取消',
    success: (res) => {
      if (res.confirm) {
        uni.makePhoneCall({ phoneNumber: '4008008888' });
      }
    }
  });
};

const logout = () => {
  uni.showModal({
    title: '退出登录',
    content: '确定要退出当前账号吗？',
    confirmColor: '#F54949',
    success: async (res) => {
      if (!res.confirm) return;
      uni.showLoading({ title: '退出中' });
      try {
        await authApi.logout();
        uni.hideLoading();
        uni.showToast({ title: '已退出登录', icon: 'none' });
        setTimeout(() => {
          uni.switchTab({ url: '/pages/me/me' });
        }, 300);
      } catch (e) {
        uni.hideLoading();
        if (e.code === 401) {
          uni.showToast({ title: '已退出登录', icon: 'none' });
          setTimeout(() => uni.switchTab({ url: '/pages/me/me' }), 300);
        } else {
          uni.showToast({ title: e.message || '退出失败', icon: 'none' });
        }
      }
    }
  });
};
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: $mall-background;
}

.container {
  max-width: 480px;
  margin: 0 auto;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}

.group-card {
  width: 100%;
  background-color: $mall-card;
  border-radius: 16px;
  border: 1px solid $mall-border;
  box-shadow: $mall-shadow-2;
  overflow: hidden;
  padding: 0 16px;
}

.group-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 0;
}

.group-text {
  flex: 1;
  font-size: 14px;
  color: $mall-foreground;
}

.group-value {
  font-size: 13px;
  color: $mall-muted-foreground;
}

.group-divider {
  height: 1px;
  background-color: $mall-border;
}

.logout-btn {
  margin-top: 24px;
  width: 100%;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  background-color: $mall-card;
  border: 1px solid $mall-border;
  color: $mall-primary;
  font-size: 15px;
  font-weight: 600;
  box-shadow: $mall-shadow-2;
}

.version-text {
  font-size: 11px;
  color: $mall-muted-foreground;
}
</style>