<template>
  <view class="page">
    <view class="container">
      <!-- 收货地址 -->
      <view class="address-card" @click="chooseAddress">
        <view class="address-icon">
          <uni-icons type="location" size="18" color="#F54949" />
        </view>
        <view v-if="currentAddress" class="address-info">
          <view class="address-row">
            <text class="address-name">{{ currentAddress.name }}</text>
            <text class="address-phone">{{ currentAddress.phone }}</text>
          </view>
          <text class="address-text">{{ currentAddress.regionText }} {{ currentAddress.detail }}</text>
        </view>
        <view v-else class="address-empty">请选择收货地址</view>
        <uni-icons type="right" size="14" color="#8A8A8A" />
      </view>

      <!-- 商品列表 -->
      <view class="goods-card">
        <view class="goods-item" v-for="(item, index) in items" :key="item.cartItemId">
          <image class="goods-image" :src="item.image" mode="aspectFill" />
          <view class="goods-info">
            <text class="goods-name">{{ item.name }}</text>
            <text class="goods-sku">{{ item.skuText }}</text>
          </view>
          <view class="goods-price-col">
            <text class="goods-price">¥{{ item.price }}</text>
            <text class="goods-qty">x{{ item.quantity }}</text>
          </view>
        </view>
      </view>

      <!-- 金额明细 -->
      <view class="summary-card">
        <view class="summary-row">
          <text class="summary-label">商品金额</text>
          <text class="summary-value">¥{{ totalAmount }}</text>
        </view>
        <view class="summary-row">
          <text class="summary-label">运费</text>
          <text class="summary-value">¥{{ freight }}</text>
        </view>
        <view class="summary-row total">
          <text class="summary-label">合计</text>
          <text class="summary-value primary">¥{{ payAmount }}</text>
        </view>
      </view>
    </view>

    <!-- 底部 -->
    <view class="bottom-bar">
      <view class="bottom-inner">
        <text class="pay-label">
          实付款：<text class="pay-price">¥{{ payAmount }}</text>
        </text>
        <view class="submit-btn" @click="submitOrder">立即支付</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import { orderApi } from '@/api';

const CHECKOUT_ADDRESS_KEY = 'checkoutAddressId';

const items = ref([]);
const currentAddress = ref(null);
const totalAmount = ref(0);
const freight = ref(0);
const payAmount = ref(0);
let checkoutIds = null;
let directSkuId = null;
let directQuantity = 0;
let loading = false;

const loadPreview = async () => {
  if (loading) return;
  loading = true;
  try {
    const data = directSkuId
      ? await orderApi.previewDirect(directSkuId, directQuantity)
      : await orderApi.preview(checkoutIds);
    items.value = data.items;
    totalAmount.value = data.totalAmount;
    freight.value = data.freight;
    payAmount.value = data.payAmount;
    const defaultAddress = data.addresses.find((item) => item.isDefault) || data.addresses[0] || null;
    const savedId = Number(uni.getStorageSync(CHECKOUT_ADDRESS_KEY));
    currentAddress.value = data.addresses.find((item) => item.id === savedId) || defaultAddress;
  } catch (e) {
    if (e.code === 400) {
      uni.showToast({ title: e.message || '没有待结算的商品', icon: 'none' });
      setTimeout(() => uni.navigateBack(), 600);
    } else if (e.code === 1203 || e.code === 1104) {
      uni.showToast({ title: e.message || '部分商品不可购买', icon: 'none' });
    } else if (e.code !== 401) {
      uni.showToast({ title: e.message || '结算信息加载失败', icon: 'none' });
    }
  } finally {
    loading = false;
  }
};

onLoad((options) => {
  uni.removeStorageSync(CHECKOUT_ADDRESS_KEY);
  if (options.cartItemIds) {
    checkoutIds = options.cartItemIds.split(',').map(Number);
  }
  if (options.skuId) {
    directSkuId = Number(options.skuId);
    directQuantity = Number(options.quantity) || 1;
  }
});

onShow(() => {
  loadPreview();
});

const chooseAddress = () => {
  uni.navigateTo({ url: '/pages/address/address?select=1' });
};

