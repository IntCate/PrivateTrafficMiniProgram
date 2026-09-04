<template>
  <view class="page">
    <view class="container">
      <view class="form-card">
        <view class="form-item">
          <text class="form-label">收货人</text>
          <input class="form-input" type="text" placeholder="请输入收货人姓名" :value="form.name" @input="onInput('name', $event)" />
        </view>
        <view class="form-item">
          <text class="form-label">手机号</text>
          <input class="form-input" type="number" maxlength="11" placeholder="请输入手机号" :value="form.phone" @input="onInput('phone', $event)" />
        </view>
        <picker mode="region" :value="form.region" @change="onRegionChange">
          <view class="form-item">
            <text class="form-label">所在地区</text>
            <view class="form-value">
              <text :class="{ placeholder: !form.regionText }">{{ form.regionText || '请选择省 / 市 / 区' }}</text>
              <uni-icons type="right" size="14" color="#8A8A8A" />
            </view>
          </view>
        </picker>
        <view class="form-item form-item-textarea">
          <text class="form-label">详细地址</text>
          <textarea
            class="form-textarea"
            placeholder="街道、楼牌号等"
            placeholder-style="font-size:14px;line-height:21px;color:#8A8A8A"
            :value="form.detail"
            @input="onInput('detail', $event)"
          />
        </view>
        <view class="form-item switch-item">
          <text class="form-label">设为默认地址</text>
          <switch :checked="form.isDefault" color="#F54949" style="transform: scale(0.8)" @change="onDefaultChange" />
        </view>
      </view>

      <view class="save-btn" @click="save">保存</view>
      <view v-if="isEdit" class="delete-btn" @click="remove">删除地址</view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { addressApi } from '@/api';

const isEdit = ref(false);
const editId = ref(null);
const form = ref({
  name: '',
  phone: '',
  region: ['上海市', '上海市', '浦东新区'],
  regionText: '上海市 上海市 浦东新区',
  detail: '',
  isDefault: false
});

onLoad(async (options) => {
  if (options.id) {
    isEdit.value = true;
    editId.value = Number(options.id);
    try {
      const data = await addressApi.list();
      const target = data.list.find((item) => item.id === editId.value);
      if (target) {
        form.value = {
          name: target.name,
          phone: target.phone,
          region: [target.province, target.city, target.district],
          regionText: target.regionText,
          detail: target.detail,
          isDefault: target.isDefault
        };
      }
    } catch (e) {
      if (e.code !== 401) {
        uni.showToast({ title: e.message || '地址加载失败', icon: 'none' });
      }
    }
  }
});

const onInput = (key, e) => {
  form.value[key] = e.detail.value;
};

const onRegionChange = (e) => {
  form.value.region = e.detail.value;
  form.value.regionText = e.detail.value.join(' ');
};

const onDefaultChange = (e) => {
  form.value.isDefault = e.detail.value;
};

const validate = () => {
  if (!form.value.name.trim()) {
    uni.showToast({ title: '请填写收货人姓名', icon: 'none' });
    return false;
  }
  if (!/^1\d{10}$/.test(form.value.phone.trim())) {
    uni.showToast({ title: '请填写正确的手机号', icon: 'none' });
    return false;
  }
  if (!form.value.detail.trim()) {
    uni.showToast({ title: '请填写详细地址', icon: 'none' });
    return false;
  }
  return true;
};

const save = async () => {
  if (!validate()) return;
  const [province, city, district] = form.value.region;
  const payload = {
    name: form.value.name.trim(),
    phone: form.value.phone.trim(),
    province,
    city,
    district,
    detail: form.value.detail.trim(),
    isDefault: form.value.isDefault
  };
  try {
    if (isEdit.value) {
      await addressApi.update(editId.value, payload);
    } else {
      await addressApi.add(payload);
    }
    uni.showToast({ title: '保存成功', icon: 'success' });
    setTimeout(() => uni.navigateBack(), 300);
  } catch (e) {
    uni.showToast({ title: e.message || '保存失败', icon: 'none' });
  }
};

const remove = () => {
  uni.showModal({
    title: '删除地址',
    content: '确定要删除这个收货地址吗？',
    confirmColor: '#F54949',
    success: async (res) => {
      if (!res.confirm) return;
      try {
        await addressApi.remove(editId.value);
        uni.showToast({ title: '已删除', icon: 'none' });
        setTimeout(() => uni.navigateBack(), 300);
      } catch (e) {
        uni.showToast({ title: e.message || '删除失败', icon: 'none' });
      }
    }
  });
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

.form-card {
  background-color: $mall-card;
  border-radius: 16px;
  border: 1px solid $mall-border;
  box-shadow: $mall-shadow-2;
  padding: 4px 16px;
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

.form-input {
  flex: 1;
  height: 32px;
  font-size: 14px;
  color: $mall-foreground;
}

.form-value {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  color: $mall-foreground;
}

.form-value .placeholder {
  color: $mall-muted-foreground;
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
  height: 42px;
  margin: 0;
  padding: 0;
  font-size: 14px;
  color: $mall-foreground;
  line-height: 21px;
}

.switch-item {
  justify-content: space-between;
}

.switch-item .form-label {
  width: auto;
  flex: 1;
  white-space: nowrap;
}

.save-btn {
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

.delete-btn {
  margin-top: 12px;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  border: 1px solid $mall-primary;
  color: $mall-primary;
  font-size: 15px;
  font-weight: 600;
}
</style>