<template>
  <div class="login-page" dir="rtl">
    <div class="login-hero">
      <div class="hero-overlay"></div>
      <img class="hero-bg" src="https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=900&auto=format&fit=crop&q=80" alt="" />
      <div class="hero-logo">
        <div class="logo-circle">🍽️</div>
        <h1 class="brand-name">{{ brandName }}</h1>
        <p class="brand-sub">با شماره موبایل وارد شوید</p>
      </div>
    </div>

    <div class="login-card">
      <div v-if="step === 'phone'">
        <h2 class="card-title">ورود / ثبت‌نام</h2>
        <p class="card-sub">شماره موبایل خود را وارد کنید</p>
        <div class="input-group">
          <span class="input-prefix">+۹۸</span>
          <input
            ref="phoneInput"
            class="phone-input"
            type="tel"
            inputmode="numeric"
            maxlength="10"
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
            maxlength="1"
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
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const brandName = ref(window._BOOT?.restaurant_name || window._BOOT?.brand_name || 'رستوران')
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
  const cleaned = phone.value.replace(/\D/g, '')
  return cleaned.length === 10 && cleaned.startsWith('9')
})

const displayPhone = computed(() => {
  const cleaned = phone.value.replace(/\D/g, '')
  return `0${cleaned}`
})

const otpCode = computed(() => otpDigits.value.join(''))

function onPhoneInput(e) {
  phone.value = e.target.value.replace(/\D/g, '').slice(0, 10)
}

async function sendOtp() {
  if (!isPhoneValid.value || sending.value) return
  sending.value = true
  error.value = ''
  try {
    const fullPhone = `0${phone.value.replace(/\D/g, '')}`
    await fetch('/api/method/restaurant.api.send_otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': getCsrfToken() },
      body: JSON.stringify({ mobile: fullPhone }),
    })
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
    const fullPhone = `0${phone.value.replace(/\D/g, '')}`
    const res = await fetch('/api/method/restaurant.api.verify_otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': getCsrfToken() },
      body: JSON.stringify({ mobile: fullPhone, otp: otpCode.value }),
    })
    const data = await res.json()
    if (data?.message?.success) {
      window.location.href = '/customer/dashboard'
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
  const val = event.target.value.replace(/\D/g, '').slice(0, 1)
  otpDigits.value[index] = val
  if (val && index < 5) {
    otpRefs.value[index + 1]?.focus()
  }
  if (otpCode.value.length === 6) verifyOtp()
}

function onOtpKeydown(index, event) {
  if (event.key === 'Backspace' && !otpDigits.value[index] && index > 0) {
    otpRefs.value[index - 1]?.focus()
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

function getCsrfToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? match[1] : ''
}

onMounted(() => phoneInput.value?.focus())
onUnmounted(() => clearInterval(countdownTimer))
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f7f0e8;
  direction: rtl;
}

.login-hero {
  position: relative;
  height: 280px;
  overflow: hidden;
  flex-shrink: 0;
}

.hero-bg {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, rgba(30,15,5,0.5) 0%, rgba(30,15,5,0.8) 100%);
}

.hero-logo {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  text-align: center;
}

.logo-circle {
  width: 70px;
  height: 70px;
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(10px);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  border: 2px solid rgba(255,255,255,0.3);
}

.brand-name {
  color: #fff;
  font-size: 1.6rem;
  font-weight: 800;
  margin: 0;
}

.brand-sub {
  color: rgba(255,255,255,0.75);
  font-size: 0.9rem;
  margin: 0;
}

.login-card {
  background: #fff;
  border-radius: 32px 32px 0 0;
  margin-top: -24px;
  flex: 1;
  padding: 2rem 1.5rem 6rem;
  position: relative;
  z-index: 2;
  max-width: 480px;
  width: 100%;
  margin-left: auto;
  margin-right: auto;
}

.back-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: none;
  border: none;
  color: var(--text-muted, #846b58);
  font-size: 0.9rem;
  font-family: inherit;
  cursor: pointer;
  padding: 0;
  margin-bottom: 1.2rem;
}

.card-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text-primary, #3f2a1d);
  margin: 0 0 0.4rem;
}

.card-sub {
  font-size: 0.9rem;
  color: var(--text-muted, #846b58);
  margin: 0 0 1.8rem;
}

.input-group {
  display: flex;
  align-items: center;
  border: 2px solid #e5ddd4;
  border-radius: 16px;
  overflow: hidden;
  background: #fdf8f1;
  transition: border-color 0.2s;
}
.input-group:focus-within { border-color: var(--accent-green, #6f4a31); }

.input-prefix {
  padding: 0 1rem;
  font-size: 0.95rem;
  color: var(--text-muted, #846b58);
  font-weight: 600;
  border-left: 2px solid #e5ddd4;
  background: #f1e7db;
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
  color: var(--text-muted, #846b58);
  text-align: center;
  margin: 0.6rem 0 1.5rem;
}

.primary-btn {
  width: 100%;
  padding: 1rem;
  background: var(--accent-green, #6f4a31);
  color: #fff;
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
  color: var(--text-muted, #846b58);
  font-size: 0.82rem;
}
.divider::before, .divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #e5ddd4;
}

.ghost-btn {
  width: 100%;
  display: block;
  padding: 0.9rem;
  border: 2px solid var(--accent-green, #6f4a31);
  border-radius: 16px;
  color: var(--accent-green, #6f4a31);
  text-align: center;
  font-size: 0.95rem;
  font-weight: 700;
  text-decoration: none;
  transition: background 0.2s;
}
.ghost-btn:hover { background: rgba(111,74,49,0.06); }

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
  border: 2px solid #e5ddd4;
  border-radius: 14px;
  text-align: center;
  font-size: 1.3rem;
  font-weight: 700;
  font-family: inherit;
  background: #fdf8f1;
  outline: none;
  transition: border-color 0.2s;
}
.otp-box:focus { border-color: var(--accent-green, #6f4a31); }

.timer-row { text-align: center; margin-bottom: 1.2rem; }
.timer-text { font-size: 0.85rem; color: var(--text-muted, #846b58); }
.resend-btn {
  display: block;
  width: 100%;
  text-align: center;
  background: none;
  border: none;
  color: var(--accent-green, #6f4a31);
  font-size: 0.9rem;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  margin-bottom: 1.2rem;
}

.error-msg {
  color: #e74c3c;
  font-size: 0.85rem;
  text-align: center;
  margin-top: 0.75rem;
  background: #fff0f0;
  border-radius: 10px;
  padding: 0.6rem 0.8rem;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
