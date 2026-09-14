<template>
  <ManagementPageScaffold title="گزارش‌های مدیریتی" subtitle="انتخاب سریع نوع گزارش با کارت‌های یکپارچه">
    <section class="report-grid">
      <a class="report-link" v-for="report in reports" :key="report.key" :href="`/management/reports/${report.key}`">
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
  { key: 'product-sales', title: 'فروش محصولات', desc: 'گزارش تفصیلی هر محصول: تعداد، مبلغ و سهم از فروش' },
  { key: 'category-sales', title: 'فروش دسته‌بندی‌ها', desc: 'میزان فروش هر دسته‌بندی محصول' },
  { key: 'table-sales', title: 'فروش جایگاه‌ها', desc: 'فروش به تفکیک میز و جایگاه' },
  { key: 'shift-sales', title: 'فروش بر اساس شیفت', desc: 'تفکیک فروش بر اساس شیفت‌های کاری' },
  { key: 'payment-methods', title: 'روش‌های پرداخت', desc: 'فروش بر اساس نقدی، کارتی و نسیه' },
  { key: 'product-mix', title: 'ترکیب محصولات', desc: 'تحلیل هم خریدی (A کنار B چند درصد)' },
  { key: 'order-status', title: 'وضعیت سفارش‌ها', desc: 'تعداد و مبلغ بر اساس وضعیت' },
  { key: 'channel-split', title: 'کانال‌های فروش', desc: 'سهم بیرون‌بر، ارسال، سالن' },
  { key: 'cashier-performance', title: 'عملکرد اپراتور', desc: 'فروش و تعداد سفارش بر اساس کاربر' },
  { key: 'cancellations', title: 'لغو سفارش', desc: 'تعداد و مبلغ سفارش‌های لغو شده' },
  { key: 'modifier-usage', title: 'استفاده از افزودنی‌ها', desc: 'محبوب‌ترین modifier ها' },
  { key: 'inventory-valuation', title: 'ارزش‌گذاری موجودی', desc: 'ارزش ریالی و مقداری موجودی انبارها به تفکیک قلم' },
  { key: 'stock-movements', title: 'گردش انبار', desc: 'ورود، خروج، انتقال و ارزش گردش‌ها در بازه' },
  { key: 'inventory-waste', title: 'ضایعات و اتلاف انبار', desc: 'ارزش ضایعات، خسارات و اوتی‌ها به تفکیک قلم' },
  { key: 'customer-analytics', title: 'تحلیل مشتریان (RFM)', desc: 'ارزش طول عمر مشتری، نرخ بازگشت و سگمنت‌های رفتاری' },
  { key: 'campaign-performance', title: 'عملکرد کمپین‌ها', desc: 'مشارکت، فروش کانال و بودجه پاداش هر کمپین' },
  { key: 'wallet-summary', title: 'گزارش اعتباردهی', desc: 'شارژ، مصرف و پاداش‌های واریزشده به کیف پول‌ها' },
  { key: 'credit-transactions', title: 'سوابق کارت اعتباری', desc: 'تراکنش‌های کیف پول الکترونیکی مشتریان' },
  { key: 'care-feedback', title: 'نظرات سایت', desc: 'دیدگاه‌های ثبت‌شده مشتریان درباره محصولات فروشگاه' },
  { key: 'survey-analytics', title: 'تحلیل نظرسنجی', desc: 'میانگین امتیاز، توزیع پاسخ‌ها و نارضایتی‌ها' },
  { key: 'courier-performance', title: 'عملکرد پیک‌ها', desc: 'تحویل‌ها، زمان ارسال و درآمد هر پیک' },
  { key: 'kitchen-performance', title: 'عملکرد آشپزخانه', desc: 'مدت آماده‌سازی سفارش‌ها و وضعیت تولید' },
  { key: 'profit-loss', title: 'سود و زیان', desc: 'فروش، بهای تمام‌شده، هزینه‌ها و سود خالص ماهانه' },
  { key: 'breakeven', title: 'نقطه سربه‌سر', desc: 'حداقل فروش پوشش هزینه‌ها و حاشیه امنیت' },
  { key: 'waiter-performance', title: 'عملکرد گارسون‌ها', desc: 'سفارش، فروش و امتیاز رضایت هر گارسون' },
  { key: 'menu-engineering', title: 'مهندسی منو', desc: 'محبوبیت و حاشیه سود هر آیتم؛ ستاره‌ها و معمای‌ها' },
  { key: 'tax-reconciliation', title: 'تطبیق مالیات (مودیان)', desc: 'صورتحساب‌های ارسال‌شده، خطاها و وضعیت ثبت' },
  { key: 'branch-performance', title: 'عملکرد شعب', desc: 'مقایسه فروش و رشد شعب در بازه' },
  { key: 'vendor-sales', title: 'فروش غرفه‌ها', desc: 'فروش و کمیسیون غرفه‌داران و همکاران' },
  { key: 'receipt-payment-balance', title: 'تراز دریافت و پرداخت', desc: 'جریان نقد، بانک و آمار دریافتی‌ها' },
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
