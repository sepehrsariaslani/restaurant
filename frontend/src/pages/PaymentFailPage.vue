<template>
  <div class="fail-page" dir="rtl">
    <div class="fail-body">

      <div class="fail-icon-wrap">
        <div class="fail-circle">
          <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        </div>
      </div>

      <h1 class="fail-title">پرداخت ناموفق</h1>
      <p class="fail-subtitle">متأسفانه پرداخت شما با موفقیت انجام نشد.</p>

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
        <p class="help-note">سفارش شما <strong>ذخیره نشده</strong> و هزینه‌ای از حساب کسر نشده است.</p>
      </div>

      <div class="actions">
        <a :href="retryUrl" class="primary-btn">🔄 تلاش مجدد</a>
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
  background: #f7f0e8;
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
  background: linear-gradient(135deg, #e05353, #c0392b);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(192,57,43,0.28);
  animation: pop 0.4s cubic-bezier(0.34,1.56,0.64,1);
}

@keyframes pop {
  from { transform: scale(0.5); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.fail-title {
  font-size: 1.7rem;
  font-weight: 800;
  color: #3f2a1d;
  margin: 0;
}

.fail-subtitle {
  color: #9e8878;
  font-size: 0.95rem;
  margin: -0.25rem 0 0;
  line-height: 1.6;
}

.info-card {
  width: 100%;
  background: #fff;
  border-radius: 16px;
  padding: 1.1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  box-shadow: 0 1px 4px rgba(111,74,49,0.07);
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.info-label { font-size: 0.85rem; color: #9e8878; }
.info-val { font-size: 1rem; color: #3f2a1d; letter-spacing: 0.03em; }

.status-pill {
  background: #fdecea;
  color: #c0392b;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.2rem 0.7rem;
  border-radius: 20px;
}

.help-card {
  width: 100%;
  background: #fff;
  border-radius: 16px;
  padding: 1.1rem 1.25rem;
  text-align: right;
  box-shadow: 0 1px 4px rgba(111,74,49,0.07);
}

.help-card h3 {
  font-size: 0.95rem;
  font-weight: 700;
  color: #3f2a1d;
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
  color: #5a4030;
  line-height: 1.5;
}

.help-note {
  font-size: 0.85rem;
  color: #9e8878;
  margin: 0;
  background: #f7f0e8;
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
  background: #6f4a31;
  color: #fff;
  padding: 0.9rem;
  border-radius: 12px;
  text-decoration: none;
  font-weight: 700;
  font-size: 1rem;
  transition: background 0.2s;
}

.primary-btn:hover { background: #5a3a27; }

.secondary-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  color: #6f4a31;
  padding: 0.85rem;
  border-radius: 12px;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  border: 1.5px solid #c4a882;
  transition: background 0.2s;
}

.secondary-btn:hover { background: #fdf5ee; }

.ghost-link {
  color: #9e8878;
  font-size: 0.88rem;
  text-decoration: none;
  padding: 0.5rem;
}

.support-note {
  margin-top: 0.25rem;
}

.support-note p {
  font-size: 0.82rem;
  color: #b0998a;
  margin: 0;
}
</style>
