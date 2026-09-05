<template>
  <view class="page">
    <!-- 状态筛选 -->
    <view class="tabs">
      <view
        v-for="(tab, index) in tabs"
        :key="index"
        class="tab"
        :class="{ active: activeTab === index }"
        @click="switchTab(index)"
      >
        {{ tab.name }}
      </view>
    </view>

    <swiper class="list-area" :current="activeTab" @change="onSwiperChange">
      <swiper-item v-for="(tab, index) in tabs" :key="index">
        <scroll-view class="list-scroll" scroll-y>
          <view class="container">
            <view v-if="filteredOrders(tab.status).length" class="order-card" v-for="order in filteredOrders(tab.status)" :key="order.id" @click="goDetail(order.id)">
              <view class="order-header">
                <text class="order-no">订单号 {{ order.orderNo }}</text>
                <view class="order-status-wrap">
                  <text v-if="order.status === 'pending' && order.payDeadline" class="order-countdown">剩余 {{ countdownText(order.id) }}</text>
                  <text v-else class="order-status">{{ order.statusText }}</text>
                </view>
              </view>
              <view class="order-item" v-for="(item, index) in order.items" :key="index">
                <image class="order-image" :src="item.image" mode="aspectFill" />
                <view class="order-info">
                  <text class="order-name">{{ item.productName }}</text>
                  <text class="order-sku">{{ item.skuText }}</text>
                </view>
                <view class="order-price-col">
                  <text class="order-price">¥{{ item.price }}</text>
                  <text class="order-qty">x{{ item.quantity }}</text>
                </view>
              </view>
              <view class="order-footer">
                <text class="order-total">
                  共{{ itemCount(order) }}件 合计
                  <text class="order-total-price">¥{{ order.payAmount }}</text>
                </text>
                <view class="order-actions">
                  <view v-if="order.availableActions.includes('cancel')" class="mini-btn ghost" @click.stop="cancelOrder(order.id)">取消订单</view>
                  <view v-if="order.availableActions.includes('refund')" class="mini-btn ghost" @click.stop="refundOrder(order.id, order.status)">{{ refundLabel(order.status) }}</view>
                  <view v-if="order.availableActions.includes('pay')" class="mini-btn primary" @click.stop="payOrder(order.id)">去支付</view>
                  <view v-if="order.availableActions.includes('remind')" class="mini-btn ghost" @click.stop="remindShip(order.id)">提醒发货</view>
                  <view v-if="order.availableActions.includes('confirm')" class="mini-btn primary" @click.stop="confirmReceipt(order.id)">确认收货</view>
                  <view v-if="order.availableActions.includes('buyAgain')" class="mini-btn ghost" @click.stop="buyAgain(order.id)">再次购买</view>
                </view>
              </view>
            </view>

            <view v-else class="empty">
              <uni-icons type="list" size="44" color="#F2E8E2" />
              <text class="empty-text">暂无相关订单</text>
            </view>
          </view>
        </scroll-view>
      </swiper-item>
    </swiper>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad, onShow, onUnload } from '@dcloudio/uni-app';
import { orderApi } from '@/api';
import { useOrderActions } from '@/composables/useOrderActions';

const tabs = [
  { name: '全部', status: '' },
  { name: '待付款', status: 'pending' },
  { name: '待发货', status: 'paid' },
  { name: '待收货', status: 'shipped' },
  { name: '售后/退款', status: 'refund' }
];

const activeTab = ref(0);
const orders = ref([]);
const countdowns = ref({});
let countdownTimer = null;

const pad = (n) => String(n).padStart(2, '0');

const formatRemain = (ms) => {
  if (ms <= 0) return '00:00:00';
  const total = Math.floor(ms / 1000);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return `${pad(h)}:${pad(m)}:${pad(s)}`;
};

const countdownText = (id) => countdowns.value[id] || '';

const startCountdowns = () => {
  if (countdownTimer) clearInterval(countdownTimer);
  const tick = () => {
    const next = {};
    orders.value.forEach((order) => {
      if (order.status === 'pending' && order.payDeadline) {
        next[order.id] = formatRemain(new Date(order.payDeadline).getTime() - Date.now());
      }
    });
    countdowns.value = next;
  };
  tick();
  countdownTimer = setInterval(tick, 1000);
};

