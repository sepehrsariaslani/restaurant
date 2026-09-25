<template>
  <section class="customer-page__hero" :class="heroClass">
    <div class="customer-page__topbar" :class="{ 'customer-page__topbar--compact': compact }">
      <button
        v-if="showBack"
        class="customer-page__back"
        type="button"
        :aria-label="backLabel"
        @click="goBack"
      >
        <ChevronRight :size="20" aria-hidden="true" />
      </button>
      <span v-else class="customer-page-header__spacer" aria-hidden="true"></span>

      <div class="customer-page__titles">
        <p v-if="eyebrow" class="customer-page__eyebrow">
          <slot name="eyebrow-icon" />
          {{ eyebrow }}
        </p>
        <h1 class="customer-page__title">{{ title }}</h1>
        <p v-if="subtitle" class="customer-page__subtitle">{{ subtitle }}</p>
      </div>

      <slot name="action">
        <span class="customer-page-header__spacer" aria-hidden="true"></span>
      </slot>
    </div>

    <slot />
  </section>
</template>

<script setup>
import { ChevronRight } from 'lucide-vue-next'

const props = defineProps({
  eyebrow: { type: String, default: '' },
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  heroClass: { type: [String, Array, Object], default: '' },
  compact: { type: Boolean, default: false },
  showBack: { type: Boolean, default: true },
  backLabel: { type: String, default: 'بازگشت' },
  fallbackHref: { type: String, default: '/menu' },
})

function goBack() {
  const previousUrl = document.referrer
  if (window.history.length > 1 && previousUrl && new URL(previousUrl).origin === window.location.origin) {
    window.history.back()
    return
  }
  window.location.assign(props.fallbackHref)
}
</script>

<style scoped>
.customer-page-header__spacer {
  display: block;
  width: 44px;
  min-width: 44px;
  height: 44px;
}
</style>
