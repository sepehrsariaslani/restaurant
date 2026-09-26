<template>
  <div class="customer-page wallet-page" dir="rtl">
    <CustomerPageHeader eyebrow="حساب من" title="کیف پول من" subtitle="موجودی قابل برداشت و اعتبار خرید شما جداگانه نگه‌داری می‌شوند." fallback-href="/customer/dashboard">
      <template #eyebrow-icon><Wallet :size="16" /></template>
      <template #action><a class="customer-page__action" href="/customer/orders">سفارش‌های من</a></template>
    </CustomerPageHeader>
    <main class="customer-page__body wallet-body">
      <p v-if="loading" class="wallet-status" role="status">در حال دریافت کیف پول…</p>
      <p v-if="error" class="wallet-error" role="alert">{{ error }} <button type="button" @click="loadWallet">تلاش دوباره</button></p>
      <p v-if="message" class="wallet-success" role="status">{{ message }}</p>

      <section class="wallet-balances" aria-label="موجودی‌های کیف پول">
        <article class="wallet-balance-card wallet-balance-card--cash customer-glass-card">
          <span class="wallet-icon"><Banknote :size="22" /></span>
          <small>موجودی قابل برداشت</small>
          <strong>{{ formatMoney(wallet.withdrawable_balance || 0, currency) }}</strong>
          <p>برای واریز به شبای بانکی، درخواست برداشت ثبت کنید.</p>
        </article>
        <article class="wallet-balance-card wallet-balance-card--cashback customer-glass-card">
          <span class="wallet-icon"><Gift :size="22" /></span>
          <small>اعتبار خرید (کش‌بک)</small>
          <strong>{{ formatMoney(wallet.cashback_balance || 0, currency) }}</strong>
          <p>فقط برای پرداخت سفارش در فروشگاه مصرف می‌شود و قابل برداشت نیست.</p>
        </article>
      </section>

      <section class="wallet-rules customer-glass-card">
        <div><Gift :size="19" /><h2>قانون بازگشت وجه خرید</h2></div>
        <p v-if="rules.club_enabled && Number(rules.cashback_percent) > 0">
          {{ Number(rules.cashback_percent).toLocaleString('fa-IR') }}٪ از سفارش‌های واجد شرایط پس از نهایی‌شدن به اعتبار خرید شما برمی‌گردد.
          <template v-if="Number(rules.cashback_min_order) > 0"> حداقل مبلغ سفارش: {{ formatMoney(rules.cashback_min_order, currency) }}.</template>
        </p>
        <p v-else>در حال حاضر قانون کش‌بک فعالی برای خریدها تنظیم نشده است.</p>
        <p class="wallet-rules-note">اعتبار خرید با موجودی قابل برداشت یکی نیست؛ درخواست پرداخت بانکی فقط از موجودی قابل برداشت کم می‌شود.</p>
      </section>

      <section class="withdraw-card customer-glass-card">
        <div class="wallet-section-head"><div><h2>درخواست واریز به حساب</h2><p>مبلغ درخواست پس از ثبت موقتاً از موجودی قابل برداشت کنار گذاشته می‌شود.</p></div><ArrowDownToLine :size="20" /></div>
        <form class="withdraw-form" @submit.prevent="submitWithdrawal">
          <label class="customer-field">مبلغ درخواست ({{ currencyLabel }})
            <input v-model.number="form.amount" class="customer-input" type="number" min="1" :max="Number(wallet.withdrawable_balance || 0)" step="1" required />
          </label>
          <label class="customer-field">شماره شبای بانکی
            <input v-model.trim="form.bank_iban" class="customer-input" dir="ltr" inputmode="latin" autocomplete="off" placeholder="IR…" required />
          </label>
          <label class="customer-field">نام صاحب حساب
            <input v-model.trim="form.account_holder" class="customer-input" autocomplete="name" required />
          </label>
          <label class="customer-field">توضیح (اختیاری)
            <input v-model.trim="form.note" class="customer-input" maxlength="240" placeholder="" />
          </label>
          <button class="withdraw-submit" type="submit" :disabled="saving || Number(form.amount) <= 0 || Number(form.amount) > Number(wallet.withdrawable_balance || 0)">
            {{ saving ? 'در حال ثبت درخواست…' : 'ثبت درخواست برداشت' }}
          </button>
        </form>
        <p class="wallet-footnote">درخواست‌ها توسط پشتیبانی بررسی و پرداخت بانکی به‌صورت دستی تأیید می‌شوند؛ ثبت درخواست به معنی واریز آنی نیست.</p>
      </section>

      <section class="wallet-history customer-glass-card">
        <div class="wallet-section-head"><div><h2>درخواست‌های برداشت</h2><p>وضعیت پیگیری درخواست‌های قبلی</p></div><Landmark :size="20" /></div>
        <div v-if="withdrawalRequests.length" class="wallet-request-list">
          <article v-for="row in withdrawalRequests" :key="row.name" class="wallet-request-row">
            <div><strong>{{ formatMoney(row.amount, currency) }}</strong><small>{{ row.bank_iban }} · {{ formatDate(row.creation) }}</small></div>
            <span class="request-status" :class="statusClass(row.status)">{{ row.status }}</span>
          </article>
        </div>
        <p v-else class="wallet-empty">هنوز درخواست برداشتی ثبت نکرده‌اید.</p>
      </section>

      <section class="wallet-history customer-glass-card">
        <div class="wallet-section-head"><div><h2>گردش کیف پول</h2><p>آخرین تغییرهای موجودی</p></div><History :size="20" /></div>
        <div v-if="transactions.length" class="wallet-transaction-list">
          <article v-for="row in transactions" :key="row.name" class="wallet-transaction-row">
            <span class="transaction-mark" :class="row.direction === 'واریز' ? 'is-credit' : 'is-debit'"><ArrowUpRight v-if="row.direction === 'واریز'" :size="18" /><ArrowDownLeft v-else :size="18" /></span>
            <div class="transaction-description"><strong>{{ row.kind }}</strong><small>{{ row.bucket === 'کش‌بک' ? 'اعتبار خرید' : 'موجودی قابل برداشت' }} · {{ formatDate(row.entry_date) }}</small><small v-if="row.note">{{ row.note }}</small></div>
            <strong class="transaction-amount" :class="row.direction === 'واریز' ? 'is-credit' : 'is-debit'">{{ row.direction === 'واریز' ? '+' : '−' }}{{ formatMoney(row.amount, currency) }}</strong>
          </article>
        </div>
        <p v-else class="wallet-empty">تراکنشی برای نمایش وجود ندارد.</p>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ArrowDownLeft, ArrowDownToLine, ArrowUpRight, Banknote, Gift, History, Landmark, Wallet } from 'lucide-vue-next'
