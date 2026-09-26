<template>
  <div class="customer-page dashboard-page" dir="rtl">
    <CustomerPageHeader
      eyebrow="حساب من"
      :title="customerName"
      subtitle="سفارش‌ها و اطلاعات شما، همیشه در دسترس."
      hero-class="dashboard-hero"
      compact
      :show-back="false"
      fallback-href="/menu"
    >
      <template #eyebrow-icon><Sparkles :size="14" aria-hidden="true" /></template>
      <template #action>
        <a v-if="customerMobile" href="/customer/profile" class="hero-profile-link" aria-label="ویرایش اطلاعات شخصی">
          <span>{{ avatarLetter }}</span>
        </a>
        <span v-else class="customer-page-header__spacer" aria-hidden="true"></span>
      </template>

    </CustomerPageHeader>

    <div class="customer-page__body">
      <section class="customer-section customer-glass-card account-summary">
        <div class="account-summary__main">
          <span class="customer-icon-badge"><UserRound :size="22" /></span>
          <div>
            <h2>{{ customerMobile ? 'اطلاعات حساب مشتری' : 'حساب کاربری مهمان' }}</h2>
            <p>{{ customerMobile || 'برای ذخیره و پیگیری سفارش‌ها وارد حساب شوید.' }}</p>
          </div>
        </div>
        <div class="account-summary__actions">
          <a v-if="customerMobile" href="/customer/profile" class="customer-page__ghost-action">
            <Pencil :size="16" />
            ویرایش اطلاعات
          </a>
          <button v-if="customerMobile" class="customer-page__ghost-action logout-mini" type="button" @click="logout">
            <LogOut :size="16" />
            خروج
          </button>
          <a v-else href="/customer/login?redirect=/customer/dashboard" class="customer-page__ghost-action">
            ورود / ثبت‌نام
          </a>
        </div>
      </section>

      <nav class="account-shortcuts customer-glass-card" aria-label="مدیریت حساب">
        <a href="/order/type"><ShoppingBag :size="22" /><span><strong>شروع سفارش</strong><small>انتخاب روش دریافت و غذا</small></span><ChevronLeft :size="18" /></a>
        <a href="/customer/orders"><ReceiptText :size="22" /><span><strong>سفارش‌های من</strong><small>پیگیری و سفارش دوباره</small></span><ChevronLeft :size="18" /></a>
        <a href="/customer/nutrition"><CalendarDays :size="22" /><span><strong>برنامهٔ غذایی من</strong><small>هدف روزانه، حساسیت‌ها و انتخاب وعده‌ها</small></span><ChevronLeft :size="18" /></a>
        <a href="/customer/addresses"><MapPin :size="22" /><span><strong>آدرس‌های من</strong><small>خانه، محل کار و نشانی‌های ذخیره‌شده</small></span><ChevronLeft :size="18" /></a>
        <a href="/customer/vehicles"><CarFront :size="22" /><span><strong>خودروهای من</strong><small>تحویل راحت درب ماشین</small></span><ChevronLeft :size="18" /></a>
        <a href="/table-reservation"><CalendarDays :size="22" /><span><strong>رزرو میز</strong><small>انتخاب روز، ساعت و میز</small></span><ChevronLeft :size="18" /></a>
        <a href="/customer/branches"><Store :size="22" /><span><strong>شعبه‌ها</strong><small>نشانی و ساعت کار</small></span><ChevronLeft :size="18" /></a>
      </nav>
      <p v-if="profileLoading" class="customer-section__hint" role="status">در حال دریافت اطلاعات حساب…</p>
      <p v-if="profileError" class="customer-danger-text" role="alert">{{ profileError }}</p>

      <section v-if="club && club.points_enabled !== false" class="customer-section customer-glass-card club-summary">
        <div class="club-summary__head">
          <span class="customer-icon-badge club-badge"><Star :size="22" /></span>
          <div>
            <h2>باشگاه مشتریان</h2>
            <p v-if="club.loyalty_tier" class="club-tier">سطح شما: {{ club.loyalty_tier }}</p>
          </div>
        </div>
        <div class="club-summary__stats">
          <article class="club-stat">
            <small>موجودی قابل برداشت</small>
            <strong>{{ (club.withdrawable_balance ?? club.wallet_balance ?? 0).toLocaleString('fa-IR') }} <small>{{ currencyLabel }}</small></strong>
          </article>
          <article class="club-stat">
            <small>اعتبار خرید (کش‌بک)</small>
            <strong>{{ (club.cashback_balance || 0).toLocaleString('fa-IR') }} <small>{{ currencyLabel }}</small></strong>
          </article>
          <article class="club-stat">
            <small>امتیاز وفاداری</small>
            <strong>{{ (club.points_balance || 0).toLocaleString('fa-IR') }}</strong>
          </article>
        </div>
        <p v-if="club.points_enabled && club.points_rial_value" class="club-hint">
          هر {{ club.points_min_redeem ? club.points_min_redeem.toLocaleString('fa-IR') : '—' }}+ امتیاز قابل تبدیل به اعتبار است؛ هر امتیاز {{ club.points_rial_value.toLocaleString('fa-IR') }} {{ currencyLabel }}.
          <template v-if="club.points_expiry_days">امتیازها تا {{ club.points_expiry_days.toLocaleString('fa-IR') }} روز معتبرند.</template>
        </p>
        <p v-if="clubMessage" class="club-msg ok">{{ clubMessage }}</p>
        <p v-if="clubError" class="club-msg err">{{ clubError }}</p>
        <div class="club-summary__actions" v-if="club.points_enabled">
          <button
            v-if="canRedeemPoints"
            type="button"
            class="customer-page__ghost-action club-redeem-btn"
            :disabled="redeemBusy"
            @click="redeemAllPoints"
          >
            <Wallet :size="16" />
            {{ redeemBusy ? 'در حال تبدیل...' : 'تبدیل امتیاز به اعتبار' }}
          </button>
        </div>
        <a class="customer-page__ghost-action club-wallet-link" href="/customer/wallet"><Wallet :size="16" /> جزئیات کیف پول و درخواست برداشت</a>
      </section>

      <section class="customer-section customer-glass-card customer-list-card recent-orders-section">
        <div class="customer-section__head">
          <div>
            <h2>سفارش‌های اخیر</h2>
            <p>پیگیری سریع سفارش‌ها و خریدهای قبلی.</p>
          </div>
          <a href="/customer/orders" class="customer-page__ghost-action section-action">همه سفارش‌ها</a>
        </div>

        <div v-if="recentOrders.length" class="recent-orders-list">
          <a v-for="order in recentOrders" :key="order.order_code || order.name" class="recent-order-row" :href="orderDetailUrl(order)">
            <span class="customer-icon-badge"><ReceiptText :size="18" /></span>
            <div>
              <strong>{{ order.order_code || order.name }}</strong>
              <small>{{ formatOrderMeta(order) }}</small>
            </div>
            <ChevronLeft :size="17" />
          </a>
        </div>
        <div v-else-if="!profileLoading && !profileError" class="inline-empty">
          <ReceiptText :size="24" />
          <p>هنوز سفارشی ثبت نشده است.</p>
          <a href="/order/type" class="primary-btn">شروع سفارش</a>
        </div>
      </section>

    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  CarFront,
  CalendarDays,
  ChevronLeft,
  LogOut,
  MapPin,
  Pencil,
  ReceiptText,
  ShoppingBag,
  Sparkles,
  Star,
  Store,
  UserRound,
  Wallet,
} from 'lucide-vue-next'
import { customerLogout, getCustomerProfile, getMenuItems, getMyWallet, redeemMyPoints } from '@/utils/api'
import { formatMoney, formatStatus, normalizeMobile } from '@/utils/format'
import { hasCustomerSession } from '@/utils/customerAuth'
import CustomerPageHeader from '@/components/customer/CustomerPageHeader.vue'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
const customer = ref({ name: '', mobile: '' })
const club = ref(null)
const redeemBusy = ref(false)
const clubMessage = ref('')
const clubError = ref('')
const currencyLabel = computed(() => (currency.value === 'TOMAN' || currency.value === 'IRT' ? 'تومان' : 'ریال'))
const canRedeemPoints = computed(() => {
  if (!club.value || !club.value.points_enabled) return false
  const balance = Number(club.value.points_balance) || 0
  const minRedeem = Number(club.value.points_min_redeem) || 0
  return balance > 0 && balance >= minRedeem
})

