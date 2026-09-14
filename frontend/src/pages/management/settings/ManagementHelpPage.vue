<template>
  <ManagementPageScaffold title="راهنما و خدمات" subtitle="پشتیبانی، آموزش و همراهی تیم نوش‌یار در تمام مراحل راه‌اندازی و بهره‌برداری">
    <div class="help-grid">
      <ManagementSurfaceCard title="ساعات پاسخ‌گویی پشتیبانی" tone="soft">
        <ul class="help-list">
          <li><strong>شنبه تا چهارشنبه:</strong> ساعت ۱۰ تا ۱۹ — بک‌آفیس واتساپ و ثبت تیکت</li>
          <li><strong>پنجشنبه:</strong> پاسخ‌گویی ۱۰ تا ۱۷ برای بک‌آفیس واتساپ و تیکت + شیفت شب از ۱۸ تا ۲۲ برای پشتیبانی بک‌آفیس واتساپ</li>
          <li><strong>جمعه و روزهای تعطیل:</strong> شیفت‌های ۱۰ تا ۲۲</li>
        </ul>
        <p class="muted help-note">در هر دو شیفت صبح و شب، تیم پشتیبانی مستقر در مجموعه (ساعات کاری) نیز در دسترس است.</p>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="سوپروایزر اختصاصی" tone="soft">
        <ul class="help-list">
          <li>رسیدگی به مشکلات و پیگیری آن‌ها تا رفع کامل</li>
          <li>معرفی امکانات جدید سیستم متناسب با نیاز شما</li>
          <li>ارتباط مستقیم برای هماهنگی درخواست‌ها و بهبودها</li>
        </ul>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="بارگذاری دیتای اولیه" tone="soft">
        <ul class="help-list">
          <li>بارگذاری اولیه محصولات، پرسنل، مشتریان و تنظیمات اولیه سیستم</li>
          <li>بررسی صحت داده‌ها قبل از شروع بهره‌برداری</li>
        </ul>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="آموزش" tone="soft">
        <ul class="help-list">
          <li>جلسات آنبوردینگ هنگام شروع کار با پنل</li>
          <li>وبینارها و جلسات دوره‌ای معرفی قابلیت‌های تازه</li>
          <li>پایگاه دانش دانش‌بنیان + ویدئوهای آموزشی کوتاه برای هر بخش</li>
          <li>آموزش‌های حضوری و مجازی متناسب با نیاز مجموعه</li>
        </ul>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="اکانت منیجر" tone="soft" class="span-2">
        <ul class="help-list">
          <li>بررسی عملکرد کمپین‌ها و ارائه راهکار بهبود</li>
          <li>کاست کنترل و قیمت‌گذاری اقلام منو</li>
          <li>سفرهای کاهش هزینه و افزایش فروش در کنار شما</li>
        </ul>
      </ManagementSurfaceCard>
    </div>

    <ManagementSurfaceCard title="دسترسی سریع" subtitle="میان‌بر به بخش‌های پرکاربرد پنل">
      <div class="quick-grid">
        <a class="quick-link" v-for="link in quickLinks" :key="link.url" :href="link.url">
          <strong>{{ link.label }}</strong>
          <small class="muted">{{ link.caption }}</small>
        </a>
      </div>
    </ManagementSurfaceCard>
  </ManagementPageScaffold>
</template>

<script setup>
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'

const quickLinks = [
  { label: 'باشگاه مشتریان', caption: 'وفاداری، پیامک و کیف پول', url: '/management/club' },
  { label: 'گزارش‌ها', caption: 'فروش، انبار و تحلیل', url: '/management/reports' },
  { label: 'رزرواسیون', caption: 'مدیریت رزرو میز', url: '/management/reservations' },
  { label: 'مرکز تماس', caption: 'کالر آیدی و تماس ورودی', url: '/management/call-center' },
  { label: 'شعب', caption: 'مدیریت و عملکرد شعبه‌ها', url: '/management/branches' },
  { label: 'حسابداری یکپارچه', caption: 'تراز دریافت و پرداخت', url: '/management/accounting' },
  { label: 'تنظیمات سایت', caption: 'پیکربندی فروشگاه', url: '/management/site-settings' },
  { label: 'نظرسنجی', caption: 'سوالات و پاسخ مشتریان', url: '/management/surveys' },
]
</script>

<style scoped>
.help-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.9rem;
}

.span-2 {
  grid-column: span 2;
}

.help-list {
  margin: 0;
  padding: 0 1.1rem 0 0;
  display: grid;
  gap: 0.45rem;
  font-size: 0.9rem;
  line-height: 1.9;
}

.help-note {
  margin-top: 0.6rem;
  font-size: 0.82rem;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.6rem;
}

.quick-link {
  display: grid;
  gap: 0.15rem;
  padding: 0.7rem 0.85rem;
  border-radius: 12px;
  border: 1px solid var(--border-color, rgba(0, 0, 0, 0.08));
  text-decoration: none;
  color: inherit;
  transition: border-color 0.15s ease, transform 0.15s ease;
}

.quick-link:hover {
  border-color: var(--mg-primary);
  transform: translateY(-1px);
}

.quick-link small {
  font-size: 0.76rem;
}

.muted {
  color: var(--mg-text-muted);
}

@media (max-width: 920px) {
  .help-grid {
    grid-template-columns: 1fr;
  }

  .span-2 {
    grid-column: span 1;
  }

  .quick-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
