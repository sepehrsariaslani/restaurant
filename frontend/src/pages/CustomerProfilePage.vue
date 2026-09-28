<template>
  <div class="customer-page profile-page" dir="rtl">
    <CustomerPageHeader
      :eyebrow="isLoggedIn ? 'ویرایش حساب' : 'حساب مشتری'"
      :title="isLoggedIn ? 'ویرایش اطلاعات شخصی' : 'ورود برای مدیریت حساب'"
      :subtitle="isLoggedIn ? 'اطلاعات تماس برای سفارش‌های بعدی شما استفاده می‌شود.' : 'برای دیدن و ویرایش اطلاعات شخصی، ابتدا وارد حساب خود شوید.'"
      hero-class="profile-hero"
      fallback-href="/customer/dashboard"
    >
      <template #eyebrow-icon><UserRound :size="14" aria-hidden="true" /></template>
      <template #action>
        <a class="customer-page__action" :href="isLoggedIn ? '/customer/dashboard' : '/customer/login?redirect=/customer/profile'">
          <LayoutDashboard :size="16" />
          <span>{{ isLoggedIn ? 'حساب من' : 'ورود' }}</span>
        </a>
      </template>

      <div class="profile-hero__meta">
        <div class="profile-avatar">
          <span>{{ avatarLetter }}</span>
        </div>
        <div>
          <strong>{{ form.name || 'مهمان عزیز' }}</strong>
          <p>{{ form.phone || 'شماره ثبت نشده' }}</p>
        </div>
      </div>
    </CustomerPageHeader>

    <div class="customer-page__body">
      <p v-if="error" class="customer-section__hint customer-danger-text" role="alert">{{ error }} <a v-if="needsSignIn" href="/customer/login?redirect=%2Fcustomer%2Fprofile">ورود دوباره</a></p>

      <section v-if="!isLoggedIn" class="customer-glass-card customer-empty profile-login-prompt">
        <div class="customer-icon-badge"><UserRound :size="28" /></div>
        <h3>اطلاعات حساب در دسترس نیست</h3>
        <p>پس از ورود با شماره موبایل، می‌توانید اطلاعات شخصی خود را اینجا مدیریت کنید.</p>
        <a class="primary-btn" href="/customer/login?redirect=/customer/profile">ورود به حساب</a>
      </section>

      <section v-else class="customer-section customer-glass-card customer-list-card" :aria-busy="loading">
        <div class="customer-section__head">
          <div>
            <h2>اطلاعات قابل ویرایش</h2>
            <p>نام و ایمیل را ویرایش کنید؛ شماره موبایل، شناسه ورود شماست.</p>
          </div>
        </div>

        <div class="customer-stack">
          <div class="customer-field">
            <label>نام و نام خانوادگی</label>
            <input class="customer-input" v-model="form.name" placeholder="مثلاً: علی محمدی" autocomplete="name" />
          </div>
          <div class="customer-field">
            <label>شماره موبایل</label>
            <input class="customer-input" v-model="form.phone" placeholder="۰۹۱۲۳۴۵۶۷۸۹" dir="ltr" type="tel" readonly />
            <small class="customer-field__hint">شماره موبایل شناسه ورود شماست و از اینجا تغییر نمی‌کند.</small>
          </div>
          <div class="customer-field">
            <label>ایمیل (اختیاری)</label>
            <input class="customer-input" v-model="form.email" placeholder="example@email.com" dir="ltr" type="email" autocomplete="email" />
          </div>
          <button class="customer-primary-cta save-cta" :disabled="saving" @click="saveProfile">
            <LoaderCircle v-if="saving" :size="18" class="spin" />
            <Save v-else :size="18" />
            <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره تغییرات' }}</span>
          </button>
          <p class="customer-success-text save-success" v-if="saved">پروفایل با موفقیت ذخیره شد.</p>
        </div>
      </section>

      <section v-if="isLoggedIn" class="customer-section customer-glass-card customer-list-card password-section">
        <div class="customer-section__head">
          <div>
            <h2>تغییر رمز عبور</h2>
            <p>برای امنیت حساب، رمز فعلی و رمز جدید را وارد کنید.</p>
          </div>
        </div>
        <div class="customer-stack">
          <div class="customer-field">
            <label>رمز عبور فعلی</label>
            <input class="customer-input" v-model="passwordForm.current" type="password" autocomplete="current-password" />
          </div>
          <div class="customer-field">
            <label>رمز عبور جدید</label>
            <input class="customer-input" v-model="passwordForm.next" type="password" minlength="8" autocomplete="new-password" />
          </div>
          <div class="customer-field">
            <label>تکرار رمز عبور جدید</label>
            <input class="customer-input" v-model="passwordForm.confirm" type="password" minlength="8" autocomplete="new-password" />
          </div>
          <button class="customer-primary-cta save-cta" :disabled="changingPassword" @click="changePassword">
            <LoaderCircle v-if="changingPassword" :size="18" class="spin" />
            <Save v-else :size="18" />
            <span>{{ changingPassword ? 'در حال تغییر...' : 'تغییر رمز عبور' }}</span>
          </button>
          <p class="customer-success-text save-success" v-if="passwordSaved">رمز عبور با موفقیت تغییر کرد.</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { LayoutDashboard, LoaderCircle, Save, UserRound } from 'lucide-vue-next'