async function redeemAllPoints() {
  if (!customer.value.mobile || redeemBusy.value) return
  redeemBusy.value = true
  clubMessage.value = ''
  clubError.value = ''
  try {
    const points = Number(club.value?.points_balance) || 0
    const payload = await redeemMyPoints({ mobile: customer.value.mobile, points })
    const credited = Number(payload?.amount_credited) || 0
    clubMessage.value = `${(payload?.points_used || points).toLocaleString('fa-IR')} امتیاز به ${credited.toLocaleString('fa-IR')} ${currencyLabel.value} اعتبار تبدیل شد.`
    if (club.value) {
      club.value = {
        ...club.value,
        points_balance: Number(payload?.points_balance) || 0,
        wallet_balance: Number(payload?.wallet_balance) || club.value.wallet_balance,
        cashback_balance: Number(payload?.cashback_balance) || club.value.cashback_balance,
      }
      try {
        const walletData = await getMyWallet()
        club.value = { ...club.value, ...walletData.wallet }
      } catch (_) {}
    }
  } catch (err) {
    clubError.value = err?.message || 'تبدیل امتیاز انجام نشد.'
  } finally {
    redeemBusy.value = false
  }
}

const profileLoading = ref(false)
const profileError = ref('')
const orders = ref([])
const currency = ref('TOMAN')

