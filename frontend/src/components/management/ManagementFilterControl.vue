<template>
  <label class="filter-control">
    <span class="filter-label">{{ label }}</span>
    <SearchableDropdown
      :model-value="modelValue"
      :options="options"
      :placeholder="placeholder"
      :search-placeholder="searchPlaceholder"
      :include-empty-option="includeEmptyOption"
      :empty-label="emptyLabel"
      :clearable="clearable"
      :multiple="multiple"
      @update:model-value="$emit('update:modelValue', $event)"
    />
  </label>
</template>

<script setup>
import SearchableDropdown from '@/components/SearchableDropdown.vue'

defineProps({
  modelValue: {
    type: [String, Number, Array],
    default: '',
  },
  options: {
    type: Array,
    default: () => [],
  },
  label: {
    type: String,
    default: 'فیلتر',
  },
  placeholder: {
    type: String,
    default: 'انتخاب کنید',
  },
  searchPlaceholder: {
    type: String,
    default: 'جستجو...',
  },
  includeEmptyOption: {
    type: Boolean,
    default: true,
  },
  emptyLabel: {
    type: String,
    default: 'همه',
  },
  clearable: {
    type: Boolean,
    default: true,
  },
  multiple: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.filter-control {
  display: grid;
  gap: 0.24rem;
  min-width: 210px;
}

.filter-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-muted);
}
</style>
