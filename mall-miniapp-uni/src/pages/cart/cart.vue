<template>
  <view class="page" @tap="closeAllSwipe">
    <view class="container">
      <!-- 搜索与管理 -->
      <view class="search-filter">
        <view class="search-box">
          <uni-icons type="search" size="16" color="#8A8A8A" />
          <input type="text" placeholder="搜你想找的" class="search-input" />
        </view>
        <view class="manage-btn" @click="toggleManage">{{ manageMode ? '完成' : '管理' }}</view>
      </view>

      <!-- 购物车商品 -->
      <simple-swipe-action v-if="cartItems.length" ref="swipeActionRef">
        <view id="cart-items" class="cart-list">
          <simple-swipe-action-item
            v-for="(item, index) in cartItems"
            :key="item.id"
            :right-options="manageMode ? [] : swipeOptions"
            @click="() => removeItem(index)"
          >
            <view class="cart-item" :class="{ unavailable: isUnavailable(item) }" @tap="onCartTap(index)">
              <view
                class="checkbox"
                :class="{ checked: item.selected, disabled: isUnavailable(item) }"
                @click.stop="toggleSelect(item)"
              >
                <uni-icons v-if="item.selected" type="checkmarkempty" size="12" color="#FFFFFF" />
              </view>
              <image class="cart-image" :src="item.image" mode="aspectFill" />
              <view class="cart-info">
                <view class="cart-top">
                  <text class="cart-name">{{ item.name }}</text>
                  <text v-if="isUnavailable(item)" class="cart-badge">已下架</text>
                  <view v-if="!manageMode && !isUnavailable(item)" class="quantity-control">
                    <view class="qty-btn" @click.stop="decrease(item)">-</view>
                    <text class="qty-value">{{ item.quantity }}</text>
                    <view class="qty-btn" @click.stop="increase(item)">+</view>
                  </view>
                </view>
                <view class="cart-sku" @click.stop="openSkuPanel(item)">
                  <text class="cart-sku-text">{{ item.skuText }}</text>
                  <uni-icons type="settings-filled" size="12" color="#999" />
                </view>
                <text class="cart-price">¥{{ item.price }}</text>
              </view>
            </view>
          </simple-swipe-action-item>
        </view>
      </simple-swipe-action>

      <!-- 空购物车 -->
      <view v-else class="empty">
        <uni-icons type="cart" size="56" color="#F2E8E2" />
        <text class="empty-text">购物车还是空的，去逛逛吧</text>
      </view>
    </view>

    <!-- 底部结算 -->
    <view v-if="cartItems.length" class="settlement-bar">
      <view class="settlement-inner">
        <view class="select-all" @click="toggleSelectAll">
          <view class="checkbox" :class="{ checked: allSelected }">
            <uni-icons v-if="allSelected" type="checkmarkempty" size="12" color="#FFFFFF" />
          </view>
          <text class="select-text">全选</text>
        </view>
        <view v-if="manageMode" class="settlement-right">
          <view class="settle-btn delete-all-btn" :class="{ disabled: selectedCount === 0 }" @click="deleteSelected">全部删除</view>
        </view>
        <view v-else class="settlement-right">
          <text class="total-text">合计：<text class="total-price">¥{{ totalPrice }}</text></text>
          <view class="settle-btn" @click="settle">结算</view>
        </view>
      </view>
    </view>

    <!-- 修改规格弹层 -->
    <view v-if="skuPanelVisible" class="sku-mask" @click="closeSkuPanel">
      <view class="sku-panel" @click.stop>
        <view class="sku-panel-head">
          <image class="sku-panel-image" :src="skuPanelItem.image" mode="aspectFill" />
          <view class="sku-panel-info">
            <text class="sku-panel-price">¥{{ skuPanelCurrentSku ? skuPanelCurrentSku.price : 0 }}</text>
            <text class="sku-panel-stock">库存 {{ skuPanelCurrentSku ? skuPanelCurrentSku.stock : 0 }} 件</text>
            <text class="sku-panel-selected">已选：{{ skuPanelCurrentSku ? skuPanelCurrentSku.skuText : '' }}</text>
          </view>
          <view class="sku-panel-close" @click="closeSkuPanel">
            <uni-icons type="closeempty" size="20" color="#8A8A8A" />
          </view>
        </view>

        <scroll-view class="sku-panel-body" scroll-y>
          <view class="sku-group" v-for="(group, gi) in skuPanelAttrGroups" :key="group.name">
            <text class="sku-group-label">{{ group.name }}</text>
            <view class="sku-options">
              <view
                v-for="(value, vi) in group.values"
                :key="value"
                class="sku-option"
                :class="{ active: skuPanelSelected[gi] === vi }"
                @click="skuPanelSelected[gi] = vi"
              >
                {{ value }}
              </view>
            </view>
          </view>
          <view class="sku-group quantity-group">
            <text class="sku-group-label">数量</text>
            <view class="quantity-control">
              <view class="qty-btn" @click="skuPanelQuantity > 1 && skuPanelQuantity--">-</view>
              <text class="qty-value">{{ skuPanelQuantity }}</text>
              <view class="qty-btn" @click="skuPanelCurrentSku && skuPanelQuantity < skuPanelCurrentSku.stock && skuPanelQuantity++">+</view>
            </view>
          </view>
        </scroll-view>

        <view class="sku-panel-footer">
          <view class="action-btn btn-outline sku-cancel-btn" @click="closeSkuPanel">取消</view>
          <view class="action-btn btn-primary sku-confirm-btn" @click="confirmSkuChange">确定</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue';
