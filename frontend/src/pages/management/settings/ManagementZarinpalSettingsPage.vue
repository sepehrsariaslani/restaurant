<template>
  <ManagementPageScaffold title="تنظیمات زرین‌پال" subtitle="وضعیت اتصال درگاه پرداخت اینترنتی">
    <ManagementSurfaceCard tone="soft" title="قرارداد درگاه هنوز فعال نشده است" subtitle="برای جلوگیری از ثبت تنظیمات ناقص، این صفحه تا زمان آماده‌شدن endpoint امن backend فقط وضعیت را نمایش می‌دهد.">
      <div class="status-row" role="status" aria-live="polite">
        <span class="status-dot" aria-hidden="true"></span>
        <strong>تنظیمات زرین‌پال در این نسخه قابل ویرایش نیست</strong>
      </div>
      <p class="muted">پرداخت‌های ثبت‌شده و تسویهٔ سفارش‌ها از مسیرهای فعلی POS و حسابداری مدیریت می‌شوند.</p>
      <div class="actions">
        <a class="secondary-btn" href="/management/accounting">رفتن به حسابداری</a>
        <a class="primary-btn" href="/management/pos">رفتن به POS</a>
      </div>
    </ManagementSurfaceCard>
  </ManagementPageScaffold>
</template>

<script setup>
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
</script>

<style scoped>
.muted {
  margin: 0.8rem 0 0;
  color: var(--mg-text-muted);
  line-height: 1.8;
}
.status-row {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  color: var(--mg-text-main);
}
.status-dot {
  width: 0.65rem;
  height: 0.65rem;
  border-radius: 50%;
  background: var(--mg-warning);
  box-shadow: 0 0 0 0.25rem var(--mg-warning-soft);
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 1rem;
}
</style>
