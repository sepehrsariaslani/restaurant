<template>
  <footer class="app-footer" dir="rtl">
    <div class="footer-inner">
      <section class="brand-col">
        <a href="/" class="brand-row">
          <span class="brand-dot"></span>
          <div>
            <strong>{{ branding.name }}</strong>
            <small>{{ branding.tagline }}</small>
          </div>
        </a>
        <p>
          {{ branding.hero_subtitle || 'منوی آنلاین با شخصی سازی کامل، سفارش سریع، و رهگیری دقیق تولید.' }}
        </p>
      </section>

      <section class="links-col">
        <h4>ناوبری سریع</h4>
        <a href="/">خانه</a>
        <a href="/menu">منو</a>
        <a href="/about-us">درباره ما</a>
        <a href="/faq">سوالات متداول</a>
        <a href="/cart">سبد سفارش</a>
      </section>

      <section class="links-col">
        <h4>خدمات</h4>
        <a href="/menu">سفارشی سازی آیتم</a>
        <a href="/cart">تکمیل سفارش</a>
        <a v-if="hasLastOrder" :href="lastOrderUrl">پیگیری سفارش</a>
      </section>
          <div class="footer-bottom">
      <small>© {{ year }} {{ branding.name }} - همه حقوق محفوظ است.</small>
    </div>
    </div>


  </footer>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  branding: {
    type: Object,
    default: () => ({
      name: 'Veederakht Restaurant',
      tagline: 'منوی آنلاین',
      hero_subtitle: '',
    }),
  },
  hasLastOrder: {
    type: Boolean,
    default: false,
  },
  lastOrderUrl: {
    type: String,
    default: '/',
  },
})

const year = computed(() => new Date().getFullYear())
</script>

<style scoped>
.app-footer {
  color: var(--text-primary);
}

.footer-inner {
  width: min(1180px, calc(100% - 2rem));
  margin: 0 auto;
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  box-shadow: 0 10px 22px rgb(15 23 42 / 0.08);
  padding: 2rem;
  display: grid;
  border-radius: 30px;
  grid-template-columns: 1.2fr 1fr 1fr;
  gap: 0.8rem;
}

.brand-row {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.brand-dot {
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 999px;
  background: var(--accent-green);
}

.brand-row strong {
  display: block;
  font-size: 0.92rem;
}

.brand-row small {
  display: block;
  color: var(--text-muted);
  font-size: 0.72rem;
}

.brand-col p {
  margin: 0.45rem 0 0;
  color: var(--text-muted);
  font-size: 0.8rem;
  line-height: 1.8;
}

.links-col {
  display: grid;
  align-content: start;
  gap: 0.32rem;
}

.links-col h4 {
  margin: 0;
  font-size: 0.9rem;
  color: var(--accent-green);
}

.links-col a {
  color: var(--text-primary);
  font-size: 0.8rem;
}

.links-col a:hover {
  color: var(--accent-green);
}

.footer-bottom {
  width: min(1180px, calc(100% - 2rem));
  margin: 0.45rem auto 0;
  border-top: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  text-align: center;
  padding: 0.72rem 1rem;
}

.footer-bottom small {
  color: var(--text-muted);
}

@media (max-width: 880px) {
  .footer-inner {
    grid-template-columns: 1fr;
    margin-bottom:100px;
  }
}
</style>
