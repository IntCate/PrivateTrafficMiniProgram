<template>
  <view class="page">
    <view class="container">
      <!-- 搜索栏 -->
      <view class="search-filter">
        <view class="search-box">
          <uni-icons type="search" size="16" color="#8A8A8A" />
          <input type="text" placeholder="搜你想找的" class="search-input" v-model="keyword" @confirm="loadProducts" />
        </view>
      </view>

      <!-- 主体：左侧分类 + 右侧商品 -->
      <view class="main-content">
        <scroll-view class="category-sidebar" scroll-y enhanced :show-scrollbar="false">
          <view
            v-for="(cat, index) in categories"
            :key="cat.id"
            class="category-item"
            :class="{ active: activeCategory === cat.id }"
            @click="selectCategory"
            :data-index="index"
          >
            {{ cat.name }}
          </view>
        </scroll-view>

        <scroll-view class="product-area" scroll-y :scroll-top="productScrollTop" enhanced :show-scrollbar="false">
          <view class="product-list">
            <view v-for="item in allProducts" :key="item.id" class="product-card" @click="goDetail(item)">
              <image class="product-image" :src="toAbs(item.mainImage)" mode="aspectFill" />
              <view class="product-info">
                <text class="product-name">{{ item.name }}</text>
                <text class="product-desc">{{ item.subTitle }}</text>
                <view class="product-bottom">
                  <view class="product-price">
                    <text class="price-current">¥{{ item.price }}</text>
                    <text class="price-original">¥{{ item.originalPrice }}</text>
                  </view>
                  <view class="add-btn" @click.stop="openSkuPanel(item)">
                    <text class="add-btn-plus">+</text>
                  </view>
                </view>
              </view>
            </view>
            <view v-if="!allProducts.length" class="empty">
              <uni-icons type="search" size="44" color="#F2E8E2" />
              <text class="empty-text">{{ keyword.trim() ? '无此商品或已下架' : '暂无相关商品' }}</text>
            </view>
          </view>
        </scroll-view>
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
          <view class="action-btn btn-primary sku-confirm-btn" @click="confirmSku">加入购物车</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { categoryApi, productApi, cartApi } from '@/api';
import { onWS } from '@/api/ws';
import { toAbs } from '@/api/config';

const categories = ref([{ id: null, name: '全部' }]);
const activeCategory = ref(null);
const productScrollTop = ref(0);
const keyword = ref('');
const allProducts = ref([]);

// SKU 选择弹层状态
const skuPanelVisible = ref(false);
const skuPanelLoading = ref(false);
const skuProduct = ref(null);
const selected = ref([]);
const quantity = ref(1);

const loadCategories = async () => {
  try {
    const data = await categoryApi.list();
    categories.value = [{ id: null, name: '全部' }, ...data.list];
  } catch (e) {
    // 分类加载失败时保留"全部"
  }
};

const loadProducts = async () => {
  try {
    const data = await productApi.list({
      categoryId: activeCategory.value,
      keyword: keyword.value || undefined,
      page: 1,
      pageSize: 50,
    });
    allProducts.value = data.list;
    if (keyword.value.trim() && !data.list.length) {
      uni.showToast({ title: '无此商品或已下架', icon: 'none' });
    }
  } catch (e) {
    uni.showToast({ title: e.message || '商品加载失败', icon: 'none' });
  }
};

// 每次进入本页（含切换 tab 回来）都刷新分类与商品，确保后台改动（分类排序/上下架）能同步
onShow(() => {
  loadCategories();
  loadProducts();
});

// 订阅运营数据变化：后台改分类/上下架商品后自动刷新（分类排序 & 商品列表）
onWS('catalog_changed', () => {
  loadCategories();
  loadProducts();
});

const selectCategory = (e) => {
  const index = Number(e.currentTarget.dataset.index);
  const cat = categories.value[index];
  if (!cat) return;
  activeCategory.value = cat.id;
  productScrollTop.value += 1;
  loadProducts();
};

const goDetail = (item) => {
  uni.navigateTo({ url: `/pages/product-detail/product-detail?id=${item.id}` });
};

