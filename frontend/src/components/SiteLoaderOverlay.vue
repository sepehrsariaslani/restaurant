<template>
  <Transition name="loader-fade">
    <div
      v-if="isVisible"
      class="site-loader-overlay"
      :style="overlayStyle"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <SiteLoaderRenderer :settings="normalized" />
    </div>
  </Transition>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import SiteLoaderRenderer from '@/components/SiteLoaderRenderer.vue'
import { normalizeLoaderSettings } from '@/utils/loaderSettings'

const props = defineProps({
  settings: {
    type: Object,
    default: () => ({}),
  },
  enableNavigationLoader: {
    type: Boolean,
    default: true,
  },
})

const normalized = computed(() => normalizeLoaderSettings(props.settings || {}))
const isVisible = ref(false)
let loadFallbackTimer = null
let hideTimer = null
let navigationHideTimer = null

const overlayStyle = computed(() => ({
  background: normalized.value.overlayColor,
}))

function clearTimers() {
  if (loadFallbackTimer) {
    window.clearTimeout(loadFallbackTimer)
    loadFallbackTimer = null
  }
  if (hideTimer) {
    window.clearTimeout(hideTimer)
    hideTimer = null
  }
  if (navigationHideTimer) {
    window.clearTimeout(navigationHideTimer)
    navigationHideTimer = null
  }
}

function hideAfterMinimumTime() {
  clearTimers()
  const delay = Math.max(0, Number(normalized.value.minDurationMs || 0))
  hideTimer = window.setTimeout(() => {
    isVisible.value = false
  }, delay)
}

function isValidInternalLink(anchor) {
  if (!anchor) {
    return false
  }
  if (anchor.target && anchor.target !== '_self') {
    return false
  }
  if (anchor.hasAttribute('download')) {
    return false
  }
  const href = String(anchor.getAttribute('href') || '').trim()
  if (!href || href.startsWith('#') || href.startsWith('javascript:') || href.startsWith('mailto:') || href.startsWith('tel:')) {
    return false
  }
  try {
    const target = new URL(href, window.location.origin)
    const isSameOrigin = target.origin === window.location.origin
    const isManagement = target.pathname.startsWith('/management')
    const isSameLocation = target.pathname === window.location.pathname && target.search === window.location.search
    return isSameOrigin && !isManagement && !isSameLocation
  } catch (error) {
    return false
  }
}

function onDocumentClick(event) {
  const anchor = event.target?.closest?.('a[href]')
  if (!isValidInternalLink(anchor)) {
    return
  }
  isVisible.value = true
  if (navigationHideTimer) {
    window.clearTimeout(navigationHideTimer)
  }
  navigationHideTimer = window.setTimeout(() => {
    if (document.visibilityState === 'visible') {
      isVisible.value = false
    }
  }, 2000)
}

onMounted(() => {
  if (!normalized.value.enabled) {
    return
  }
  isVisible.value = true

  if (document.readyState === 'complete') {
    hideAfterMinimumTime()
  } else {
    window.addEventListener('load', hideAfterMinimumTime, { once: true })
    loadFallbackTimer = window.setTimeout(hideAfterMinimumTime, 3000)
  }

  if (props.enableNavigationLoader) {
    document.addEventListener('click', onDocumentClick, true)
  }
})

onBeforeUnmount(() => {
  clearTimers()
  window.removeEventListener('load', hideAfterMinimumTime)
  document.removeEventListener('click', onDocumentClick, true)
})
</script>

<style scoped>
.site-loader-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: grid;
  place-items: center;
  padding: 1rem;
  backdrop-filter: blur(4px);
}

.loader-fade-enter-active,
.loader-fade-leave-active {
  transition: opacity 0.42s ease;
}

.loader-fade-enter-from,
.loader-fade-leave-to {
  opacity: 0;
}
</style>
