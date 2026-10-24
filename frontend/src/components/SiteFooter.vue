<template>
  <footer class="site-footer" dir="rtl">
    <div class="footer-inner">
      <div class="footer-order">
        <div class="footer-order__copy">
          <span class="footer-eyebrow"><Sparkles :size="16" aria-hidden="true" /> برای یک انتخاب خوش‌طعم</span>
          <h2>سفارش بعدی‌تان از همین‌جا شروع می‌شود.</h2>
          <p>منو را ببینید، آیتم دلخواهتان را انتخاب کنید و روش دریافت را مشخص کنید.</p>
        </div>
        <a class="footer-order__action" href="/menu">دیدن منو <ArrowUpLeft :size="18" aria-hidden="true" /></a>
      </div>

      <div class="footer-grid">
        <div class="footer-brand">
          <a class="footer-logo" href="/">{{ brandName }}</a>
          <p>{{ description || 'غذای تازه و خوش‌طعم، با انتخابی ساده و سفارشی برای شما.' }}</p>
          <div class="footer-social" v-if="instagram || telegram">
            <a v-if="instagram" :href="instagram" target="_blank" rel="noopener noreferrer" aria-label="اینستاگرام"><Instagram :size="18" aria-hidden="true" /></a>
            <a v-if="telegram" :href="telegram" target="_blank" rel="noopener noreferrer" aria-label="تلگرام"><Send :size="18" aria-hidden="true" /></a>
          </div>
          <div v-if="showEnamadTrustseal" class="footer-trustseal" aria-label="نماد اعتماد">
            <a referrerpolicy="origin" target="_blank" href="https://trustseal.enamad.ir/?id=8041746&Code=2PT46vOdEVXChL4zRLKfLaNM6LjFqu2g">
              <img referrerpolicy="origin" src="https://trustseal.enamad.ir/logo.aspx?id=8041746&Code=2PT46vOdEVXChL4zRLKfLaNM6LjFqu2g" alt="" style="cursor:pointer" code="2PT46vOdEVXChL4zRLKfLaNM6LjFqu2g">
            </a>
          </div>
        </div>

        <nav class="footer-links" aria-label="دسترسی‌های فوتر">
          <h3>دسترسی سریع</h3>
          <a href="/">خانه</a>
          <a href="/menu">منو</a>
          <a href="/cart">سبد سفارش</a>
          <a href="/blog">مجله و مقاله‌ها</a>
          <a href="/about-us">درباره ما</a>
          <a href="/cooperation">درخواست همکاری</a>
          <a href="/faq">سوالات متداول</a>
        </nav>

        <div class="footer-contact">
          <h3>ارتباط با ما</h3>
          <a v-if="phone" :href="`tel:${phone}`"><Phone :size="18" aria-hidden="true" /><span dir="ltr">{{ phone }}</span></a>
          <a v-if="email" :href="`mailto:${email}`"><Mail :size="18" aria-hidden="true" /><span>{{ email }}</span></a>
          <p v-if="address"><MapPin :size="18" aria-hidden="true" /><span>{{ address }}</span></p>
          <p v-if="!phone && !email && !address">برای ثبت سفارش، منوی آنلاین همیشه در دسترس شماست.</p>
        </div>
      </div>

      <div class="footer-bottom">
        <small>{{ copyright || `تمامی حقوق برای ${brandName} محفوظ است.` }}</small>
        <a href="/menu">بازگشت به منو <ArrowUpLeft :size="15" aria-hidden="true" /></a>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'
import { ArrowUpLeft, Instagram, Mail, MapPin, Phone, Send, Sparkles } from 'lucide-vue-next'

const showEnamadTrustseal = computed(() => {
  const hostname = window.location.hostname.toLowerCase()
  return hostname === 'veederakht.ir' || hostname === 'www.veederakht.ir'
})

defineProps({
  brandName: { type: String, default: '' },
  description: { type: String, default: '' },
  phone: { type: String, default: '' },
  email: { type: String, default: '' },
  address: { type: String, default: '' },
  instagram: { type: String, default: '' },
  telegram: { type: String, default: '' },
  copyright: { type: String, default: '' },
})
</script>

