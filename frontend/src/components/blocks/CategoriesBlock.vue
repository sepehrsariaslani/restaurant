<template>
  <section class="blk categories" dir="rtl" v-if="categories.length">
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
        <div class="cat-card__media" :style="cat.image ? { backgroundImage: `url('${cat.image}')` } : {}">
          <span v-if="!cat.image" class="cat-card__ph">{{ cat.title.slice(0, 1) }}</span>
        </div>
        <span class="cat-card__label">{{ cat.title }}</span>
        <small v-if="cat.count" class="cat-card__count">{{ cat.count }} \u0622\u06cc\u062a\u0645</small>
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
        <span
          class="cat-circle__img"
          :style="cat.image ? { backgroundImage: `url('${cat.image}')` } : {}"
        >
          <span v-if="!cat.image" class="cat-card__ph">{{ cat.title.slice(0, 1) }}</span>
        </span>
        <span class="cat-circle__label">{{ cat.title }}</span>
      </a>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
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
  (props.categories || []).map((c) => {
    const slug = String(c.slug || c.name || '').trim()
    return {
      key: slug || c.title,
      title: String(c.title || c.name || '').trim(),
      image: String(c.image || c.icon || '').trim(),
      count: Number(c.item_count || (Array.isArray(c.items) ? c.items.length : 0)) || 0,
      href: slug ? `/menu?category=${encodeURIComponent(slug)}` : '/menu',
    }
  }),
)
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
}

.cat-card__media {
  aspect-ratio: 1 / 1;
  border-radius: var(--blk-radius-sm);
  background: var(--blk-surface-soft) center / cover no-repeat;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.18s ease;
}

.cat-card:hover .cat-card__media {
  transform: translateY(-3px);
}

.cat-card__ph {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--blk-accent);
  opacity: 0.6;
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

.cat-circle__img {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: var(--blk-surface-soft) center / cover no-repeat;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid transparent;
  transition: border-color 0.15s ease, transform 0.15s ease;
}

.cat-circle:hover .cat-circle__img {
  border-color: var(--blk-accent);
  transform: translateY(-2px);
}

.cat-circle__label {
  font-size: 0.85rem;
  font-weight: 700;
  text-align: center;
}
</style>
