<template>
  <div class="login-page" dir="rtl">
    <section class="login-hero" :aria-label="`ورود به ${brandName}`">
      <div class="hero-overlay"></div>
      <div class="hero-logo">
        <span class="logo-circle" aria-hidden="true"><Utensils :size="28" /></span>
        <h1 class="brand-name">{{ brandName }}</h1>
        <p class="brand-sub">طعم تازه، سفارش ساده</p>
      </div>
    </section>

    <section class="login-card" aria-label="ورود یا ثبت‌نام مشتری">
      <div v-if="step === 'phone'">
        <h2 class="card-title">ورود / ثبت‌نام</h2>
        <p class="card-sub">برای دریافت کد تأیید، شماره موبایل‌تان را وارد کنید.</p>
        <div class="input-group">
          <span class="input-prefix">+۹۸</span>
          <input
            ref="phoneInput"
            class="phone-input"
            type="tel"
            inputmode="numeric"
            maxlength="14"
            autocomplete="tel-national"
            aria-label="شماره موبایل"
            placeholder="۹۱۲ ۳۴۵ ۶۷۸۹"
            v-model="phone"
            @input="onPhoneInput"
            @keydown.enter="sendOtp"
            dir="ltr"
          />
        </div>
        <p class="input-hint">کد تأیید به این شماره ارسال می‌شود</p>
        <button class="primary-btn" :disabled="!isPhoneValid || sending" @click="sendOtp">
          <span v-if="sending" class="spinner"></span>
          <span v-else>ارسال کد تأیید</span>
        </button>
        <div class="divider"><span>یا</span></div>
        <a href="/menu" class="ghost-btn">ورود مهمان به منو</a>
      </div>

      <div v-else-if="step === 'otp'">
        <button class="back-row" @click="step = 'phone'">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
          تغییر شماره
        </button>
        <h2 class="card-title">کد تأیید</h2>
        <p class="card-sub">کد ۶ رقمی ارسال‌شده به <strong dir="ltr">{{ displayPhone }}</strong> را وارد کنید</p>

        <div class="otp-row">
          <input
            v-for="(_, i) in 6"
            :key="i"
            :ref="el => otpRefs[i] = el"
            class="otp-box"
            type="tel"
            inputmode="numeric"
            :maxlength="i === 0 ? 6 : 1"
            :autocomplete="i === 0 ? 'one-time-code' : 'off'"
            :aria-label="`رقم ${(i + 1).toLocaleString('fa-IR')} از کد تأیید`"
            v-model="otpDigits[i]"
            @input="onOtpInput(i, $event)"
            @keydown="onOtpKeydown(i, $event)"
            dir="ltr"
          />
        </div>

        <div class="timer-row" v-if="countdown > 0">
          <span class="timer-text">ارسال مجدد تا {{ countdown }} ثانیه</span>
        </div>
        <button v-else class="resend-btn" @click="sendOtp">ارسال مجدد کد</button>

        <button class="primary-btn" :disabled="otpCode.length < 6 || verifying" @click="verifyOtp">
          <span v-if="verifying" class="spinner"></span>
          <span v-else>تأیید و ورود</span>
        </button>
      </div>

      <p class="error-msg" v-if="error">{{ error }}</p>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Utensils } from 'lucide-vue-next'
import { sendOtp as sendOtpAPI, verifyOtp as verifyOtpAPI } from '@/utils/api'
import { normalizeMobile } from '@/utils/format'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
const props = defineProps({
  boot: { type: Object, default: () => ({}) },
})
const brandName = computed(() =>
  props.boot?.branding?.name || window._BOOT?.restaurant_name || window._BOOT?.brand_name || 'رستوران',
)
const step = ref('phone')
const phone = ref('')
const otpDigits = ref(['', '', '', '', '', ''])
const otpRefs = ref([])
const sending = ref(false)
const verifying = ref(false)
const error = ref('')
const countdown = ref(0)
let countdownTimer = null

const phoneInput = ref(null)

const isPhoneValid = computed(() => {
  const cleaned = normalizeMobile(phone.value)
  return cleaned.length === 10 && cleaned.startsWith('9')
})

const displayPhone = computed(() => {
  const cleaned = normalizeMobile(phone.value)
  return `0${cleaned}`
})

const otpCode = computed(() => otpDigits.value.join(''))

