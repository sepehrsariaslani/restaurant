<template>
  <ManagementPageScaffold title="گزارش‌های مدیریتی" subtitle="انتخاب سریع نوع گزارش با کارت‌های یکپارچه">
    <section class="report-grid">
      <a class="report-link" v-for="report in reports" :key="report.key" :href="`/desk/reports/${report.key}`">
        <ManagementSurfaceCard class="report-card" tone="soft">
          <strong>{{ report.title }}</strong>
          <small class="muted">{{ report.desc }}</small>
        </ManagementSurfaceCard>
      </a>
    </section>
  </ManagementPageScaffold>
</template>

<script setup>
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'

const reports = [
  { key: 'sales-summary', title: 'خلاصه فروش', desc: 'فروش کل، تعداد سفارش و میانگین سبد' },
  { key: 'sales-trend', title: 'روند فروش', desc: 'نمودار فروش روزانه' },
  { key: 'sales-hourly', title: 'فروش ساعتی', desc: 'ساعات پرترافیک فروش' },
  { key: 'top-products', title: 'محصولات پرفروش', desc: 'برترین محصولات بر اساس فروش' },
  { key: 'product-mix', title: 'ترکیب محصولات', desc: 'تحلیل هم خریدی (A کنار B چند درصد)' },
  { key: 'order-status', title: 'وضعیت سفارش‌ها', desc: 'تعداد و مبلغ بر اساس وضعیت' },
  { key: 'channel-split', title: 'کانال‌های فروش', desc: 'سهم بیرون‌بر، ارسال، سالن' },
  { key: 'cashier-performance', title: 'عملکرد اپراتور', desc: 'فروش و تعداد سفارش بر اساس کاربر' },
  { key: 'cancellations', title: 'لغو سفارش', desc: 'تعداد و مبلغ سفارش‌های لغو شده' },
  { key: 'modifier-usage', title: 'استفاده از افزودنی‌ها', desc: 'محبوب‌ترین modifier ها' },
]
</script>

<style scoped>
.report-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.65rem;
}

.report-link {
  display: block;
}

.report-card {
  min-height: 116px;
  display: grid;
  gap: 0.3rem;
}

.report-card strong {
  font-size: 0.92rem;
}

.report-card small {
  line-height: 1.65;
  font-size: 0.78rem;
}

@media (max-width: 980px) {
  .report-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .report-grid {
    grid-template-columns: 1fr;
  }
}
</style>
