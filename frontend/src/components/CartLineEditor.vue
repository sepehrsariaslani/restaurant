<template>
  <GlassCard class="line-card">
    <div class="line-main">
      <a class="product-visual" :href="`/item/${line.item_slug}?edit=${line.id}`" :aria-label="`مشاهده ${line.item_title}`">
        <img :src="lineItemImage" :alt="line.item_title" class="thumb" width="144" height="144" loading="lazy" />
      </a>

      <div class="body">
        <div class="line-title-row">
          <h3><a :href="`/item/${line.item_slug}?edit=${line.id}`">{{ line.item_title }}</a></h3>
          <button class="remove-btn" type="button" :aria-label="`حذف ${line.item_title} از سبد`" @click="$emit('remove')"><Trash2 :size="18" aria-hidden="true" /></button>
        </div>
        <p class="muted" v-if="isBuilderItem">{{ builderSummaryText }}</p>
        <p class="muted" v-else-if="summary.length">{{ summary[0] }}</p>
        <span class="unit-price">قیمت هر عدد {{ formatMoney(line.unit_price_preview, currency) }}</span>
      </div>
    </div>

    <div class="foot-row">
      <div class="line-actions">
        <a v-if="isBuilderItem" class="mini-btn" :href="builderEditUrl"><Pencil :size="15" aria-hidden="true" /> سفارشی‌سازی</a>
        <button v-else-if="hasEditableOptions" class="mini-btn" type="button" @click="$emit('edit-customization')"><Pencil :size="15" aria-hidden="true" /> ویرایش مواد</button>
        <a v-else class="mini-btn" :href="`/item/${line.item_slug}?edit=${line.id}`"><Pencil :size="15" aria-hidden="true" /> جزئیات محصول</a>
      </div>
      <div class="qty-side" role="group" :aria-label="`تعداد ${line.item_title}`">
        <button class="qty-btn" type="button" :aria-label="`کم کردن ${line.item_title}`" @click="$emit('qty-change', Number(line.qty) - 1)">−</button>
        <strong>{{ Number(line.qty).toLocaleString('fa-IR') }}</strong>
        <button class="qty-btn qty-btn--add" type="button" :aria-label="`افزودن ${line.item_title}`" @click="$emit('qty-change', Number(line.qty) + 1)">+</button>
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
import { Pencil, Trash2 } from 'lucide-vue-next'
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

const fallbackImage = '/assets/restaurant/images/restaurant-food-placeholder.svg'

const summary = computed(() =>
  summarizeCustomizationForDisplay(props.line.customization || {}, props.line.ingredient_catalog || []),
)
const hasEditableOptions = computed(() => (props.line.ingredient_catalog || []).length > 0)
const lineItemImage = computed(
  () => String(props.line?.item_image || props.line?.image || props.line?.item?.image || '').trim() || fallbackImage,
)

const isBuilderItem = computed(() => {
  const c = props.line?.customization || {}
  const nested = c.builder_selection || {}
  return Boolean(
    c.builder_summary ||
    nested.summary ||
    nested.selection_id ||
    (Array.isArray(c.builder_portion_rows) && c.builder_portion_rows.length),
  )
})

const builderSummaryText = computed(() => {
  const c = props.line?.customization || {}
  const nested = c.builder_selection || {}
  return c.builder_summary || nested.summary || 'سفارشی‌سازی بیلدر'
})

const builderDetails = computed(() => {
  const c = props.line?.customization || {}
  const rows = Array.isArray(c.builder_portion_rows)
    ? c.builder_portion_rows
    : Array.isArray(c.builder_selections)
      ? c.builder_selections
      : Array.isArray(c.builder_selection?.selections)
        ? c.builder_selection.selections
        : []
  if (!rows.length) return []
  return rows.map((s) => {
    const label = s.step_title || s.step_key || ''
    const option = s.option_label || s.option_key || ''
    const qty = Number(s.portion_count ?? s.qty ?? 0)
    const suffix = qty > 0 ? ` × ${qty.toLocaleString('fa-IR')}` : ''
    return label && option ? `${label}: ${option}${suffix}` : `${label || option || ''}${suffix}`
  }).filter(Boolean)
})

const builderEditUrl = computed(() => {
  const c = props.line?.customization || {}
  const nested = c.builder_selection || {}
  const editId = nested.selection_id || c.builder_selection_id || ''
  return `/item/${props.line.item_slug}?edit=${props.line.id}&builder_edit=${editId}`
})
</script>

