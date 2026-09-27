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

      <section class="wallet-charge-card customer-glass-card" aria-labelledby="wallet-charge-title">
        <div class="wallet-section-head">
          <div>
            <h2 id="wallet-charge-title">شارژ کیف پول</h2>
            <p>شارژ آنلاین هنوز فعال نیست؛ درخواست دستی ثبت کنید تا پس از بررسی پرداخت به موجودی قابل برداشت اضافه شود.</p>
          </div>
          <ArrowUpRight :size="21" aria-hidden="true" />
        </div>

        <template v-if="charge.enabled">
          <div v-if="charge.iban || charge.card_number || charge.bank_name || charge.account_holder" class="charge-payment-details">
            <article v-if="charge.bank_name"><small>بانک</small><strong>{{ charge.bank_name }}</strong></article>
            <article v-if="charge.account_holder"><small>صاحب حساب</small><strong>{{ charge.account_holder }}</strong></article>
            <article v-if="charge.iban" class="charge-copy-row"><span><small>شماره شبا</small><strong dir="ltr">{{ charge.iban }}</strong></span><button type="button" class="wallet-copy-button" @click="copyChargeDetail('شبا', charge.iban)">کپی</button></article>
            <article v-if="charge.card_number" class="charge-copy-row"><span><small>شماره کارت</small><strong dir="ltr">{{ charge.card_number }}</strong></span><button type="button" class="wallet-copy-button" @click="copyChargeDetail('شماره کارت', charge.card_number)">کپی</button></article>
          </div>
          <p class="charge-instructions">{{ charge.instructions || (charge.iban || charge.card_number ? 'مبلغ را به حساب بالا واریز کنید و شماره پیگیری را در فرم وارد کنید.' : 'اطلاعات واریز هنوز ثبت نشده است. درخواست را ثبت کنید تا پشتیبانی روش پرداخت را به شما اعلام کند.') }}</p>
          <p v-if="copyMessage" class="wallet-success" role="status">{{ copyMessage }}</p>
          <form class="charge-form" @submit.prevent="submitChargeRequest">
            <label class="customer-field">مبلغ شارژ ({{ currencyLabel }})
              <input v-model.number="chargeForm.amount" class="customer-input" type="number" min="1" step="1" required inputmode="numeric" />
            </label>
            <label class="customer-field">شماره پیگیری پرداخت (اختیاری)
              <input v-model.trim="chargeForm.payment_reference" class="customer-input" maxlength="120" autocomplete="off" placeholder="اگر واریز کرده‌اید، وارد کنید" />
            </label>
            <label class="customer-field charge-form__note">توضیح (اختیاری)
              <input v-model.trim="chargeForm.note" class="customer-input" maxlength="240" placeholder="" />
            </label>
            <button class="withdraw-submit" type="submit" :disabled="chargeSaving || Number(chargeForm.amount) <= 0">
              {{ chargeSaving ? 'در حال ثبت…' : 'ثبت درخواست شارژ' }}
            </button>
          </form>
          <p class="wallet-footnote">ثبت درخواست به‌تنهایی موجودی را زیاد نمی‌کند؛ بعد از بررسی و تأیید پرداخت توسط پشتیبانی، مبلغ در کیف پول ثبت می‌شود.</p>
        </template>
        <p v-else class="wallet-empty">درخواست شارژ در حال حاضر غیرفعال است؛ برای راهنمایی با پشتیبانی تماس بگیرید.</p>
      </section>

      <section class="wallet-history customer-glass-card">
        <div class="wallet-section-head"><div><h2>درخواست‌های شارژ</h2><p>وضعیت درخواست و پرداخت‌های قبلی</p></div><History :size="20" /></div>
        <div v-if="chargeRequests.length" class="wallet-request-list">
          <article v-for="row in chargeRequests" :key="row.name" class="wallet-charge-request-row">
            <div class="charge-request-summary">
              <strong>{{ formatMoney(row.amount, currency) }}</strong>
              <small>{{ row.name }} · {{ formatDate(row.creation) }}</small>
              <small v-if="row.payment_reference">شماره پیگیری: {{ row.payment_reference }}</small>
              <small v-if="row.review_note">پاسخ پشتیبانی: {{ row.review_note }}</small>
            </div>
            <span class="request-status" :class="statusClass(row.status)">{{ row.status }}</span>
            <form v-if="row.status === 'در انتظار پرداخت'" class="charge-reference-form" @submit.prevent="submitChargeReference(row)">
              <label class="customer-field">شماره پیگیری واریز
                <input v-model.trim="chargeReferences[row.name]" class="customer-input" maxlength="120" required autocomplete="off" />
              </label>
              <button class="wallet-copy-button" type="submit" :disabled="chargeReferenceSaving === row.name || !chargeReferences[row.name]?.trim()">
                {{ chargeReferenceSaving === row.name ? 'در حال ثبت…' : 'ارسال برای بررسی' }}
              </button>
            </form>
          </article>
        </div>
        <p v-else class="wallet-empty">هنوز درخواست شارژی ثبت نکرده‌اید.</p>
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
import { getMenuBoot, getMyWallet, requestMyWalletCharge, requestMyWalletWithdrawal, submitMyWalletChargeReference } from '@/utils/api'
import { formatMoney } from '@/utils/format'

