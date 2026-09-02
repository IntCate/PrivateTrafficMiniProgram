<template>
  <view class="page">
    <view class="container">
      <!-- 问候区 -->
      <view class="greeting">
        <view class="avatar">
          <uni-icons type="person" size="24" color="#FFFFFF" />
        </view>
        <view class="user-info">
          <text class="greet-text">下午好</text>
          <text class="user-name">{{ member ? member.nickname : '请登录' }}</text>
        </view>
        <view class="member-cards">
          <navigator url="/pages/me/me" open-type="switchTab" class="member-card">
            <text class="card-value">{{ member ? member.points.toLocaleString() : '--' }}</text>
            <text class="card-label">积分</text>
          </navigator>
          <navigator url="/pages/me/me" open-type="switchTab" class="member-card">
            <text class="card-value">{{ member ? member.couponCount : '--' }}</text>
            <text class="card-label">优惠券</text>
          </navigator>
        </view>
      </view>

      <!-- 搜索 -->
      <view class="search-box">
        <uni-icons type="search" size="16" color="#8A8A8A" />
        <input type="text" placeholder="搜你想找的" class="search-input" />
      </view>

      <!-- 主横幅 -->
      <navigator url="/pages/products/products" open-type="switchTab" class="hero-banner">
        <image class="hero-image" :src="heroBanner ? heroBanner.image : '/static/hero-banner.jpg'" mode="aspectFill" />
        <view class="hero-overlay"></view>
        <view class="hero-content">
          <text class="hero-tag">{{ heroBanner ? heroBanner.tag : '限时特惠' }}</text>
          <text class="hero-title">{{ heroBanner ? heroBanner.title : '夏季新品 火热开售' }}</text>
          <view class="hero-btn">立即抢购</view>
        </view>
      </navigator>

      <!-- 品牌承诺 -->
      <view class="brand-promises">
        <template v-for="(item, index) in promises" :key="index">
          <view class="promise-item">
            <view class="promise-icon">{{ promiseIcons[index % promiseIcons.length] }}</view>
            <text class="promise-text">{{ item }}</text>
          </view>
          <view v-if="index < promises.length - 1" class="promise-divider"></view>
        </template>
      </view>

      <!-- 主题精选 -->
      <view class="featured-themes">
        <text class="section-title">主题精选</text>
        <view class="theme-viewport" @touchstart="onTouchStart" @touchend="onTouchEnd">
          <view class="theme-track" :style="trackStyle">
            <navigator
              v-for="(theme, index) in trackItems"
              :key="index"
              url="/pages/products/products"
              open-type="switchTab"
              class="theme-card"
            >
              <image class="theme-image" :src="theme.image" mode="aspectFill" />
              <view class="theme-overlay"></view>
              <view class="theme-content">
                <text class="theme-name">{{ theme.name }}</text>
                <text class="theme-desc">{{ theme.desc }}</text>
              </view>
            </navigator>
          </view>
          <view class="theme-dots">
            <view
              v-for="(theme, index) in themes"
              :key="index"
              class="theme-dot"
              :class="{ active: index === activeIndex }"
            ></view>
          </view>
        </view>
      </view>

    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { homeApi } from '@/api';

const member = ref(null);
const banners = ref([]);
const themes = ref([
  { name: '夏季焕新', desc: '轻盈出行', image: '/static/product-sneakers.jpg' },
  { name: '会员专享', desc: '积分翻倍', image: '/static/product-skincare.jpg' },
  { name: '通勤百搭', desc: '从容有型', image: '/static/product-bag.jpg' },
  { name: '影音数码', desc: '降噪新声', image: '/static/product-headphones.jpg' }
]);
const promises = ref(['正品保障', '7天无理由', '极速发货']);
const promiseIcons = ['正', '退', '快', '惠', '省'];

const heroBanner = computed(() => banners.value[0] || null);

const step = 363;
const current = ref(0);
const noTransition = ref(false);
let timer = null;
let startX = 0;

const trackItems = computed(() => (themes.value.length ? [...themes.value, themes.value[0]] : []));
const activeIndex = computed(() => (themes.value.length ? current.value % themes.value.length : 0));
const trackStyle = computed(() => ({
  transform: `translateX(-${current.value * step}rpx)`,
  transition: noTransition.value ? 'none' : 'transform 0.45s ease'
}));

const next = () => {
  if (!themes.value.length) return;
  current.value++;
  if (current.value >= themes.value.length) {
    setTimeout(() => {
      noTransition.value = true;
      current.value = 0;
      setTimeout(() => {
        noTransition.value = false;
      }, 30);
    }, 450);
  }
};

