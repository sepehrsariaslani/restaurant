<template>
  <div class="fail-page" dir="rtl">
    <div class="fail-body">

      <div class="fail-icon-wrap">
        <div class="fail-circle">
          <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        </div>
      </div>

      <h1 class="fail-title">پرداخت ناموفق بود</h1>
      <p class="fail-subtitle">اطلاعات سفارش شما محفوظ است. می‌توانید دوباره پرداخت را امتحان کنید یا روش پرداخت را تغییر دهید.</p>

      <div class="info-card" v-if="orderCode">
        <div class="info-row">
          <span class="info-label">کد سفارش</span>
          <strong class="info-val">{{ orderCode }}</strong>
        </div>
        <div class="info-row">
          <span class="info-label">وضعیت</span>
          <span class="status-pill">ناموفق</span>
        </div>
      </div>

      <div class="help-card">
        <h3>چه اتفاقی افتاد؟</h3>
        <ul>
          <li>اتصال اینترنت قطع شده بود</li>
          <li>موجودی کافی در حساب نبود</li>
          <li>اطلاعات کارت نادرست وارد شد</li>
          <li>درگاه بانکی در دسترس نبود</li>
        </ul>
        <p class="help-note">اگر سفارش قبلاً ثبت شده باشد، حذف نشده است. در صورت کسر وجه، وضعیت پرداخت از طریق پشتیبانی قابل پیگیری است.</p>
      </div>

      <div class="actions">
        <a :href="retryUrl" class="primary-btn">تلاش مجدد</a>
        <a href="/checkout" class="secondary-btn">تغییر روش پرداخت</a>
        <a href="/cart" class="secondary-btn">بازگشت به سبد</a>
        <a href="/menu" class="ghost-link">رفتن به منو</a>
      </div>

      <div class="support-note">
        <p>اگر مشکل ادامه داشت با پشتیبانی تماس بگیرید.</p>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const params = new URLSearchParams(window.location.search)
const orderCode = computed(() => params.get('order') || params.get('order_code') || '')
const retryUrl = computed(() => orderCode.value ? `/payment/${orderCode.value}` : '/checkout')
</script>

<style scoped>
.fail-page {
  min-height: 100vh;
  background: var(--ds-color-bg-page);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 3rem 1rem 6rem;
}

.fail-body {
  width: 100%;
  max-width: 440px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  text-align: center;
}

.fail-icon-wrap {
  margin-bottom: 0.25rem;
}

.fail-circle {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: var(--ds-color-status-danger);
  color: var(--ds-color-status-danger-foreground, var(--ds-color-text-inverse));
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px color-mix(in srgb, var(--ds-color-status-danger) 28%, transparent);
  animation: pop 0.4s cubic-bezier(0.34,1.56,0.64,1);
}

@keyframes pop {
  from { transform: scale(0.5); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.fail-title {
  font-size: 1.7rem;
  font-weight: 800;
  color: var(--ds-color-text-primary);
  margin: 0;
}

.fail-subtitle {
  color: var(--ds-color-text-secondary);
  font-size: 0.95rem;
  margin: -0.25rem 0 0;
  line-height: 1.6;
}

.info-card {
  width: 100%;
  background: var(--ds-color-surface-raised);
  border: 1px solid var(--ds-color-border);
  border-radius: 16px;
  padding: 1.1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  box-shadow: var(--ds-shadow-sm);
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.info-label { font-size: 0.85rem; color: var(--ds-color-text-muted); }
.info-val { font-size: 1rem; color: var(--ds-color-text-primary); letter-spacing: 0.03em; }

.status-pill {
  background: var(--ds-color-status-danger-soft);
  color: var(--ds-color-status-danger);
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.2rem 0.7rem;
  border-radius: 20px;
}

.help-card {
  width: 100%;
  background: var(--ds-color-surface-raised);
  border: 1px solid var(--ds-color-border);
  border-radius: 16px;
  padding: 1.1rem 1.25rem;
  text-align: right;
  box-shadow: var(--ds-shadow-sm);
}

.help-card h3 {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--ds-color-text-primary);
  margin: 0 0 0.7rem;
}

.help-card ul {
  margin: 0 0 0.75rem;
  padding-right: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.help-card li {
  font-size: 0.87rem;
  color: var(--ds-color-text-secondary);
  line-height: 1.5;
}

.help-note {
  font-size: 0.85rem;
  color: var(--ds-color-text-secondary);
  margin: 0;
  background: var(--ds-color-surface-muted);
  border-radius: 8px;
  padding: 0.55rem 0.8rem;
}

.actions {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.primary-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: var(--ds-color-action-primary);
  color: var(--ds-color-action-primary-foreground, var(--ds-color-text-inverse));
  padding: 0.9rem;
  border-radius: 12px;
  text-decoration: none;
  font-weight: 700;
  font-size: 1rem;
  transition: background 0.2s;
}

.primary-btn:hover { background: color-mix(in srgb, var(--ds-color-action-primary) 88%, var(--ds-color-text-primary)); }

.secondary-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--ds-color-surface-raised);
  color: var(--ds-color-action-primary);
  padding: 0.85rem;
  border-radius: 12px;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  border: 1.5px solid var(--ds-color-border);
  transition: background 0.2s;
}

.secondary-btn:hover { background: var(--ds-color-action-primary-soft); }

.ghost-link {
  color: var(--ds-color-text-muted);
  font-size: 0.88rem;
  text-decoration: none;
  padding: 0.5rem;
}

.support-note {
  margin-top: 0.25rem;
}

.support-note p {
  font-size: 0.82rem;
  color: var(--ds-color-text-muted);
  margin: 0;
}
.fail-page :is(a, button):focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 3px; }
@media (prefers-reduced-motion: reduce) { .fail-circle { animation: none; } }
</style>