const AUTH_KEY = 'restaurant-customer-auth-v1'
let auth = {}
try { auth = JSON.parse(localStorage.getItem(AUTH_KEY) || '{}') } catch {}
const wallet = ref({ withdrawable_balance: 0, cashback_balance: 0 })
const rules = ref({})
const charge = ref({ enabled: true })
const transactions = ref([])
const withdrawalRequests = ref([])
const chargeRequests = ref([])
const loading = ref(false), saving = ref(false), error = ref(''), message = ref(''), currency = ref('IRR')
const form = reactive({ amount: '', bank_iban: '', account_holder: auth.customer_name || '' , note: '' })
const chargeForm = reactive({ amount: '', payment_reference: '', note: '' })
const chargeReferences = reactive({})
const chargeSaving = ref(false), chargeReferenceSaving = ref(''), copyMessage = ref('')
const currencyLabel = computed(() => ['TOMAN', 'IRT'].includes(currency.value) ? 'تومان' : 'ریال')

function formatDate(value = '') {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString('fa-IR', { year: 'numeric', month: 'short', day: 'numeric' })
}
function statusClass(value) { return ['پرداخت شد', 'تأیید شد'].includes(value) ? 'is-paid' : value === 'رد شد' ? 'is-rejected' : 'is-pending' }

async function loadWallet() {
  loading.value = true; error.value = ''
  try {
    const data = await getMyWallet()
    wallet.value = data?.wallet || wallet.value
    rules.value = data?.rules || {}
    charge.value = data?.charge || charge.value
    transactions.value = data?.transactions || []
    withdrawalRequests.value = data?.withdrawal_requests || []
    chargeRequests.value = data?.charge_requests || []
  } catch (err) { error.value = err?.message || 'کیف پول دریافت نشد.' }
  finally { loading.value = false }
}

async function copyChargeDetail(label, value) {
  try {
    await navigator.clipboard.writeText(String(value || ''))
    copyMessage.value = `${label} کپی شد.`
    window.setTimeout(() => { copyMessage.value = '' }, 2200)
  } catch {
    copyMessage.value = 'کپی خودکار در دسترس نیست؛ اطلاعات را دستی انتخاب کنید.'
  }
}

async function submitChargeRequest() {
  if (chargeSaving.value || Number(chargeForm.amount) <= 0) return
  chargeSaving.value = true; error.value = ''; message.value = ''
  try {
    const hasReference = Boolean(chargeForm.payment_reference.trim())
    await requestMyWalletCharge({
      amount: chargeForm.amount,
      payment_reference: chargeForm.payment_reference,
      note: chargeForm.note,
    })
    message.value = hasReference
      ? 'درخواست شارژ و شماره پیگیری برای بررسی ارسال شد؛ موجودی پس از تأیید به‌روزرسانی می‌شود.'
      : 'درخواست شارژ ثبت شد. پس از واریز، شماره پیگیری را در درخواست ثبت کنید.'
    chargeForm.amount = ''; chargeForm.payment_reference = ''; chargeForm.note = ''
    await loadWallet()
  } catch (err) { error.value = err?.message || 'ثبت درخواست شارژ انجام نشد.' }
  finally { chargeSaving.value = false }
}

