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
      <div class="auth-method-tabs" role="group" aria-label="روش ورود">
        <button type="button" :class="{ active: authMethod === 'password' }" :aria-pressed="authMethod === 'password'" @click="selectAuthMethod('password')">ایمیل / رمز عبور</button>
        <button type="button" :class="{ active: authMethod === 'otp' }" :aria-pressed="authMethod === 'otp'" @click="selectAuthMethod('otp')">کد پیامکی</button>
      </div>

      <div v-if="emailVerificationLoading" class="email-verification-state" role="status">در حال بررسی پیوند و فعال‌سازی حساب شما…</div>

      <div v-if="authMethod === 'otp' && step === 'phone'">
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

      <div v-else-if="authMethod === 'otp' && step === 'otp'">
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

      <div v-else class="password-panel">
        <div v-if="step === 'email_sent'" class="email-verification-state">
          <h2 class="card-title">پیوند تأیید فرستاده شد</h2>
          <p class="card-sub">برای فعال‌کردن حساب، صندوق ورودی <strong dir="ltr">{{ verificationEmail }}</strong> را باز کنید و پیوند تأیید را بزنید. بعد از تأیید، حساب شما خودکار وارد می‌شود.</p>
          <button class="primary-btn" type="button" :disabled="sending" @click="beginPasswordRegistration">{{ sending ? 'در حال ارسال…' : 'ارسال دوبارهٔ پیوند' }}</button>
          <button class="mode-switch" type="button" @click="setAccountMode('login')">بازگشت به ورود</button>
        </div>
        <div v-else-if="step === 'register_otp'">
          <button class="back-row" type="button" @click="step = 'phone'; otpDigits = ['', '', '', '', '', '']">تغییر اطلاعات ثبت‌نام</button>
          <h2 class="card-title">تأیید شماره</h2>
          <p class="card-sub">کد شش‌رقمی ارسال‌شده به <strong dir="ltr">{{ registrationDisplayPhone }}</strong> را وارد کنید تا حساب به شمارهٔ خودتان متصل شود.</p>
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
          <div class="timer-row" v-if="countdown > 0"><span class="timer-text">ارسال مجدد تا {{ countdown }} ثانیه</span></div>
          <button v-else class="resend-btn" type="button" :disabled="sending" @click="beginPasswordRegistration">ارسال دوبارهٔ کد</button>
          <button class="primary-btn" type="button" :disabled="otpCode.length < 6 || registering" @click="finishPasswordRegistration">
            <span v-if="registering" class="spinner"></span>
            <span v-else>تأیید کد و ساخت حساب</span>
          </button>
        </div>

        <template v-else-if="accountMode === 'login'">
          <h2 class="card-title">ورود به حساب</h2>
          <p class="card-sub">با ایمیل یا شماره موبایل و رمز عبور وارد شوید.</p>
          <form class="password-form" @submit.prevent="loginWithPassword">
            <label class="auth-field"><span>ایمیل یا شماره موبایل</span><input ref="identifierInput" v-model.trim="identifier" type="text" autocomplete="username" :inputmode="identifier.includes('@') ? 'email' : 'tel'" placeholder="name@example.com یا 09…" required /></label>
            <label class="auth-field"><span>رمز عبور</span><input v-model="password" type="password" autocomplete="current-password" required @keydown.enter.prevent="loginWithPassword" /></label>
            <button class="primary-btn" type="submit" :disabled="!canLoginWithPassword || loggingIn">
              <span v-if="loggingIn" class="spinner"></span>
              <span v-else>ورود</span>
            </button>
          </form>
          <button class="mode-switch" type="button" @click="setAccountMode('register')">حساب ندارید؟ <strong>ثبت‌نام کنید</strong></button>
          <div class="divider"><span>یا</span></div>
          <a href="/menu" class="ghost-btn">ورود مهمان به منو</a>
        </template>

        <template v-else>
          <h2 class="card-title">ساخت حساب مشتری</h2>
          <p class="card-sub">پس از تأیید ایمیل، با ایمیل یا شماره موبایل و همین رمز وارد می‌شوید.</p>
          <form class="password-form" @submit.prevent="beginPasswordRegistration">
            <label class="auth-field"><span>نام و نام خانوادگی</span><input v-model.trim="registerName" type="text" autocomplete="name" required /></label>
            <label class="auth-field"><span>ایمیل <small>(پیوند فعال‌سازی به این نشانی می‌آید)</small></span><input v-model.trim="registerEmail" type="email" autocomplete="email" placeholder="name@example.com" required /></label>
            <label class="auth-field"><span>شماره موبایل</span><input v-model="registerPhone" type="tel" inputmode="numeric" autocomplete="tel" placeholder="09…" @input="onRegistrationPhoneInput" required /></label>
            <label class="auth-field"><span>کد معرفی <small>(اختیاری)</small></span><input v-model.trim="registerReferralCode" type="text" autocomplete="off" dir="ltr" placeholder="کد مربی یا دوست شما" /></label>
            <label class="auth-field"><span>رمز عبور</span><input v-model="registerPassword" type="password" autocomplete="new-password" required /></label>
            <label class="auth-field"><span>تکرار رمز عبور</span><input v-model="registerPasswordConfirmation" type="password" autocomplete="new-password" required /></label>
            <p class="auth-hint">حساب و هرگونه تخفیف یا اتصال به مربی فقط پس از تأیید ایمیل فعال می‌شود.</p>
            <button class="primary-btn" type="submit" :disabled="!canStartRegistration || sending">
              <span v-if="sending" class="spinner"></span>
              <span v-else>ارسال پیوند تأیید</span>
            </button>
          </form>
          <button class="mode-switch" type="button" @click="setAccountMode('login')">قبلاً ثبت‌نام کرده‌اید؟ <strong>وارد شوید</strong></button>
        </template>
      </div>

      <p class="error-msg" v-if="error">{{ error }}</p>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Utensils } from 'lucide-vue-next'