import { onShow, onHide } from '@dcloudio/uni-app';
import { cartApi, productApi } from '@/api';

const cartItems = ref([]);
const totalPrice = ref(0);

const skuPanelVisible = ref(false);
const skuPanelItem = ref(null);
const skuPanelSkus = ref([]);
const skuPanelSelected = ref([]);
const skuPanelQuantity = ref(1);

const skuPanelAttrGroups = computed(() => {
  const groups = [];
  skuPanelSkus.value.forEach((s) => {
    s.attrs.forEach((a) => {
      let group = groups.find((g) => g.name === a.name);
      if (!group) {
        group = { name: a.name, values: [] };
        groups.push(group);
      }
      if (!group.values.includes(a.value)) group.values.push(a.value);
    });
  });
  return groups;
});

const skuPanelCurrentSku = computed(() => {
  if (!skuPanelSkus.value.length) return null;
  const selectedAttrs = skuPanelAttrGroups.value.map((g, gi) => ({ name: g.name, value: g.values[skuPanelSelected.value[gi]] }));
  return (
    skuPanelSkus.value.find((s) => selectedAttrs.every((a) => s.attrs.some((sa) => sa.name === a.name && sa.value === a.value))) ||
    skuPanelSkus.value[0]
  );
});

const isUnavailable = (item) => item.onSale === false || item.stock <= 0;

const allSelected = computed(() => {
  const avail = cartItems.value.filter((item) => !isUnavailable(item));
  return avail.length > 0 && avail.every((item) => item.selected);
});

const manageMode = ref(false);
const swipeActionRef = ref(null);

const syncCart = (data) => {
  cartItems.value = data.list;
  totalPrice.value = data.totalPrice;
};

const reload = async () => {
  try {
    const data = await cartApi.list();
    syncCart(data);
  } catch (e) {
    if (e.code !== 401) {
      uni.showToast({ title: e.message || '购物车加载失败', icon: 'none' });
    }
  }
};

onShow(reload);

onHide(() => {
  skuPanelVisible.value = false;
});

const closeAllSwipe = () => {
  if (swipeActionRef.value) {
    swipeActionRef.value.closeAll();
  }
  uni.$emit('closeSwipeActionAll');
};

const swipeOptions = [
  { text: '删除', style: { backgroundColor: '#F54949', color: '#FFFFFF' } }
];

const toggleManage = () => {
  manageMode.value = !manageMode.value;
  closeAllSwipe();
};

const onCartTap = (index) => {
  const item = cartItems.value[index];
  if (!item) return;
  if (manageMode.value) {
    toggleSelect(item);
    return;
  }
  uni.navigateTo({ url: `/pages/product-detail/product-detail?id=${item.productId}` });
};

const selectedCount = computed(() => cartItems.value.filter((item) => item.selected).length);

const deleteSelected = async () => {
  const ids = cartItems.value.filter((item) => item.selected).map((item) => item.id);
  if (!ids.length) {
    uni.showToast({ title: '请先选择商品', icon: 'none' });
    return;
  }
  try {
    const data = await cartApi.removeItems(ids);
    syncCart(data);
    manageMode.value = false;
  } catch (e) {
    uni.showToast({ title: e.message || '删除失败', icon: 'none' });
  }
};