// 售后/退款 tab：让"申请中"（售后中）的单子排最前，其余按后端返回顺序（新到旧）
const REFUND_PRIORITY = { '申请中': 0 };

const filteredOrders = (status) => {
  if (status === 'refund') {
    return orders.value
      .filter((order) => order.status === status)
      .slice()
      .sort(
        (a, b) =>
          (REFUND_PRIORITY[a.statusText] ?? 1) - (REFUND_PRIORITY[b.statusText] ?? 1)
      );
  }
  if (!status) return orders.value;
  return orders.value.filter((order) => order.status === status);
};

const itemCount = (order) => order.items.reduce((sum, item) => sum + item.quantity, 0);

const reload = async () => {
  try {
    const data = await orderApi.list({ page: 1, pageSize: 50 });
    orders.value = data.list;
    startCountdowns();
  } catch (e) {
    if (e.code !== 401) {
      uni.showToast({ title: e.message || '订单加载失败', icon: 'none' });
    }
  }
};

onLoad((options) => {
  if (options.status !== undefined && options.status !== '') {
    activeTab.value = Number(options.status);
  }
  reload();
});

onShow(() => {
  reload();
});

onUnload(() => {
  if (countdownTimer) clearInterval(countdownTimer);
});

const switchTab = (index) => {
  activeTab.value = index;
};

const onSwiperChange = (e) => {
  activeTab.value = e.detail.current;
};

const goDetail = (id) => {
  uni.navigateTo({ url: `/pages/order-detail/order-detail?id=${id}` });
};

const { payOrder, cancelOrder, refundLabel, refundOrder, remindShip, confirmReceipt, buyAgain } = useOrderActions({
  onSuccess: reload,
  buyAgainNav: 'navigate',
});
</script>

<style lang="scss" scoped>
.page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: $mall-background;
  overflow: hidden;
}

// 标签栏
.tabs {
  display: flex;
  background-color: $mall-background;
  border-bottom: 1px solid $mall-border;
  flex-shrink: 0;
}

.tab {
  flex: 1;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: $mall-muted-foreground;
  white-space: nowrap;
}

.tab.active {
  color: $mall-primary;
  font-weight: 600;
  border-bottom: 2px solid $mall-primary;
  margin-bottom: -1px;
}

// 列表
.list-area {
  flex: 1;
  min-height: 0;
  width: 100%;
}

.list-scroll {
  width: 100%;
  height: 100%;
}

.container {
  max-width: 480px;
  margin: 0 auto;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.order-card {
  background-color: $mall-card;
  border-radius: 16px;
  border: 1px solid $mall-border;
  box-shadow: $mall-shadow-2;
  overflow: hidden;
  padding: 0 16px;
}

.order-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid $mall-border;
}

.order-no {
  font-size: 12px;
  color: $mall-muted-foreground;
}

.order-status {
  font-size: 13px;
  font-weight: 600;
  color: $mall-primary;
}

.order-status-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.order-countdown {
  font-size: 13px;
  color: $mall-primary;
  font-weight: 600;
}

.order-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
}

.order-item + .order-item {
  border-top: 1px solid $mall-border;
}

.order-image {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  background-color: $mall-muted;
  flex-shrink: 0;
}

.order-info {
  flex: 1;
  min-width: 0;
}

.order-name {
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

.order-sku {
  display: block;
  font-size: 11px;
  color: $mall-muted-foreground;
  margin-top: 4px;
}

.order-price-col {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.order-price {
  font-size: 14px;
  font-weight: bold;
  color: $mall-foreground;
}

.order-qty {
  font-size: 11px;
  color: $mall-muted-foreground;
}

.order-footer {
  display: flex;
  flex-direction: column;
  padding: 12px 0;
  border-top: 1px solid $mall-border;
}

.order-total {
  text-align: right;
  font-size: 12px;
  color: $mall-muted-foreground;
}

.order-total-price {
  font-size: 15px;
  font-weight: bold;
  color: $mall-primary;
}

.order-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.mini-btn {
  padding: 0 18px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  font-size: 12px;
  line-height: 1;
}

.mini-btn.primary {
  background-color: $mall-primary;
  color: $mall-primary-foreground;
  font-weight: 600;
}

.mini-btn.ghost {
  border: 1px solid $mall-border;
  color: $mall-muted-foreground;
}

// 空状态
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 80px 0;
}

.empty-text {
  font-size: 13px;
  color: $mall-muted-foreground;
}
</style>