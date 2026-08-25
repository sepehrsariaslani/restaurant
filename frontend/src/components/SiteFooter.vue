<template>
  <footer class="site-footer" dir="rtl">
    <div class="footer-inner">
      <section class="footer-cta" aria-label="شروع سفارش">
        <div>
          <span class="footer-cta-kicker">آماده سفارش هستید؟</span>
          <h2>محبوب‌ترین آیتم‌ها را سریع انتخاب کنید و سفارش را بسازید.</h2>
        </div>
        <div class="footer-cta-actions">
          <a href="/menu" class="footer-primary-link">مشاهده منو</a>
          <a href="/cart" class="footer-secondary-link">سبد سفارش</a>
        </div>
      </section>

      <div class="footer-grid">
        <div class="footer-col footer-brand-col">
          <a href="/" class="footer-logo">{{ brandName }}</a>
          <p class="footer-desc">{{ description || 'منوی آنلاین با سفارش سریع، مواد تازه و تجربه‌ای روان برای انتخاب غذای دلخواه شما.' }}</p>
          <div class="footer-trust-row" aria-label="مزیت‌ها">
            <span>تازه‌پز</span>
            <span>سفارش سریع</span>
            <span>پرداخت امن</span>
          </div>
          <div class="footer-social" v-if="instagram || telegram">
            <a v-if="instagram" :href="instagram" target="_blank" rel="noopener" class="social-link">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                <rect x="2" y="2" width="20" height="20" rx="5" ry="5"/>
                <circle cx="12" cy="12" r="5"/>
                <circle cx="17.5" cy="6.5" r="0.5" fill="currentColor"/>
              </svg>
              اینستاگرام
            </a>
            <a v-if="telegram" :href="telegram" target="_blank" rel="noopener" class="social-link">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                <path d="M22 2L11 13"/>
                <path d="M22 2L15 22l-4-9-9-4 20-7z"/>
              </svg>
              تلگرام
            </a>
          </div>
        </div>

        <div class="footer-col">
          <h4 class="footer-heading">دسترسی سریع</h4>
          <nav class="footer-links">
            <a href="/" class="footer-link">خانه</a>
            <a href="/menu" class="footer-link">منو</a>
            <a href="/cart" class="footer-link">سبد خرید</a>
            <a href="/about-us" class="footer-link">درباره ما</a>
            <a href="/faq" class="footer-link">سوالات متداول</a>
          </nav>
        </div>

        <div class="footer-col">
          <h4 class="footer-heading">ارتباط با ما</h4>
          <div class="footer-contacts">
            <a v-if="phone" :href="`tel:${phone}`" class="footer-contact-item">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.99 12 19.79 19.79 0 0 1 2 3.18 2 2 0 0 1 3.98 1h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9a16 16 0 0 0 6.07 6.07l1.36-1.36a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
              </svg>
              {{ phone }}
            </a>
            <a v-if="email" :href="`mailto:${email}`" class="footer-contact-item">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
              {{ email }}
            </a>
            <p v-if="address" class="footer-contact-item footer-address">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
              {{ address }}
            </p>
            <p v-if="!phone && !email && !address" class="footer-contact-item footer-address">
              سفارش آنلاین شما از طریق منو و سبد خرید در دسترس است.
            </p>
          </div>
        </div>
      </div>

      <div class="footer-divider"></div>
      <div class="footer-bottom-bar">
        <span class="footer-copy">{{ copyright || `تمامی حقوق برای ${brandName} محفوظ است.` }}</span>
      </div>
    </div>

    <div class="footer-brand-bg" aria-hidden="true">
      <span class="footer-brand-ghost">{{ brandName }}</span>
    </div>
  </footer>
</template>

<script setup>
defineProps({
  brandName: {
    type: String,
    default: '',
  },
  description: {
    type: String,
    default: '',
  },
  phone: {
    type: String,
    default: '',
  },
  email: {
    type: String,
    default: '',
  },
  address: {
    type: String,
    default: '',
  },
  instagram: {
    type: String,
    default: '',
  },
  telegram: {
    type: String,
    default: '',
  },
  copyright: {
    type: String,
    default: '',
  },
})
</script>

<style scoped>
.site-footer {
  position: relative;
  overflow: hidden;
  background: var(--palette-deep-sapphire, #6F4A31);
  color: rgb(255 255 255 / 0.9);
  direction: rtl;
  isolation: isolate;
}

.footer-inner {
  position: relative;
  z-index: 2;
  width: min(1200px, calc(100% - 2.5rem));
  margin: 0 auto;
  padding: 3.5rem 0 1.5rem;
}

.footer-cta {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.4rem;
  margin-bottom: 2.4rem;
  padding: clamp(1.2rem, 3vw, 2rem);
  border-radius: 28px;
  overflow: hidden;
  background:
    radial-gradient(circle at 10% 20%, rgb(255 255 255 / 0.18), transparent 30%),
    linear-gradient(135deg, rgb(255 255 255 / 0.13), rgb(255 255 255 / 0.06));
  border: 1px solid rgb(255 255 255 / 0.16);
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.16), 0 18px 42px rgb(0 0 0 / 0.12);
}

.footer-cta::after {
  content: '';
  position: absolute;
  inset-inline-start: -4rem;
  top: -5rem;
  width: 12rem;
  height: 12rem;
  border-radius: 999px;
  background: rgb(var(--palette-june-bud-rgb, 201 223 144) / 0.18);
  filter: blur(1px);
  pointer-events: none;
}