const removeItem = async (index) => {
  const item = cartItems.value[index];
  if (!item) return;
  try {
    const data = await cartApi.removeItems([item.id]);
    syncCart(data);
  } catch (e) {
    uni.showToast({ title: e.message || '删除失败', icon: 'none' });
  }
};

const toggleSelect = async (item) => {
  try {
    const data = await cartApi.updateItem(item.id, { selected: !item.selected });
    syncCart(data);
  } catch (e) {
    uni.showToast({ title: e.message || '操作失败', icon: 'none' });
  }
};

const toggleSelectAll = async () => {
  try {
    const data = await cartApi.selectAll(!allSelected.value);
    syncCart(data);
  } catch (e) {
    uni.showToast({ title: e.message || '操作失败', icon: 'none' });
  }
};

const increase = async (item) => {
  try {
    const data = await cartApi.updateItem(item.id, { quantity: item.quantity + 1 });
    syncCart(data);
  } catch (e) {
    uni.showToast({ title: e.message || '操作失败', icon: 'none' });
  }
};

const decrease = async (item) => {
  if (item.quantity <= 1) return;
  try {
    const data = await cartApi.updateItem(item.id, { quantity: item.quantity - 1 });
    syncCart(data);
  } catch (e) {
    uni.showToast({ title: e.message || '操作失败', icon: 'none' });
  }
};

const openSkuPanel = async (item) => {
  if (isUnavailable(item)) return;
  try {
    const detail = await productApi.detail(item.productId);
    skuPanelItem.value = item;
    skuPanelSkus.value = detail.skus;
    skuPanelQuantity.value = item.quantity;
    const currentAttrs = detail.skus.find((s) => s.id === item.skuId);
    if (currentAttrs) {
      skuPanelSelected.value = skuPanelAttrGroups.value.map((g) => {
        const attr = currentAttrs.attrs.find((a) => a.name === g.name);
        return attr ? g.values.indexOf(attr.value) : 0;
      });
    } else {
      skuPanelSelected.value = skuPanelAttrGroups.value.map(() => 0);
    }
    skuPanelVisible.value = true;
  } catch (e) {
    uni.showToast({ title: e.message || '加载规格失败', icon: 'none' });
  }
};

const closeSkuPanel = () => {
  skuPanelVisible.value = false;
};

const confirmSkuChange = async () => {
  if (!skuPanelCurrentSku.value || !skuPanelItem.value) return;
  try {
    const data = await cartApi.updateItem(skuPanelItem.value.id, {
      skuId: skuPanelCurrentSku.value.id,
      quantity: skuPanelQuantity.value,
    });
    syncCart(data);
    closeSkuPanel();
    uni.showToast({ title: '规格已更新', icon: 'none' });
  } catch (e) {
    uni.showToast({ title: e.message || '更新失败', icon: 'none' });
  }
};

const settle = () => {
  const selected = cartItems.value.filter((item) => item.selected);
  if (!selected.length) {
    uni.showToast({ title: '请先选择商品', icon: 'none' });
    return;
  }
  const unavailable = selected.filter((item) => isUnavailable(item));
  if (unavailable.length) {
    uni.showToast({ title: '存在已下架或库存不足的商品，请先移除', icon: 'none' });
    return;
  }
  const ids = selected.map((item) => item.id).join(',');
  uni.navigateTo({ url: `/pages/order-confirm/order-confirm?cartItemIds=${ids}` });
};
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: $mall-background;
  padding-bottom: calc(var(--window-bottom) + 76px);
}

.container {
  max-width: 480px;
  margin: 0 auto;
  padding: 12px 16px;
}

