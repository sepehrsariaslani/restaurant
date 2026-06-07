<template>
  <div
    class="menu-card"
    :class="`menu-card--${resolvedVariant}`"
  >
    <template v-if="resolvedVariant === 'classic'">
      <div class="classic-img-wrap">
        <img :src="resolvedImage" :alt="item.title" class="classic-img" />
        <span class="classic-price-badge">{{ formatMoney(item.base_price, currency) }}</span>
      </div>
      <div class="classic-body">
        <p class="classic-cat">{{ item.category_title || 'منو' }}</p>
        <h3 class="classic-title">{{ item.title }}</h3>
        <p class="classic-desc muted">{{ item.short_desc || 'توضیحی برای این آیتم ثبت نشده است.' }}</p>
        <div class="classic-rating" v-if="reviewCnt > 0">
          <span class="cr-stars">
            <span v-for="s in 5" :key="s" class="cr-star" :class="{ filled: s <= Math.round(avgRating) }">★</span>
          </span>
          <span class="cr-count">{{ avgRating }} ({{ reviewCnt }})</span>
        </div>
        <div class="classic-footer">
          <div class="classic-tags">
            <span class="ctag" v-for="tag in itemTags" :key="tag">{{ tag }}</span>
          </div>
          <div class="classic-actions">
            <a :href="`/item/${item.slug}`" class="classic-link">مشاهده ↗</a>
            <button class="classic-add" type="button" @click="$emit('quick-add', item)">+</button>
          </div>
        </div>
      </div>
    </template>

    <template v-else-if="resolvedVariant === 'dark'">
      <div class="dark-img-wrap">
        <img :src="resolvedImage" :alt="item.title" class="dark-img" />
        <div class="dark-gradient"></div>
        <span class="dark-delivery-label">Free Delivery until 16/06/2026</span>
      </div>
      <div class="dark-body">
        <div class="dark-info">
          <h3 class="dark-title">{{ item.title }}</h3>
          <div class="dark-tags">
            <span class="dtag" v-for="tag in itemTags" :key="tag">{{ tag }}</span>
          </div>
        </div>
        <div class="dark-price-col">
          <strong class="dark-price">{{ formatMoney(item.base_price, currency) }}</strong>
          <a :href="`/item/${item.slug}`" class="dark-link">مشاهده ↗</a>
        </div>
      </div>
    </template>

    <template v-else>
      <button class="navy-add-btn" type="button" @click="$emit('quick-add', item)" aria-label="افزودن">+</button>
      <div class="navy-img-wrap">
        <img :src="resolvedImage" :alt="item.title" class="navy-img" />
      </div>
      <div class="navy-body">
        <p class="navy-cat">{{ item.category_title || 'منو' }}</p>
        <h3 class="navy-title">{{ item.title }}</h3>
        <div class="navy-rating">
          <span class="navy-star">★</span>
          <span class="navy-rating-val">{{ item.rating || '4.8' }}</span>
        </div>
        <div class="navy-footer">
          <span class="navy-price">{{ formatMoney(item.base_price, currency) }}</span>
          <a :href="`/item/${item.slug}`" class="navy-arrow-btn" aria-label="مشاهده">→</a>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatMoney } from '@/utils/format'
import { getAverageRating, getReviewCount } from '@/utils/reviewsStore'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
  currency: {
    type: String,
    default: 'TOMAN',
  },
  cardVariant: {
    type: String,
    default: 'classic',
  },
})

defineEmits(['quick-add'])

const VALID_VARIANTS = ['classic', 'dark', 'navy']
const resolvedVariant = computed(() => {
  const v = String(props.cardVariant || 'classic').trim()
  return VALID_VARIANTS.includes(v) ? v : 'classic'
})

const resolvedImage = computed(
  () => props.item.image || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=900&auto=format&fit=crop&q=60',
)

const itemTags = computed(() => {
  const raw = props.item.tags || props.item.item_tags || []
  const arr = Array.isArray(raw) ? raw : []
  return arr
    .slice(0, 3)
    .map((t) => (typeof t === 'string' ? t : String(t?.tag || t?.name || '')))
    .filter(Boolean)
})

const itemSlug = computed(() => String(props.item.slug || '').trim())
const avgRating = computed(() => getAverageRating(itemSlug.value))
const reviewCnt = computed(() => getReviewCount(itemSlug.value))
</script>