.footer-cta-kicker {
  display: inline-flex;
  margin-bottom: 0.45rem;
  color: var(--palette-deep-saffron, #C98D42);
  font-size: 0.8rem;
  font-weight: 900;
}

.footer-cta h2 {
  margin: 0;
  max-width: 620px;
  color: #fff;
  font-size: clamp(1.25rem, 3vw, 2rem);
  line-height: 1.35;
  letter-spacing: -0.03em;
}

.footer-cta-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  flex-shrink: 0;
}

.footer-primary-link,
.footer-secondary-link {
  min-height: 2.75rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 0.65rem 1.05rem;
  font-size: 0.86rem;
  font-weight: 800;
  text-decoration: none;
  transition: transform 0.18s ease, background 0.18s ease, color 0.18s ease;
}

.footer-primary-link {
  background: var(--palette-june-bud, #c9df90);
  color: var(--palette-deep-sapphire, #6F4A31);
}

.footer-secondary-link {
  border: 1px solid rgb(255 255 255 / 0.2);
  color: rgb(255 255 255 / 0.86);
}

.footer-primary-link:hover,
.footer-secondary-link:hover {
  transform: translateY(-2px);
}

.footer-secondary-link:hover {
  background: rgb(255 255 255 / 0.12);
  color: #fff;
}

.footer-grid {
  display: grid;
  grid-template-columns: 1.6fr 1fr 1fr;
  gap: 2.5rem 3rem;
}

.footer-col {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.footer-logo {
  display: inline-block;
  font-size: 1.55rem;
  font-weight: 900;
  color: #fff;
  text-decoration: none;
  letter-spacing: -0.02em;
  line-height: 1;
}

.footer-desc {
  margin: 0;
  font-size: 0.88rem;
  line-height: 1.7;
  color: rgb(255 255 255 / 0.72);
  max-width: 280px;
}

.footer-trust-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.footer-trust-row span {
  display: inline-flex;
  align-items: center;
  min-height: 1.75rem;
  border-radius: 999px;
  padding: 0.25rem 0.7rem;
  background: rgb(255 255 255 / 0.08);
  border: 1px solid rgb(255 255 255 / 0.1);
  color: rgb(255 255 255 / 0.76);
  font-size: 0.75rem;
  font-weight: 700;
}

.footer-social {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.social-link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.85rem;
  border-radius: 999px;
  border: 1px solid rgb(255 255 255 / 0.25);
  color: rgb(255 255 255 / 0.85);
  font-size: 0.8rem;
  text-decoration: none;
  transition: background 0.18s, border-color 0.18s;
}

.social-link:hover {
  background: rgb(255 255 255 / 0.12);
  border-color: rgb(255 255 255 / 0.45);
}

.footer-heading {
  margin: 0 0 0.3rem;
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--palette-deep-saffron, #C98D42);
}

.footer-links {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.footer-link {
  color: rgb(255 255 255 / 0.75);
  text-decoration: none;
  font-size: 0.88rem;
  transition: color 0.15s;
  width: max-content;
}

.footer-link:hover {
  color: #fff;
}

.footer-contacts {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.footer-contact-item {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  color: rgb(255 255 255 / 0.75);
  font-size: 0.85rem;
  text-decoration: none;
  line-height: 1.5;
  transition: color 0.15s;
}

.footer-contact-item:hover {
  color: #fff;
}

.footer-contact-item svg {
  flex-shrink: 0;
  margin-top: 0.15rem;
  opacity: 0.75;
}

.footer-address {
  margin: 0;
}

.footer-divider {
  margin: 2.5rem 0 1rem;
  border: none;
  height: 1px;
  background: rgb(255 255 255 / 0.12);
}

.footer-bottom-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-bottom: 0.5rem;
}

.footer-copy {
  font-size: 0.78rem;
  color: rgb(255 255 255 / 0.5);
  text-align: center;
}

.footer-brand-bg {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  overflow: hidden;
  pointer-events: none;
  height: 45%;
  mask-image: linear-gradient(to top, transparent 0%, rgb(0 0 0 / 0.08) 40%, transparent 100%);
  -webkit-mask-image: linear-gradient(to top, transparent 0%, rgb(0 0 0 / 0.08) 40%, transparent 100%);
}

.footer-brand-ghost {
  display: block;
  font-size: clamp(4rem, 16vw, 13rem);
  font-weight: 900;
  line-height: 0.85;
  color: #fff;
  opacity: 0.07;
  white-space: nowrap;
  letter-spacing: -0.03em;
  user-select: none;
  padding-bottom: 0.5rem;
}

@media (max-width: 900px) {
  .footer-cta {
    align-items: stretch;
    flex-direction: column;
  }

  .footer-cta-actions {
    width: 100%;
  }

  .footer-primary-link,
  .footer-secondary-link {
    flex: 1 1 10rem;
  }

  .footer-grid {
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
  }

  .footer-brand-col {
    grid-column: span 2;
  }
}

@media (max-width: 580px) {
  .footer-inner {
    width: min(100% - 1.5rem, 1200px);
    padding: 2.4rem 0 6rem;
  }

  .footer-cta {
    border-radius: 22px;
  }

  .footer-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .footer-brand-col {
    grid-column: span 1;
  }
}
</style>
