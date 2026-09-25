<template>
  <button
    type="button"
    class="share-website-button"
    :class="[attrs.class, `share-website-button--${appearance}`]"
    :aria-label="label"
    :title="label"
    :aria-busy="isSharing ? 'true' : undefined"
    :disabled="isSharing"
    @click="sharePage"
  >
    <slot>
      <Share2 :size="iconSize" aria-hidden="true" />
      <span v-if="appearance !== 'icon'">{{ label }}</span>
    </slot>
  </button>

  <Teleport to="body">
    <Transition name="share-feedback">
      <div
        v-if="feedbackMessage"
        class="share-website-feedback"
        dir="rtl"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        {{ feedbackMessage }}
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { onBeforeUnmount, ref, useAttrs } from 'vue'
import { Share2 } from 'lucide-vue-next'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  title: { type: String, default: '' },
  text: { type: String, default: '' },
  url: { type: String, default: '' },
  label: { type: String, default: 'اشتراک‌گذاری' },
  appearance: {
    type: String,
    default: 'icon',
    validator: (value) => ['icon', 'action', 'menu'].includes(value),
  },
  iconSize: { type: Number, default: 18 },
})

const emit = defineEmits(['shared', 'copied', 'error'])
const attrs = useAttrs()
const feedbackMessage = ref('')
const isSharing = ref(false)
let feedbackTimer = null

function notify(message) {
  feedbackMessage.value = message
  clearTimeout(feedbackTimer)
  feedbackTimer = setTimeout(() => {
    feedbackMessage.value = ''
    feedbackTimer = null
  }, 2200)
}

async function copyText(value) {
  if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(value)
      return true
    } catch (_) {
      // Continue to the selection-based fallback when clipboard permission is unavailable.
    }
  }

  if (typeof document === 'undefined' || !document.body) return false
  const field = document.createElement('textarea')
  field.value = value
  field.setAttribute('readonly', '')
  field.style.position = 'fixed'
  field.style.opacity = '0'
  field.style.pointerEvents = 'none'
  field.style.left = '-9999px'
  document.body.appendChild(field)
  field.select()

  let copied = false
  try {
    copied = document.execCommand('copy')
  } catch (_) {
    copied = false
  } finally {
    field.remove()
  }
  return copied
}

async function copyPageLink(url) {
  const copied = await copyText(url)
  if (copied) {
    notify('پیوند صفحه کپی شد')
    emit('copied', url)
    return
  }
  notify('کپی پیوند انجام نشد')
  emit('error', new Error('Clipboard copy failed'))
}

async function sharePage() {
  if (isSharing.value || typeof window === 'undefined') return
  const url = String(props.url || window.location.href).trim()
  if (!url) {
    notify('پیوند این صفحه در دسترس نیست')
    return
  }

  const title = String(props.title || document.title || '').trim()
  const text = String(props.text || '').trim()
  const data = { title, url, ...(text ? { text } : {}) }
  isSharing.value = true
  try {
    if (typeof navigator !== 'undefined' && typeof navigator.share === 'function') {
      try {
        await navigator.share(data)
        notify('صفحه به اشتراک گذاشته شد')
        emit('shared', data)
        return
      } catch (error) {
        if (error?.name === 'AbortError') return
      }
    }
    await copyPageLink(url)
  } finally {
    isSharing.value = false
  }
}

onBeforeUnmount(() => clearTimeout(feedbackTimer))
</script>

<style scoped>
.share-website-button {
  min-width: 44px;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  font: inherit;
  cursor: pointer;
  transition: color var(--ds-motion-fast, 160ms), background var(--ds-motion-fast, 160ms), border-color var(--ds-motion-fast, 160ms), transform var(--ds-motion-fast, 160ms);
}

.share-website-button:disabled {
  cursor: wait;
  opacity: 0.7;
}

.share-website-button--icon {
  width: 44px;
  height: 44px;
  border: 0;
  border-radius: 50%;
  color: var(--ds-color-text-primary);
  background: color-mix(in srgb, var(--ds-color-surface-raised) 84%, transparent);
  box-shadow: var(--ds-shadow-sm, 0 4px 12px rgb(0 0 0 / 0.14));
  backdrop-filter: blur(8px);
}

.share-website-button--action {
  padding: 0.55rem 0.9rem;
  border: 1.5px solid var(--ds-color-border);
  border-radius: 14px;
  color: var(--ds-color-text-secondary);
  background: var(--ds-color-surface-raised);
  font-size: 0.82rem;
  font-weight: 600;
}

.share-website-button--menu {
  width: 100%;
  min-height: 72px;
  padding: 0.55rem;
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) 16px;
  align-items: center;
  gap: 0.5rem;
  border: 1px solid var(--ds-color-border);
  border-radius: 17px;
  color: var(--ds-color-text-primary);
  background: var(--ds-color-surface);
  text-align: start;
}

.share-website-button--icon:hover,
.share-website-button--action:hover {
  color: var(--ds-color-action-primary);
  border-color: var(--ds-color-action-primary);
  background: var(--ds-color-action-primary-soft);
}

.share-website-button--menu:hover {
  border-color: color-mix(in srgb, var(--ds-color-action-primary) 38%, var(--ds-color-border));
  background: color-mix(in srgb, var(--ds-color-action-primary) 5%, var(--ds-color-surface));
}

.share-website-button:focus-visible {
  outline: 3px solid var(--ds-color-focus-ring);
  outline-offset: 3px;
}

.share-website-feedback {
  position: fixed;
  z-index: var(--ds-z-overlay, 1100);
  bottom: calc(5.4rem + env(safe-area-inset-bottom));
  left: 50%;
  max-width: min(90vw, 32rem);
  padding: 0.6rem 1rem;
  border-radius: 999px;
  color: var(--ds-color-action-primary-foreground);
  background: var(--ds-color-action-primary);
  box-shadow: var(--ds-shadow-md);
  font-size: 0.82rem;
  font-weight: 600;
  text-align: center;
  white-space: normal;
  transform: translateX(-50%);
}

.share-feedback-enter-active,
.share-feedback-leave-active {
  transition: opacity var(--ds-motion-fast, 160ms), transform var(--ds-motion-fast, 160ms);
}

.share-feedback-enter-from,
.share-feedback-leave-to {
  opacity: 0;
  transform: translate(-50%, 10px);
}

@media (min-width: 768px) {
  .share-website-feedback { bottom: 2rem; }
}

@media (prefers-reduced-motion: reduce) {
  .share-website-button,
  .share-feedback-enter-active,
  .share-feedback-leave-active {
    transition-duration: 0.01ms;
  }
}
</style>
