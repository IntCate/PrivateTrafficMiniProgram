<template>
  <view class="page">
    <view v-if="order" class="container">
      <!-- 状态横幅 -->
      <view class="status-banner">
        <text class="status-title">{{ order.statusText }}</text>
        <text class="status-desc">{{ order.statusDesc }}</text>
      </view>

      <!-- 收货信息 -->
      <view class="address-card">
        <view class="address-row">
          <text class="address-name">{{ order.receiver.name }}</text>
          <text class="address-phone">{{ order.receiver.phone }}</text>
        </view>
        <text class="address-text">{{ order.receiver.regionText }} {{ order.receiver.detail }}</text>
      </view>

      <!-- 商品列表 -->
      <view class="goods-card">
        <view class="goods-item" v-for="(item, index) in order.items" :key="index">
          <image class="goods-image" :src="item.image" mode="aspectFill" />
          <view class="goods-info">
            <text class="goods-name">{{ item.productName }}</text>
            <text class="goods-sku">{{ item.skuText }}</text>
          </view>
          <view class="goods-price-col">
            <text class="goods-price">¥{{ item.price }}</text>
            <text class="goods-qty">x{{ item.quantity }}</text>
          </view>
        </view>
      </view>

      <!-- 订单信息 -->
      <view class="info-card">
        <view class="info-row">
          <text class="info-label">商品金额</text>
          <text class="info-value">¥{{ order.totalAmount }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">运费</text>
          <text class="info-value">¥{{ order.freight }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">实付款</text>
          <text class="info-value primary">¥{{ order.payAmount }}</text>
        </view>
        <view class="info-row divider">
          <text class="info-label">订单编号</text>
          <text class="info-value">{{ order.orderNo }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">下单时间</text>
          <text class="info-value">{{ order.createTime }}</text>
        </view>
      </view>
    </view>

    <view v-else class="empty">
      <uni-icons type="list" size="44" color="#F2E8E2" />
      <text class="empty-text">订单不存在或已删除</text>
    </view>

    <!-- 底部操作 -->
    <view v-if="order" class="bottom-bar">
      <view class="bottom-inner">
        <view class="bottom-actions">
          <view v-if="order.availableActions.includes('cancel')" class="wide-btn ghost" @click="cancelOrder">取消订单</view>
          <view v-if="order.availableActions.includes('refund')" class="wide-btn ghost" @click="refundOrder(null, order.status)">{{ refundLabel(order.status) }}</view>
          <view v-if="order.availableActions.includes('pay')" class="wide-btn primary" @click="payOrder">立即支付</view>
          <view v-if="order.availableActions.includes('remind')" class="wide-btn ghost" @click="remindShip">提醒发货</view>
          <view v-if="order.availableActions.includes('confirm')" class="wide-btn primary" @click="confirmReceipt">确认收货</view>
          <view v-if="order.availableActions.includes('buyAgain')" class="wide-btn ghost" @click="buyAgain">再次购买</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { orderApi } from '@/api';
import { useOrderActions } from '@/composables/useOrderActions';

const order = ref(null);
let orderId = null;

onLoad((options) => {
  orderId = Number(options.id);
  reload();
});

const reload = async () => {
  try {
    const data = await orderApi.detail(orderId);
    order.value = data;
  } catch (e) {
    if (e.code === 404) {
      order.value = null;
    } else if (e.code !== 401) {
      uni.showToast({ title: e.message || '订单加载失败', icon: 'none' });
    }
  }
};

const { payOrder, cancelOrder, refundLabel, refundOrder, remindShip, confirmReceipt, buyAgain } = useOrderActions({
  getOrderId: () => orderId,
  onSuccess: (data) => {
    if (data) {
      order.value = data;
    } else {
      reload();
    }
  },
  afterCancel: () => {
    setTimeout(() => uni.navigateBack(), 300);
  },
});
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

// 状态横幅
.status-banner {
  padding: 20px;
  background: linear-gradient(135deg, $mall-primary-light, $mall-background);
  border-radius: 16px;
  border: 1px solid $mall-border;
  box-shadow: $mall-shadow-2;
}

.status-title {
  display: block;
  font-size: 20px;
  font-weight: bold;
  color: $mall-foreground;
}

.status-desc {
  display: block;
  font-size: 12px;
  color: $mall-muted-foreground;
  margin-top: 6px;
}

// 收货信息
.address-card {
  padding: 16px;
  background-color: $mall-card;
  border-radius: 16px;
  border: 1px solid $mall-border;
  box-shadow: $mall-shadow-2;
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
  margin-top: 6px;
  line-height: 1.5;
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
  font-size: 14px;
  font-weight: bold;
  color: $mall-foreground;
}

.goods-qty {
  font-size: 11px;
  color: $mall-muted-foreground;
}

// 订单信息
.info-card {
  background-color: $mall-card;
  border-radius: 16px;
  border: 1px solid $mall-border;
  box-shadow: $mall-shadow-2;
  padding: 4px 16px;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
}

.info-row + .info-row {
  border-top: 1px solid $mall-border;
}

.info-row.divider {
  margin-top: 12px;
}

.info-label {
  font-size: 13px;
  color: $mall-muted-foreground;
}

.info-value {
  font-size: 13px;
  color: $mall-foreground;
}

.info-value.primary {
  font-size: 16px;
  font-weight: bold;
  color: $mall-primary;
}

// 空状态
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 120px 0;
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

.bottom-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.wide-btn {
  padding: 0 28px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  font-size: 14px;
  font-weight: 600;
  line-height: 1;
}

.wide-btn.primary {
  background-color: $mall-primary;
  color: $mall-primary-foreground;
  box-shadow: $mall-shadow-2;
}

.wide-btn.ghost {
  border: 1px solid $mall-border;
  color: $mall-muted-foreground;
}
</style>