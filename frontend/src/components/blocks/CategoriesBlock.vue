<template>
  <section class="blk categories" dir="rtl" v-if="normalized.length">
    <div class="blk__head">
      <span v-if="eyebrow" class="blk__eyebrow">{{ eyebrow }}</span>
      <h2 class="blk__title">{{ title }}</h2>
      <p v-if="subtitle" class="blk__subtitle">{{ subtitle }}</p>
    </div>

    <!-- GRID -->
    <div v-if="variant === 'grid'" class="cat-grid">
      <a
        v-for="(cat, idx) in normalized"
        :key="cat.key || idx"
        class="cat-card"
        :href="cat.href"
      >
        <CategoryMedia :image="cat.image" :icon="cat.icon" />
        <span class="cat-card__label">{{ cat.title }}</span>
        <small class="cat-card__count">{{ formatCount(cat.count) }} آیتم</small>
      </a>
    </div>

    <!-- PILLS -->
    <div v-else-if="variant === 'pills'" class="cat-pills">
      <a v-for="(cat, idx) in normalized" :key="cat.key || idx" class="cat-pill" :href="cat.href">
        {{ cat.title }}
      </a>
    </div>

    <!-- CIRCLES -->
    <div v-else class="cat-circles">
      <a v-for="(cat, idx) in normalized" :key="cat.key || idx" class="cat-circle" :href="cat.href">
        <CategoryMedia :image="cat.image" :icon="cat.icon" variant="circle" />
        <span class="cat-circle__label">{{ cat.title }}</span>
      </a>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import CategoryMedia from '@/components/blocks/CategoryMedia.vue'
import '@/components/blocks/blocks.css'

const props = defineProps({
  variant: { type: String, default: 'grid' },
  eyebrow: { type: String, default: '' },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  categories: { type: Array, default: () => [] },
  currency: { type: String, default: 'IRR' },
})

const normalized = computed(() =>
  (props.categories || [])
    .map((c) => {
      const slug = String(c.slug || c.name || '').trim()
      const iconValue = String(c.menu_icon || c.icon || '').trim()
      const imageValue = String(c.image || (iconValue.startsWith('/') || iconValue.startsWith('http') ? iconValue : '')).trim()
      return {
        key: slug || c.title,
        title: String(c.title || c.name || '').trim(),
        image: imageValue,
        icon: iconValue,
        count: Number(c.item_count || (Array.isArray(c.items) ? c.items.length : 0)) || 0,
        href: slug ? `/menu?category=${encodeURIComponent(slug)}` : '/menu',
      }
    })
    .filter((category) => category.title && category.count > 0),
)

function formatCount(value) {
  return new Intl.NumberFormat('fa-IR').format(value)
}
</script>

<style scoped>
.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: var(--blk-gap);
}

.cat-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  text-decoration: none;
  color: inherit;
  border-radius: var(--blk-radius-sm);
}

.cat-card:hover :deep(.category-media) {
  transform: translateY(-3px);
  border-color: color-mix(in srgb, var(--ds-color-action-primary) 44%, var(--ds-color-border));
}

.cat-card:focus-visible,
.cat-circle:focus-visible {
  outline: 3px solid var(--ds-color-focus-ring, var(--ds-color-action-accent));
  outline-offset: 4px;
}

.cat-card__label {
  font-size: 0.92rem;
  font-weight: 700;
}

.cat-card__count {
  font-size: 0.75rem;
  color: var(--blk-ink-soft);
}

/* Pills */
.cat-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

.cat-pill {
  padding: 0.55rem 1.1rem;
  border-radius: 999px;
  border: 1px solid var(--blk-border);
  background: var(--blk-surface);
  font-size: 0.9rem;
  font-weight: 700;
  text-decoration: none;
  color: inherit;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.cat-pill:hover {
  background: color-mix(in srgb, var(--blk-accent) 10%, transparent);
  border-color: var(--blk-accent);
}

/* Circles */
.cat-circles {
  display: flex;
  flex-wrap: wrap;
  gap: clamp(1rem, 3vw, 2rem);
  justify-content: center;
}

.cat-circle {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: inherit;
  width: 96px;
}

.cat-circle:hover :deep(.category-media) {
  border-color: var(--ds-color-action-primary);
  transform: translateY(-2px);
}

.cat-circle__label {
  font-size: 0.85rem;
  font-weight: 700;
  text-align: center;
}

@media (max-width: 620px) {
  .cat-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .65rem; }
  .cat-card { display: grid; grid-template-columns: 64px minmax(0, 1fr); grid-template-rows: auto auto; align-items: center; gap: 0 .65rem; border: 1px solid var(--ds-color-border); background: var(--ds-color-surface-raised); padding: .55rem; }
  .cat-card :deep(.category-media) { grid-row: 1 / 3; width: 64px; height: 64px; min-height: 0; border-radius: 12px; }
  .cat-card__label { align-self: end; font-size: .82rem; line-height: 1.35; }
  .cat-card__count { align-self: start; font-size: .7rem; }
}
@media (max-width: 360px) {
  .cat-grid { grid-template-columns: 1fr; }
}
</style>
