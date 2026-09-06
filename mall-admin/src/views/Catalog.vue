<script setup>
import { ref } from 'vue'

import CategoryPanel from '@/components/catalog/CategoryPanel.vue'
import ProductTable from '@/components/catalog/ProductTable.vue'

// 当前选中分类 id（null 表示全部商品）
const selectedCategoryId = ref(null)
</script>

<template>
  <div class="catalog">
    <div class="catalog-left">
      <CategoryPanel @select="selectedCategoryId = $event" />
    </div>
    <div class="catalog-right">
      <ProductTable :category-id="selectedCategoryId" />
    </div>
  </div>
</template>

<style scoped>
.catalog {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.catalog-left {
  width: 260px;
  flex-shrink: 0;
}
.catalog-right {
  flex: 1;
  min-width: 0;
}
</style>