<style scoped>
.line-card {
  position: relative;
  display: grid;
  gap: 0.8rem;
  border-radius: 22px;
  padding: 0.9rem;
  background: var(--ds-color-surface-raised, rgb(var(--palette-eggshell-rgb) / 0.98));
  border: 1px solid var(--ds-color-border, rgb(var(--palette-deep-sapphire-rgb) / 0.12));
}

.remove-btn {
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 0;
  background: transparent;
  color: var(--ds-color-text-muted, #846b58);
  flex: 0 0 auto;
}

.line-main {
  display: grid;
  grid-template-columns: clamp(96px, 16vw, 128px) minmax(0, 1fr);
  gap: 0.85rem;
  align-items: start;
}

.product-visual {
  width: clamp(96px, 16vw, 128px);
  aspect-ratio: 1;
  overflow: hidden;
  display: block;
  border-radius: 16px;
  background: var(--ds-color-product-media-surface);
}

.thumb {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  display: block;
}

.body {
  min-width: 0;
}

.line-title-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 0.25rem; }
.line-title-row h3 a { color: inherit; text-decoration: none; }
.line-title-row h3 a:hover { color: var(--ds-color-action-primary); }

.body h3 {
  margin: 0;
  font-size: clamp(1rem, 2vw, 1.2rem);
  line-height: 1.55;
  padding-top: .25rem;
}

.body p {
  margin: 0.2rem 0;
  font-size: 0.82rem;
  line-height: 1.7;
}

.unit-price {
  display: block;
  margin-top: 0.35rem;
  font-size: 0.8rem;
  color: var(--ds-color-text-muted);
}

.qty-side {
  display: flex;
  align-items: center;
  gap: 0;
  border: 1px solid var(--ds-color-border, rgb(var(--palette-deep-sapphire-rgb) / 0.14));
  border-radius: 999px;
  overflow: hidden;
  background: var(--ds-color-surface-raised, #fff);
}

.qty-btn {
  width: 44px;
  height: 44px;
  border: 0;
  background: transparent;
  color: var(--ds-color-action-primary, var(--accent-green));
  font-size: 1.35rem;
  line-height: 1;
}

.foot-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 0.65rem;
  padding-top: 0.8rem;
  border-top: 1px solid var(--ds-color-border);
}

.line-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.34rem;
}

.mini-btn {
  border-radius: 999px;
  border: 1px solid var(--ds-color-border, rgb(var(--palette-deep-saffron-rgb) / 0.32));
  min-height: 44px;
  padding: 0.34rem 0.76rem;
  background: var(--ds-color-surface-raised, #fff);
  color: var(--ds-color-text-primary, var(--text-primary));
  font-size: 0.74rem;
  white-space: nowrap;
  display: inline-flex;
  gap: .35rem;
  align-items: center;
  text-decoration: none;
}

.line-total {
  white-space: nowrap;
  font-size: 1.04rem;
  color: var(--ds-color-text-primary);
}

.extra-list {
  margin: 0;
  padding-inline-start: 1rem;
  color: var(--text-muted);
  font-size: 0.8rem;
  display: grid;
  gap: 0.18rem;
}

.qty-btn--add {
  background: var(--ds-color-action-primary, var(--accent-green));
  color: var(--ds-color-action-primary-foreground, var(--ds-color-text-inverse, #fff));
}

.remove-btn:focus-visible,
.qty-btn:focus-visible,
.mini-btn:focus-visible,
.product-visual:focus-visible {
  outline: 3px solid var(--ds-color-focus-ring, var(--accent-orange));
  outline-offset: 3px;
}

.qty-side > strong {
  min-width: 30px;
  text-align: center;
}

@media (max-width: 620px) {
  .line-card { padding: .75rem; gap: .65rem; }
  .line-main { grid-template-columns: 84px minmax(0, 1fr); gap: .7rem; }
  .product-visual { width: 84px; border-radius: 14px; }
  .body h3 { font-size: .95rem; }
  .foot-row { grid-template-columns: minmax(0, 1fr) auto; row-gap: .55rem; }
  .line-total { grid-column: 1 / -1; grid-row: 1; font-size: 1rem; }
  .line-actions { grid-column: 1; grid-row: 2; }
  .qty-side { grid-column: 2; grid-row: 2; }
}
</style>