<style scoped>
.site-footer { border-top: 1px solid var(--ds-color-border); background: var(--ds-color-surface-muted); color: var(--ds-color-text-primary); }
.footer-inner { width: min(1160px, calc(100% - 2rem)); margin: auto; padding: clamp(2rem, 5vw, 3.5rem) 0 1.25rem; }
.footer-order { display: flex; align-items: center; justify-content: space-between; gap: 1.5rem; padding: clamp(1.25rem, 3vw, 2rem); border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-lg); background: var(--ds-color-surface-raised); box-shadow: var(--ds-shadow-sm); }
.footer-eyebrow { display: inline-flex; align-items: center; gap: .45rem; color: var(--ds-color-action-accent); font-size: .8rem; font-weight: 800; }
.footer-order h2 { margin: .45rem 0 .25rem; font-size: clamp(1.25rem, 2.8vw, 1.8rem); line-height: 1.4; }
.footer-order p { margin: 0; color: var(--ds-color-text-secondary); font-size: .88rem; line-height: 1.7; }
.footer-order__action { display: inline-flex; align-items: center; justify-content: center; gap: .5rem; flex: none; min-height: 48px; padding: .65rem 1.15rem; border-radius: var(--ds-radius-md); background: var(--ds-color-action-accent); color: var(--ds-color-action-accent-foreground); font-size: .9rem; font-weight: 800; text-decoration: none; }
.footer-order__action:hover { filter: brightness(.96); }
.footer-grid { display: grid; grid-template-columns: minmax(0, 1.7fr) repeat(2, minmax(0, 1fr)); gap: 2rem; padding: 2.5rem .25rem; }
.footer-logo { display: inline-block; color: var(--ds-color-action-primary); font-size: 1.35rem; font-weight: 900; text-decoration: none; }
.footer-brand p { max-width: 29rem; margin: .6rem 0 1rem; color: var(--ds-color-text-secondary); line-height: 1.9; font-size: .88rem; }
.footer-social { display: flex; gap: .5rem; }
.footer-social a { display: grid; place-items: center; width: 44px; height: 44px; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface-raised); color: var(--ds-color-action-primary); }
.footer-trustseal { display: inline-flex; margin-top: 1rem; padding: .45rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface-raised); }
.footer-trustseal img { display: block; width: 96px; height: auto; }
.footer-links, .footer-contact { display: flex; flex-direction: column; align-items: flex-start; gap: .55rem; }
.footer-grid h3 { margin: 0 0 .25rem; color: var(--ds-color-text-primary); font-size: .95rem; }
.footer-links a, .footer-contact a, .footer-contact p { margin: 0; color: var(--ds-color-text-secondary); text-decoration: none; font-size: .86rem; line-height: 1.7; }
.footer-links a { min-height: 32px; }
.footer-contact a, .footer-contact p { display: flex; align-items: flex-start; gap: .55rem; overflow-wrap: anywhere; }
.footer-contact svg { flex: none; margin-top: .2rem; color: var(--ds-color-action-primary); }
.footer-links a:hover, .footer-contact a:hover { color: var(--ds-color-action-primary); }
.footer-bottom { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding-top: 1rem; border-top: 1px solid var(--ds-color-border); color: var(--ds-color-text-muted); }
.footer-bottom small { font-size: .75rem; }
.footer-bottom a { display: inline-flex; align-items: center; gap: .3rem; color: var(--ds-color-action-primary); text-decoration: none; font-size: .78rem; font-weight: 700; }
.site-footer a:focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 3px; }
@media (max-width: 760px) { .footer-order { align-items: stretch; flex-direction: column; } .footer-order__action { align-self: flex-start; } .footer-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.5rem; } .footer-brand { grid-column: 1 / -1; } .footer-inner { padding-bottom: calc(7rem + env(safe-area-inset-bottom)); } }
@media (max-width: 420px) { .footer-grid { grid-template-columns: 1fr 1fr; gap: 1.3rem .7rem; } .footer-contact { grid-column: 1 / -1; } .footer-bottom { align-items: flex-start; flex-direction: column; } }
@media (prefers-reduced-motion: reduce) { .footer-order__action { transition: none; } }
</style>
