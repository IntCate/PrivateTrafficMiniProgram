<template>
  <view class="page">
    <view class="container">
      <view v-if="favorites.length" class="favorite-list">
        <view class="favorite-card" v-for="item in favorites" :key="item.id" @click="goDetail(item)">
          <image class="favorite-image" :src="item.image" mode="aspectFill" />
          <view class="favorite-info">
            <text class="favorite-name">{{ item.name }}</text>
            <view class="favorite-bottom">
              <text class="favorite-price">¥{{ item.price }}</text>
              <view class="remove-btn" @click.stop="removeFavorite(item)">
                <uni-icons type="heart-filled" size="16" color="#F54949" />
              </view>
            </view>
          </view>
        </view>
      </view>

      <view v-else class="empty">
        <uni-icons type="heart-filled" size="44" color="#F2E8E2" />
        <text class="empty-text">还没有收藏的商品</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { favoriteApi } from '@/api';

const favorites = ref([]);

const loadFavorites = async () => {
  try {
    const data = await favoriteApi.list({ page: 1, pageSize: 50 });
    favorites.value = data.list;
  } catch (e) {
    if (e.code !== 401) {
      uni.showToast({ title: e.message || '加载失败', icon: 'none' });
    }
  }
};

onShow(loadFavorites);

const goDetail = (item) => {
  uni.navigateTo({ url: `/pages/product-detail/product-detail?id=${item.productId}` });
};

const removeFavorite = async (item) => {
  try {
    await favoriteApi.remove(item.productId);
    favorites.value = favorites.value.filter((f) => f.productId !== item.productId);
    uni.showToast({ title: '已取消收藏', icon: 'none' });
  } catch (e) {
    uni.showToast({ title: e.message || '操作失败', icon: 'none' });
  }
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
}

.favorite-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.favorite-card {
  background-color: $mall-card;
  border-radius: 16px;
  border: 1px solid $mall-border;
  box-shadow: $mall-shadow-2;
  overflow: hidden;
}

.favorite-image {
  width: 100%;
  aspect-ratio: 1;
  background-color: $mall-muted;
}

.favorite-info {
  padding: 10px 12px 12px;
}

.favorite-name {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: $mall-foreground;
  line-height: 18px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 36px;
}

.favorite-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.favorite-price {
  font-size: 16px;
  font-weight: bold;
  color: $mall-primary;
}

.remove-btn {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background-color: $mall-muted;
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
</style>