// 计算规格组（由商品 skus 聚合）
const attrGroups = computed(() => {
  if (!skuProduct.value || !skuProduct.value.skus.length) return [];
  const groups = [];
  skuProduct.value.skus.forEach((s) => {
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

// 依据当前选择匹配出具体 SKU
const currentSku = computed(() => {
  if (!skuProduct.value || !skuProduct.value.skus.length) return null;
  const selectedAttrs = attrGroups.value.map((g, gi) => ({ name: g.name, value: g.values[selected.value[gi]] }));
  return (
    skuProduct.value.skus.find((s) => selectedAttrs.every((a) => s.attrs.some((sa) => sa.name === a.name && sa.value === a.value))) ||
    skuProduct.value.skus[0]
  );
});

const currentPrice = computed(() =>
  currentSku.value ? currentSku.value.price : skuProduct.value ? skuProduct.value.price : 0
);

const currentImage = computed(() => {
  const raw =
    currentSku.value && currentSku.value.image
      ? currentSku.value.image
      : skuProduct.value
        ? skuProduct.value.mainImage
        : '';
  return toAbs(raw);
});

// 点击"+"：加载商品详情并弹出规格选择
const openSkuPanel = async (item) => {
  if (skuPanelLoading.value) return;
  try {
    skuPanelLoading.value = true;
    const detail = await productApi.detail(item.id);
    skuProduct.value = detail;
    quantity.value = 1;
    selected.value = attrGroups.value.map(() => 0);
    skuPanelVisible.value = true;
  } catch (e) {
    uni.showToast({ title: e.message || '商品加载失败', icon: 'none' });
  } finally {
    skuPanelLoading.value = false;
  }
};

const closeSkuPanel = () => {
  skuPanelVisible.value = false;
  skuProduct.value = null;
};

const confirmSku = async () => {
  if (!currentSku.value) {
    uni.showToast({ title: '暂无可售规格', icon: 'none' });
    return;
  }
  try {
    await cartApi.addItem(currentSku.value.id, quantity.value, false);
    closeSkuPanel();
    uni.showToast({ title: '已加入购物车', icon: 'none' });
  } catch (e) {
    uni.showToast({ title: e.message || '加入失败', icon: 'none' });
  }
};
</script>

<style lang="scss" scoped>
.page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: $mall-background;
  overflow: hidden;
}

.container {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 480px;
  margin: 0 auto;
  padding: 12px 16px;
  box-sizing: border-box;
  overflow: hidden;
}

// 搜索栏
.search-filter {
  display: flex;
  flex-shrink: 0;
}

.search-box {
  flex: 1;
  min-width: 0;
}

// 主体
.main-content {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

// 左侧分类
.category-sidebar {
  width: 88px;
  flex-shrink: 0;
  background-color: $mall-muted;
  border-radius: $mall-radius-lg;
}

.category-item {
  position: relative;
  padding: 12px 4px;
  font-size: 13px;
  color: $mall-foreground;
  text-align: center;
}

.category-item.active {
  color: $mall-primary;
  font-weight: 600;
}

.category-item.active::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 16px;
  border-radius: 2px;
  background-color: $mall-primary;
}

// 右侧商品
.product-area {
  flex: 1;
  min-height: 0;
}

.product-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-bottom: 12px;
}

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

.product-card {
  width: 100%;
  display: flex;
  background-color: $mall-card;
  border-radius: 12px;
  box-shadow: $mall-shadow-1, inset 0 0 0 1px $mall-border;
  overflow: hidden;
  flex-shrink: 0;
}

.product-image {
  width: 84px;
  height: 84px;
  flex-shrink: 0;
  background-color: $mall-muted;
}

.product-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 8px 12px;
}

.product-name {
  font-size: 13px;
  font-weight: 500;
  color: $mall-foreground;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-desc {
  flex: 1;
  min-height: 0;
  font-size: 11px;
  color: $mall-muted-foreground;
  margin-top: 2px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.product-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 6px;
}

.product-price {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.price-current {
  font-size: 14px;
  font-weight: bold;
  color: $mall-primary;
}

.price-original {
  font-size: 11px;
  color: $mall-muted-foreground;
  text-decoration: line-through;
}

.add-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: $mall-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: $mall-shadow-2;
  flex-shrink: 0;
  line-height: 1;
  padding: 0;
}

.add-btn-plus {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 500;
  line-height: 1;
  color: $mall-primary-foreground;
}

// SKU 弹层
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

.quantity-group .quantity-control {
  margin-left: auto;
}

.quantity-control {
  flex-shrink: 0;
  margin-left: 0;
  display: flex;
  align-items: center;
  border: 1px solid $mall-border;
  border-radius: 6px;
  overflow: hidden;
  height: 18px;
  box-sizing: border-box;
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