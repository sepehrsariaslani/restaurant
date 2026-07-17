<template>
  <aside class="category-sidebar">
    <header>
      <h3>دسته بندی</h3>
      <small>{{ categories.length }} دسته</small>
    </header>

    <div class="category-list" v-if="!loading">
      <button
        type="button"
        class="category-item"
        :class="{ active: selectedCategory === '' }"
        @click="$emit('update:selectedCategory', '')"
      >
        همه دسته ها
      </button>
      <button
        v-for="category in categories"
        :key="category.slug || category.name"
        type="button"
        class="category-item"
        :class="{ active: selectedCategory === category.slug }"
        @click="$emit('update:selectedCategory', category.slug)"
      >
        {{ category.title || category.name }}
      </button>
    </div>

    <p class="hint" v-else>در حال بارگذاری دسته‌ها...</p>
  </aside>
</template>

<script setup>
defineProps({
  categories: {
    type: Array,
    default: () => [],
  },
  selectedCategory: {
    type: String,
    default: '',
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['update:selectedCategory'])
</script>

<style scoped>
.category-sidebar {
  border-radius: 18px;
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-surface);
  padding: 0.75rem;
  color: var(--mg-text-main);
  min-height: 620px;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.6rem;
}

header h3 {
  margin: 0;
  font-size: 0.9rem;
}

header small {
  color: rgb(var(--mg-primary-rgb, 1 90 114) / 0.72);
  font-size: 0.72rem;
}

.category-list {
  display: grid;
  gap: 0.35rem;
}

.category-item {
  width: 100%;
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  padding: 0.48rem 0.55rem;
  text-align: right;
  background: var(--mg-bg-surface);
  color: var(--mg-text-main);
  cursor: pointer;
}

.category-item.active {
  background: var(--mg-primary);
  color: var(--mg-bg-surface);
  border-color: var(--mg-primary);
  font-weight: 600;
}

.hint {
  margin: 0;
  color: rgb(var(--mg-primary-rgb, 1 90 114) / 0.72);
  font-size: 0.78rem;
}

@media (max-width: 980px) {
  .category-sidebar {
    min-height: 0;
  }

  .category-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