const prev = () => {
  if (!themes.value.length) return;
  noTransition.value = true;
  if (current.value <= 0) current.value = themes.value.length - 1;
  else current.value--;
  setTimeout(() => {
    noTransition.value = false;
  }, 30);
};

const onTouchStart = (e) => {
  startX = e.touches[0].clientX;
};

const onTouchEnd = (e) => {
  const deltaX = e.changedTouches[0].clientX - startX;
  if (Math.abs(deltaX) > 30) {
    if (deltaX < 0) next();
    else prev();
  }
};

const loadData = async () => {
  try {
    const data = await homeApi.getIndex();
    member.value = data.member;
    banners.value = data.banners;
    themes.value = data.themes;
    promises.value = data.promises;
  } catch (e) {
    // 接口失败时保持默认展示
  }
};

// 每次回到首页 tab 都刷新数据（含用户昵称/积分，与其他 tab 页修改后保持同步）
onShow(() => {
  loadData();
});

onMounted(() => {
  timer = setInterval(next, 3000);
});

onUnmounted(() => {
  clearInterval(timer);
});
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

// 问候区
.greeting {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: $mall-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.greet-text {
  display: block;
  font-size: 12px;
  color: $mall-muted-foreground;
}

.user-name {
  display: block;
  font-size: 15px;
  font-weight: bold;
  color: $mall-foreground;
}

.member-cards {
  display: flex;
  gap: 8px;
}

.member-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 12px;
  background-color: $mall-card;
  border-radius: 12px;
  border: 1px solid $mall-border;
}

.card-value {
  font-size: 12px;
  font-weight: bold;
  color: $mall-foreground;
}

.card-label {
  font-size: 10px;
  color: $mall-muted-foreground;
}

// 搜索
.search-box {
  margin: 8px 0;
}

// 主横幅
.hero-banner {
  position: relative;
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 16px;
  overflow: hidden;
  margin: 12px 0;
}

.hero-image {
  width: 100%;
  height: 100%;
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.5), transparent 60%);
}

.hero-content {
  position: absolute;
  bottom: 16px;
  left: 16px;
  right: 16px;
  color: #fff;
}

.hero-tag {
  display: block;
  font-size: 12px;
  opacity: 0.9;
}

.hero-title {
  display: block;
  font-size: 20px;
  font-weight: bold;
  margin-top: 4px;
}

.hero-btn {
  display: inline-block;
  margin-top: 12px;
  padding: 6px 16px;
  background-color: $mall-primary;
  color: $mall-primary-foreground;
  font-size: 12px;
  font-weight: 600;
  border-radius: 8px;
}

// 品牌承诺
.brand-promises {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin: 8px 0;
  background-color: $mall-card;
  border-radius: 12px;
  border: 1px solid $mall-border;
}

.promise-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.promise-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: bold;
  color: $mall-accent-foreground;
  background-color: rgba($mall-accent, 0.15);
}

.promise-text {
  font-size: 10px;
  color: $mall-muted-foreground;
}

.promise-divider {
  flex-shrink: 0;
  width: 1px;
  height: 24px;
  background-color: $mall-border;
}

// 主题精选
.featured-themes {
  padding: 12px 0;
}

.section-title {
  display: block;
  font-size: 15px;
  font-weight: bold;
  color: $mall-foreground;
  margin-bottom: 12px;
}

.theme-viewport {
  position: relative;
  width: 100%;
  height: 280rpx;
  overflow: hidden;
}

.theme-track {
  display: flex;
  gap: 32rpx;
  height: 100%;
}

.theme-card {
  position: relative;
  display: block;
  flex-shrink: 0;
  width: 331rpx;
  height: 240rpx;
  border-radius: 12px;
  overflow: hidden;
}

.theme-dots {
  position: absolute;
  bottom: 8rpx;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8rpx;
  z-index: 2;
}

.theme-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 9999px;
  background-color: rgba(28, 28, 30, 0.25);
}

.theme-dot.active {
  width: 22rpx;
  background-color: $mall-primary;
}

.theme-image {
  width: 100%;
  height: 100%;
}

.theme-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.6), transparent);
}

.theme-content {
  position: absolute;
  bottom: 12px;
  left: 12px;
  color: #fff;
}

.theme-name {
  display: block;
  font-size: 12px;
  font-weight: 600;
}

.theme-desc {
  display: block;
  font-size: 10px;
  opacity: 0.8;
  margin-top: 2px;
}

</style>