import {
  customerLoginPassword,
  customerRegisterPassword,
  customerRegisterWithEmail,
  customerVerifyEmailRegistration,
  sendOtp as sendOtpAPI,
  verifyOtp as verifyOtpAPI,
} from '@/utils/api'
import { normalizeMobile } from '@/utils/format'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
const referralCode = new URLSearchParams(window.location.search).get('ref') || ''
const props = defineProps({
  boot: { type: Object, default: () => ({}) },
})
const brandName = computed(() =>
  props.boot?.branding?.name || window._BOOT?.restaurant_name || window._BOOT?.brand_name || 'رستوران',
)
const authMethod = ref('password')
const accountMode = ref('login')
const step = ref('phone')
const phone = ref('')
const identifier = ref('')
const password = ref('')
const registerName = ref('')
const registerEmail = ref('')
const verificationEmail = ref('')
const registerReferralCode = ref(referralCode)
const registerPhone = ref('')
const registerPassword = ref('')
const registerPasswordConfirmation = ref('')
const registrationCustomerToken = ref('')
const otpDigits = ref(['', '', '', '', '', ''])
const otpRefs = ref([])
const sending = ref(false)
const verifying = ref(false)
const loggingIn = ref(false)
const registering = ref(false)
const emailVerificationLoading = ref(false)
const error = ref('')
const countdown = ref(0)
let countdownTimer = null

const phoneInput = ref(null)
const identifierInput = ref(null)

const isPhoneValid = computed(() => {
  const cleaned = normalizeMobile(phone.value)
  return cleaned.length === 10 && cleaned.startsWith('9')
})

const displayPhone = computed(() => {
  const cleaned = normalizeMobile(phone.value)
  return `0${cleaned}`
})

const otpCode = computed(() => otpDigits.value.join(''))
const registrationMobile = computed(() => {
  let cleaned = normalizeMobile(registerPhone.value)
  if (cleaned.startsWith('0098') && cleaned.length > 10) cleaned = cleaned.slice(4)
  else if (cleaned.startsWith('98') && cleaned.length > 10) cleaned = cleaned.slice(2)
  else if (cleaned.startsWith('0') && cleaned.length > 10) cleaned = cleaned.slice(1)
  return cleaned.length === 10 && cleaned.startsWith('9') ? `0${cleaned}` : ''
})
const registrationDisplayPhone = computed(() => registrationMobile.value || registerPhone.value)
const canLoginWithPassword = computed(() => Boolean(identifier.value.trim() && password.value))
const canStartRegistration = computed(() => Boolean(
  registerName.value.trim()
  && registerEmail.value.trim().includes('@')
  && registrationMobile.value
  && registerPassword.value.length >= 8
  && registerPassword.value === registerPasswordConfirmation.value,
))

