<template>
  <section class="category-masonry glass-card" dir="rtl" v-if="resolvedCategories.length">
    <h3 class="section-title">دسته بندی غذاها</h3>

    <div class="masonry">
      <a
        v-for="(cat, index) in resolvedCategories"
        :key="cat.key"
        :href="cat.url"
        class="masonry-item"
        :class="`size-${index % 5}`"
      >
        <img :src="cat.image" :alt="cat.title" />

        <div class="overlay">
          <h4>{{ cat.title }}</h4>
          <span class="count" v-if="cat.count">
            {{ cat.count }} آیتم
          </span>
        </div>
      </a>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  categories: {
    type: Array,
    default: () => [],
  },
})

const resolvedCategories = computed(() => {
  return (props.categories || []).map((cat, idx) => ({
    key: cat.slug || `cat-${idx}`,
    title: cat.title || 'دسته بندی',
    image:
      cat.image ||
      'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=900&auto=format&fit=crop&q=60',
    url: cat.slug ? `/menu?category=${cat.slug}` : '/menu',
    count: cat.items_count || null,
  }))
})
</script>

<style scoped>
.category-masonry {
  margin: 0.4rem 0;
  padding: 1rem;
}

.section-title {
  margin-bottom: 0.95rem;
  font-size: 1.3rem;
}

/* masonry layout */

.masonry {
  column-count: 4;
  column-gap: 0.7rem;
}

.masonry-item {
  position: relative;
  display: block;
  break-inside: avoid;
  margin-bottom: 0.7rem;
  border-radius: 16px;
  overflow: hidden;
}

.masonry-item img {
  width: 100%;
  display: block;
  object-fit: cover;
  transition: transform 0.4s ease;
}

/* variable heights */

.size-0 img { height: 160px; }
.size-1 img { height: 220px; }
.size-2 img { height: 190px; }
.size-3 img { height: 260px; }
.size-4 img { height: 180px; }

.masonry-item:hover img {
  transform: scale(1.06);
}

/* overlay */

.overlay {
  position: absolute;
  inset: 0;
  background: rgb(15 23 42 / 0.5);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 0.75rem;
  color: #fff;
}

.overlay h4 {
  margin: 0;
  font-size: 1rem;
}

.count {
  font-size: 0.78rem;
  opacity: 0.85;
}

/* responsive */

@media (max-width: 900px) {
  .masonry {
    column-count: 3;
  }
}

@media (max-width: 520px) {
  .masonry {
    column-count: 2;
  }

  .size-3 img {
    height: 200px;
  }
}
</style>
