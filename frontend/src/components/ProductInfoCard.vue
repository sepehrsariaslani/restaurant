<template>
  <div class="product-hero-card">
    <!-- Text Content (left in RTL) -->
    <div class="product-hero__content">
      <!-- Category chips / badges row -->
      <div class="product-hero__chips" v-if="item.category_title || item.subcategory_title">
        <span
          v-if="item.category_title"
          class="product-hero__chip product-hero__chip--category"
        >{{ item.category_title }}</span>
        <span
          v-if="item.subcategory_title"
          class="product-hero__chip product-hero__chip--combo"
        >{{ item.subcategory_title }}</span>
      </div>

      <!-- Product title -->
      <h2 class="product-hero__title">{{ item.title }}</h2>

      <!-- Short description -->
      <p v-if="item.short_desc || item.long_desc" class="product-hero__desc">
        {{ item.short_desc || item.long_desc }}
      </p>
    </div>

    <!-- Image Column (right in RTL) -->
    <div class="product-hero__image-col">
      <img
        class="product-hero__image"
        :src="resolvedImage"
        :alt="item.title"
        loading="lazy"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  item: { type: Object, required: true },
})

const fallbackImage = 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=900&auto=format&fit=crop&q=60'

const resolvedImage = computed(() => {
  const img = String(props.item?.image || props.item?.item_image || props.item?.website_image || '').trim()
  return img || fallbackImage
})
</script>

<style scoped>
.product-hero-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px;
  gap: 24px;
  align-items: center;
  direction: rtl;
  padding: 24px;
  min-height: 230px;
  background: var(--glass-bg, #ffffff);
  border-radius: 24px;
  border: 1px solid var(--theme-border, rgba(0, 0, 0, 0.06));
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

/* ── Image column (right side in RTL) ── */
.product-hero__image-col {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 220px;
  height: 200px;
}

.product-hero__image {
  width: 210px;
  height: 190px;
  object-fit: contain;
  border-radius: 16px;
  display: block;
}

/* ── Text content column (left side in RTL) ── */
.product-hero__content {
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: stretch;
  text-align: right;
  gap: 0.4rem;
}

/* ── Category chips ── */
.product-hero__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.2rem;
}

.product-hero__chip {
  display: inline-block;
  padding: 3px 12px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  line-height: 1.5;
  white-space: nowrap;
}

.product-hero__chip--category {
  background: var(--accent-green20, #fff0e8);
  color: var(--accent-orange, #ff5a1f);
}

.product-hero__chip--combo {
  background: var(--accent-cream20, #e8f0ec);
  color: var(--accent-green, #24473b);
}

/* ── Title ── */
.product-hero__title {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--text-primary, #3f2a1d);
  line-height: 1.35;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  max-width: 100%;
}

/* ── Description ── */
.product-hero__desc {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-secondary, #654a38);
  text-align: right;
  line-height: 1.6;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  max-width: 100%;
}

/* ── Tablet ── */
@media (max-width: 768px) {
  .product-hero-card {
    grid-template-columns: minmax(0, 1fr) 160px;
    gap: 16px;
    padding: 20px;
    border-radius: 22px;
  }

  .product-hero__image-col {
    width: 160px;
    height: 150px;
  }

  .product-hero__image {
    width: 140px;
    height: 130px;
  }

  .product-hero__title {
    font-size: 1.35rem;
  }
}

/* ── Mobile ── */
@media (max-width: 600px) {
  .product-hero-card {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 20px;
    min-height: auto;
    border-radius: 22px;
  }

  .product-hero__image-col {
    width: 100%;
    height: auto;
    order: -1;
  }

  .product-hero__image {
    width: 140px;
    height: 140px;
    margin: 0 auto;
  }

  .product-hero__title {
    font-size: 1.25rem;
  }

  .product-hero__chips {
    justify-content: flex-start;
  }
}

@media (max-width: 360px) {
  .product-hero-card {
    padding: 16px;
    gap: 12px;
  }

  .product-hero__image {
    width: 120px;
    height: 120px;
  }

  .product-hero__title {
    font-size: 1.1rem;
  }

  .product-hero__chip {
    font-size: 0.65rem;
    padding: 2px 8px;
  }
}
</style>
