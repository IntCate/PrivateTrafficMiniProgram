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
              <image class="product-image" :src="item.mainImage" mode="aspectFill" />
              <view class="product-info">
                <text class="product-name">{{ item.name }}</text>
                <text class="product-desc">{{ item.subTitle }}</text>
                <view class="product-bottom">
                  <view class="product-price">
                    <text class="price-current">¥{{ item.price }}</text>
                    <text class="price-original">¥{{ item.originalPrice }}</text>
                  </view>
                  <view class="add-btn" @click.stop="addToCart(item)">
                    <uni-icons type="plus" size="13" color="#FFFFFF" />
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
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { categoryApi, productApi, cartApi } from '@/api';

const categories = ref([{ id: null, name: '全部' }]);
const activeCategory = ref(null);
const productScrollTop = ref(0);
const keyword = ref('');
const allProducts = ref([]);

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

onMounted(() => {
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

const addToCart = async (item) => {
  try {
    const detail = await productApi.detail(item.id);
    const sku = detail && detail.skus && detail.skus[0];
    if (!sku) {
      uni.showToast({ title: '暂无可售规格', icon: 'none' });
      return;
    }
    await cartApi.addItem(sku.id, 1, false);
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
}
</style>