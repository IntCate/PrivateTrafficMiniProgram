<template>
  <view class="page">
    <view class="container">
      <!-- 用户卡片 -->
      <view id="user-card" class="user-card">
        <view class="user-main" @click="openEdit">
          <view class="avatar">
            <image v-if="member.avatar" class="avatar-img" :src="toAbs(member.avatar)" mode="aspectFill" />
            <uni-icons v-else type="person" size="28" color="#FFFFFF" />
          </view>
          <view class="user-info">
            <view class="name-row">
              <text class="user-name">{{ member.nickname }}</text>
              <view class="member-badge">{{ member.memberLevelText }}</view>
            </view>
            <text class="welcome-text">欢迎来到快乐购商城</text>
          </view>
          <view class="settings-btn" @click.stop="goPage('/pages/settings/settings')">
            <uni-icons type="gear" size="18" color="#8A8A8A" />
          </view>
        </view>
        <view class="asset-row">
          <view class="asset-item">
            <text class="asset-value">{{ member.couponCount }}</text>
            <text class="asset-label">优惠券</text>
          </view>
          <view class="asset-divider"></view>
          <view class="asset-item">
            <text class="asset-value">{{ member.points }}</text>
            <text class="asset-label">积分</text>
          </view>
        </view>
      </view>

      <!-- 订单状态 -->
      <view id="order-status" class="order-card">
        <view class="card-header">
          <text class="card-title">我的订单</text>
          <view class="card-more" @click="goOrders()">
            全部订单 <text class="arrow">›</text>
          </view>
        </view>
        <view class="order-grid">
          <view class="order-item" @click="goOrders(1)">
            <view class="order-icon-wrap">
              <uni-icons type="wallet" size="22" color="#1C1C1E" />
              <view v-if="pendingCount > 0" class="badge">{{ pendingCount }}</view>
            </view>
            <text class="order-label">待付款</text>
          </view>
          <view class="order-item" @click="goOrders(2)">
            <view class="order-icon-wrap">
              <uni-icons type="email" size="22" color="#1C1C1E" />
              <view v-if="paidCount > 0" class="badge">{{ paidCount }}</view>
            </view>
            <text class="order-label">待发货</text>
          </view>
          <view class="order-item" @click="goOrders(3)">
            <view class="order-icon-wrap">
              <text class="order-icon-text">送</text>
              <view v-if="shippedCount > 0" class="badge">{{ shippedCount }}</view>
            </view>
            <text class="order-label">待收货</text>
          </view>
          <view class="order-item" @click="goOrders(4)">
            <view class="order-icon-wrap">
              <text class="order-icon-text">退</text>
              <view v-if="refundCount > 0" class="badge">{{ refundCount }}</view>
            </view>
            <text class="order-label">售后/退款</text>
          </view>
        </view>
      </view>

      <!-- 菜单列表 -->
      <view id="menu-list" class="menu-list">
        <view class="menu-item" @click="goOrders()">
          <uni-icons type="compose" size="18" color="#1C1C1E" />
          <text class="menu-text">我的订单</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-divider"></view>
        <view class="menu-item" @click="goPage('/pages/favorites/favorites')">
          <uni-icons type="heart" size="18" color="#1C1C1E" />
          <text class="menu-text">我的收藏</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-divider"></view>
        <view class="menu-item" @click="goPage('/pages/address/address')">
          <uni-icons type="location" size="18" color="#1C1C1E" />
          <text class="menu-text">收货地址</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-divider"></view>
        <view class="menu-item" @click="contactService">
          <uni-icons type="headphones" size="18" color="#1C1C1E" />
          <text class="menu-text">客服中心</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-divider"></view>
        <view class="menu-item" @click="goPage('/pages/settings/settings')">
          <uni-icons type="gear" size="18" color="#1C1C1E" />
          <text class="menu-text">设置</text>
          <text class="menu-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 资料编辑弹层（头像居上横幅式） -->
    <view v-if="showEdit" class="modal-mask" @click="closeEdit">
      <view class="modal-card" :style="modalCardStyle" @click.stop>
        <!-- 横幅头像区 -->
        <view class="edit-banner">
          <image v-if="editAvatar" class="banner-bg-img" :src="toAbs(editAvatar)" mode="aspectFill" />
          <view class="banner-mask"></view>
          <view class="banner-deco deco-1"></view>
          <view class="banner-deco deco-2"></view>
          <view class="banner-avatar-wrap">
            <button class="banner-avatar" open-type="chooseAvatar" @chooseavatar="onChooseAvatar" @click.stop>
              <image v-if="editAvatar" class="banner-avatar-img" :src="toAbs(editAvatar)" mode="aspectFill" />
              <view v-else class="banner-avatar-empty">
                <uni-icons type="person" size="30" color="#FFFFFF" />
              </view>
              <view class="avatar-camera">
                <uni-icons type="camera" size="12" color="#FFFFFF" />
              </view>
            </button>
            <view class="banner-hint">点击更换头像</view>
          </view>
        </view>
        <!-- 表单 -->
        <view class="edit-body">
          <view class="edit-label">昵称</view>
          <view class="edit-input-wrap">
            <input class="edit-input" type="nickname" maxlength="20" v-model="editNickname" :cursor-spacing="16" :adjust-position="true" placeholder="请输入昵称（1-20 字）" placeholder-style="color:#A8A8A8" />
            <text class="input-count">{{ editNickname.length }}/20</text>
          </view>
          <view class="edit-actions">
            <view class="edit-btn ghost" @click="closeEdit">取消</view>
            <view class="edit-btn primary" @click="saveProfile">保存</view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { memberApi } from '@/api';
