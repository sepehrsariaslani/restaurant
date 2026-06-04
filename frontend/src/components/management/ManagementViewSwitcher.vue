<template>
  <div class="view-switcher" role="tablist" aria-label="نوع نمایش">
    <button
      v-for="mode in normalizedModes"
      :key="mode.value"
      type="button"
      class="switch-btn"
      :class="{ active: modelValue === mode.value }"
      role="tab"
      :aria-selected="modelValue === mode.value"
      @click="$emit('update:modelValue', mode.value)"
    >
      <span class="icon" aria-hidden="true">{{ mode.icon }}</span>
      <span>{{ mode.label }}</span>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: 'list',
  },
  modes: {
    type: Array,
    default: () => [
      { value: 'list', label: 'لیست', icon: '≡' },
      { value: 'gallery', label: 'گالری', icon: '▤' },
      { value: 'tree', label: 'درخت', icon: '⋰' },
    ],
  },
})

defineEmits(['update:modelValue'])

const normalizedModes = computed(() => {
  return (props.modes || []).map((mode) => ({
    value: String(mode?.value || '').trim() || 'list',
    label: String(mode?.label || mode?.value || '').trim() || 'نمایش',
    icon: String(mode?.icon || '•'),
  }))
})
</script>

<style scoped>
.view-switcher {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.22);
  border-radius: 999px;
  padding: 0.2rem;
  background: rgb(var(--palette-eggshell-rgb) / 0.75);
}

.switch-btn {
  border: none;
  border-radius: 999px;
  padding: 0.35rem 0.62rem;
  background: transparent;
  color: var(--text-muted);
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.76rem;
  font-weight: 600;
  cursor: pointer;
}

.switch-btn.active {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.9);
  color: #fff;
}

.switch-btn .icon {
  font-size: 0.75rem;
  line-height: 1;
}
</style>
