<template>
  <section class="blk popular" dir="rtl" v-if="items.length">
    <div class="blk__head blk__head--between">
      <div>
        <span v-if="eyebrow" class="blk__eyebrow popular__eyebrow">{{ eyebrow }}</span>
        <h2 class="blk__title">{{ title }}</h2>
        <p v-if="subtitle" class="blk__subtitle">{{ subtitle }}</p>
      </div>
      <a v-if="moreLabel" class="blk__more" :href="moreHref">{{ moreLabel }}</a>
    </div>

    <!-- SHOWCASE: one large lead item + ranked list -->
    <div v-if="variant === 'showcase'" class="pop-showcase">
      <a class="pop-lead" :href="hrefFor(lead)">
        <div class="pop-lead__media" :style="bgFor(lead)">
          <span class="pop-badge">\u0645\u062d\u0628\u0648\u0628 \u0634\u0645\u0627\u0631\u0647 \u06f1</span>
        </div>
        <div class="pop-lead__body">
          <h3>{{ lead.title }}</h3>
          <p v-if="lead.short_desc">{{ lead.short_desc }}</p>
          <strong class="pop-price">{{ priceFor(lead) }}</strong>
        </div>
      </a>
      <ol class="pop-list">
        <li v-for="(item, idx) in rest" :key="item.slug || idx">
          <a class="pop-row" :href="hrefFor(item)">
            <span class="pop-rank">{{ idx + 2 }}</span>
            <span class="pop-thumb" :style="bgFor(item)"></span>
            <span class="pop-row__info">
              <strong>{{ item.title }}</strong>
              <small v-if="item.short_desc">{{ item.short_desc }}</small>
            </span>
            <span class="pop-row__price">{{ priceFor(item) }}</span>
          </a>
        </li>
      </ol>
    </div>

    <!-- RANKED GRID: cards with rank badges -->
    <div v-else class="pop-grid">
      <a
        v-for="(item, idx) in items"
        :key="item.slug || idx"
        class="pop-card"
        :href="hrefFor(item)"
      >
        <div class="pop-card__media" :style="bgFor(item)">
          <span class="pop-badge pop-badge--sm">#{{ idx + 1 }}</span>
        </div>
        <div class="pop-card__body">
          <strong>{{ item.title }}</strong>
          <small v-if="item.short_desc">{{ item.short_desc }}</small>
          <div class="pop-card__foot">
            <span class="pop-price">{{ priceFor(item) }}</span>
            <button type="button" class="pop-add" @click.prevent="$emit('quick-add', item)">\u0627\u0641\u0632\u0648\u062f\u0646</button>
          </div>
        </div>
      </a>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import '@/components/blocks/blocks.css'

const props = defineProps({
  variant: { type: String, default: 'showcase' },
  eyebrow: { type: String, default: '\u0645\u062d\u0628\u0648\u0628\u200c\u062a\u0631\u06cc\u0646\u200c\u0647\u0627' },
  title: { type: String, default: '\u0645\u062d\u0628\u0648\u0628 \u0645\u0634\u062a\u0631\u06cc\u200c\u0647\u0627' },
  subtitle: { type: String, default: '' },
  moreLabel: { type: String, default: '\u0645\u0634\u0627\u0647\u062f\u0647 \u0645\u0646\u0648' },
  moreHref: { type: String, default: '/menu' },
  items: { type: Array, default: () => [] },
  currency: { type: String, default: 'IRR' },
})

defineEmits(['quick-add'])

const fallbackImage =
  'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=900&auto=format&fit=crop&q=70'

const lead = computed(() => props.items[0] || {})
const rest = computed(() => props.items.slice(1, 5))

function hrefFor(item) {
  const slug = String(item?.slug || '').trim()
  return slug ? `/menu/${slug}` : '/menu'
}

function bgFor(item) {
  const img = String(item?.image || '').trim() || fallbackImage
  return { backgroundImage: `url('${img}')` }
}

function priceFor(item) {
  const value = Number(item?.base_price || 0)
  if (!value) return ''
  try {
    return new Intl.NumberFormat('fa-IR').format(value)
  } catch (_) {
    return String(value)
  }
}
</script>

