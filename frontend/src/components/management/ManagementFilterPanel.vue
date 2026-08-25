<template>
  <section class="glass-card filter-panel" :class="{ compact }">
    <header class="filter-head" v-if="title || subtitle || $slots.actions">
      <div>
        <h3 v-if="title">{{ title }}</h3>
        <p v-if="subtitle" class="muted">{{ subtitle }}</p>
      </div>
      <slot name="actions" />
    </header>

    <div class="filter-body">
      <slot name="before" />

      <div class="primary-row" v-if="showSearch">
        <label class="search-wrap">
          <span v-if="searchLabel">{{ searchLabel }}</span>
          <input
            class="input"
            type="text"
            :value="search"
            :placeholder="searchPlaceholder"
            @input="onSearchInput"
            @keydown.enter.prevent="emit('apply')"
          />
        </label>
      </div>

      <div class="fields-row">
        <slot />
      </div>

      <slot name="after" />

      <footer class="action-row" v-if="showApply || showReset || $slots['extra-actions']">
        <button
          v-if="showApply"
          type="button"
          class="primary-btn"
          :disabled="loading"
          @click="emit('apply')"
        >
          {{ loading ? loadingLabel : applyLabel }}
        </button>
        <button
          v-if="showReset"
          type="button"
          class="secondary-btn"
          :disabled="loading"
          @click="emit('reset')"
        >
          {{ resetLabel }}
        </button>
        <slot name="extra-actions" />
      </footer>
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
  search: {
    type: String,
    default: '',
  },
  searchLabel: {
    type: String,
    default: '',
  },
  searchPlaceholder: {
    type: String,
    default: 'جستجو...',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  showSearch: {
    type: Boolean,
    default: true,
  },
  showApply: {
    type: Boolean,
    default: true,
  },
  showReset: {
    type: Boolean,
    default: true,
  },
  applyLabel: {
    type: String,
    default: 'اعمال فیلتر',
  },
  resetLabel: {
    type: String,
    default: 'حذف فیلترها',
  },
  loadingLabel: {
    type: String,
    default: 'در حال اعمال...',
  },
  compact: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:search', 'apply', 'reset'])

function onSearchInput(event) {
  emit('update:search', event?.target?.value || '')
}
</script>

<style scoped>
.filter-panel {
  border-radius: 18px;
  border: 1px solid var(--border, var(--mg-border-light));
  background: var(--bg-card, #fff);
  box-shadow: var(--shadow-sm, 0 8px 22px rgb(15 23 42 / 0.045));
}

.filter-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.6rem;
}

.filter-head h3 {
  margin: 0;
  font-size: 0.95rem;
}

.filter-head p {
  margin: 0.2rem 0 0;
  font-size: 0.76rem;
}

.filter-body {
  display: grid;
  gap: 0.6rem;
}

.primary-row {
  display: grid;
}

.search-wrap {
  display: grid;
  gap: 0.22rem;
  font-size: 0.78rem;
}

.fields-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.55rem;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.compact .fields-row {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 980px) {
  .fields-row,
  .compact .fields-row {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
