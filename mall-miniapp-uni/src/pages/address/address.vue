<template>
  <view class="page">
    <view class="container">
      <view v-if="addresses.length" class="address-list">
        <view
          v-for="item in addresses"
          :key="item.id"
          class="address-card"
          :class="{ selected: selectMode && selectedId === item.id }"
          @click="selectAddress(item)"
        >
          <view class="address-row">
            <text class="address-name">{{ item.name }}</text>
            <text class="address-phone">{{ item.phone }}</text>
            <view v-if="item.isDefault" class="default-tag">默认</view>
          </view>
          <text class="address-text">{{ item.regionText }} {{ item.detail }}</text>
          <view class="address-bottom">
            <view v-if="selectMode" class="select-hint">
              <uni-icons
                :type="selectedId === item.id ? 'checkmarkempty' : 'circle'"
                size="16"
                :color="selectedId === item.id ? '#F54949' : '#D8CFC8'"
              />
              <text class="select-hint-text">{{ selectedId === item.id ? '已选择' : '点击选择' }}</text>
            </view>
            <view v-else class="select-hint"></view>
            <view class="edit-btn" @click.stop="editAddress(item)">
              <uni-icons type="compose" size="14" color="#8A8A8A" />
              <text class="edit-text">编辑</text>
            </view>
          </view>
        </view>
      </view>

      <view v-else class="empty">
        <uni-icons type="location" size="44" color="#F2E8E2" />
        <text class="empty-text">还没有收货地址，点击下方添加</text>
      </view>
    </view>

    <!-- 底部新增 -->
    <view class="bottom-bar">
      <view class="bottom-inner">
        <view class="add-btn" @click="addAddress">新增收货地址</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import { addressApi } from '@/api';

const CHECKOUT_ADDRESS_KEY = 'checkoutAddressId';

const addresses = ref([]);
const selectMode = ref(false);
const selectedId = ref(null);

onLoad((options) => {
  selectMode.value = options.select === '1';
});

onShow(async () => {
  try {
    const data = await addressApi.list();
    addresses.value = data.list;
    const savedId = Number(uni.getStorageSync(CHECKOUT_ADDRESS_KEY));
    if (selectMode.value && savedId) selectedId.value = savedId;
  } catch (e) {
    if (e.code !== 401) {
      uni.showToast({ title: e.message || '地址加载失败', icon: 'none' });
    }
  }
});

const selectAddress = (item) => {
  if (!selectMode.value) return;
  selectedId.value = item.id;
  uni.setStorageSync(CHECKOUT_ADDRESS_KEY, item.id);
  uni.navigateBack();
};

const editAddress = (item) => {
  const query = selectMode.value ? '&select=1' : '';
  uni.navigateTo({ url: `/pages/address-edit/address-edit?id=${item.id}${query}` });
};

const addAddress = () => {
  const query = selectMode.value ? '?select=1' : '';
  uni.navigateTo({ url: `/pages/address-edit/address-edit${query}` });
};
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: $mall-background;
  padding-bottom: calc(70px + env(safe-area-inset-bottom));
}

.container {
  max-width: 480px;
  margin: 0 auto;
  padding: 12px 16px;
}

.address-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.address-card {
  padding: 16px;
  background-color: $mall-card;
  border-radius: 16px;
  border: 1px solid $mall-border;
  box-shadow: $mall-shadow-2;
}

.address-card.selected {
  border-color: $mall-primary;
}

.address-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.address-name {
  font-size: 15px;
  font-weight: bold;
  color: $mall-foreground;
}

.address-phone {
  font-size: 13px;
  color: $mall-muted-foreground;
}

.default-tag {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  color: $mall-primary;
  background-color: rgba($mall-primary, 0.1);
}

.address-text {
  display: block;
  font-size: 12px;
  color: $mall-muted-foreground;
  margin-top: 8px;
  line-height: 1.5;
}

.address-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
}

.select-hint {
  display: flex;
  align-items: center;
  gap: 4px;
}

.select-hint-text {
  font-size: 11px;
  color: $mall-muted-foreground;
}

.edit-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid $mall-border;
  border-radius: 9999px;
}

.edit-text {
  font-size: 12px;
  color: $mall-foreground;
}

// 空状态
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 100px 0;
}

.empty-text {
  font-size: 13px;
  color: $mall-muted-foreground;
}

// 底部
.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: $mall-card;
  border-top: 1px solid $mall-border;
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 100;
}

.bottom-inner {
  max-width: 480px;
  margin: 0 auto;
  padding: 10px 16px;
}

.add-btn {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  background-color: $mall-primary;
  color: $mall-primary-foreground;
  font-size: 15px;
  font-weight: 600;
  box-shadow: $mall-shadow-2;
}
</style>