import CustomerPageHeader from '@/components/customer/CustomerPageHeader.vue'
import { getMenuBoot, getMyWallet, requestMyWalletWithdrawal } from '@/utils/api'
import { formatMoney } from '@/utils/format'

const AUTH_KEY = 'restaurant-customer-auth-v1'
let auth = {}
try { auth = JSON.parse(localStorage.getItem(AUTH_KEY) || '{}') } catch {}
const wallet = ref({ withdrawable_balance: 0, cashback_balance: 0 })
const rules = ref({})
const transactions = ref([])
const withdrawalRequests = ref([])
const loading = ref(false), saving = ref(false), error = ref(''), message = ref(''), currency = ref('IRR')
const form = reactive({ amount: '', bank_iban: '', account_holder: auth.customer_name || '' , note: '' })
const currencyLabel = computed(() => ['TOMAN', 'IRT'].includes(currency.value) ? 'تومان' : 'ریال')

function formatDate(value = '') {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString('fa-IR', { year: 'numeric', month: 'short', day: 'numeric' })
}
function statusClass(value) { return value === 'پرداخت شد' ? 'is-paid' : value === 'رد شد' ? 'is-rejected' : 'is-pending' }

async function loadWallet() {
  loading.value = true; error.value = ''
  try {
    const data = await getMyWallet()
    wallet.value = data?.wallet || wallet.value
    rules.value = data?.rules || {}
    transactions.value = data?.transactions || []
    withdrawalRequests.value = data?.withdrawal_requests || []
  } catch (err) { error.value = err?.message || 'کیف پول دریافت نشد.' }
  finally { loading.value = false }
}

async function submitWithdrawal() {
  if (saving.value) return
  saving.value = true; error.value = ''; message.value = ''
  try {
    await requestMyWalletWithdrawal({ amount: form.amount, bank_iban: form.bank_iban, account_holder: form.account_holder, note: form.note })
    message.value = 'درخواست برداشت ثبت شد و برای بررسی به پشتیبانی ارسال شد.'
    form.amount = ''; form.note = ''
    await loadWallet()
  } catch (err) { error.value = err?.message || 'ثبت درخواست برداشت انجام نشد.' }
  finally { saving.value = false }
}

