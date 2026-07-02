<template>
  <component
    :is="def.component"
    v-if="def"
    v-bind="resolvedProps"
    @quick-add="$emit('quick-add', $event)"
  />
</template>

<script setup>
import { computed } from 'vue'
import { getBlockType } from '@/utils/blockRegistry'

const props = defineProps({
  block: { type: Object, required: true },
  boot: { type: Object, default: () => ({}) },
})

defineEmits(['quick-add'])

const def = computed(() => getBlockType(props.block?.type))

const resolvedProps = computed(() => {
  if (!def.value) return {}
  try {
    return def.value.toProps(props.block, props.boot) || {}
  } catch (err) {
    // A single bad block should never take down the whole page.
    // eslint-disable-next-line no-console
    console.error('Block render failed', props.block?.type, err)
    return {}
  }
})
</script>