const createOrder = async () => {
  if (directSkuId) {
    return orderApi.createDirect({
      addressId: currentAddress.value.id,
      skuId: directSkuId,
      quantity: directQuantity
    });
  }
  return orderApi.create({
    addressId: currentAddress.value.id,
    items: items.value.map((item) => ({ skuId: item.skuId, quantity: item.quantity }))
  });
};

const submitOrder = () => {
  if (!currentAddress.value) {
    uni.showToast({ title: '请先选择收货地址', icon: 'none' });
    return;
  }
  if (!items.value.length) return;
  uni.showModal({
    title: '确认支付',
    content: `支付金额 ¥${payAmount.value}`,
    confirmText: '确认支付',
    cancelText: '暂不支付',
    confirmColor: '#F54949',
    success: async (res) => {
      try {
        uni.showLoading({ title: '提交中' });
        const order = await createOrder();
        if (!res.confirm) {
          uni.hideLoading();
          uni.showToast({ title: '订单已提交，待支付', icon: 'none' });
          setTimeout(() => {
            uni.redirectTo({ url: '/pages/orders/orders?status=1' });
          }, 800);
          return;
        }
        setTimeout(async () => {
          try {
            await orderApi.pay(order.id, 'mock');
            uni.hideLoading();
            uni.showToast({ title: '支付成功', icon: 'success' });
            setTimeout(() => {
              uni.redirectTo({ url: '/pages/orders/orders' });
            }, 800);
          } catch (e) {
            uni.hideLoading();
            if (e.code === 409) {
              uni.showToast({ title: '订单已支付', icon: 'none' });
              setTimeout(() => {
                uni.redirectTo({ url: '/pages/orders/orders' });
              }, 800);
            } else {
              uni.showToast({ title: e.message || '支付失败', icon: 'none' });
            }
          }
        }, 800);
      } catch (e) {
        uni.hideLoading();
        uni.showToast({ title: e.message || '创建订单失败', icon: 'none' });
      }
    }
  });
};
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: $mall-background;
  padding-bottom: calc(60px + env(safe-area-inset-bottom));
}

.container {
  max-width: 480px;
  margin: 0 auto;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

// 地址卡片
.address-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background-color: $mall-card;
  border-radius: 16px;
  border: 1px solid $mall-border;
  box-shadow: $mall-shadow-2;
}

.address-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: rgba($mall-primary, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.address-info {
  flex: 1;
  min-width: 0;
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

.address-text {
  display: block;
  font-size: 12px;
  color: $mall-muted-foreground;
  margin-top: 4px;
  line-height: 1.5;
}

.address-empty {
  flex: 1;
  font-size: 14px;
  color: $mall-muted-foreground;
}

// 商品
.goods-card {
  background-color: $mall-card;
  border-radius: 16px;
  border: 1px solid $mall-border;
  box-shadow: $mall-shadow-2;
  overflow: hidden;
  padding: 0 16px;
}

.goods-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
}

.goods-item + .goods-item {
  border-top: 1px solid $mall-border;
}

.goods-image {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  background-color: $mall-muted;
  flex-shrink: 0;
}

.goods-info {
  flex: 1;
  min-width: 0;
}

.goods-name {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: $mall-foreground;
  line-height: 18px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.goods-sku {
  display: block;
  font-size: 11px;
  color: $mall-muted-foreground;
  margin-top: 4px;
}

.goods-price-col {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.goods-price {
  font-size: 15px;
  font-weight: bold;
  color: $mall-primary;
}

.goods-qty {
  font-size: 11px;
  color: $mall-muted-foreground;
}

// 金额明细
.summary-card {
  background-color: $mall-card;
  border-radius: 16px;
  border: 1px solid $mall-border;
  box-shadow: $mall-shadow-2;
  padding: 4px 16px;
}

.summary-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
}

.summary-row + .summary-row {
  border-top: 1px solid $mall-border;
}

.summary-row.total {
  padding: 14px 0;
}

.summary-label {
  font-size: 13px;
  color: $mall-foreground;
}

.summary-value {
  font-size: 13px;
  color: $mall-foreground;
}

.summary-value.primary {
  font-size: 17px;
  font-weight: bold;
  color: $mall-primary;
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
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pay-label {
  font-size: 13px;
  color: $mall-foreground;
}

.pay-price {
  font-size: 20px;
  font-weight: bold;
  color: $mall-primary;
}

.submit-btn {
  padding: 0 32px;
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