<template>
  <div class="bom-permission-denied" dir="rtl">
    <div class="denied-icon">
      <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
        <path d="M7 11V7a5 5 0 0 1 10 0v4" />
      </svg>
    </div>
    <h2 class="denied-title">دسترسی محدود</h2>
    <p class="denied-message">
      برای مشاهده فرمول ساخت محصولات باید وارد حساب کاربری خود شوید.
      این بخش مخصوص کاربران با دسترسی به اطلاعات تولید و BOM است.
    </p>
    <div class="denied-actions">
      <a href="/customer/login?redirect=/bom-preview/" class="denied-login-btn">ورود به حساب کاربری</a>
      <a href="/menu" class="denied-back-link">بازگشت به منو</a>
    </div>
  </div>
</template>

<script setup>
// No logic needed — static permission denied page
</script>

<style scoped>
.bom-permission-denied {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  padding: 2rem 1.5rem;
  text-align: center;
}

.denied-icon {
  color: var(--text-muted, #7a6e64);
  margin-bottom: 1.25rem;
}

.denied-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--ink-800, #1e1a17);
  margin: 0 0 0.75rem;
}

.denied-message {
  font-size: 0.9rem;
  color: var(--ink-600, #4a4038);
  line-height: 1.7;
  max-width: 420px;
  margin: 0 0 1.5rem;
}

.denied-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: center;
}

.denied-login-btn {
  display: inline-flex;
  align-items: center;
  padding: 0.65rem 1.5rem;
  border-radius: 999px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.9);
  color: #fff;
  font-size: 0.88rem;
  font-weight: 600;
  text-decoration: none;
  transition: background 0.2s ease;
}

.denied-login-btn:hover {
  background: rgb(var(--palette-deep-sapphire-rgb));
}

.denied-back-link {
  font-size: 0.82rem;
  color: var(--text-muted, #7a6e64);
  text-decoration: underline;
  text-underline-offset: 3px;
}

.denied-back-link:hover {
  color: var(--ink-700, #2e2820);
}
</style>
