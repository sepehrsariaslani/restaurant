<template>
  <section class="login-gate" dir="rtl">
    <article class="login-shell">
      <aside class="login-visual">
        <p class="visual-kicker">NooshYar Management</p>
        <h1>ورود به داشبورد مدیریت</h1>
        <p class="visual-subtitle">تا قبل از لاگین، هیچ بخش مدیریتی نمایش داده نمی‌شود.</p>
        <div class="bear-frame" aria-hidden="true">
          <img src="/NooshYar%20Image.png" alt="NooshYar Bear" />
        </div>
      </aside>

      <section class="login-form-panel">
        <header class="login-head">
          <p class="kicker">خوش آمدید</p>
          <h2>ورود حساب مدیریت</h2>
          <p class="muted">نام کاربری و رمز عبور را وارد کنید.</p>
        </header>

        <form class="login-form" @submit.prevent="submitLogin">
          <label>
            <span>نام کاربری</span>
            <input v-model.trim="credentials.usr" class="input" autocomplete="username" placeholder="user@example.com" />
          </label>

          <label>
            <span>رمز عبور</span>
            <input
              v-model="credentials.pwd"
              class="input"
              type="password"
              autocomplete="current-password"
              placeholder="رمز عبور"
            />
          </label>

          <p v-if="error" class="error">{{ error }}</p>

          <button class="primary-btn login-submit" type="submit" :disabled="submitting">
            {{ submitting ? 'در حال ورود...' : 'ورود به پنل' }}
          </button>
        </form>
      </section>
    </article>
  </section>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { loginManagementUser } from '@/utils/api'

const props = defineProps({
  redirectTo: {
    type: String,
    default: '/management',
  },
})

const emit = defineEmits(['login-success'])

const credentials = reactive({
  usr: '',
  pwd: '',
})

const submitting = ref(false)
const error = ref('')

function resolveRedirectPath() {
  const redirect = String(props.redirectTo || '/management').trim()
  if (!redirect.startsWith('/management')) {
    return '/management'
  }
  return redirect
}

async function submitLogin() {
  error.value = ''
  if (!credentials.usr || !credentials.pwd) {
    error.value = 'نام کاربری و رمز عبور را وارد کنید.'
    return
  }

  submitting.value = true
  try {
    await loginManagementUser({
      usr: credentials.usr,
      pwd: credentials.pwd,
    })
    credentials.pwd = ''
    emit('login-success')
    if (typeof window !== 'undefined') {
      window.location.replace(resolveRedirectPath())
    }
  } catch (loginError) {
    error.value = loginError.message || 'ورود ناموفق بود.'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.login-gate {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 1rem;
}

.login-shell {
  --paper-light: #f8f2e8;
  --paper-mid: #e3c7a0;
  --paper-dark: #6f4a31;
  --paper-deep: #3f291b;
  width: min(980px, 100%);
  border: 1px solid rgb(111 74 49 / 0.24);
  border-radius: 26px;
  background:
    linear-gradient(140deg, rgb(248 242 232 / 0.98), rgb(239 226 205 / 0.95)),
    #f8f2e8;
  box-shadow: 0 24px 56px rgb(74 48 30 / 0.2);
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(320px, 1.1fr) minmax(0, 1fr);
}

.login-visual {
  padding: 1rem 1.1rem;
  background:
    radial-gradient(circle at 12% 14%, rgb(227 199 160 / 0.24), transparent 44%),
    radial-gradient(circle at 90% 85%, rgb(111 74 49 / 0.22), transparent 44%),
    linear-gradient(160deg, #f2dec1 0%, #d4b085 100%);
  border-left: 1px solid rgb(111 74 49 / 0.18);
  display: grid;
  gap: 0.5rem;
  align-content: start;
}

.visual-kicker {
  margin: 0;
  font-size: 0.74rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgb(63 41 27 / 0.78);
}

.login-visual h1 {
  margin: 0;
  font-size: 1.36rem;
  line-height: 1.45;
  color: #4f3322;
}

.visual-subtitle {
  margin: 0;
  color: rgb(79 51 34 / 0.82);
  font-size: 0.82rem;
}

.bear-frame {
  margin-top: 0.3rem;
  border-radius: 20px;
  border: 1px solid rgb(111 74 49 / 0.28);
  background: rgb(255 250 242 / 0.82);
  box-shadow: inset 0 0 0 1px rgb(255 255 255 / 0.42), 0 16px 28px rgb(79 51 34 / 0.16);
  overflow: hidden;
}

.bear-frame img {
  width: 100%;
  display: block;
  object-fit: cover;
}

.login-form-panel {
  padding: 1rem;
  display: grid;
  align-content: center;
  gap: 0.82rem;
}

.login-head {
  display: grid;
  gap: 0.28rem;
}

.kicker {
  margin: 0;
  font-size: 0.72rem;
  color: rgb(111 74 49 / 0.78);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.login-head h2 {
  margin: 0;
  font-size: 1.24rem;
  color: #4b2f20;
}

.login-head p {
  margin: 0;
  font-size: 0.79rem;
  color: rgb(75 47 32 / 0.72);
}

.login-form {
  display: grid;
  gap: 0.72rem;
}

.login-form label {
  display: grid;
  gap: 0.28rem;
  font-size: 0.8rem;
  color: #5f412d;
}

.login-form .input {
  border-color: rgb(111 74 49 / 0.28);
  background: rgb(255 255 255 / 0.72);
}

.login-form .input:focus {
  border-color: rgb(111 74 49 / 0.62);
  box-shadow: 0 0 0 3px rgb(111 74 49 / 0.16);
}

.login-submit {
  width: 100%;
  border-radius: 14px;
  padding: 0.72rem 1rem;
  background: linear-gradient(130deg, #7b5638 0%, #5a3a27 100%);
  box-shadow: 0 14px 24px rgb(79 51 34 / 0.25);
}

.login-submit:hover {
  box-shadow: 0 16px 26px rgb(79 51 34 / 0.3);
}

.error {
  margin: 0;
  color: var(--danger);
  font-size: 0.78rem;
}

@media (max-width: 920px) {
  .login-gate {
    padding: 0.6rem;
  }

  .login-shell {
    grid-template-columns: 1fr;
  }

  .login-visual {
    border-left: 0;
    border-bottom: 1px solid rgb(111 74 49 / 0.18);
    padding: 0.8rem;
  }

  .login-visual h1 {
    font-size: 1.12rem;
  }

  .bear-frame {
    max-height: 260px;
  }

  .bear-frame img {
    height: 100%;
    object-position: center top;
  }

  .login-form-panel {
    padding: 0.85rem;
  }
}
</style>