function passwordLoginIdentifier() {
  const value = identifier.value.trim()
  if (value.includes('@')) return value.toLowerCase()
  let digits = normalizeMobile(value)
  if (digits.startsWith('0098')) digits = digits.slice(4)
  else if (digits.startsWith('98') && digits.length > 10) digits = digits.slice(2)
  else if (digits.startsWith('0') && digits.length > 10) digits = digits.slice(1)
  return digits.length === 10 && digits.startsWith('9') ? '0' + digits : value
}

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
    if (result?.cooldown) {
      error.value = result.message || 'برای ارسال دوباره کد، کمی صبر کنید.'
      return
    }
    if (result?.debug_otp) console.info('[Restaurant OTP]', result.debug_otp)
    step.value = 'otp'
    otpDigits.value = ['', '', '', '', '', '']
    startCountdown(120)
    setTimeout(() => otpRefs.value[0]?.focus(), 100)
  } catch (e) {
    error.value = String(e?.message || '').trim() || 'خطا در ارسال کد. لطفاً دوباره تلاش کنید.'
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
      persistCustomerSession(data, fullPhone)
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

function persistCustomerSession(data = {}, fallbackMobile = '') {
  const customer = data.customer || {}
  const mobile = customer.mobile || data.mobile || fallbackMobile
  try {
    localStorage.setItem(CUSTOMER_AUTH_KEY, JSON.stringify({
      mobile,
      customer_name: customer.name || '',
      customer_id: customer.customer_id || '',
      email: customer.email || '',
      verified_at: new Date().toISOString(),
      customer_token: data.customer_token || '',
    }))
    localStorage.setItem('customer_phone', mobile)
    if (customer.name) localStorage.setItem('customer_name', customer.name)
  } catch {}
}

function selectAuthMethod(method) {
  authMethod.value = method
  step.value = 'phone'
  error.value = ''
  otpDigits.value = ['', '', '', '', '', '']
  registrationCustomerToken.value = ''
}

function setAccountMode(mode) {
  accountMode.value = mode
  step.value = 'phone'
  error.value = ''
  password.value = ''
  registrationCustomerToken.value = ''
}

async function loginWithPassword() {
  if (!canLoginWithPassword.value || loggingIn.value) return
  loggingIn.value = true
  error.value = ''
  try {
    const result = await customerLoginPassword(passwordLoginIdentifier(), password.value)
    if (!result?.success || !result?.customer_token) throw new Error('ورود با این اطلاعات انجام نشد.')
    persistCustomerSession(result)
    window.location.href = postLoginDestination()
  } catch (e) {
    error.value = e.message || 'ایمیل/شماره یا رمز عبور نادرست است.'
  } finally {
    loggingIn.value = false
  }
}

function onRegistrationPhoneInput(event) {
  let cleaned = normalizeMobile(event.target.value)
  if (cleaned.startsWith('0098') && cleaned.length > 10) cleaned = cleaned.slice(4)
  else if (cleaned.startsWith('98') && cleaned.length > 10) cleaned = cleaned.slice(2)
  else if (cleaned.startsWith('0') && cleaned.length > 10) cleaned = cleaned.slice(1)
  registerPhone.value = cleaned.slice(0, 11)
}

async function beginPasswordRegistration() {
  if (!canStartRegistration.value || sending.value) {
    if (registerPassword.value !== registerPasswordConfirmation.value) error.value = 'تکرار رمز عبور با رمز واردشده یکسان نیست.'
    else if (registerPassword.value.length < 8) error.value = 'رمز عبور باید دست‌کم ۸ نویسه باشد.'
    return
  }
  sending.value = true
  error.value = ''
  try {
    const result = await customerRegisterWithEmail({
      name: registerName.value.trim(),
      email: registerEmail.value.trim(),
      mobile: registrationMobile.value,
      password: registerPassword.value,
      referral_code: registerReferralCode.value.trim(),
    })
    if (result?.status !== 'verification_sent') throw new Error('ارسال پیوند تأیید انجام نشد.')
    verificationEmail.value = result.email || registerEmail.value.trim()
    step.value = 'email_sent'
  } catch (e) {
    error.value = e.message || 'ارسال پیوند تأیید ناموفق بود؛ ایمیل و اطلاعات ثبت‌نام را بررسی کنید.'
  } finally {
    sending.value = false
  }
}

async function finishPasswordRegistration() {
  if (registering.value || otpCode.value.length < 6) return
  registering.value = true
  error.value = ''
  try {
    if (!registrationCustomerToken.value) {
      const verified = await verifyOtpAPI({
        mobile: registrationMobile.value,
        otp: otpCode.value,
        customer_name: registerName.value.trim(),
      })
      if (!(verified?.success || verified?.verified) || !verified?.customer_token) {
        throw new Error('کد تأیید معتبر نیست یا منقضی شده است.')
      }
      registrationCustomerToken.value = verified.customer_token
    }
    const result = await customerRegisterPassword({
      customer_token: registrationCustomerToken.value,
      name: registerName.value.trim(),
      email: registerEmail.value.trim(),
      password: registerPassword.value,
      referral_code: referralCode,
    })
    if (!result?.success || !result?.customer_token) throw new Error('ساخت حساب انجام نشد؛ دوباره تلاش کنید.')
    persistCustomerSession(result, registrationMobile.value)
    window.location.href = postLoginDestination()
  } catch (e) {
    error.value = e.message || 'ساخت حساب ناموفق بود؛ اطلاعات را بررسی کنید.'
  } finally {
    registering.value = false
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
  if (otpCode.value.length === 6) {
    if (authMethod.value === 'otp') verifyOtp()
    else finishPasswordRegistration()
  }
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

onMounted(() => {
  const verificationToken = new URLSearchParams(window.location.search).get('verify_email') || ''
  if (verificationToken) {
    emailVerificationLoading.value = true
    customerVerifyEmailRegistration(verificationToken).then((result) => {
      if (!result?.success || !result?.customer_token) throw new Error('فعال‌سازی حساب انجام نشد.')
      persistCustomerSession(result)
      window.location.replace(postLoginDestination())
    }).catch((err) => {
      error.value = err?.message || 'پیوند تأیید معتبر نیست یا منقضی شده است.'
    }).finally(() => {
      emailVerificationLoading.value = false
    })
    return
  }
  if (identifierInput.value) identifierInput.value.focus()
  else phoneInput.value?.focus()
})
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
  grid-row: 1;
  min-height: min(600px, calc(100dvh - 5rem));
  width: 100%;
  display: grid;
  place-items: center;
  overflow: hidden;
  isolation: isolate;
  border-radius: 32px;
  background: var(--ds-color-surface-muted);
  border: 1px solid var(--ds-color-border);
}

.hero-overlay {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  background:
    radial-gradient(ellipse at 80% 15%, var(--ds-color-action-accent-soft), transparent 42%),
    radial-gradient(ellipse at 15% 85%, var(--ds-color-action-primary-soft), transparent 42%);
}

.hero-overlay::before,
.hero-overlay::after {
  content: '';
  position: absolute;
  width: clamp(240px, 35vw, 440px);
  aspect-ratio: 1;
  border: 1px solid var(--ds-color-border);
  border-radius: 50%;
}

.hero-overlay::before {
  inset-inline-start: -18%;
  bottom: -32%;
  box-shadow:
    0 0 0 24px color-mix(in srgb, var(--ds-color-surface-raised) 35%, transparent),
    0 0 0 52px color-mix(in srgb, var(--ds-color-surface-raised) 25%, transparent);
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
  color: var(--ds-color-action-primary);
}

.logo-circle {
  width: 76px;
  height: 76px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid var(--ds-color-border);
  background: var(--ds-color-surface-raised);
  color: var(--ds-color-action-primary);
}

.brand-name {
  color: inherit;
  font-size: clamp(1.6rem, 2.5vw, 2.2rem);
  font-weight: 800;
  margin: 0;
}

.brand-sub {
  color: var(--ds-color-text-secondary);
  font-size: 1rem;
  margin: 0;
  line-height: 1.7;
}

.login-card {
  grid-column: 1;
  grid-row: 1;
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

.auth-method-tabs { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .35rem; margin-bottom: 1.25rem; padding: .3rem; border: 1px solid var(--ds-color-border); border-radius: 15px; background: var(--ds-color-surface-muted); }
.auth-method-tabs button { min-height: 44px; border: 0; border-radius: 11px; background: transparent; color: var(--ds-color-text-secondary); font: inherit; font-size: .83rem; font-weight: 700; cursor: pointer; }
.auth-method-tabs button.active { background: var(--ds-color-surface-raised); color: var(--ds-color-action-primary); box-shadow: var(--ds-shadow-sm); }
.password-form { display: grid; gap: .85rem; }
.auth-field { display: grid; gap: .38rem; color: var(--ds-color-text-secondary); font-size: .84rem; font-weight: 650; }
.auth-field small { color: var(--ds-color-text-muted); font-size: .76rem; font-weight: 400; }
.auth-field input { width: 100%; min-height: 48px; padding: .7rem .8rem; border: 1px solid var(--ds-color-border); border-radius: 13px; background: var(--ds-color-surface); color: var(--ds-color-text-primary); font: inherit; direction: ltr; text-align: start; }
.auth-field input:focus { outline: 3px solid var(--ds-color-action-primary-soft); border-color: var(--ds-color-action-primary); }
.auth-hint { margin: 0; color: var(--ds-color-text-muted); font-size: .76rem; line-height: 1.8; }
.email-verification-state { padding: .75rem; border: 1px solid var(--ds-color-border); border-radius: 16px; background: var(--ds-color-action-accent-soft); }
.mode-switch { display: block; width: 100%; margin-top: .9rem; padding: .5rem; border: 0; background: transparent; color: var(--ds-color-text-secondary); font: inherit; font-size: .86rem; cursor: pointer; }
.mode-switch strong { color: var(--ds-color-action-primary); }

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
    grid-row: auto;
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
    grid-row: auto;
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