const customerName = computed(() => customer.value.name || 'مهمان عزیز')
const customerMobile = computed(() => normalizeMobile(customer.value.mobile || ''))
const recentOrders = computed(() => orders.value.slice(0, 3))
const avatarLetter = computed(() => {
  const name = customerName.value
  return name !== 'مهمان عزیز' ? name.slice(0, 1) : 'ک'
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

function formatDate(value = '') {
  if (!value) return '-'
  try {
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return date.toLocaleDateString('fa-IR', { month: 'short', day: 'numeric' })
  } catch {
    return value
  }
}

function formatOrderMeta(order = {}) {
  const date = formatDate(order.created_at || order.transaction_date || order.creation)
  const total = formatMoney(order.grand_total || order.total || 0, currency.value)
  return `${formatStatus(order.status)} · ${date} · ${total}`
}

function orderDetailUrl(order = {}) {
  const code = encodeURIComponent(order.order_code || order.name || '')
  return `/customer/orders/${code}?mobile=${encodeURIComponent(customerMobile.value)}`
}

async function logout() {
  if (!confirm('آیا مطمئن هستید که می‌خواهید خارج شوید؟')) return
  try { await customerLogout() } catch {}
  localStorage.removeItem(CUSTOMER_AUTH_KEY)
  localStorage.removeItem('customer_name')
  localStorage.removeItem('customer_phone')
  localStorage.removeItem('customer_email')
  window.location.href = '/customer/login'
}

onMounted(async () => {
  const auth = readAuth()
  if (!hasCustomerSession()) {
    window.location.replace('/customer/login?redirect=%2Fcustomer%2Fdashboard')
    return
  }
  customer.value = { name: auth.name, mobile: auth.mobile }
  if (auth.mobile) {
    profileLoading.value = true
    try {
      const profile = await getCustomerProfile({ mobile: auth.mobile })
      customer.value = profile?.customer || customer.value
      club.value = profile?.club || null
      orders.value = profile?.orders || []
      if (profile?.currency) currency.value = profile.currency
      if (customer.value.name) localStorage.setItem('customer_name', customer.value.name)
    } catch (err) { profileError.value = err.message || 'اطلاعات حساب دریافت نشد؛ صفحه را دوباره باز کنید.' }
    finally { profileLoading.value = false }
  }

})
</script>

<style scoped>
.account-shortcuts { margin-bottom: 1.25rem; padding: .2rem 1rem; }
.account-shortcuts a { display: flex; align-items: center; gap: .9rem; padding: 1rem 0; color: var(--ds-color-action-primary); text-decoration: none; min-height: 76px; }
.account-shortcuts a + a { border-top: 1px solid var(--ds-color-border); }
.account-shortcuts span { display: grid; gap: .25rem; flex: 1; }
.account-shortcuts strong { color: var(--ds-color-text-primary); font-size: .95rem; }
.account-shortcuts small { color: var(--ds-color-text-muted); font-size: .8rem; }

.dashboard-page {
  padding-bottom: 8rem;
}

.dashboard-hero {
  margin-bottom: 0.2rem;
}

.hero-profile-link {
  width: 52px;
  height: 52px;
  border-radius: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--ds-color-action-primary);
  text-decoration: none;
  font-size: 1.1rem;
  font-weight: 800;
  background: var(--ds-color-action-primary-soft);
  border: 1px solid rgb(255 255 255 / 0.18);
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.14);
}

