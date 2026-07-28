<template>
  <div class="customer-page dashboard-page" dir="rtl">
    <section class="customer-page__hero dashboard-hero">
      <div class="customer-page__topbar customer-page__topbar--compact">
        <div>
          <p class="customer-page__eyebrow">
            <Sparkles :size="14" />
            حساب من
          </p>
          <h1 class="customer-page__title">{{ customerName }}</h1>
          <p class="customer-page__subtitle">مرکز مدیریت سفارش‌ها، آدرس‌ها و اطلاعات حساب شما.</p>
        </div>
        <a href="/customer/profile" class="hero-profile-link" aria-label="ویرایش اطلاعات شخصی">
          <span>{{ avatarLetter }}</span>
        </a>
      </div>

      <button class="hero-search" type="button" @click="goSearch">
        <Search :size="18" />
        <span>جستجو در منو، غذاها و پیشنهادها...</span>
      </button>

      <div class="hero-stats customer-grid customer-grid--2">
        <article class="hero-stat customer-glass-card">
          <small>سفارش‌های اخیر</small>
          <strong>{{ orders.length.toLocaleString('fa-IR') }}</strong>
        </article>
        <article class="hero-stat customer-glass-card">
          <small>آیتم‌های سبد</small>
          <strong>{{ cartCount.toLocaleString('fa-IR') }}</strong>
        </article>
      </div>
    </section>

    <div class="customer-page__body">
      <section class="customer-section customer-glass-card account-summary">
        <div class="account-summary__main">
          <span class="customer-icon-badge"><UserRound :size="22" /></span>
          <div>
            <h2>{{ customerName }}</h2>
            <p>{{ customerMobile || 'برای ذخیره سفارش‌ها وارد حساب شوید.' }}</p>
          </div>
        </div>
        <div class="account-summary__actions">
          <a href="/customer/profile" class="customer-page__ghost-action">
            <Pencil :size="16" />
            ویرایش اطلاعات
          </a>
          <button v-if="customerMobile" class="customer-page__ghost-action logout-mini" type="button" @click="logout">
            <LogOut :size="16" />
            خروج
          </button>
          <a v-else href="/customer/login?redirect=/customer/dashboard" class="customer-page__ghost-action">
            ورود
          </a>
        </div>
      </section>

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
            <small>اعتبار کیف پول</small>
            <strong>{{ (club.wallet_balance || 0).toLocaleString('fa-IR') }} <small>{{ currencyLabel }}</small></strong>
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
      </section>

      <section class="customer-section">
        <div class="customer-section__head">
          <div>
            <h2>شروع سفارش</h2>
            <p>مسیر اصلی سفارش را از اینجا شروع کنید.</p>
          </div>
        </div>
        <div class="order-choice-grid">
          <a href="/order/type" class="order-choice customer-glass-card order-choice--primary">
            <span class="customer-icon-badge"><Bike :size="22" /></span>
            <div>
              <strong>شروع سفارش جدید</strong>
              <small>حضوری، بیرون‌بر یا ارسال را شفاف انتخاب کنید</small>
            </div>
            <ChevronLeft :size="18" />
          </a>
          <a href="/customer/orders" class="order-choice customer-glass-card">
            <span class="customer-icon-badge"><PackageCheck :size="22" /></span>
            <div>
              <strong>تکرار سفارش قبلی</strong>
              <small>از سفارش‌های اخیر دوباره سفارش دهید</small>
            </div>
            <ChevronLeft :size="18" />
          </a>
          <a :href="lastOrderUrl" class="order-choice customer-glass-card">
            <span class="customer-icon-badge"><UtensilsCrossed :size="22" /></span>
            <div>
              <strong>پیگیری سفارش</strong>
              <small>وضعیت سفارش فعلی یا اخیر را ببینید</small>
            </div>
            <ChevronLeft :size="18" />
          </a>
        </div>
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
        <div v-else class="inline-empty">
          <ReceiptText :size="24" />
          <p>هنوز سفارشی ثبت نشده است.</p>
          <a href="/order/type" class="primary-btn">شروع سفارش</a>
        </div>
      </section>

      <section class="customer-section">
        <div class="customer-section__head">
          <div>
            <h2>مدیریت حساب</h2>
            <p>کارهای پرتکرار حساب شما.</p>
          </div>
        </div>
        <div class="account-action-grid">
          <a href="/customer/addresses" class="account-action-card customer-glass-card">
            <span class="customer-icon-badge"><MapPin :size="21" /></span>
            <div>
              <strong>آدرس‌ها</strong>
              <small>ثبت آدرس و لوکیشن</small>
            </div>
          </a>
          <a href="/customer/orders" class="account-action-card customer-glass-card">
            <span class="customer-icon-badge"><ReceiptText :size="21" /></span>
            <div>
              <strong>سفارش‌ها</strong>
              <small>تاریخچه و پیگیری</small>
            </div>
          </a>
          <a href="/cart" class="account-action-card customer-glass-card">
            <span class="customer-icon-badge"><ShoppingCart :size="21" /></span>
            <div>
              <strong>سبد خرید</strong>
              <small>{{ cartCount > 0 ? `${cartCount} آیتم در سبد` : 'آماده تکمیل سفارش' }}</small>
            </div>
          </a>
          <a href="/customer/branches" class="account-action-card customer-glass-card">
            <span class="customer-icon-badge"><Store :size="21" /></span>
            <div>
              <strong>شعبه‌ها</strong>
              <small>آدرس و ساعات کاری</small>
            </div>
          </a>
        </div>
      </section>

      <section class="customer-section" v-if="specialOffers.length">
        <div class="customer-section__head">
          <div>
            <h2>پیشنهاد برای سفارش بعدی</h2>
            <p>چند انتخاب سریع از منو.</p>
          </div>
          <a href="/menu" class="customer-page__ghost-action offers-link">مشاهده منو</a>
        </div>

        <div class="offers-scroll">
          <a v-for="offer in specialOffers" :key="offer.id" href="/menu" class="offer-card customer-glass-card">
            <div class="offer-card__image-wrap">
              <img :src="offer.image" :alt="offer.title" loading="lazy" />
            </div>
            <div class="offer-card__body">
              <strong>{{ offer.title }}</strong>
              <p>{{ offer.subtitle }}</p>
            </div>
          </a>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  Bike,
  ChevronLeft,
  LogOut,
  MapPin,
  PackageCheck,
  Pencil,
  ReceiptText,
  Search,
  ShoppingCart,
  Sparkles,
  Star,
  Store,
  UserRound,
  UtensilsCrossed,
  Wallet,
} from 'lucide-vue-next'
import { cartState } from '@/stores/cartStore'
import { getCustomerProfile, getMenuItems, redeemMyPoints } from '@/utils/api'
import { formatMoney, formatStatus, normalizeMobile } from '@/utils/format'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
const cartCount = computed(() => cartState.lines.reduce((sum, line) => sum + (Number(line.qty) || 0), 0))
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
      }
    }
  } catch (err) {
    clubError.value = err?.message || 'تبدیل امتیاز انجام نشد.'
  } finally {
    redeemBusy.value = false
  }
}