import CustomerPageHeader from '@/components/customer/CustomerPageHeader.vue'
import { changeCustomerPassword, getCustomerProfile, saveCustomerProfile } from '@/utils/api'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
const saving = ref(false)
const saved = ref(false)
const changingPassword = ref(false)
const passwordSaved = ref(false)
const loading = ref(false)
const error = ref('')
const needsSignIn = computed(() => { try { return !JSON.parse(localStorage.getItem(CUSTOMER_AUTH_KEY) || '{}').customer_token } catch { return true } })

const form = ref({
  name: '',
  phone: '',
  email: '',
})
const passwordForm = ref({ current: '', next: '', confirm: '' })

function readAuth() {
  try {
    const auth = JSON.parse(localStorage.getItem(CUSTOMER_AUTH_KEY) || '{}')
    return {
      mobile: auth.mobile || '',
      name: auth.customer_name || localStorage.getItem('customer_name') || '',
    }
  } catch {
    return { mobile: '', name: '' }
  }
}

function updateStoredAuthName(name = '') {
  try {
    const auth = JSON.parse(localStorage.getItem(CUSTOMER_AUTH_KEY) || '{}')
    localStorage.setItem(CUSTOMER_AUTH_KEY, JSON.stringify({ ...auth, customer_name: name }))
  } catch {}
}

try {
  const auth = readAuth()
  form.value.name = auth.name
  form.value.phone = auth.mobile
  form.value.email = localStorage.getItem('customer_email') || ''
} catch {}

const avatarLetter = computed(() => (form.value.name ? form.value.name.slice(0, 1) : 'ک'))
const isLoggedIn = computed(() => Boolean(String(form.value.phone || '').trim()))


async function saveProfile() {
  if (saving.value) return
  if (!readAuth().mobile) {
    window.location.href = '/customer/login?redirect=/customer/profile'
    return
  }
  if (!form.value.name.trim()) { error.value = 'نام و نام خانوادگی را وارد کنید.'; return }
  saving.value = true
  saved.value = false
  error.value = ''
  try {
    const result = await saveCustomerProfile({ name: form.value.name.trim(), email: form.value.email.trim() })
    if (!result?.customer?.customer_id) throw new Error('سرور ذخیره اطلاعات را تأیید نکرد؛ دوباره تلاش کنید.')
    const name = form.value.name.trim()
    localStorage.setItem('customer_name', name)
    localStorage.setItem('customer_email', form.value.email.trim())
    updateStoredAuthName(name)
    saved.value = true
    setTimeout(() => { saved.value = false }, 3000)
  } catch (err) { error.value = err.message || 'ذخیره اطلاعات حساب انجام نشد.' } finally {
    saving.value = false
  }
}

async function changePassword() {
  if (changingPassword.value) return
  error.value = ''
  passwordSaved.value = false
  if (!passwordForm.value.current) { error.value = 'رمز عبور فعلی را وارد کنید.'; return }
  if (passwordForm.value.next.length < 8) { error.value = 'رمز عبور جدید باید دست‌کم ۸ نویسه باشد.'; return }
  if (passwordForm.value.next !== passwordForm.value.confirm) { error.value = 'تکرار رمز عبور جدید با رمز واردشده یکسان نیست.'; return }
  changingPassword.value = true
  try {
    const result = await changeCustomerPassword({
      current_password: passwordForm.value.current,
      new_password: passwordForm.value.next,
      confirm_password: passwordForm.value.confirm,
    })
    if (!result?.success) throw new Error('تغییر رمز عبور تأیید نشد؛ دوباره تلاش کنید.')
    passwordForm.value = { current: '', next: '', confirm: '' }
    passwordSaved.value = true
    setTimeout(() => { passwordSaved.value = false }, 3000)
  } catch (err) { error.value = err.message || 'تغییر رمز عبور انجام نشد.' } finally { changingPassword.value = false }
}

onMounted(async () => {
  const auth = readAuth()
  if (!auth.mobile || needsSignIn.value) {
    window.location.replace('/customer/login?redirect=%2Fcustomer%2Fprofile')
    return
  }
  loading.value = true
  try {
    const data = await getCustomerProfile({ mobile: auth.mobile })
    const customer = data?.customer || {}
    form.value.name = customer.name || auth.name || form.value.name
    form.value.phone = customer.mobile || auth.mobile
    form.value.email = customer.email || ''
  } catch (err) {
    error.value = err?.message || 'خطا در دریافت پروفایل'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.hero-side-placeholder {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
}

.profile-hero__meta {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  margin-top: 0.9rem;
}

.profile-avatar {
  width: 72px;
  height: 72px;
  border-radius: 24px;
  background: var(--ds-color-action-primary-soft);
  border: 1px solid rgb(255 255 255 / 0.18);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.7rem;
  font-weight: 800;
  color: var(--ds-color-action-primary);
}

.profile-hero__meta strong {
  display: block;
  font-size: 1.02rem;
}

.profile-hero__meta p {
  margin: 0.3rem 0 0;
  color: var(--ds-color-text-secondary);
}

.save-cta {
  margin-top: 0.3rem;
}

.save-success {
  margin: 0.2rem 0 0;
  text-align: center;
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
