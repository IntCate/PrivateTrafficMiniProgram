<template>
  <view class="page">
    <view class="container">
      <view class="card">
        <view class="card-hint">订单号 #{{ orderId }}</view>

        <view class="form-item">
          <text class="form-label">售后类型</text>
          <radio-group class="radio-group" @change="onTypeChange">
            <label v-for="opt in typeOptions" :key="opt.value" class="radio-item">
              <radio :value="opt.value" :checked="form.type === opt.value" color="#F54949" />
              <text>{{ opt.label }}</text>
            </label>
          </radio-group>
        </view>

        <view class="form-item form-item-textarea">
          <text class="form-label">售后原因</text>
          <textarea
            class="form-textarea"
            placeholder="请描述您遇到的问题，如破损、少件、不合适等"
            placeholder-style="font-size:14px;line-height:21px;color:#8A8A8A"
            :value="form.reason"
            @input="onReasonInput"
          />
        </view>

        <view class="form-item form-item-images">
          <text class="form-label">凭证图片</text>
          <view class="image-preview">
            <image
              v-for="(url, idx) in form.images"
              :key="idx"
              class="thumb"
              :src="toAbs(url)"
              mode="aspectFill"
              @tap="removeImage(idx)"
            />
            <view v-if="form.images.length < 6" class="add-image" @tap="chooseImage">
              <text class="add-plus">+</text>
              <text class="add-text">最多6张</text>
            </view>
          </view>
        </view>
      </view>

      <view class="submit-btn" @tap="submit">提交售后申请</view>
      <view class="tip">售后处理期间订单将暂停流转，审核结果会实时同步到订单详情。</view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { orderApi } from '@/api';
import { BASE_URL, TOKEN_KEY } from '@/api/config';

const orderId = ref(null);
const orderStatus = ref('');
const form = ref({ type: 'refund', reason: '', images: [] });

const typeOptions = ref([]);

onLoad((options) => {
  orderId.value = Number(options.id);
  orderStatus.value = options.status || '';
  // paid(待发货) 仅退款；shipped/completed 可选 仅退款 或 退货退款
  if (orderStatus.value === 'paid') {
    typeOptions.value = [{ value: 'refund', label: '仅退款' }];
    form.value.type = 'refund';
  } else {
    typeOptions.value = [
      { value: 'refund', label: '仅退款（保留商品）' },
      { value: 'return', label: '退货退款（需寄回商品）' }
    ];
    form.value.type = 'return';
  }
});

const onTypeChange = (e) => {
  form.value.type = e.detail.value;
};

const onReasonInput = (e) => {
  form.value.reason = e.detail.value;
};

const toAbs = (url) => (url && url.startsWith('/uploads/') ? BASE_URL + url : url);

const chooseImage = () => {
  const remain = 6 - form.value.images.length;
  uni.chooseImage({
    count: remain,
    sizeType: ['compressed'],
    success: (res) => {
      const paths = res.tempFilePaths;
      const token = uni.getStorageSync(TOKEN_KEY) || '';
      const jobs = paths.map(
        (p) =>
          new Promise((resolve, reject) => {
            uni.uploadFile({
              url: `${BASE_URL}/api/upload`,
              filePath: p,
              name: 'file',
              header: token ? { Authorization: `Bearer ${token}` } : {},
              success: (resp) => {
                try {
                  const body = JSON.parse(resp.data);
                  if (body.code === 0) resolve(body.data.url);
                  else reject(body);
                } catch (err) {
                  reject({ code: -1, message: '上传失败' });
                }
              },
              fail: () => reject({ code: -1, message: '上传失败' })
            });
          })
      );
      Promise.all(jobs).then((urls) => {
        form.value.images = [...form.value.images, ...urls];
      });
    }
  });
};

const removeImage = (idx) => {
  form.value.images.splice(idx, 1);
};

const submit = async () => {
  if (!form.value.type) {
    uni.showToast({ title: '请选择售后类型', icon: 'none' });
    return;
  }
  if (!form.value.reason.trim()) {
    uni.showToast({ title: '请填写售后原因', icon: 'none' });
    return;
  }
  try {
    await orderApi.refund(orderId.value, {
      type: form.value.type,
      reason: form.value.reason.trim(),
      images: form.value.images
    });
    uni.showToast({ title: '售后申请已提交', icon: 'success' });
    setTimeout(() => uni.navigateBack(), 400);
  } catch (e) {
    uni.showToast({ title: e.message || '申请失败', icon: 'none' });
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

.card {
  background-color: $mall-card;
  border-radius: 16px;
  border: 1px solid $mall-border;
  box-shadow: $mall-shadow-2;
  padding: 4px 16px;
}

.card-hint {
  padding: 12px 0 4px;
  font-size: 12px;
  color: $mall-muted-foreground;
}

.form-item {
  display: flex;
  align-items: center;
  padding: 14px 0;
}

.form-item + .form-item {
  border-top: 1px solid $mall-border;
}

.form-label {
  width: 72px;
  flex-shrink: 0;
  font-size: 14px;
  color: $mall-foreground;
}

.radio-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: $mall-foreground;
}

.radio-item radio {
  transform: scale(0.8);
}

.form-item-textarea {
  align-items: flex-start;
}

.form-item-textarea .form-label {
  line-height: 21px;
}

.form-textarea {
  flex: 1;
  box-sizing: content-box;
  width: 100%;
  height: 64px;
  margin: 0;
  padding: 0;
  font-size: 14px;
  color: $mall-foreground;
  line-height: 21px;
}

.form-item-images {
  align-items: flex-start;
}

.form-item-images .form-label {
  line-height: 40px;
}

.image-preview {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.thumb {
  width: 74px;
  height: 74px;
  border-radius: 8px;
  background-color: $mall-border;
}

.add-image {
  width: 74px;
  height: 74px;
  border-radius: 8px;
  border: 1px dashed $mall-border;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.add-plus {
  font-size: 24px;
  line-height: 26px;
  color: $mall-muted-foreground;
}

.add-text {
  font-size: 10px;
  color: $mall-muted-foreground;
}

.submit-btn {
  margin-top: 16px;
  height: 46px;
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

.tip {
  margin-top: 12px;
  text-align: center;
  font-size: 12px;
  color: $mall-muted-foreground;
}
</style>