<style scoped>
.popular__eyebrow {
  color: #b4531f;
  background: color-mix(in srgb, #f2994a 16%, transparent);
}

/* Showcase */
.pop-showcase {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  gap: var(--blk-gap);
  align-items: start;
}

.pop-lead {
  display: flex;
  flex-direction: column;
  border-radius: var(--blk-radius);
  overflow: hidden;
  background: var(--blk-surface);
  border: 1px solid var(--blk-border);
  text-decoration: none;
  color: inherit;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.pop-lead:hover {
  transform: translateY(-3px);
  box-shadow: 0 20px 46px rgb(0 0 0 / 0.1);
}

.pop-lead__media {
  position: relative;
  aspect-ratio: 16 / 10;
  background: var(--blk-surface-soft) center / cover no-repeat;
}

.pop-lead__body {
  padding: 1.1rem 1.2rem 1.3rem;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.pop-lead__body h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 800;
}

.pop-lead__body p {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.8;
  color: var(--blk-ink-soft);
}

.pop-badge {
  position: absolute;
  inset-block-start: 0.75rem;
  inset-inline-start: 0.75rem;
  padding: 0.32rem 0.8rem;
  border-radius: 999px;
  background: linear-gradient(135deg, #f2994a, #eb5757);
  color: #fff;
  font-size: 0.75rem;
  font-weight: 800;
  box-shadow: 0 8px 20px rgb(235 87 87 / 0.35);
}

.pop-badge--sm {
  inset-block-start: 0.6rem;
  inset-inline-start: 0.6rem;
  padding: 0.24rem 0.6rem;
  font-size: 0.72rem;
}

.pop-price {
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--blk-accent);
}

.pop-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.pop-row {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.6rem 0.7rem;
  border-radius: var(--blk-radius-sm);
  background: var(--blk-surface);
  border: 1px solid var(--blk-border);
  text-decoration: none;
  color: inherit;
  transition: background 0.15s ease;
}

.pop-row:hover {
  background: var(--blk-surface-soft);
}

.pop-rank {
  flex: 0 0 auto;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.82rem;
  font-weight: 800;
  color: var(--blk-accent);
  background: color-mix(in srgb, var(--blk-accent) 12%, transparent);
}

.pop-thumb {
  flex: 0 0 auto;
  width: 52px;
  height: 52px;
  border-radius: 12px;
  background: var(--blk-surface-soft) center / cover no-repeat;
}

.pop-row__info {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.pop-row__info strong {
  font-size: 0.92rem;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pop-row__info small {
  font-size: 0.76rem;
  color: var(--blk-ink-soft);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pop-row__price {
  flex: 0 0 auto;
  font-size: 0.88rem;
  font-weight: 800;
  color: var(--blk-accent);
}

/* Ranked grid */
.pop-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: var(--blk-gap);
}

.pop-card {
  display: flex;
  flex-direction: column;
  border-radius: var(--blk-radius);
  overflow: hidden;
  background: var(--blk-surface);
  border: 1px solid var(--blk-border);
  text-decoration: none;
  color: inherit;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.pop-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 18px 40px rgb(0 0 0 / 0.08);
}

.pop-card__media {
  position: relative;
  aspect-ratio: 4 / 3;
  background: var(--blk-surface-soft) center / cover no-repeat;
}

.pop-card__body {
  padding: 0.8rem 0.85rem 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.pop-card__body strong {
  font-size: 0.95rem;
  font-weight: 800;
}

.pop-card__body small {
  font-size: 0.78rem;
  line-height: 1.6;
  color: var(--blk-ink-soft);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.pop-card__foot {
  margin-top: 0.4rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.pop-add {
  border: 0;
  cursor: pointer;
  padding: 0.4rem 0.85rem;
  border-radius: 999px;
  font: inherit;
  font-size: 0.8rem;
  font-weight: 700;
  color: #fff;
  background: var(--blk-accent);
}

@media (max-width: 800px) {
  .pop-showcase {
    grid-template-columns: 1fr;
  }
}
</style>
