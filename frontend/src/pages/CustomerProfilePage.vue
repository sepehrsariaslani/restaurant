<template>
  <div class="profile-page" dir="rtl">
    <!-- Header -->
    <div class="page-header">
      <button class="back-btn" @click="goBack" aria-label="بازگشت">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
      </button>
      <h1 class="page-title">پروفایل من</h1>
      <div style="width:40px"></div>
    </div>

    <!-- Avatar -->
    <div class="avatar-section">
      <div class="avatar-circle">{{ avatarLetter }}</div>
      <button class="change-avatar-btn" type="button">ویرایش تصویر</button>
    </div>

    <!-- Form -->
    <div class="form-card">
      <div class="form-group">
        <label>نام و نام خانوادگی</label>
        <input class="form-input" v-model="form.name" placeholder="مثلاً: علی محمدی" />
      </div>
      <div class="form-group">
        <label>شماره موبایل</label>
        <input class="form-input" v-model="form.phone" placeholder="۰۹۱۲۳۴۵۶۷۸۹" dir="ltr" type="tel" readonly />
        <small class="field-hint">شماره موبایل قابل تغییر نیست</small>
      </div>
      <div class="form-group">
        <label>ایمیل (اختیاری)</label>
        <input class="form-input" v-model="form.email" placeholder="example@email.com" dir="ltr" type="email" />
      </div>
      <div class="form-group">
        <label>تاریخ تولد</label>
        <input class="form-input" v-model="form.birthday" placeholder="۱۳۷۰/۰۱/۰۱" />
      </div>

      <button class="save-btn" :disabled="saving" @click="saveProfile">
        <span v-if="saving" class="spinner"></span>
        <span v-else>ذخیره تغییرات</span>
      </button>
      <p class="success-msg" v-if="saved">✓ پروفایل با موفقیت ذخیره شد</p>
    </div>

    <!-- Menu Items -->
    <div class="menu-list">
      <a href="/customer/addresses" class="menu-item">
        <span class="mi-icon">📍</span>
        <span class="mi-label">آدرس‌های من</span>
        <svg class="mi-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
      </a>
      <a href="/customer/branches" class="menu-item">
        <span class="mi-icon">🏪</span>
        <span class="mi-label">شعبه‌ها</span>
        <svg class="mi-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
      </a>
      <button class="menu-item logout-item" @click="logout">
        <span class="mi-icon">🚪</span>
        <span class="mi-label" style="color:#e74c3c">خروج از حساب</span>
      </button>
    </div>

    <div class="bottom-spacer"></div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const saving = ref(false)
const saved = ref(false)

const form = ref({
  name: '',
  phone: '',
  email: '',
  birthday: '',
})

try {
  form.value.name = localStorage.getItem('customer_name') || ''
  form.value.phone = localStorage.getItem('customer_phone') || ''
  form.value.email = localStorage.getItem('customer_email') || ''
} catch {}

const avatarLetter = computed(() => {
  return form.value.name ? form.value.name.slice(0, 1) : '👤'
})

function goBack() { window.history.back() }

async function saveProfile() {
  saving.value = true
  saved.value = false
  try {
    await new Promise(r => setTimeout(r, 600))
    localStorage.setItem('customer_name', form.value.name)
    localStorage.setItem('customer_email', form.value.email)
    saved.value = true
    setTimeout(() => { saved.value = false }, 3000)
  } finally {
    saving.value = false
  }
}

function logout() {
  if (!confirm('آیا مطمئن هستید که می‌خواهید خارج شوید؟')) return
  localStorage.removeItem('customer_name')
  localStorage.removeItem('customer_phone')
  localStorage.removeItem('customer_email')
  window.location.href = '/customer/login'
}
</script>

<style scoped>
.profile-page { min-height: 100vh; background: #f7f0e8; direction: rtl; padding-bottom: 7rem; }

.page-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 3.5rem 1rem 1rem;
  background: #fff;
  border-bottom: 1px solid #ede3d8;
}
.back-btn {
  width: 40px; height: 40px; border-radius: 50%;
  background: #f7f0e8; border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  color: #3f2a1d;
}
.page-title { font-size: 1.1rem; font-weight: 800; color: #3f2a1d; margin: 0; }

.avatar-section {
  display: flex; flex-direction: column; align-items: center;
  padding: 2rem 1rem 1rem; gap: 0.75rem;
}
.avatar-circle {
  width: 90px; height: 90px; border-radius: 50%;
  background: linear-gradient(135deg, #6f4a31, #c98d42);
  display: flex; align-items: center; justify-content: center;
  font-size: 2.2rem; color: #fff; font-weight: 800;
  box-shadow: 0 8px 24px rgba(111,74,49,0.3);
}
.change-avatar-btn {
  background: none; border: none; color: #6f4a31; font-size: 0.85rem;
  font-weight: 600; font-family: inherit; cursor: pointer;
}

.form-card {
  background: #fff; border-radius: 24px; margin: 0 1rem 1rem;
  padding: 1.5rem; box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}
.form-group { margin-bottom: 1.2rem; }
.form-group label { display: block; font-size: 0.82rem; font-weight: 700; color: #846b58; margin-bottom: 0.45rem; }
.form-input {
  width: 100%; padding: 0.85rem 1rem;
  border: 1.5px solid #e5ddd4; border-radius: 14px;
  background: #fdf8f1; font-size: 0.95rem; font-family: inherit;
  outline: none; box-sizing: border-box; transition: border-color 0.2s;
}
.form-input:focus { border-color: #6f4a31; }
.form-input[readonly] { color: #846b58; }
.field-hint { font-size: 0.72rem; color: #b0997f; margin-top: 0.3rem; display: block; }

.save-btn {
  width: 100%; padding: 1rem;
  background: #6f4a31; color: #fff; border: none;
  border-radius: 16px; font-size: 1rem; font-weight: 700;
  font-family: inherit; cursor: pointer; margin-top: 0.5rem;
  display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  transition: opacity 0.2s;
}
.save-btn:disabled { opacity: 0.55; }

.success-msg { text-align: center; color: #2e7d32; font-size: 0.88rem; margin-top: 0.8rem; }

.menu-list { background: #fff; border-radius: 24px; margin: 0 1rem; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06); }
.menu-item {
  display: flex; align-items: center; gap: 0.9rem;
  padding: 1rem 1.2rem; text-decoration: none; color: inherit;
  border-bottom: 1px solid #f1e7db; width: 100%; background: none;
  font-family: inherit; cursor: pointer; font-size: 0.95rem;
}
.menu-item:last-child { border-bottom: none; }
.mi-icon { font-size: 1.3rem; flex-shrink: 0; }
.mi-label { flex: 1; font-weight: 600; color: #3f2a1d; }
.mi-arrow { color: #c5b09a; flex-shrink: 0; }
.logout-item { border: none; }

.spinner { width: 18px; height: 18px; border: 2px solid rgba(255,255,255,0.4); border-top-color: #fff; border-radius: 50%; animation: spin 0.7s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }
.bottom-spacer { height: 2rem; }
</style>