.hero-search {
  width: 100%;
  min-height: 52px;
  border: 1px solid rgb(255 255 255 / 0.15);
  border-radius: 18px;
  background: rgb(255 255 255 / 0.12);
  color: color-mix(in srgb, var(--ds-color-action-primary-foreground, #fff) 84%, transparent);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.95rem 1rem;
  font: inherit;
  cursor: pointer;
  backdrop-filter: blur(10px);
}

.hero-search span {
  font-size: 0.9rem;
}

.account-summary {
  padding: 1rem;
  display: grid;
  gap: 0.9rem;
}

.club-summary {
  padding: 1rem;
  display: grid;
  gap: 0.85rem;
}

.club-summary__head {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.club-summary__head h2 {
  margin: 0;
  font-size: 1.02rem;
}

.club-tier {
  margin: 0.24rem 0 0;
  font-size: 0.78rem;
  color: var(--ds-color-action-accent, #b8722d);
  font-weight: 700;
}

.club-badge {
  background: var(--ds-color-action-accent-soft, rgb(255 89 0 / 0.13));
  color: var(--ds-color-text-primary);
}

.club-summary__stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(125px, 1fr));
  gap: 0.65rem;
}

.club-wallet-link {
  display: inline-flex;
  width: fit-content;
  align-items: center;
  gap: 0.45rem;
  margin-top: 0.85rem;
  text-decoration: none;
}

.club-stat {
  display: grid;
  gap: 0.2rem;
  padding: 0.65rem 0.8rem;
  border-radius: 14px;
  background: var(--surface-soft, rgba(255, 255, 255, 0.5));
  border: 1px solid var(--border-soft, rgba(0, 0, 0, 0.06));
}

.club-stat small {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.club-stat strong {
  font-size: 1rem;
}

.club-hint {
  margin: 0;
  font-size: 0.76rem;
  color: var(--text-muted);
  line-height: 1.7;
}

.club-msg {
  margin: 0;
  font-size: 0.8rem;
}

.club-msg.ok {
  color: var(--ds-color-status-success, #2f7b47);
}

.club-msg.err {
  color: var(--ds-color-status-danger, #b3402e);
}

.club-summary__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.club-redeem-btn {
  font-weight: 700;
}

.account-summary__main,
.account-summary__actions {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.account-summary__main h2 {
  margin: 0;
  font-size: 1.02rem;
}

.account-summary__main p {
  margin: 0.24rem 0 0;
  color: var(--text-muted);
  font-size: 0.82rem;
}

.account-summary__actions {
  flex-wrap: wrap;
}

.logout-mini {
  color: var(--danger);
  border-color: rgb(var(--danger-rgb) / 0.16);
  background: rgb(var(--danger-rgb) / 0.06);
}

.recent-orders-list {
  display: grid;
  gap: 0.55rem;
}

.recent-order-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.72rem;
  border-radius: 18px;
  color: inherit;
  text-decoration: none;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.04);
}

.recent-order-row div {
  flex: 1;
  min-width: 0;
}

.recent-order-row strong {
  display: block;
  direction: ltr;
  text-align: right;
  font-size: 0.9rem;
}

.recent-order-row small {
  display: block;
  margin-top: 0.16rem;
  color: var(--text-muted);
  font-size: 0.76rem;
  line-height: 1.6;
}

.inline-empty {
  display: grid;
  justify-items: center;
  gap: 0.65rem;
  padding: 1.2rem 0.75rem;
  text-align: center;
  color: var(--text-muted);
}

.inline-empty p {
  margin: 0;
}

.account-action-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.account-action-card {
  min-height: 112px;
  padding: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: inherit;
  text-decoration: none;
}

.section-action,
.offers-link {
  text-decoration: none;
}

.offers-scroll {
  display: flex;
  gap: 0.85rem;
  overflow-x: auto;
  padding-bottom: 0.2rem;
  scrollbar-width: none;
}

.offers-scroll::-webkit-scrollbar {
  display: none;
}

.offer-card {
  min-width: 185px;
  text-decoration: none;
  color: inherit;
}

.offer-card__image-wrap {
  position: relative;
  height: 118px;
  overflow: hidden;
  border-radius: 22px 22px 0 0;
}

.offer-card__image-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.offer-card__body {
  padding: 0.9rem;
}

.offer-card__body strong {
  display: block;
  font-size: 0.9rem;
}

.offer-card__body p {
  margin: 0.3rem 0 0;
  font-size: 0.76rem;
  color: var(--text-muted);
}

@media (max-width: 480px) {
  .account-action-grid {
    grid-template-columns: 1fr;
  }
}
</style>