async function submitChargeReference(row) {
  const reference = String(chargeReferences[row.name] || '').trim()
  if (!reference || chargeReferenceSaving.value) return
  chargeReferenceSaving.value = row.name; error.value = ''; message.value = ''
  try {
    await submitMyWalletChargeReference({ request_name: row.name, payment_reference: reference })
    message.value = 'شماره پیگیری برای بررسی پشتیبانی ارسال شد.'
    delete chargeReferences[row.name]
    await loadWallet()
  } catch (err) { error.value = err?.message || 'ارسال شماره پیگیری انجام نشد.' }
  finally { chargeReferenceSaving.value = '' }
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
.wallet-rules, .withdraw-card, .wallet-history, .wallet-charge-card { padding: 1.2rem; }
.wallet-rules > div, .wallet-section-head { display: flex; align-items: center; justify-content: space-between; gap: .8rem; margin-bottom: .7rem; }
.wallet-rules > div { justify-content: flex-start; color: var(--ds-color-action-accent-foreground); }
.wallet-rules h2, .wallet-section-head h2 { margin: 0; font-size: 1.02rem; color: var(--ds-color-text-primary); }
.wallet-rules-note { margin-top: .4rem !important; }
.wallet-section-head > div { display: grid; gap: .2rem; }
.wallet-charge-card > .wallet-section-head > svg { flex: 0 0 auto; color: var(--ds-color-action-accent); }
.charge-payment-details { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr)); gap: .65rem; margin-block: 1rem .7rem; }
.charge-payment-details article { display: flex; min-width: 0; align-items: center; justify-content: space-between; gap: .6rem; padding: .75rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface); }
.charge-payment-details article > span { display: grid; min-width: 0; gap: .25rem; }
.charge-payment-details small { color: var(--ds-color-text-muted); font-size: .76rem; }
.charge-payment-details strong { overflow-wrap: anywhere; color: var(--ds-color-text-primary); font-size: .9rem; }
.charge-instructions { margin: .4rem 0 1rem; color: var(--ds-color-text-secondary); font-size: .86rem; line-height: 1.8; }
.charge-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .8rem; align-items: end; margin-top: 1rem; }
.charge-form__note { grid-column: 1 / -1; }
.withdraw-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .8rem; margin-top: 1rem; }
.withdraw-submit { min-height: 48px; align-self: end; border: 0; border-radius: var(--ds-radius-md); background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground); font: inherit; font-weight: 800; cursor: pointer; }
.withdraw-submit:disabled { opacity: .55; cursor: not-allowed; }
.wallet-footnote { margin-top: .8rem; }
.wallet-request-list, .wallet-transaction-list { display: grid; }
.wallet-request-row, .wallet-transaction-row { display: flex; align-items: center; gap: .75rem; justify-content: space-between; padding: .85rem 0; border-top: 1px solid var(--ds-color-border); }
.wallet-charge-request-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: .65rem 1rem; padding: .9rem 0; border-top: 1px solid var(--ds-color-border); }
.charge-request-summary { display: grid; min-width: 0; gap: .25rem; }
.charge-request-summary small { color: var(--ds-color-text-muted); font-size: .78rem; overflow-wrap: anywhere; }
.charge-reference-form { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: end; gap: .65rem; grid-column: 1 / -1; }
.wallet-copy-button { min-height: 44px; padding: .5rem .9rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface-raised); color: var(--ds-color-action-primary); font: inherit; font-weight: 700; cursor: pointer; }
.wallet-copy-button:disabled { opacity: .55; cursor: not-allowed; }
.wallet-copy-button:focus-visible, .withdraw-submit:focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 2px; }
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
@media (max-width: 640px) { .wallet-balances, .withdraw-form, .charge-form { grid-template-columns: 1fr; } .charge-form__note { grid-column: auto; } .wallet-charge-request-row, .charge-reference-form { grid-template-columns: 1fr; } .charge-reference-form { grid-column: auto; } .wallet-balance-card, .wallet-rules, .withdraw-card, .wallet-history, .wallet-charge-card { padding: 1rem; } .withdraw-submit { min-height: 50px; } }
</style>