function onPhoneInput(e) {
  let cleaned = normalizeMobile(e.target.value)
  if (cleaned.startsWith('0098') && cleaned.length > 10) cleaned = cleaned.slice(4)
  else if (cleaned.startsWith('98') && cleaned.length > 10) cleaned = cleaned.slice(2)
  else if (cleaned.startsWith('0') && cleaned.length > 10) cleaned = cleaned.slice(1)
  phone.value = cleaned.slice(0, 10)
}

async function sendOtp() {
  if (!isPhoneValid.value || sending.value) return
  sending.value = true
  error.value = ''
  try {
    const fullPhone = `0${normalizeMobile(phone.value)}`
    const result = await sendOtpAPI({ mobile: fullPhone })
    if (result?.debug_otp) console.info('[Restaurant OTP]', result.debug_otp)
    step.value = 'otp'
    otpDigits.value = ['', '', '', '', '', '']
    startCountdown(120)
    setTimeout(() => otpRefs.value[0]?.focus(), 100)
  } catch (e) {
    error.value = 'خطا در ارسال کد. لطفاً دوباره تلاش کنید.'
  } finally {
    sending.value = false
  }
}

async function verifyOtp() {
  if (otpCode.value.length < 6 || verifying.value) return
  verifying.value = true
  error.value = ''
  try {
    const fullPhone = `0${normalizeMobile(phone.value)}`
    const data = await verifyOtpAPI({ mobile: fullPhone, otp: otpCode.value })
    if (data?.success || data?.verified) {
      const customer = data.customer || {}
      try {
        localStorage.setItem(CUSTOMER_AUTH_KEY, JSON.stringify({
          mobile: fullPhone,
          customer_name: customer.name || '',
          customer_id: customer.customer_id || '',
          verified_at: new Date().toISOString(),
        }))
        localStorage.setItem('customer_phone', fullPhone)
        if (customer.name) localStorage.setItem('customer_name', customer.name)
      } catch {}
      window.location.href = postLoginDestination()
    } else {
      error.value = 'کد وارد شده اشتباه است.'
    }
  } catch (e) {
    error.value = 'خطا در تأیید. لطفاً دوباره تلاش کنید.'
  } finally {
    verifying.value = false
  }
}

function onOtpInput(index, event) {
  const digits = normalizeMobile(event.target.value)
  if (digits.length > 1) {
    const nextDigits = [...otpDigits.value]
    digits.slice(0, 6 - index).split('').forEach((digit, offset) => {
      nextDigits[index + offset] = digit
    })
    otpDigits.value = nextDigits
    event.target.value = nextDigits[index] || ''
    const nextIndex = Math.min(index + digits.length, 5)
    otpRefs.value[nextIndex]?.focus()
  } else {
    const val = digits.slice(0, 1)
    otpDigits.value[index] = val
    if (val && index < 5) otpRefs.value[index + 1]?.focus()
  }
  if (otpCode.value.length === 6) verifyOtp()
}

function onOtpKeydown(index, event) {
  if (event.key === 'Backspace' && !otpDigits.value[index] && index > 0) {
    otpRefs.value[index - 1]?.focus()
  }
}

function postLoginDestination() {
  const fallback = '/customer/dashboard'
  const requested = new URLSearchParams(window.location.search).get('redirect') || fallback
  if (!requested.startsWith('/') || requested.startsWith('//') || requested.includes('\\')) return fallback

  try {
    const destination = new URL(requested, window.location.origin)
    if (destination.origin !== window.location.origin || destination.pathname.startsWith('/customer/login')) return fallback
    return `${destination.pathname}${destination.search}${destination.hash}`
  } catch {
    return fallback
  }
}

function startCountdown(seconds) {
  countdown.value = seconds
  clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(countdownTimer)
  }, 1000)
}

onMounted(() => phoneInput.value?.focus())
onUnmounted(() => clearInterval(countdownTimer))
</script>

<style scoped>
.login-page {
  min-height: 100dvh;
  width: min(1160px, 100%);
  margin-inline: auto;
  padding: clamp(1rem, 3vw, 2.5rem);
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 0.95fr);
  align-items: center;
  gap: clamp(1rem, 3vw, 2.5rem);
  background:
    radial-gradient(ellipse at 12% 12%, var(--ds-color-action-accent-soft) 0, transparent 42%),
    var(--ds-color-bg-page);
  direction: rtl;
}

