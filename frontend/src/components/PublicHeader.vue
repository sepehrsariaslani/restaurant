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
import MenuHeroHeader from '@/components/MenuHeroHeader.vue'
import SiteHeaderMinimal from '@/components/SiteHeaderMinimal.vue'

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
  search: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['search', 'update:search'])

const resolvedVariant = computed(() => String(props.headerVariant || 'classic').trim() || 'classic')

const resolvedComponent = computed(() => {
  if (resolvedVariant.value === 'search-card') {
    return MenuHeroHeader
  }
  if (resolvedVariant.value === 'minimal') {
    return SiteHeaderMinimal
  }
  return AppHeader
})

const headerKey = computed(() => `${resolvedVariant.value}:${props.page || 'public'}`)

const resolvedProps = computed(() => {
  if (resolvedVariant.value === 'search-card') {
    return {
      branding: props.branding,
      search: props.search,
      cartCount: props.cartCount,
    }
  }

  if (resolvedVariant.value === 'minimal') {
    return {
      branding: props.branding,
      cartCount: props.cartCount,
    }
  }

  return {
    branding: props.branding,
    cartCount: props.cartCount,
    hasLastOrder: props.hasLastOrder,
    lastOrderUrl: props.lastOrderUrl,
    page: props.page,
  }
})

const resolvedListeners = computed(() => {
  if (resolvedVariant.value !== 'search-card') {
    return {}
  }

  return {
    'update:search': (value) => emit('update:search', value),
    search: () => emit('search'),
  }
})
</script>