import { BASE_URL, TOKEN_KEY } from '@/api/config';

const member = ref({ nickname: '', avatar: '', memberLevelText: '', couponCount: 0, points: 0 });
const pendingCount = ref(0);
const paidCount = ref(0);
const shippedCount = ref(0);
const refundCount = ref(0);
const showEdit = ref(false);
const editNickname = ref('');
const editAvatar = ref('');

onShow(async () => {
  try {
    const data = await memberApi.overview();
    member.value = data.member;
    pendingCount.value = data.orderStats.pending || 0;
    paidCount.value = data.orderStats.paid || 0;
    shippedCount.value = data.orderStats.shipped || 0;
    refundCount.value = data.orderStats.refund || 0;
  } catch (e) {
    if (e.code !== 401) {
      uni.showToast({ title: e.message || '会员信息加载失败', icon: 'none' });
    }
  }
});

const goOrders = (status) => {
  const url = status === undefined ? '/pages/orders/orders' : `/pages/orders/orders?status=${status}`;
  uni.navigateTo({ url });
};

const goPage = (url) => {
  uni.navigateTo({ url });
};

const openEdit = () => {
  editNickname.value = member.value.nickname;
  editAvatar.value = member.value.avatar || '';
  keyboardOffset.value = 0;
  // 监听键盘高度，弹层上移防遮挡
  if (typeof uni.onKeyboardHeightChange === 'function') {
    offKeyboardHeight = uni.onKeyboardHeightChange((res) => {
      keyboardOffset.value = (res && res.height) || 0;
    });
  }
  showEdit.value = true;
};

const closeEdit = () => {
  if (offKeyboardHeight) {
    offKeyboardHeight();
    offKeyboardHeight = null;
  }
  keyboardOffset.value = 0;
  showEdit.value = false;
};

// 头像相对路径 → 可访问的完整 URL（售后凭证图同款）
const toAbs = (url) => (url && url.startsWith('/uploads/') ? BASE_URL + url : url);

// 键盘高度：监听键盘弹出，弹层上移避免输入框被遮挡（官方 onKeyboardHeightChange）
const keyboardOffset = ref(0);
let offKeyboardHeight = null;
const modalCardStyle = computed(() => {
  const ty = keyboardOffset.value > 0 ? -Math.round(keyboardOffset.value * 0.5) : 0;
  return { transform: `translateY(${ty}px)` };
});

// 微信 chooseAvatar 选图 → 上传到本平台 /api/upload(avatar) → 得到 /uploads/avatar/ 相对路径
const onChooseAvatar = (e) => {
  const tempPath = e.detail && e.detail.avatarUrl;
  if (!tempPath) return;
  const token = uni.getStorageSync(TOKEN_KEY) || '';
  uni.uploadFile({
    url: `${BASE_URL}/api/upload`,
    filePath: tempPath,
    name: 'file',
    formData: { category: 'avatar' },
    header: token ? { Authorization: `Bearer ${token}` } : {},
    success: (resp) => {
      try {
        const body = JSON.parse(resp.data);
        if (body.code === 0) {
          editAvatar.value = body.data.url;
        } else {
          uni.showToast({ title: body.message || '上传失败', icon: 'none' });
        }
      } catch {
        uni.showToast({ title: '上传失败', icon: 'none' });
      }
    },
    fail: () => uni.showToast({ title: '上传失败', icon: 'none' })
  });
};

const saveProfile = async () => {
  const nickname = editNickname.value.trim();
  if (!nickname || nickname.length > 20) {
    uni.showToast({ title: '昵称长度需为 1-20 字', icon: 'none' });
    return;
  }
  try {
    const data = await memberApi.updateProfile({
      nickname,
      avatar: editAvatar.value.trim() || undefined
    });
    member.value.nickname = data.nickname;
    if (data.avatar) member.value.avatar = data.avatar;
    showEdit.value = false;
    uni.showToast({ title: '资料已更新', icon: 'success' });
  } catch (e) {
    uni.showToast({ title: e.message || '保存失败', icon: 'none' });
  }
};

