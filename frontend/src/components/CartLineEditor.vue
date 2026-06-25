<template>
  <GlassCard class="line-card">
    <button class="remove-btn" type="button" @click="$emit('remove')">×</button>

    <div class="line-main">
      <img :src="lineItemImage" :alt="line.item_title" class="thumb" />

      <div class="body">
        <h3>{{ line.item_title }}</h3>
        <p class="muted" v-if="isBuilderItem">{{ builderSummaryText }}</p>
        <p class="muted" v-else-if="summary.length">{{ summary[0] }}</p>
        <p class="muted" v-else>سفارشی سازی نشده</p>
        <strong>{{ formatMoney(line.unit_price_preview, currency) }}</strong>
      </div>

      <div class="qty-side">
        <button class="qty-btn" type="button" @click="$emit('qty-change', Number(line.qty) - 1)">−</button>
        <strong>{{ line.qty }}</strong>
        <button class="qty-btn" type="button" @click="$emit('qty-change', Number(line.qty) + 1)">+</button>
      </div>
    </div>

    <div class="foot-row">
      <div class="line-actions">
        <a v-if="isBuilderItem" class="mini-btn" :href="builderEditUrl">ویرایش سفارشی‌سازی</a>
        <button v-else class="mini-btn" type="button" @click="$emit('edit-customization')">ویرایش مواد</button>
        <a class="mini-btn" :href="`/item/${line.item_slug}?edit=${line.id}`">صفحه محصول</a>
      </div>
      <strong class="line-total">{{ formatMoney(line.line_total_preview, currency) }}</strong>
    </div>

    <ul class="extra-list" v-if="isBuilderItem && builderDetails.length">
      <li v-for="entry in builderDetails.slice(0, 3)" :key="entry">{{ entry }}</li>
    </ul>
    <ul class="extra-list" v-else-if="summary.length > 1">
      <li v-for="entry in summary.slice(1, 3)" :key="entry">{{ entry }}</li>
    </ul>
  </GlassCard>
</template>

<script setup>
import { computed } from 'vue'
import GlassCard from './GlassCard.vue'
import { formatMoney } from '@/utils/format'
import { summarizeCustomizationForDisplay } from '@/utils/itemConfig'

const props = defineProps({
  line: {
    type: Object,
    required: true,
  },
  currency: {
    type: String,
    default: 'TOMAN',
  },
})

defineEmits(['qty-change', 'remove', 'edit-customization'])

const fallbackImage = 'https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?w=500&auto=format&fit=crop&q=60'

const summary = computed(() =>
  summarizeCustomizationForDisplay(props.line.customization || {}, props.line.ingredient_catalog || []),
)
const lineItemImage = computed(
  () => String(props.line?.item_image || props.line?.image || props.line?.item?.image || '').trim() || fallbackImage,
)

const isBuilderItem = computed(() => {
  const c = props.line?.customization || {}
  return Boolean(c.builder_selection_id && c.builder_summary)
})

const builderSummaryText = computed(() => {
  const c = props.line?.customization || {}
  return c.builder_summary || 'سفارشی‌سازی بیلدر'
})

const builderDetails = computed(() => {
  const c = props.line?.customization || {}
  if (!c.builder_selections || !Array.isArray(c.builder_selections)) return []
  return c.builder_selections.map((s) => {
    const label = s.step_title || s.step_key || ''
    const option = s.option_label || s.option_key || ''
    return label && option ? `${label}: ${option}` : label || option || ''
  }).filter(Boolean)
})

const builderEditUrl = computed(() => {
  const c = props.line?.customization || {}
  const editId = c.builder_selection_id || ''
  return `/item/${props.line.item_slug}?edit=${props.line.id}&builder_edit=${editId}`
})
</script>

<style scoped>
.line-card {
  position: relative;
  display: grid;
  gap: 0.6rem;
  border-radius: 26px;
  padding: 0.78rem;
}

.remove-btn {
  position: absolute;
  top: 0.46rem;
  inset-inline-start: 0.46rem;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 1px solid rgba(206, 94, 94, 0.35);
  background: rgba(255, 246, 246, 0.8);
  color: #b84f4f;
  font-size: 0.95rem;
  line-height: 1;
}

.line-main {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr) auto;
  gap: 0.58rem;
  align-items: center;
  padding-top: 0.22rem;
}

.thumb {
  width: 72px;
  height: 72px;
  object-fit: contain;
  object-position: center;
  background: transparent;
  border-radius: 20px;
}

.body {
  min-width: 0;
}

.body h3 {
  margin: 0;
  font-size: 1.03rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.body p {
  margin: 0.2rem 0;
  font-size: 0.76rem;
}

.body strong {
  font-size: 0.95rem;
}

.qty-side {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.qty-btn {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.38);
  background: rgb(var(--palette-deep-saffron-rgb) / 0.14);
  color: var(--accent-gold);
  font-size: 1.2rem;
  line-height: 1;
}

.foot-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.42rem;
}

.line-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.34rem;
}

.mini-btn {
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.32);
  padding: 0.34rem 0.68rem;
  background: rgb(var(--palette-eggshell-rgb) / 0.72);
  color: var(--text-primary);
  font-size: 0.74rem;
  white-space: nowrap;
}

.line-total {
  white-space: nowrap;
}

.extra-list {
  margin: 0;
  padding-inline-start: 1rem;
  color: var(--text-muted);
  font-size: 0.76rem;
  display: grid;
  gap: 0.18rem;
}
</style>