const orders = ref([])
const specialOffers = ref([])
const currency = ref('TOMAN')

const customerName = computed(() => customer.value.name || 'مهمان عزیز')
const customerMobile = computed(() => normalizeMobile(customer.value.mobile || ''))
const recentOrders = computed(() => orders.value.slice(0, 3))
const lastOrderUrl = computed(() => {
  const code = cartState.lastOrder?.order_code
  const mobile = cartState.lastOrder?.mobile || customerMobile.value
  return code && mobile ? `/order-success/${encodeURIComponent(code)}?mobile=${encodeURIComponent(mobile)}` : '/customer/orders'
})
const avatarLetter = computed(() => {
  const name = customerName.value
  return name !== 'مهمان عزیز' ? name.slice(0, 1) : 'ک'
})

function goSearch() {
  window.location.href = '/search'
}

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

function logout() {
  if (!confirm('آیا مطمئن هستید که می‌خواهید خارج شوید؟')) return
  localStorage.removeItem(CUSTOMER_AUTH_KEY)
  localStorage.removeItem('customer_name')
  localStorage.removeItem('customer_phone')
  localStorage.removeItem('customer_email')
  window.location.href = '/customer/login'
}

onMounted(async () => {
  const auth = readAuth()
  customer.value = { name: auth.name, mobile: auth.mobile }
  if (auth.mobile) {
    try {
      const profile = await getCustomerProfile({ mobile: auth.mobile })
      customer.value = profile?.customer || customer.value
      club.value = profile?.club || null
      orders.value = profile?.orders || []
      if (profile?.currency) currency.value = profile.currency
      if (customer.value.name) localStorage.setItem('customer_name', customer.value.name)
    } catch {}
  }
  try {
    const menu = await getMenuItems({ page_size: 6 })
    specialOffers.value = (menu?.items || []).slice(0, 6).map((item) => ({
      id: item.slug || item.name,
      title: item.title,
      subtitle: item.short_desc || item.category_title || 'پیشنهاد امروز',
      image: item.image || 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&auto=format&fit=crop&q=60',
    }))
  } catch {}
})
</script>

<style scoped>
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
  color: #fff;
  text-decoration: none;
  font-size: 1.1rem;
  font-weight: 800;
  background: rgb(255 255 255 / 0.16);
  border: 1px solid rgb(255 255 255 / 0.18);
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.14);
}

.hero-search {
  width: 100%;
  min-height: 52px;
  border: 1px solid rgb(255 255 255 / 0.15);
  border-radius: 18px;
  background: rgb(255 255 255 / 0.12);
  color: rgb(255 255 255 / 0.84);
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

.hero-stats {
  margin-top: 0.95rem;
}

.hero-stat {
  padding: 0.85rem 0.95rem;
  color: #fff;
  background: rgb(255 255 255 / 0.1);
  border-color: rgb(255 255 255 / 0.12);
  box-shadow: none;
}

.hero-stat small {
  display: block;
  font-size: 0.74rem;
  color: rgb(255 255 255 / 0.68);
}

.hero-stat strong {
  display: block;
  margin-top: 0.3rem;
  font-size: 1.1rem;
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
  color: var(--color-primary, #b8722d);
  font-weight: 700;
}

.club-badge {
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
  color: #7a4a12;
}

.club-summary__stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.65rem;
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
  color: #2f7b47;
}

.club-msg.err {
  color: #b3402e;
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

.order-choice-grid {
  display: grid;
  gap: 0.8rem;
}

.order-choice {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  padding: 1rem;
  color: inherit;
  text-decoration: none;
}

.order-choice--primary {
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  box-shadow: 0 14px 30px rgb(var(--palette-deep-sapphire-rgb) / 0.1);
}

.order-choice div {
  flex: 1;
  min-width: 0;
}

.order-choice strong,
.account-action-card strong {
  display: block;
  font-size: 0.96rem;
  margin-bottom: 0.2rem;
}

.order-choice small,
.account-action-card small {
  display: block;
  color: var(--text-muted);
  line-height: 1.7;
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

@media (min-width: 760px) {
  .order-choice-grid {
    grid-template-columns: 1.2fr 1fr 1fr;
  }
}

@media (max-width: 480px) {
  .account-action-grid {
    grid-template-columns: 1fr;
  }
}
</style>