const contactService = () => {
  uni.showModal({
    title: '客服中心',
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
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: $mall-background;
}

.container {
  max-width: 480px;
  margin: 0 auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

// 用户卡片
.user-card {
  padding: 20px;
  border-radius: 16px;
  background: linear-gradient(135deg, $mall-primary-light, $mall-background);
  border: 1px solid $mall-border;
  box-shadow: $mall-shadow-2;
}

.user-main {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background-color: $mall-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}

.avatar-img {
  width: 100%;
  height: 100%;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  font-size: 17px;
  font-weight: bold;
  color: $mall-foreground;
}

.member-badge {
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 10px;
  font-weight: 600;
  color: $mall-accent-foreground;
  background-color: $mall-accent;
  white-space: nowrap;
}

.welcome-text {
  display: block;
  font-size: 12px;
  color: $mall-muted-foreground;
  margin-top: 4px;
}

.settings-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: $mall-card;
  border: 1px solid $mall-border;
  display: flex;
  align-items: center;
  justify-content: center;
}

.asset-row {
  display: flex;
  align-items: center;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid $mall-border;
}

.asset-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.asset-value {
  font-size: 18px;
  font-weight: bold;
  color: $mall-foreground;
}

.asset-label {
  font-size: 11px;
  color: $mall-muted-foreground;
}

.asset-divider {
  width: 1px;
  height: 24px;
  background-color: $mall-border;
}

// 订单卡片
.order-card {
  padding: 16px;
  background-color: $mall-card;
  border-radius: 16px;
  border: 1px solid $mall-border;
  box-shadow: $mall-shadow-2;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.card-title {
  font-size: 14px;
  font-weight: bold;
  color: $mall-foreground;
}

.card-more {
  font-size: 12px;
  color: $mall-muted-foreground;
  display: flex;
  align-items: center;
}

.arrow {
  margin-left: 2px;
}

.order-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.order-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 8px 0;
}

.order-icon-wrap {
  position: relative;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.order-icon-text {
  font-size: 14px;
  color: $mall-foreground;
  font-weight: 500;
}

.badge {
  position: absolute;
  top: -6px;
  right: -8px;
  min-width: 14px;
  height: 14px;
  padding: 0 4px;
  border-radius: 7px;
  background-color: $mall-primary;
  color: $mall-primary-foreground;
  font-size: 9px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
}

.order-label {
  font-size: 11px;
  color: $mall-foreground;
}

// 菜单
.menu-list {
  background-color: $mall-card;
  border-radius: 16px;
  border: 1px solid $mall-border;
  box-shadow: $mall-shadow-2;
  overflow: hidden;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
}

.menu-text {
  flex: 1;
  font-size: 14px;
  color: $mall-foreground;
}

.menu-arrow {
  font-size: 16px;
  color: $mall-muted-foreground;
}

.menu-divider {
  height: 1px;
  background-color: $mall-border;
  margin: 0 16px;
}

// 资料编辑弹层（头像居上横幅式）
.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.modal-card {
  width: 316px;
  max-width: 90vw;
  background-color: $mall-card;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: $mall-shadow-2;
}

// 横幅头像区
.edit-banner {
  position: relative;
  height: 150px;
  background: linear-gradient(135deg, $mall-primary-light, $mall-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  padding-top: 8px;
  overflow: hidden;
}

.banner-bg-img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.banner-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, rgba(59, 110, 240, 0.45), rgba(44, 74, 200, 0.78));
}

.banner-deco {
  position: absolute;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.16);
  z-index: 1;
}

.deco-1 {
  width: 120px;
  height: 120px;
  top: -40px;
  right: -20px;
}

.deco-2 {
  width: 80px;
  height: 80px;
  bottom: -30px;
  left: -10px;
  background-color: rgba(255, 255, 255, 0.10);
}

.banner-avatar-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  z-index: 2;
}

.banner-avatar {
  position: relative;
  width: 84px;
  height: 84px;
  border-radius: 50%;
  border: 3px solid #ffffff;
  background-color: $mall-card;
  overflow: hidden;
  padding: 0;
  line-height: 1;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
}

.banner-avatar::after {
  border: none;
}

.banner-avatar-img {
  width: 100%;
  height: 100%;
}

.banner-avatar-empty {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6aa1f4, #3b6ef0);
}

.avatar-camera {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: $mall-primary;
  border: 2px solid #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.banner-hint {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.92);
}

// 表单
.edit-body {
  padding: 16px 18px 18px;
}

.edit-label {
  font-size: 13px;
  color: $mall-muted-foreground;
  margin-bottom: 8px;
}

.edit-input-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: $mall-background;
  border-radius: 10px;
  padding: 0 12px;
  border: 1px solid $mall-border;
}

.edit-input {
  flex: 1;
  height: 40px;
  font-size: 14px;
  color: $mall-foreground;
}

.input-count {
  font-size: 11px;
  color: $mall-muted-foreground;
}

.edit-actions {
  display: flex;
  gap: 12px;
  margin-top: 18px;
}

.edit-btn {
  flex: 1;
  height: 42px;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
}

.edit-btn.primary {
  background: linear-gradient(135deg, $mall-primary-light, $mall-primary);
  color: #ffffff;
  font-weight: 600;
}

.edit-btn.ghost {
  border: 1px solid $mall-border;
  color: $mall-muted-foreground;
}
</style>
