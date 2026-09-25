<template>
  <div class="customer-page table-select-redirect" dir="rtl">
    <CustomerPageHeader
      eyebrow="رزرو میز"
      title="انتخاب میز آزاد"
      subtitle="میزها در مسیر رزرو و بر اساس زمان انتخابی شما نمایش داده می‌شوند."
      fallback-href="/table-reservation"
    >
      <template #eyebrow-icon><Armchair :size="14" aria-hidden="true" /></template>
    </CustomerPageHeader>

    <main class="customer-page__body">
      <section class="customer-glass-card redirect-card" role="status" aria-live="polite">
        <LoaderCircle :size="22" class="redirect-spinner" aria-hidden="true" />
        <p>در حال بازکردن مرحله‌ی انتخاب میز…</p>
        <a href="/table-reservation?step=table" class="redirect-link">ادامه‌ی رزرو میز</a>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { Armchair, LoaderCircle } from 'lucide-vue-next'
import CustomerPageHeader from '@/components/customer/CustomerPageHeader.vue'

onMounted(() => {
  window.location.replace('/table-reservation?step=table')
})
</script>

<style scoped>
.redirect-card {
  display: grid;
  justify-items: center;
  gap: var(--ds-space-3);
  max-width: 520px;
  margin-inline: auto;
  padding: var(--ds-space-8);
  color: var(--ds-color-text-secondary);
  text-align: center;
}

.redirect-card p { margin: 0; }
.redirect-spinner { color: var(--ds-color-action-primary); animation: redirect-spin .8s linear infinite; }
.redirect-link { color: var(--ds-color-action-primary); font-weight: 700; }
.redirect-link:focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 3px; }

@keyframes redirect-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .redirect-spinner { animation: none; } }
</style>