<style scoped>
.menu-card {
  border-radius: var(--radius-lg, 18px);
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* ─── CLASSIC variant ─── */
.menu-card--classic {
  background: var(--glass-bg, #fdf8f1);
  border: 1px solid var(--glass-border, #d5c3af);
  box-shadow: var(--shadow-soft);
}

.classic-img-wrap {
  position: relative;
  height: 180px;
  background: var(--theme-surface-alt, #f1e7db);
}

.classic-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
}

.classic-price-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: var(--accent-green, #6f4a31);
  color: var(--palette-eggshell, #fbf8f4);
  border-radius: 999px;
  padding: 0.22rem 0.62rem;
  font-size: 0.78rem;
  font-weight: 700;
  box-shadow: 0 4px 12px rgb(var(--palette-deep-sapphire-rgb) / 0.22);
}

.classic-body {
  padding: 0.9rem;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.classic-cat {
  margin: 0 0 0.22rem;
  font-size: 0.72rem;
  color: var(--accent-gold, #c98d42);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.classic-title {
  margin: 0 0 0.3rem;
  font-size: 1.05rem;
  color: var(--text-primary, #3f2a1d);
  line-height: 1.3;
}

.classic-desc {
  margin: 0;
  font-size: 0.8rem;
  line-height: 1.5;
  flex: 1;
  color: var(--text-muted, #846b58);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.classic-rating {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  margin: 0.25rem 0 0;
}
.cr-stars { display: flex; gap: 0.05rem; }
.cr-star { font-size: 0.78rem; color: #ddd; }
.cr-star.filled { color: #f5a623; }
.cr-count { font-size: 0.72rem; color: var(--text-muted, #846b58); }

.classic-footer {
  margin-top: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.classic-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  flex: 1;
  min-width: 0;
}

.ctag {
  background: var(--accent-green40, rgba(111,74,49,0.14));
  color: var(--text-primary, #3f2a1d);
  border-radius: 999px;
  padding: 0.15rem 0.5rem;
  font-size: 0.68rem;
}

.classic-actions {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-shrink: 0;
}

.classic-link {
  font-size: 0.78rem;
  color: var(--accent-green, #6f4a31);
  text-decoration: none;
  font-weight: 600;
  white-space: nowrap;
}

.classic-add {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: var(--accent-green, #6f4a31);
  color: var(--palette-eggshell, #fbf8f4);
  font-size: 1.1rem;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ─── DARK variant ─── */
.menu-card--dark {
  background: var(--accent-green, #6f4a31);
}

.dark-img-wrap {
  position: relative;
  height: 200px;
}

.dark-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}

.dark-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, transparent 30%, var(--accent-green, #6f4a31) 100%);
}

.dark-delivery-label {
  position: absolute;
  bottom: 8px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 0.68rem;
  color: rgba(255, 255, 255, 0.75);
}

.dark-body {
  padding: 0.75rem 0.9rem 0.9rem;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 0.5rem;
}

.dark-info {
  flex: 1;
  min-width: 0;
}

.dark-title {
  margin: 0 0 0.35rem;
  font-size: 1.05rem;
  color: #fff;
  line-height: 1.3;
}

.dark-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.22rem;
}

.dtag {
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.85);
  border-radius: 999px;
  padding: 0.12rem 0.45rem;
  font-size: 0.66rem;
}

.dark-price-col {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
  flex-shrink: 0;
}

.dark-price {
  font-size: 1.12rem;
  color: #fff;
  font-weight: 800;
}

.dark-link {
  font-size: 0.74rem;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  font-weight: 600;
  white-space: nowrap;
}

/* ─── NAVY variant ─── */
.menu-card--navy {
  background: var(--accent-green, #6f4a31);
  position: relative;
}

.menu-card--navy::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.38);
  border-radius: inherit;
  pointer-events: none;
  z-index: 0;
}

.menu-card--navy > * {
  position: relative;
  z-index: 1;
}

.navy-add-btn {
  position: absolute;
  top: 12px;
  left: 12px;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  backdrop-filter: blur(4px);
}

.navy-img-wrap {
  height: 170px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
}

.navy-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  filter: drop-shadow(0 8px 20px rgba(0, 0, 0, 0.35));
}

.navy-body {
  padding: 0.5rem 0.9rem 0.9rem;
}

.navy-cat {
  margin: 0 0 0.15rem;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.55);
  font-weight: 500;
  letter-spacing: 0.03em;
}

.navy-title {
  margin: 0 0 0.3rem;
  font-size: 1.1rem;
  color: #fff;
  line-height: 1.25;
  font-weight: 700;
}

.navy-rating {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
}

.navy-star {
  color: var(--accent-gold, #c98d42);
  font-size: 0.9rem;
}

.navy-rating-val {
  font-size: 0.78rem;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 600;
}

.navy-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navy-price {
  font-size: 1.05rem;
  color: #fff;
  font-weight: 800;
}

.navy-arrow-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: none;
  background: var(--accent-green, #6f4a31);
  color: #fff;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}
</style>