onMounted(async () => {
  if (!auth.mobile || !auth.customer_token) { window.location.replace('/customer/login?redirect=%2Fcustomer%2Fwallet'); return }
  getMenuBoot('').then((boot) => { currency.value = boot?.currency || currency.value }).catch(() => {})
  await loadWallet()
})
</script>

<style scoped>
.wallet-body { display: grid; gap: 1rem; }
.wallet-balances { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
.wallet-balance-card { display: grid; justify-items: start; gap: .5rem; padding: 1.25rem; }
.wallet-balance-card small { color: var(--ds-color-text-secondary); font-size: .86rem; }
.wallet-balance-card strong { font-size: clamp(1.25rem, 4vw, 1.8rem); direction: rtl; }
.wallet-balance-card p, .wallet-rules p, .wallet-section-head p, .wallet-footnote { margin: 0; color: var(--ds-color-text-muted); font-size: .84rem; line-height: 1.8; }
.wallet-icon { display: grid; width: 42px; height: 42px; place-items: center; border-radius: 14px; background: var(--ds-color-action-primary-soft); color: var(--ds-color-action-primary); }
.wallet-balance-card--cashback .wallet-icon { background: var(--ds-color-action-accent-soft); color: var(--ds-color-action-accent-foreground); }
.wallet-rules, .withdraw-card, .wallet-history { padding: 1.2rem; }
.wallet-rules > div, .wallet-section-head { display: flex; align-items: center; justify-content: space-between; gap: .8rem; margin-bottom: .7rem; }
.wallet-rules > div { justify-content: flex-start; color: var(--ds-color-action-accent-foreground); }
.wallet-rules h2, .wallet-section-head h2 { margin: 0; font-size: 1.02rem; color: var(--ds-color-text-primary); }
.wallet-rules-note { margin-top: .4rem !important; }
.wallet-section-head > div { display: grid; gap: .2rem; }
.withdraw-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .8rem; margin-top: 1rem; }
.withdraw-submit { min-height: 48px; align-self: end; border: 0; border-radius: var(--ds-radius-md); background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground); font: inherit; font-weight: 800; cursor: pointer; }
.withdraw-submit:disabled { opacity: .55; cursor: not-allowed; }
.wallet-footnote { margin-top: .8rem; }
.wallet-request-list, .wallet-transaction-list { display: grid; }
.wallet-request-row, .wallet-transaction-row { display: flex; align-items: center; gap: .75rem; justify-content: space-between; padding: .85rem 0; border-top: 1px solid var(--ds-color-border); }
.wallet-request-row > div { display: grid; min-width: 0; gap: .25rem; }
.wallet-request-row small, .transaction-description small { color: var(--ds-color-text-muted); font-size: .78rem; overflow-wrap: anywhere; }
.request-status { flex: 0 0 auto; border-radius: 999px; padding: .32rem .65rem; font-size: .75rem; font-weight: 700; background: var(--ds-color-surface); }
.request-status.is-pending { color: var(--ds-color-status-warning); }
.request-status.is-paid { color: var(--ds-color-status-success); }
.request-status.is-rejected { color: var(--ds-color-status-danger); }
.transaction-mark { display: grid; flex: 0 0 38px; width: 38px; height: 38px; place-items: center; border-radius: 13px; background: var(--ds-color-surface); }
.transaction-mark.is-credit, .transaction-amount.is-credit { color: var(--ds-color-status-success); }
.transaction-mark.is-debit, .transaction-amount.is-debit { color: var(--ds-color-text-secondary); }
.transaction-description { display: grid; flex: 1; min-width: 0; gap: .2rem; }
.transaction-amount { white-space: nowrap; font-size: .84rem; }
.wallet-empty, .wallet-status { color: var(--ds-color-text-muted); line-height: 1.8; }
.wallet-error { color: var(--ds-color-status-danger); line-height: 1.8; }
.wallet-error button { color: inherit; font: inherit; border: 0; background: transparent; text-decoration: underline; }
.wallet-success { color: var(--ds-color-status-success); }
@media (max-width: 640px) { .wallet-balances, .withdraw-form { grid-template-columns: 1fr; } .wallet-balance-card, .wallet-rules, .withdraw-card, .wallet-history { padding: 1rem; } .withdraw-submit { min-height: 50px; } }
</style>
