<template>
  <div class="hero-card" :class="{ 'is-mobile': mobile }">
    <!-- Image Column (right in RTL desktop, full-width mobile) -->
    <div class="hero-image-wrap">
      <img
        v-if="product.image"
        class="hero-image"
        :src="product.image"
        :alt="product.title"
        loading="lazy"
      />
      <div v-else class="hero-image-placeholder">
        {{ (product.title || '?').slice(0, 1) }}
      </div>
    </div>

    <!-- Content Column -->
    <div class="hero-content">
      <!-- Badges -->
      <div class="hero-badges" v-if="product.badges && product.badges.length">
        <span
          v-for="(badge, idx) in product.badges"
          :key="idx"
          class="hero-badge"
        >{{ badge }}</span>
      </div>

      <!-- Title -->
      <h3 class="hero-title">{{ product.title }}</h3>

      <!-- Subtitle -->
      <p v-if="product.subtitle" class="hero-subtitle">{{ product.subtitle }}</p>

      <!-- Description -->
      <p v-if="product.description" class="hero-desc">{{ product.description }}</p>

      <!-- Price -->
      <p v-if="product.price" class="hero-price">
        {{ formatPrice(product.price) }}
        <span class="hero-currency">{{ product.currency || 'TOMAN' }}</span>
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  product: {
    type: Object,
    required: true,
  },
  mobile: {
    type: Boolean,
    default: false,
  },
})

function formatPrice(value) {
  const num = Number(value || 0)
  return num.toLocaleString('fa-IR')
}
</script>

<style scoped>
.hero-card {
  display: grid;
  grid-template-columns: minmax(0, 55%) minmax(0, 45%);
  gap: 1.25rem;
  align-items: start;
  direction: rtl;
}

/* ── Image ── */
.hero-image-wrap {
  width: 100%;
  aspect-ratio: 3 / 4;
  border-radius: var(--preview-radius-sm);
  overflow: hidden;
  background: linear-gradient(135deg, rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.06), rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.04));
}

.hero-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.hero-image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  font-weight: 800;
  color: var(--preview-muted);
  background: linear-gradient(135deg, rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.08), rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.05));
}

/* ── Content ── */
.hero-content {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  text-align: right;
}

/* ── Badges ── */
.hero-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.hero-badge {
  display: inline-block;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  background: rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.12);
  color: var(--palette-deep-sapphire, #6f4a31);
}

/* ── Title ── */
.hero-title {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--preview-text);
  line-height: 1.4;
}

/* ── Subtitle ── */
.hero-subtitle {
  margin: 0;
  font-size: 0.85rem;
  color: var(--preview-muted);
}

/* ── Description ── */
.hero-desc {
  margin: 0;
  font-size: 0.88rem;
  color: var(--preview-muted);
  line-height: 1.7;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

/* ── Price ── */
.hero-price {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--preview-primary);
  font-variant-numeric: tabular-nums;
}

.hero-currency {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--preview-muted);
  margin-inline-start: 0.25rem;
}

/* ── Mobile (stacked) ── */
.hero-card.is-mobile {
  grid-template-columns: 1fr;
}

.hero-card.is-mobile .hero-image-wrap {
  aspect-ratio: 4 / 3;
  border-radius: 0;
}

.hero-card.is-mobile .hero-title {
  font-size: 1.1rem;
}
</style>