.login-hero {
  position: relative;
  grid-column: 2;
  min-height: min(600px, calc(100dvh - 5rem));
  width: 100%;
  display: grid;
  place-items: center;
  overflow: hidden;
  isolation: isolate;
  border-radius: 32px;
  background: var(--ds-color-action-primary);
  box-shadow: 0 24px 64px color-mix(in srgb, var(--ds-color-action-primary) 20%, transparent);
}

.hero-overlay {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  background:
    radial-gradient(ellipse at 80% 15%, color-mix(in srgb, var(--ds-color-action-accent) 25%, transparent), transparent 42%),
    radial-gradient(ellipse at 15% 85%, color-mix(in srgb, var(--ds-color-action-accent) 18%, transparent), transparent 42%);
}

.hero-overlay::before,
.hero-overlay::after {
  content: '';
  position: absolute;
  width: clamp(240px, 35vw, 440px);
  aspect-ratio: 1;
  border: 1px solid color-mix(in srgb, var(--ds-color-action-primary-foreground) 22%, transparent);
  border-radius: 50%;
}

.hero-overlay::before {
  inset-inline-start: -18%;
  bottom: -32%;
  box-shadow:
    0 0 0 24px color-mix(in srgb, var(--ds-color-action-primary-foreground) 5%, transparent),
    0 0 0 52px color-mix(in srgb, var(--ds-color-action-primary-foreground) 4%, transparent);
}

.hero-overlay::after {
  inset-inline-end: -24%;
  top: -38%;
  width: clamp(180px, 25vw, 320px);
  border-color: color-mix(in srgb, var(--ds-color-action-accent) 60%, transparent);
}

.hero-logo {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.85rem;
  padding: 2rem;
  text-align: center;
  color: var(--ds-color-action-primary-foreground);
}

.logo-circle {
  width: 76px;
  height: 76px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid color-mix(in srgb, var(--ds-color-action-primary-foreground) 32%, transparent);
  background: color-mix(in srgb, var(--ds-color-action-accent) 24%, transparent);
  color: var(--ds-color-action-primary-foreground);
  box-shadow: 0 12px 28px color-mix(in srgb, var(--ds-color-text-primary) 12%, transparent);
}

.brand-name {
  color: inherit;
  font-size: clamp(1.6rem, 2.5vw, 2.2rem);
  font-weight: 800;
  margin: 0;
}

.brand-sub {
  color: color-mix(in srgb, var(--ds-color-action-primary-foreground) 78%, transparent);
  font-size: 1rem;
  margin: 0;
  line-height: 1.7;
}

.login-card {
  grid-column: 1;
  align-self: center;
  width: 100%;
  max-width: 480px;
  margin: 0;
  padding: clamp(1.5rem, 3vw, 2.5rem);
  position: relative;
  z-index: 2;
  border: 1px solid var(--ds-color-border);
  border-radius: 28px;
  background: var(--ds-color-surface-raised);
  box-shadow: var(--shadow-soft);
}

.back-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: none;
  border: none;
  color: var(--ds-color-text-muted, #846b58);
  font-size: 0.9rem;
  font-family: inherit;
  cursor: pointer;
  padding: 0;
  margin-bottom: 1.2rem;
}

.card-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--ds-color-text-primary, #3f2a1d);
  margin: 0 0 0.4rem;
}

