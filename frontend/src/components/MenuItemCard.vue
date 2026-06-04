<template>
  <GlassCard hoverable class="menu-card">
    <img :src="resolvedImage" :alt="item.title" class="cover" />
    <div class="body">
      <p class="badge">{{ item.category_title || 'منو' }}</p>
      <h3>{{ item.title }}</h3>
      <p class="muted desc">{{ item.short_desc || 'توضیحی برای این آیتم ثبت نشده است.' }}</p>
      <div class="row">
        <strong>{{ formatMoney(item.base_price, currency) }}</strong>
        <div class="actions">
          <a :href="`/item/${item.slug}`" class="secondary-btn">مشاهده</a>
          <button class="primary-btn" @click="$emit('quick-add', item)">افزودن</button>
        </div>
      </div>
    </div>
  </GlassCard>
</template>

<script setup>
import { computed } from 'vue'
import GlassCard from './GlassCard.vue'
import { formatMoney } from '@/utils/format'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
  currency: {
    type: String,
    default: 'TOMAN',
  },
})

defineEmits(['quick-add'])

const resolvedImage = computed(() => props.item.image || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=900&auto=format&fit=crop&q=60')
</script>

<style scoped>
.menu-card {
  padding: 0;
}

.cover {
  width: 100%;
  height: 180px;
  object-fit: contain;
  object-position: center;
  background: transparent;
  border-radius: 16px 16px 0 0;
}

.body {
  padding: 0.9rem;
}

h3 {
  margin: 0.45rem 0 0.38rem;
  font-size: 1.1rem;
}

.desc {
  min-height: 2.7rem;
  margin: 0;
}

.row {
  margin-top: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
}

.actions {
  display: flex;
  gap: 0.45rem;
}

.actions .primary-btn,
.actions .secondary-btn {
  padding: 0.4rem 0.72rem;
  font-size: 0.82rem;
}
</style>
