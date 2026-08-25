<template>
  <component
    :is="resolvedComponent"
    :key="headerKey"
    v-bind="resolvedProps"
    v-on="resolvedListeners"
  />
</template>

<script setup>
import { computed } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import SiteHeaderMinimal from '@/components/SiteHeaderMinimal.vue'
import SiteHeaderHero from '@/components/SiteHeaderHero.vue'
import SiteHeaderGlass from '@/components/SiteHeaderGlass.vue'

const props = defineProps({
  branding: {
    type: Object,
    default: () => ({}),
  },
  cartCount: {
    type: Number,
    default: 0,
  },
  hasLastOrder: {
    type: Boolean,
    default: false,
  },
  lastOrderUrl: {
    type: String,
    default: '/menu',
  },
  page: {
    type: String,
    default: 'landing',
  },
  headerVariant: {
    type: String,
    default: 'classic',
  },
  preview: {
    type: Boolean,
    default: false,
  },
})

const resolvedVariant = computed(() => String(props.headerVariant || 'classic').trim() || 'classic')

const resolvedComponent = computed(() => {
  if (resolvedVariant.value === 'minimal') return SiteHeaderMinimal
  if (resolvedVariant.value === 'hero') return SiteHeaderHero
  if (resolvedVariant.value === 'glass') return SiteHeaderGlass
  return AppHeader
})

const headerKey = computed(() => `${resolvedVariant.value}:${props.page || 'public'}`)

const resolvedProps = computed(() => {
  if (resolvedVariant.value === 'minimal') {
    return {
      branding: props.branding,
      cartCount: props.cartCount,
      preview: props.preview,
    }
  }
  return {
    branding: props.branding,
    cartCount: props.cartCount,
    hasLastOrder: props.hasLastOrder,
    lastOrderUrl: props.lastOrderUrl,
    page: props.page,
    preview: props.preview,
  }
})
const resolvedListeners = computed(() => ({}))
</script>
