<template>
  <view class="page">
    <view v-if="loadFailed" class="empty">
      <uni-icons type="error" size="44" color="#F2E8E2" />
      <text class="empty-text">商品已下架或不存在</text>
      <view class="empty-btn" @click="goBack">返回</view>
    </view>
    <view v-else class="container">
      <!-- 商品图 -->
      <view id="gallery" class="gallery">
        <image class="gallery-image" :src="currentImage" mode="aspectFill" />
      </view>

      <!-- 价格标题 -->
      <view id="info" class="info-section">
        <view class="price-row">
          <text class="price-main">¥{{ currentPrice }}</text>
          <text class="price-original">¥{{ currentOriginalPrice }}</text>
          <view class="price-tag">热销</view>
        </view>
        <text class="product-title">{{ currentTitle }}</text>
        <text class="product-meta">已售 {{ product ? product.sales.toLocaleString() : 0 }}+ · {{ product ? product.shippingFrom : '' }}发货 · {{ product && product.isFreeShipping ? '包邮' : '运费到付' }}</text>
      </view>

      <!-- 品牌承诺 -->
      <view id="brand-promises" class="promises-section">
        <view class="promise-card">
          <text class="promise-icon">正</text>
          <text class="promise-name">正品保障</text>
        </view>
        <view class="promise-card">
          <text class="promise-icon">退</text>
          <text class="promise-name">7天无理由</text>
        </view>
        <view class="promise-card">
          <text class="promise-icon">快</text>
          <text class="promise-name">极速发货</text>
        </view>
      </view>

      <!-- 详情标签 -->
      <view id="detail-tabs" class="detail-section">
        <view class="tabs">
          <view class="tab active">商品详情</view>
          <view class="tab">参数规格</view>
          <view class="tab">用户评价</view>
        </view>
        <view class="tab-content">
          <rich-text v-if="product" class="detail-text" :nodes="product.detailHtml"></rich-text>
          <view class="spec-grid" v-if="product">
            <view class="spec-item" v-for="(value, key) in product.spec" :key="key">{{ key }}：{{ value }}</view>
          </view>
        </view>
      </view>
    </view>

    <!-- 底部操作栏 -->
    <view v-if="!loadFailed" class="bottom-action">
      <view class="action-inner">
        <view class="action-icon" @click="contactService">
          <uni-icons type="headphones" size="20" color="#8A8A8A" />
          <text class="action-icon-text">客服</text>
        </view>
        <view class="action-icon" @click="toggleFavorite">
          <uni-icons :type="favorited ? 'heart-filled' : 'heart'" size="20" :color="favorited ? '#F54949' : '#8A8A8A'" />
          <text class="action-icon-text" :style="{ color: favorited ? '#F54949' : '' }">{{ favorited ? '已收藏' : '收藏' }}</text>
        </view>
        <view class="action-icon" @click="shareProduct">
          <uni-icons type="redo" size="20" color="#8A8A8A" />
          <text class="action-icon-text">分享</text>
        </view>
        <view class="action-btn btn-outline" @click="openSkuPanel('cart')">加入购物车</view>
        <view class="action-btn btn-primary" @click="openSkuPanel('buy')">立即购买</view>
      </view>
    </view>

    <!-- SKU 选择弹层 -->
    <view v-if="skuPanelVisible" class="sku-mask" @click="closeSkuPanel">
      <view class="sku-panel" @click.stop>
        <view class="sku-panel-head">
          <image class="sku-panel-image" :src="currentImage" mode="aspectFill" />
          <view class="sku-panel-info">
            <text class="sku-panel-price">¥{{ currentPrice }}</text>
            <text class="sku-panel-stock">库存 {{ currentSku ? currentSku.stock : 0 }} 件</text>
            <text class="sku-panel-selected">已选：{{ currentSku ? currentSku.skuText : '' }}</text>
          </view>
          <view class="sku-panel-close" @click="closeSkuPanel">
            <uni-icons type="closeempty" size="20" color="#8A8A8A" />
          </view>
        </view>

        <scroll-view class="sku-panel-body" scroll-y>
          <view class="sku-group" v-for="(group, gi) in attrGroups" :key="group.name">
            <text class="sku-group-label">{{ group.name }}</text>
            <view class="sku-options">
              <view
                v-for="(value, vi) in group.values"
                :key="value"
                class="sku-option"
                :class="{ active: selected[gi] === vi }"
                @click="selected[gi] = vi"
              >
                {{ value }}
              </view>
            </view>
          </view>
          <view class="sku-group quantity-group">
            <text class="sku-group-label">数量</text>
            <view class="quantity-control">
              <view class="qty-btn" @click="quantity > 1 && quantity--">-</view>
              <text class="qty-value">{{ quantity }}</text>
              <view class="qty-btn" @click="currentSku && quantity < currentSku.stock && quantity++">+</view>
            </view>
          </view>
        </scroll-view>

        <view class="sku-panel-footer">
          <view class="action-btn btn-outline sku-cancel-btn" @click="closeSkuPanel">取消</view>
          <view class="action-btn btn-primary sku-confirm-btn" @click="confirmSku">{{ skuPanelMode === 'cart' ? '加入购物车' : '立即购买' }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { productApi, favoriteApi, cartApi } from '@/api';

const product = ref(null);
const productId = ref(null);
const loadFailed = ref(false);
const selected = ref([]);
const quantity = ref(1);
const favorited = ref(false);
const favoriteLoading = ref(false);
const skuPanelVisible = ref(false);
const skuPanelMode = ref('cart');

const attrGroups = computed(() => {
  if (!product.value || !product.value.skus.length) return [];
  const groups = [];
  product.value.skus.forEach((s) => {
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

const currentSku = computed(() => {
  if (!product.value || !product.value.skus.length) return null;
  const selectedAttrs = attrGroups.value.map((g, gi) => ({ name: g.name, value: g.values[selected.value[gi]] }));
  return (
    product.value.skus.find((s) => selectedAttrs.every((a) => s.attrs.some((sa) => sa.name === a.name && sa.value === a.value))) ||
    product.value.skus[0]
  );
});

const currentTitle = computed(() => (product.value ? product.value.name : ''));
const currentPrice = computed(() =>
  currentSku.value ? currentSku.value.price : product.value ? product.value.price : 0
);
const currentOriginalPrice = computed(() => (product.value ? product.value.originalPrice : 0));
const currentImage = computed(() =>
  currentSku.value && currentSku.value.image
    ? currentSku.value.image
    : product.value
      ? product.value.mainImage
      : ''
);

onLoad(async (options) => {
  productId.value = Number(options.id);
  try {
    product.value = await productApi.detail(productId.value);
    loadFavoriteStatus();
  } catch (e) {
    if (e.code === 1102) {
      loadFailed.value = true;
      return;
    }
    loadFailed.value = true;
    uni.showToast({ title: e.message || '商品加载失败', icon: 'none' });
  }
});

const loadFavoriteStatus = async () => {
  try {
    const data = await favoriteApi.list({ page: 1, pageSize: 50 });
    favorited.value = (data.list || []).some((f) => f.productId === productId.value);
  } catch (e) {
    // 收藏状态加载失败不阻塞页面
  }
};

const toggleFavorite = async () => {
  if (favoriteLoading.value) return;
  favoriteLoading.value = true;
  try {
    if (favorited.value) {
      await favoriteApi.remove(productId.value);
      favorited.value = false;
      uni.showToast({ title: '已取消收藏', icon: 'none' });
    } else {
      await favoriteApi.add(productId.value);
      favorited.value = true;
      uni.showToast({ title: '收藏成功', icon: 'success' });
    }
  } catch (e) {
    uni.showToast({ title: e.message || '操作失败', icon: 'none' });
  } finally {
    favoriteLoading.value = false;
  }
};

const openSkuPanel = (mode) => {
  if (!currentSku.value) return;
  skuPanelMode.value = mode;
  selected.value = attrGroups.value.map(() => 0);
  skuPanelVisible.value = true;
};

const closeSkuPanel = () => {
  skuPanelVisible.value = false;
};

const confirmSku = async () => {
  if (!currentSku.value) return;
  if (skuPanelMode.value === 'cart') {
    try {
      await cartApi.addItem(currentSku.value.id, quantity.value, false);
      closeSkuPanel();
      uni.showToast({ title: '已加入购物车', icon: 'none' });
    } catch (e) {
      uni.showToast({ title: e.message || '加入失败', icon: 'none' });
    }
  } else {
    closeSkuPanel();
    uni.navigateTo({
      url: `/pages/order-confirm/order-confirm?skuId=${currentSku.value.id}&quantity=${quantity.value}`
    });
  }
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

const shareProduct = () => {
  uni.showToast({ title: '分享功能敬请期待', icon: 'none' });
};

const goBack = () => {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
  } else {
    uni.switchTab({ url: '/pages/index/index' });
  }
};
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: $mall-background;
  padding-bottom: calc(56px + env(safe-area-inset-bottom));
}

// 下架空态
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 140px 0;
}

.empty-text {
  font-size: 13px;
  color: $mall-muted-foreground;
}

.empty-btn {
  margin-top: 8px;
  padding: 8px 32px;
  border-radius: 9999px;
  background-color: $mall-primary;
  color: $mall-primary-foreground;
  font-size: 13px;
  font-weight: 600;
}

.container {
  max-width: 480px;
  margin: 0 auto;
  padding: 12px 16px;
}

// 商品图
.gallery {
  padding: 8px 0;
}

.gallery-image {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 16px;
  background-color: $mall-muted;
}

// 价格标题
.info-section {
  padding: 12px 0;
}

.price-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.price-main {
  font-size: 24px;
  font-weight: bold;
  color: $mall-primary;
}

.price-original {
  font-size: 14px;
  color: $mall-muted-foreground;
  text-decoration: line-through;
  margin-bottom: 4px;
}

.price-tag {
  margin-left: auto;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  color: $mall-primary;
  background-color: rgba($mall-primary, 0.1);
}

.product-title {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: $mall-foreground;
  line-height: 1.4;
  margin-top: 8px;
}

.product-meta {
  display: block;
  font-size: 12px;
  color: $mall-muted-foreground;
  margin-top: 6px;
}

// SKU 弹层
.sku-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: flex-end;
  z-index: 200;
}

.sku-panel {
  width: 100%;
  max-width: 480px;
  margin: 0 auto;
  background-color: $mall-card;
  border-radius: 16px 16px 0 0;
  padding-bottom: env(safe-area-inset-bottom);
  display: flex;
  flex-direction: column;
  max-height: 70vh;
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
  border-radius: 12px;
  background-color: $mall-muted;
  flex-shrink: 0;
}

.sku-panel-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
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
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  min-height: 0;
  padding: 16px;
  box-sizing: border-box;
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

.sku-panel-footer {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid $mall-border;
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

.quantity-control {
  display: flex;
  align-items: center;
  border: 1px solid $mall-border;
  border-radius: 6px;
  overflow: hidden;
  box-sizing: border-box;
  height: 18px;
  flex-shrink: 0;
  margin-left: auto;
}

.qty-btn {
  width: 22px;
  height: 100%;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: $mall-muted;
  color: $mall-foreground;
  font-size: 12px;
}

.qty-value {
  width: 26px;
  height: 100%;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: $mall-foreground;
  background-color: $mall-card;
}

// 品牌承诺
.promises-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 12px 0;
}

.promise-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  background-color: $mall-card;
  border-radius: 12px;
  border: 1px solid $mall-border;
}

.promise-icon {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: bold;
  color: $mall-accent-foreground;
  background-color: rgba($mall-accent, 0.15);
}

.promise-name {
  font-size: 11px;
  color: $mall-foreground;
  font-weight: 500;
}

// 详情
.detail-section {
  padding: 12px 0;
}

.tabs {
  display: flex;
  border-bottom: 1px solid $mall-border;
}

.tab {
  padding: 10px 16px;
  font-size: 14px;
  color: $mall-muted-foreground;
}

.tab.active {
  color: $mall-primary;
  font-weight: 500;
  border-bottom: 2px solid $mall-primary;
  margin-bottom: -1px;
}

.tab-content {
  padding: 16px 0;
}

.detail-text {
  display: block;
  font-size: 13px;
  color: $mall-foreground;
  line-height: 1.6;
}

.spec-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-top: 12px;
}

.spec-item {
  padding: 10px;
  background-color: $mall-card;
  border: 1px solid $mall-border;
  border-radius: 8px;
  font-size: 12px;
  color: $mall-muted-foreground;
}

// 底部操作
.bottom-action {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: $mall-background;
  border-top: 1px solid $mall-border;
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 100;
}

.action-inner {
  max-width: 480px;
  margin: 0 auto;
  padding: 8px 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  width: 32px;
}

.action-icon-text {
  font-size: 10px;
  color: $mall-muted-foreground;
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
</style>
