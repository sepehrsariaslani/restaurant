<template>
  <section class="collection-view">
    <slot name="toolbar" />

    <ManagementViewSwitcher
      v-if="showModeSelector"
      v-model="internalMode"
      :modes="modes"
      class="collection-switcher"
    />

    <slot v-if="internalMode === 'list'" name="list" />
    <slot v-else-if="internalMode === 'gallery'" name="gallery" />
    <slot v-else-if="internalMode === 'tree'" name="tree" />
    <slot v-else />
  </section>
</template>

<script setup>
import { computed } from 'vue'
import ManagementViewSwitcher from '@/components/management/ManagementViewSwitcher.vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: 'list',
  },
  modes: {
    type: Array,
    default: () => [
      { value: 'list', label: 'لیست', icon: '≡' },
      { value: 'gallery', label: 'گالری', icon: '▦' },
      { value: 'tree', label: 'درخت', icon: '⋰' },
    ],
  },
  showModeSelector: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['update:modelValue'])

const internalMode = computed({
  get() {
    return String(props.modelValue || 'list').trim() || 'list'
  },
  set(value) {
    emit('update:modelValue', String(value || 'list').trim() || 'list')
  },
})
</script>

<style scoped>
.collection-view {
  display: grid;
  gap: 0.6rem;
}

.collection-switcher {
  width: fit-content;
}
</style>
