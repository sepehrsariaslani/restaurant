<template>
  <label class="sort-control">
    <span class="sort-label">{{ label }}</span>
    <SearchableDropdown
      :model-value="modelValue"
      :options="options"
      :placeholder="placeholder"
      :search-placeholder="searchPlaceholder"
      :include-empty-option="false"
      @update:model-value="$emit('update:modelValue', $event)"
    />
  </label>
</template>

<script setup>
import SearchableDropdown from '@/components/SearchableDropdown.vue'

defineProps({
  modelValue: {
    type: String,
    default: 'latest',
  },
  options: {
    type: Array,
    default: () => [],
  },
  label: {
    type: String,
    default: 'مرتب سازی',
  },
  placeholder: {
    type: String,
    default: 'انتخاب نوع مرتب سازی',
  },
  searchPlaceholder: {
    type: String,
    default: 'جستجوی نوع مرتب سازی...',
  },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.sort-control {
  display: grid;
  gap: 0.24rem;
  min-width: 210px;
}

.sort-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-muted);
}
</style>
