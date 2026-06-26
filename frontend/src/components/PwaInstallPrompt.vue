<template>
  <transition name="pwa-install">
    <aside v-if="shouldShow" class="pwa-install" dir="rtl" role="status">
      <div class="pwa-install__icon">
        <Smartphone :size="20" />
      </div>
      <div class="pwa-install__copy">
        <strong>نصب وب‌اپ رستوران</strong>
        <span>{{ helperText }}</span>
      </div>
      <button v-if="canInstall" class="pwa-install__primary" type="button" @click="installApp">
        نصب
      </button>
      <button class="pwa-install__close" type="button" @click="dismiss" aria-label="بستن">
        <X :size="16" />
      </button>
    </aside>
  </transition>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Smartphone, X } from 'lucide-vue-next'

const DISMISS_KEY = 'restaurant_pwa_install_dismissed_at'
const DISMISS_DAYS = 14

const deferredPrompt = ref(null)
const isStandalone = ref(false)
const isDismissed = ref(false)
const isIos = ref(false)

const canInstall = computed(() => Boolean(deferredPrompt.value))
const helperText = computed(() => {
  if (canInstall.value) return 'برای دسترسی سریع‌تر، اپ را روی گوشی نصب کن.'
  if (isIos.value) return 'در Safari از Share گزینه Add to Home Screen را انتخاب کن.'
  return 'وقتی مرورگر اجازه نصب بدهد، همین‌جا نمایش داده می‌شود.'
})

const shouldShow = computed(() => {
  if (isStandalone.value || isDismissed.value) return false
  return canInstall.value || isIos.value
})

function readDismissed() {
  try {
    const raw = window.localStorage.getItem(DISMISS_KEY)
    if (!raw) return false
    const dismissedAt = Number(raw)
    if (!Number.isFinite(dismissedAt)) return false
    const maxAge = DISMISS_DAYS * 24 * 60 * 60 * 1000
    return Date.now() - dismissedAt < maxAge
  } catch (error) {
    return false
  }
}

function dismiss() {
  isDismissed.value = true
  try {
    window.localStorage.setItem(DISMISS_KEY, String(Date.now()))
  } catch (error) {
    // localStorage may be unavailable in private browsing.
  }
}

async function installApp() {
  if (!deferredPrompt.value) return
  const promptEvent = deferredPrompt.value
  deferredPrompt.value = null
  promptEvent.prompt()
  await promptEvent.userChoice.catch(() => undefined)
  dismiss()
}

function handleBeforeInstallPrompt(event) {
  event.preventDefault()
  deferredPrompt.value = event
}

function handleInstalled() {
  isStandalone.value = true
  dismiss()
}

onMounted(() => {
  const standaloneMedia = window.matchMedia?.('(display-mode: standalone)')?.matches
  isStandalone.value = Boolean(standaloneMedia || window.navigator.standalone)
  isIos.value = /iphone|ipad|ipod/i.test(window.navigator.userAgent || '')
  isDismissed.value = readDismissed()

  window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
  window.addEventListener('appinstalled', handleInstalled)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
  window.removeEventListener('appinstalled', handleInstalled)
})
</script>

<style scoped>
.pwa-install {
  position: fixed;
  left: max(0.85rem, env(safe-area-inset-left));
  right: max(0.85rem, env(safe-area-inset-right));
  bottom: calc(5.55rem + env(safe-area-inset-bottom));
  z-index: 118;
  max-width: 520px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) auto 32px;
  align-items: center;
  gap: 0.55rem;
  padding: 0.62rem;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  color: var(--text-primary);
  box-shadow: 0 16px 38px rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  backdrop-filter: blur(16px);
}

.pwa-install__icon {
  width: 38px;
  height: 38px;
  border-radius: 15px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--accent-green), var(--accent-green80, var(--accent-green)));
  color: #fff;
}

.pwa-install__copy {
  min-width: 0;
  display: grid;
  gap: 0.12rem;
}

.pwa-install__copy strong,
.pwa-install__copy span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pwa-install__copy strong {
  font-size: 0.78rem;
  font-weight: 900;
}

.pwa-install__copy span {
  color: var(--text-muted);
  font-size: 0.66rem;
  font-weight: 700;
}

.pwa-install__primary,
.pwa-install__close {
  border: 0;
  font-family: inherit;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.pwa-install__primary {
  min-height: 32px;
  border-radius: 13px;
  padding: 0 0.72rem;
  background: var(--accent-green);
  color: #fff;
  font-size: 0.72rem;
  font-weight: 900;
}

.pwa-install__close {
  width: 32px;
  height: 32px;
  border-radius: 12px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.06);
  color: var(--text-secondary);
}

.pwa-install-enter-active,
.pwa-install-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.pwa-install-enter-from,
.pwa-install-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.98);
}

@media (min-width: 920px) {
  .pwa-install {
    right: auto;
    left: 1.2rem;
    bottom: 1.2rem;
    width: 410px;
  }
}

@media (max-width: 420px) {
  .pwa-install {
    grid-template-columns: 34px minmax(0, 1fr) auto 30px;
    gap: 0.42rem;
    padding: 0.52rem;
  }

  .pwa-install__icon {
    width: 34px;
    height: 34px;
    border-radius: 13px;
  }

  .pwa-install__primary {
    padding-inline: 0.58rem;
  }
}
</style>