.card-sub {
  font-size: 0.9rem;
  color: var(--ds-color-text-muted, #846b58);
  margin: 0 0 1.8rem;
}

.input-group {
  display: flex;
  align-items: center;
  border: 2px solid var(--ds-color-border, #e5ddd4);
  border-radius: 16px;
  overflow: hidden;
  background: var(--ds-color-surface-muted, #fdf8f1);
  transition: border-color 0.2s;
}
.input-group:focus-within { border-color: var(--ds-color-action-primary); box-shadow: 0 0 0 3px var(--ds-color-action-primary-soft); }
.login-page :is(button, a, input):focus-visible {
  outline: 3px solid var(--ds-color-focus-ring);
  outline-offset: 3px;
}

.input-prefix {
  padding: 0 1rem;
  font-size: 0.95rem;
  color: var(--ds-color-text-muted, #846b58);
  font-weight: 600;
  border-left: 2px solid var(--ds-color-border, #e5ddd4);
  background: var(--ds-color-surface-muted, #f1e7db);
  align-self: stretch;
  display: flex;
  align-items: center;
}

.phone-input {
  flex: 1;
  padding: 1rem;
  border: none;
  background: transparent;
  font-size: 1.15rem;
  font-family: inherit;
  letter-spacing: 0.1em;
  outline: none;
  direction: ltr;
  text-align: center;
}

.input-hint {
  font-size: 0.78rem;
  color: var(--ds-color-text-muted, #846b58);
  text-align: center;
  margin: 0.6rem 0 1.5rem;
}

.primary-btn {
  width: 100%;
  min-height: 52px;
  padding: 0.8rem 1rem;
  background: var(--ds-color-action-primary);
  color: var(--ds-color-action-primary-foreground, #fff);
  border: none;
  border-radius: 16px;
  font-size: 1rem;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: opacity 0.2s, transform 0.15s;
}
.primary-btn:disabled { opacity: 0.55; cursor: not-allowed; }
.primary-btn:not(:disabled):active { transform: scale(0.98); }

.divider {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 1.25rem 0;
  color: var(--ds-color-text-muted, #846b58);
  font-size: 0.82rem;
}
.divider::before, .divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--ds-color-border, #e5ddd4);
}

.ghost-btn {
  width: 100%;
  min-height: 48px;
  display: block;
  padding: 0.9rem;
  border: 2px solid var(--ds-color-action-primary);
  border-radius: 16px;
  color: var(--ds-color-action-primary);
  text-align: center;
  font-size: 0.95rem;
  font-weight: 700;
  text-decoration: none;
  transition: background 0.2s;
}
.ghost-btn:hover { background: var(--ds-color-action-primary-soft); }

.otp-row {
  display: flex;
  gap: 0.6rem;
  justify-content: center;
  margin-bottom: 1.5rem;
  direction: ltr;
}

.otp-box {
  width: 46px;
  height: 54px;
  border: 2px solid var(--ds-color-border, #e5ddd4);
  border-radius: 14px;
  text-align: center;
  font-size: 1.3rem;
  font-weight: 700;
  font-family: inherit;
  background: var(--ds-color-surface-muted, #fdf8f1);
  outline: none;
  transition: border-color 0.2s;
}
.otp-box:focus { border-color: var(--ds-color-action-primary); box-shadow: 0 0 0 3px var(--ds-color-action-primary-soft); }

.timer-row { text-align: center; margin-bottom: 1.2rem; }
.timer-text { font-size: 0.85rem; color: var(--ds-color-text-muted, #846b58); }
.resend-btn {
  display: block;
  width: 100%;
  text-align: center;
  background: none;
  border: none;
  color: var(--ds-color-action-primary);
  font-size: 0.9rem;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  margin-bottom: 1.2rem;
}

.error-msg {
  color: var(--ds-color-status-danger, #e74c3c);
  font-size: 0.85rem;
  text-align: center;
  margin-top: 0.75rem;
  background: var(--ds-color-status-danger-soft, #fff0f0);
  border-radius: 10px;
  padding: 0.6rem 0.8rem;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid color-mix(in srgb, var(--ds-color-action-primary-foreground, #fff) 40%, transparent);
  border-top-color: var(--ds-color-action-primary-foreground, #fff);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 919px) {
  .login-page {
    width: 100%;
    grid-template-columns: minmax(0, 1fr);
    align-content: start;
    gap: 0;
    padding: 0.75rem 0.75rem calc(96px + env(safe-area-inset-bottom));
  }

  .login-hero {
    grid-column: 1;
    min-height: clamp(176px, 24svh, 218px);
    border-radius: 24px;
  }

  .hero-logo { gap: 0.55rem; padding: 1rem 0.8rem 1.5rem; }
  .logo-circle { width: 58px; height: 58px; }
  .logo-circle svg { width: 24px; height: 24px; }
  .brand-name { font-size: 1.45rem; }
  .brand-sub { font-size: 0.88rem; }

  .login-card {
    grid-column: 1;
    justify-self: center;
    max-width: 520px;
    margin-top: -14px;
    padding: 1.35rem 1rem 1.25rem;
    border-radius: 24px;
  }

  .card-sub { margin-bottom: 1.2rem; }
  .input-hint { margin-bottom: 1.1rem; }
  .divider { margin: 1rem 0; }
  .otp-row { gap: clamp(0.25rem, 2vw, 0.6rem); }
  .otp-box { width: clamp(36px, 10.5vw, 46px); height: clamp(46px, 12vw, 54px); }
}

@media (prefers-reduced-motion: reduce) {
  .primary-btn,
  .input-group,
  .otp-box,
  .ghost-btn { transition: none; }
  .spinner { animation: none; }
}
</style>