// 搜索与管理
.search-filter {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.search-box {
  flex: 1;
  min-width: 0;
}

.manage-btn {
  flex-shrink: 0;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 500;
  color: $mall-primary;
}

// 空购物车
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

// 购物车列表
.cart-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cart-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.cart-item.unavailable {
  opacity: 0.55;
}

.checkbox {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid $mall-border;
  margin-top: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background-color 0.2s;
}

.checkbox.checked {
  background-color: $mall-primary;
  border-color: $mall-primary;
}

.checkbox.disabled {
  border-color: $mall-muted;
}

.cart-image {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  background-color: $mall-muted;
  flex-shrink: 0;
}

.cart-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.cart-top {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: space-between;
}

.cart-badge {
  flex-shrink: 0;
  padding: 2px 6px;
  border-radius: 4px;
  background-color: $mall-muted;
  color: $mall-muted-foreground;
  font-size: 10px;
  line-height: 1.4;
}

.cart-name {
  font-size: 14px;
  font-weight: 500;
  color: $mall-foreground;
  line-height: 20px;
  flex: 1;
  min-width: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.cart-sku {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: 28px;
  box-sizing: border-box;
  background-color: $mall-muted;
  border-radius: 6px;
  padding: 4px 10px;
  margin-top: 8px;
}

.cart-sku-text {
  flex: 1;
  min-width: 0;
  font-size: 12px;
  color: $mall-muted-foreground;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 8px;
}

.cart-price {
  font-size: 16px;
  font-weight: bold;
  color: $mall-primary;
  line-height: 24px;
  margin-top: 8px;
}

.quantity-control {
  flex-shrink: 0;
  margin-left: 8px;
  display: flex;
  align-items: center;
  border: 1px solid $mall-border;
  border-radius: 6px;
  overflow: hidden;
  height: 24px;
  box-sizing: border-box;
}

.delete-all-btn {
  background-color: #F54949;
  color: #FFFFFF;
}

.delete-all-btn.disabled {
  opacity: 0.5;
}

.qty-btn {
  width: 24px;
  height: 100%;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: $mall-muted;
  color: $mall-foreground;
  font-size: 13px;
}

.qty-value {
  width: 28px;
  height: 100%;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: $mall-foreground;
  background-color: $mall-card;
}

// 修改规格弹层
.sku-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: flex-end;
}

.sku-panel {
  width: 100%;
  background-color: $mall-background;
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
  max-height: 70vh;
  display: flex;
  flex-direction: column;
}

.sku-panel-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid $mall-border;
}

.sku-panel-image {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  background-color: $mall-card;
  flex-shrink: 0;
}

.sku-panel-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sku-panel-price {
  font-size: 18px;
  font-weight: bold;
  color: $mall-primary;
}

.sku-panel-stock {
  font-size: 12px;
  color: $mall-muted-foreground;
}

.sku-panel-selected {
  font-size: 12px;
  color: $mall-foreground;
}

.sku-panel-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sku-panel-body {
  flex: 1;
  padding: 16px;
  box-sizing: border-box;
  max-height: 50vh;
}

.sku-group {
  margin-bottom: 16px;
}

.sku-group-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: $mall-foreground;
  margin-bottom: 8px;
}

.sku-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.sku-option {
  padding: 6px 16px;
  border-radius: 8px;
  font-size: 13px;
  color: $mall-foreground;
  background-color: $mall-card;
  border: 1px solid $mall-border;
}

.sku-option.active {
  color: $mall-primary;
  background-color: rgba($mall-primary, 0.05);
  border-color: $mall-primary;
  font-weight: 500;
}

.quantity-group {
  display: flex;
  align-items: center;
  width: 100%;
}

.quantity-group .sku-group-label {
  margin-bottom: 0;
  flex-shrink: 0;
}

.quantity-group .quantity-control {
  margin-left: auto;
}

.sku-panel-footer {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid $mall-border;
}

.action-btn {
  flex: 1;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  font-size: 14px;
  font-weight: 600;
}

.btn-outline {
  border: 1px solid $mall-primary;
  color: $mall-primary;
}

.btn-primary {
  background-color: $mall-primary;
  color: $mall-primary-foreground;
}

.sku-cancel-btn {
  flex: 1;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sku-confirm-btn {
  flex: 1;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

// 结算栏
.settlement-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: var(--window-bottom);
  background-color: $mall-background;
  border-top-left-radius: $mall-radius-lg;
  border-top-right-radius: $mall-radius-lg;
  box-shadow: 0 -8px 24px -8px rgba(28, 28, 30, 0.12);
  z-index: 90;
}

.settlement-inner {
  max-width: 480px;
  margin: 0 auto;
  padding: 12px 16px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.select-all {
  display: flex;
  align-items: center;
  gap: 8px;
}

.select-all .checkbox {
  margin-top: 0;
}

.select-text {
  font-size: 14px;
  color: $mall-foreground;
}

.settlement-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.total-text {
  font-size: 14px;
  color: $mall-foreground;
}

.total-price {
  font-size: 18px;
  font-weight: bold;
  color: $mall-primary;
}

.settle-btn {
  padding: 0 24px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  background-color: $mall-primary;
  color: $mall-primary-foreground;
  font-size: 14px;
  font-weight: 600;
}
</style>
