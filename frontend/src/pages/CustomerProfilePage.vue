<template>
  <div class="customer-page profile-page" dir="rtl">
    <section class="customer-page__hero profile-hero">
      <div class="customer-page__topbar">
        <button class="customer-page__back" @click="goBack" aria-label="بازگشت">
          <ChevronRight :size="20" />
        </button>
        <div class="customer-page__titles">
          <p class="customer-page__eyebrow"><UserRound :size="14" /> ویرایش حساب</p>
          <h1 class="customer-page__title">ویرایش اطلاعات شخصی</h1>
          <p class="customer-page__subtitle">این صفحه فقط برای اصلاح اطلاعات پایه حساب شماست.</p>
        </div>
        <a class="customer-page__action" href="/customer/dashboard">
          <LayoutDashboard :size="16" />
          <span>حساب من</span>
        </a>
      </div>

      <div class="profile-hero__meta">
        <div class="profile-avatar">
          <span>{{ avatarLetter }}</span>
        </div>
        <div>
          <strong>{{ form.name || 'مهمان عزیز' }}</strong>
          <p>{{ form.phone || 'شماره ثبت نشده' }}</p>
        </div>
      </div>
    </section>

    <div class="customer-page__body">
      <p v-if="error" class="customer-section__hint customer-danger-text">{{ error }}</p>

      <section class="customer-section customer-glass-card customer-list-card">
        <div class="customer-section__head">
          <div>
            <h2>اطلاعات قابل ویرایش</h2>
            <p>برای مدیریت آدرس‌ها، سفارش‌ها و شروع سفارش از صفحه «حساب من» استفاده کنید.</p>
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
          <div class="customer-field">
            <label>تاریخ تولد</label>
            <input class="customer-input" v-model="form.birthday" placeholder="۱۳۷۰/۰۱/۰۱" autocomplete="bday" />
          </div>

          <button class="customer-primary-cta save-cta" :disabled="saving" @click="saveProfile">
            <LoaderCircle v-if="saving" :size="18" class="spin" />
            <Save v-else :size="18" />
            <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره تغییرات' }}</span>
          </button>
          <p class="customer-success-text save-success" v-if="saved">پروفایل با موفقیت ذخیره شد.</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ChevronRight, LayoutDashboard, LoaderCircle, Save, UserRound } from 'lucide-vue-next'
import { getCustomerProfile } from '@/utils/api'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
const saving = ref(false)
const saved = ref(false)
const loading = ref(false)
const error = ref('')

const form = ref({
  name: '',
  phone: '',
  email: '',
  birthday: '',
})

function readAuth() {
  try {
    const auth = JSON.parse(localStorage.getItem(CUSTOMER_AUTH_KEY) || '{}')
    return {
      mobile: auth.mobile || localStorage.getItem('customer_phone') || '',
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
  form.value.birthday = localStorage.getItem('customer_birthday') || ''
} catch {}

const avatarLetter = computed(() => (form.value.name ? form.value.name.slice(0, 1) : 'ک'))

function goBack() { window.history.back() }

async function saveProfile() {
  saving.value = true
  saved.value = false
  try {
    await new Promise((resolve) => setTimeout(resolve, 450))
    const name = form.value.name.trim()
    localStorage.setItem('customer_name', name)
    localStorage.setItem('customer_email', form.value.email.trim())
    localStorage.setItem('customer_birthday', form.value.birthday.trim())
    updateStoredAuthName(name)
    saved.value = true
    setTimeout(() => { saved.value = false }, 3000)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  const auth = readAuth()
  if (!auth.mobile) return
  loading.value = true
  try {
    const data = await getCustomerProfile({ mobile: auth.mobile })
    const customer = data?.customer || {}
    form.value.name = customer.name || auth.name || form.value.name
    form.value.phone = customer.mobile || auth.mobile
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
  background: rgb(255 255 255 / 0.14);
  border: 1px solid rgb(255 255 255 / 0.18);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.7rem;
  font-weight: 800;
  color: #fff;
}

.profile-hero__meta strong {
  display: block;
  font-size: 1.02rem;
}

.profile-hero__meta p {
  margin: 0.3rem 0 0;
  color: rgb(255 255 255 / 0.72);
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
