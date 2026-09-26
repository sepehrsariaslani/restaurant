<template>
  <div class="management-collection-toolbar" dir="rtl">
    <label class="management-collection-toolbar__search">
      <Search :size="17" aria-hidden="true" />
      <span class="sr-only">{{ searchLabel }}</span>
      <input
        type="search"
        :value="search"
        :placeholder="searchPlaceholder"
        :disabled="disabled"
        @input="$emit('update:search', $event.target.value)"
        @keydown.enter.prevent="$emit('search')"
      />
      <button
        v-if="search"
        type="button"
        class="management-collection-toolbar__clear"
        :aria-label="clearLabel"
        :title="clearLabel"
        :disabled="disabled"
        @click="$emit('update:search', ''); $emit('search')"
      >
        <X :size="15" aria-hidden="true" />
      </button>
    </label>

    <div v-if="$slots.filters" class="management-collection-toolbar__filters"><slot name="filters" /></div>
    <div v-if="$slots.secondary" class="management-collection-toolbar__secondary"><slot name="secondary" /></div>
    <button
      v-if="primaryLabel"
      type="button"
      class="primary-btn management-collection-toolbar__primary"
      :disabled="disabled || primaryDisabled"
      @click="$emit('primary')"
    >
      <Plus v-if="showPlus" :size="17" aria-hidden="true" />
      {{ primaryLabel }}
    </button>
    <div v-if="$slots.below" class="management-collection-toolbar__below"><slot name="below" /></div>
  </div>
</template>

<script setup>
import { Plus, Search, X } from 'lucide-vue-next'

defineProps({
  search: { type: String, default: '' },
  searchLabel: { type: String, default: 'جستجو' },
  searchPlaceholder: { type: String, default: 'جستجو...' },
  clearLabel: { type: String, default: 'پاک کردن جستجو' },
  primaryLabel: { type: String, default: '' },
  primaryDisabled: { type: Boolean, default: false },
  showPlus: { type: Boolean, default: true },
  disabled: { type: Boolean, default: false },
})

defineEmits(['update:search', 'search', 'primary'])
</script>

<style scoped>
.management-collection-toolbar {
  display: grid;
  grid-template-columns: minmax(220px, 1.4fr) repeat(2, minmax(140px, auto)) auto;
  align-items: center;
  gap: var(--ds-space-2, .5rem);
  min-width: 0;
}

.management-collection-toolbar__search {
  display: flex;
  align-items: center;
  gap: var(--ds-space-2, .5rem);
  min-width: 0;
  min-height: 44px;
  padding-inline: var(--ds-space-3, .75rem);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-sm, 10px);
  background: var(--ds-color-surface);
  color: var(--ds-color-text-muted);
}

.management-collection-toolbar__search:focus-within {
  border-color: var(--ds-color-focus-ring);
  box-shadow: 0 0 0 3px var(--ds-color-action-accent-soft);
}

.management-collection-toolbar__search input {
  flex: 1;
  width: 100%;
  min-width: 0;
  min-height: 42px;
  padding: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--ds-color-text-primary);
  font: inherit;
}

.management-collection-toolbar__search input::placeholder { color: var(--ds-color-text-muted); }
.management-collection-toolbar__filters,
.management-collection-toolbar__secondary { display: flex; align-items: center; gap: var(--ds-space-2, .5rem); min-width: 0; flex-wrap: wrap; }
.management-collection-toolbar__primary { min-height: 44px; white-space: nowrap; }
.management-collection-toolbar__clear { display: inline-grid; place-items: center; width: 32px; height: 32px; flex: 0 0 auto; border: 0; border-radius: 50%; background: transparent; color: var(--ds-color-text-muted); cursor: pointer; }
.management-collection-toolbar__clear:hover { background: var(--ds-color-surface-muted); color: var(--ds-color-text-primary); }
.management-collection-toolbar__clear:focus-visible,
.management-collection-toolbar__primary:focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 2px; }
.management-collection-toolbar__below { grid-column: 1 / -1; min-width: 0; }

@media (max-width: 760px) {
  .management-collection-toolbar { grid-template-columns: minmax(0, 1fr) auto; }
  .management-collection-toolbar__search { grid-column: 1 / -1; }
  .management-collection-toolbar__filters { grid-column: 1 / -1; }
  .management-collection-toolbar__secondary { grid-column: 1; }
  .management-collection-toolbar__primary { grid-column: 2; }
}

@media (max-width: 420px) {
  .management-collection-toolbar { grid-template-columns: 1fr; }
  .management-collection-toolbar__secondary,
  .management-collection-toolbar__primary { grid-column: 1; width: 100%; }
}
</style>
