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

      <section class="customer-section customer-glass-card wallet-overview" aria-labelledby="wallet-overview-title">
        <div class="wallet-overview__heading">
          <span class="customer-icon-badge wallet-overview__icon"><Wallet :size="20" aria-hidden="true" /></span>
          <div>
            <h2 id="wallet-overview-title">کیف پول من</h2>
            <p>موجودی قابل برداشت و اعتبار خریدتان را جداگانه ببینید.</p>
          </div>
        </div>
        <p v-if="walletSummaryLoading" class="customer-section__hint" role="status">در حال دریافت موجودی کیف پول…</p>
        <div v-else-if="walletSummaryError" class="wallet-overview__error" role="alert">
          <span>{{ walletSummaryError }}</span>
          <button type="button" @click="loadWalletSummary">تلاش دوباره</button>
        </div>
        <div v-else class="wallet-overview__balances">
          <div><small>قابل برداشت</small><strong>{{ Number(walletSummary.withdrawable_balance || 0).toLocaleString('fa-IR') }} <small>{{ currencyLabel }}</small></strong></div>
          <div><small>اعتبار خرید (کش‌بک)</small><strong>{{ Number(walletSummary.cashback_balance || 0).toLocaleString('fa-IR') }} <small>{{ currencyLabel }}</small></strong></div>
        </div>
        <a class="wallet-overview__link" href="/customer/wallet">مشاهده جزئیات و شارژ کیف پول <ChevronLeft :size="17" aria-hidden="true" /></a>
      </section>

      <section v-if="surveyInvitations.length" class="customer-section survey-invitations" aria-labelledby="survey-invitation-title">
        <div class="survey-invitations__heading">
          <span class="customer-icon-badge survey-invitations__icon"><MessageCircle :size="20" aria-hidden="true" /></span>
          <div>
            <h2 id="survey-invitation-title">تجربهٔ سفارشتان را ثبت کنید</h2>
            <p>امتیاز شما به بهترشدن غذاها و خدمات ویدرخت کمک می‌کند.</p>
          </div>
        </div>
        <a v-for="invite in surveyInvitations" :key="invite.name" class="survey-invitation-row" :href="invite.href || surveyHref(invite)">
          <span><strong>سفارش {{ invite.order_code }}</strong><small>فرم کوتاه نظرخواهی غذا و خدمات</small></span>
          <span class="survey-invitation-action">ثبت نظر <ChevronLeft :size="16" /></span>
        </a>
      </section>

      <section v-if="feedbackReplies.length" class="customer-section customer-glass-card survey-replies" aria-labelledby="survey-replies-title">
        <div class="customer-section__head">
          <div>
            <h2 id="survey-replies-title">پاسخ تیم ویدرخت به نظر شما</h2>
            <p>پاسخ‌های مدیر دربارهٔ بازخوردهای ثبت‌شده.</p>
          </div>
        </div>
        <article v-for="review in feedbackReplies" :key="review.name" class="survey-reply-row">
          <img v-if="review.image" :src="review.image" :alt="review.item_title" loading="lazy" />
          <span v-else class="survey-reply-placeholder"><Utensils :size="17" aria-hidden="true" /></span>
          <div>
            <strong>{{ review.item_title }} · {{ Number(review.score_10 || 0).toLocaleString('fa-IR') }} از ۱۰</strong>
            <p>{{ review.manager_reply }}</p>
            <small>نظر شما: {{ review.moderation_status }}</small>
          </div>
        </article>
      </section>

      <section v-if="customerMobile" class="customer-section customer-glass-card customer-voice" aria-labelledby="customer-voice-title">
        <div class="customer-section__head">
          <div>
            <h2 id="customer-voice-title">پیشنهادها و انتقادهای من</h2>
            <p>اگر پیشنهادی، انتقادی یا درخواستی دارید، از همین‌جا برای تیم ویدرخت بفرستید.</p>
          </div>
          <MessageCircle :size="22" class="customer-voice__icon" aria-hidden="true" />
        </div>

        <form class="customer-voice__form" @submit.prevent="submitVoice">
          <label>
            نوع پیام
            <select v-model="voiceForm.type" required>
              <option v-for="type in customerVoiceTypes" :key="type" :value="type">{{ type }}</option>
            </select>
          </label>
          <label>
            موضوع
            <input v-model.trim="voiceForm.subject" type="text" maxlength="140" required placeholder="مثلاً پیشنهاد برای منوی صبحانه" />
          </label>
          <label>
            کد سفارش (اختیاری)
            <input v-model.trim="voiceForm.order_code" type="text" maxlength="140" dir="ltr" placeholder="مثلاً SAL-ORD-2026-00001" />
          </label>
          <label class="customer-voice__message-field">
            متن پیام
            <textarea v-model.trim="voiceForm.message" rows="4" maxlength="2000" required placeholder="پیام خود را برای ما بنویسید…"></textarea>
          </label>
          <p v-if="voiceError" class="customer-voice__feedback customer-voice__feedback--error" role="alert">{{ voiceError }}</p>
          <p v-if="voiceMessage" class="customer-voice__feedback customer-voice__feedback--success" role="status">{{ voiceMessage }}</p>
          <button class="customer-page__primary-action customer-voice__submit" type="submit" :disabled="voiceSaving">
            {{ voiceSaving ? 'در حال ارسال…' : 'ارسال پیام' }}
          </button>
        </form>

        <div class="customer-voice__history">
          <div class="customer-voice__history-head">
            <h3>پیام‌های قبلی</h3>
            <button type="button" class="customer-page__ghost-action" :disabled="voiceLoading" @click="loadCustomerVoices">
              {{ voiceLoading ? 'در حال دریافت…' : 'به‌روزرسانی' }}
            </button>
          </div>
          <p v-if="voiceLoading && !customerVoices.length" class="customer-section__hint" role="status">در حال دریافت پیام‌های شما…</p>
          <p v-else-if="voiceHistoryError" class="customer-voice__feedback customer-voice__feedback--error" role="alert">{{ voiceHistoryError }}</p>
          <p v-else-if="!customerVoices.length" class="customer-voice__empty">هنوز پیامی ثبت نکرده‌اید.</p>
          <article v-for="voice in customerVoices" :key="voice.name" class="customer-voice__item">
            <div class="customer-voice__item-head">
              <div>
                <strong>{{ voice.subject }}</strong>
                <small>{{ voice.type }} · {{ formatDate(voice.creation) }}</small>
              </div>
              <span class="customer-voice__status">{{ voice.status || 'جدید' }}</span>
            </div>
            <p>{{ voice.message }}</p>
            <small v-if="voice.order_code" class="customer-voice__order">سفارش مرتبط: {{ voice.order_code }}</small>
            <div v-if="voice.response" class="customer-voice__response">
              <strong>پاسخ تیم ویدرخت</strong>
              <p>{{ voice.response }}</p>
            </div>
          </article>
        </div>
      </section>

      <nav class="account-shortcuts customer-glass-card" aria-label="مدیریت حساب">
        <a href="/order/type"><ShoppingBag :size="22" /><span><strong>شروع سفارش</strong><small>انتخاب روش دریافت و غذا</small></span><ChevronLeft :size="18" /></a>
        <a href="/customer/orders"><ReceiptText :size="22" /><span><strong>سفارش‌های من</strong><small>پیگیری و سفارش دوباره</small></span><ChevronLeft :size="18" /></a>
        <a href="/customer/wallet"><Wallet :size="22" /><span><strong>کیف پول</strong><small>موجودی، شارژ و کش‌بک</small></span><ChevronLeft :size="18" /></a>
        <a href="/customer/referrals"><Handshake :size="22" /><span><strong>معرفی و دعوت اعضا</strong><small>کد شخصی، پیوند دعوت و باشگاه مربی‌گری</small></span><ChevronLeft :size="18" /></a>
        <a href="/customer/recurring-orders"><CalendarDays :size="22" /><span><strong>برنامهٔ سفارش تکراری</strong><small>مدیریت وعده‌های زمان‌بندی‌شده</small></span><ChevronLeft :size="18" /></a>
        <a href="/customer/nutrition"><CalendarDays :size="22" /><span><strong>برنامهٔ غذایی من</strong><small>هدف روزانه، حساسیت‌ها و انتخاب وعده‌ها</small></span><ChevronLeft :size="18" /></a>
        <a href="/customer/addresses"><MapPin :size="22" /><span><strong>آدرس‌های من</strong><small>خانه، محل کار و نشانی‌های ذخیره‌شده</small></span><ChevronLeft :size="18" /></a>
        <a href="/customer/vehicles"><CarFront :size="22" /><span><strong>خودروهای من</strong><small>تحویل راحت درب ماشین</small></span><ChevronLeft :size="18" /></a>
        <a href="/table-reservation"><CalendarDays :size="22" /><span><strong>رزرو میز</strong><small>انتخاب روز، ساعت و میز</small></span><ChevronLeft :size="18" /></a>
        <a href="/customer/branches"><Store :size="22" /><span><strong>شعبه‌ها</strong><small>نشانی و ساعت کار</small></span><ChevronLeft :size="18" /></a>
        <a href="/cooperation"><Handshake :size="22" /><span><strong>درخواست همکاری</strong><small>برای سازمان، باشگاه یا مربی‌ها</small></span><ChevronLeft :size="18" /></a>
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
        <a class="customer-page__ghost-action club-wallet-link" href="/customer/wallet"><Wallet :size="16" /> شارژ و جزئیات کیف پول</a>
      </section>

      <section v-if="club?.coach_invites_enabled" class="customer-section customer-glass-card coach-invites">
        <div class="coach-invites__copy">
          <span class="customer-icon-badge coach-badge"><Handshake :size="21" /></span>
          <div>
            <h2>دعوت شاگردها</h2>
            <p>شاگردها با این پیوند عضو گروه شما می‌شوند و هنگام سفارش از تخفیف استفاده می‌کنند.</p>
          </div>
        </div>
        <div class="coach-invites__terms">
          <span><strong>{{ Number(club.coach_discount_percent || 0).toLocaleString('fa-IR') }}٪</strong> تخفیف شاگرد</span>
          <span><strong>{{ Number(club.coach_commission_percent || 0).toLocaleString('fa-IR') }}٪</strong> سهم کیف پول شما</span>
          <span><strong>{{ Number(club.coach_members_count || 0).toLocaleString('fa-IR') }}</strong> عضو</span>
        </div>
        <label class="coach-invites__label" for="coach-invite-link">پیوند دعوت اختصاصی</label>
        <div class="coach-invites__link-row">
          <input id="coach-invite-link" :value="coachInviteUrl" readonly dir="ltr" aria-label="پیوند دعوت شاگردها" />
          <button type="button" class="coach-invites__copy-btn" :disabled="!coachInviteUrl" @click="copyCoachInvite">
            <Check v-if="inviteCopied" :size="16" />
            <Copy v-else :size="16" />
            {{ inviteCopied ? 'کپی شد' : 'کپی پیوند' }}
          </button>
        </div>
        <p v-if="inviteCopyError" class="club-msg err" role="alert">{{ inviteCopyError }}</p>
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
  Check,
  ChevronLeft,
  Copy,
  LogOut,
  Handshake,
  HeartPulse,
  MapPin,
  MessageCircle,
  Pencil,
  ReceiptText,
  ShoppingBag,
  Sparkles,
  Star,
  Store,
  UserRound,
  Utensils,
  Wallet,
} from 'lucide-vue-next'
import { customerLogout, getCustomerProfile, getMenuBoot, getMySurveyInvitations, getMyWallet, listMyCustomerReviews, listMyCustomerVoices, redeemMyPoints, submitMyCustomerVoice } from '@/utils/api'
import { formatMoney, formatStatus, normalizeMobile } from '@/utils/format'
import { hasCustomerSession } from '@/utils/customerAuth'
import CustomerPageHeader from '@/components/customer/CustomerPageHeader.vue'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
const customer = ref({ name: '', mobile: '' })
const club = ref(null)
const walletSummary = ref({ withdrawable_balance: 0, cashback_balance: 0 })
const walletSummaryLoading = ref(false)
const walletSummaryError = ref('')
const redeemBusy = ref(false)
const clubMessage = ref('')
const clubError = ref('')
const currencyLabel = computed(() => (currency.value === 'TOMAN' || currency.value === 'IRT' ? 'تومان' : 'ریال'))

async function loadWalletSummary() {
  walletSummaryLoading.value = true
  walletSummaryError.value = ''
  try {
    const payload = await getMyWallet()
    walletSummary.value = payload?.wallet || { withdrawable_balance: 0, cashback_balance: 0 }
  } catch (err) {
    walletSummaryError.value = err?.message || 'موجودی کیف پول دریافت نشد.'
  } finally {
    walletSummaryLoading.value = false
  }
}
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
const surveyInvitations = ref([])
const feedbackReplies = ref([])
const customerVoices = ref([])
const voiceLoading = ref(false)
const voiceSaving = ref(false)
const voiceError = ref('')
const voiceHistoryError = ref('')
const voiceMessage = ref('')
const customerVoiceTypes = ['شکایت', 'انتقاد', 'پیشنهاد', 'درخواست', 'تقدیر']
const voiceForm = ref({ type: 'پیشنهاد', subject: '', order_code: '', message: '' })
const currency = ref('IRR')

const customerName = computed(() => customer.value.name || 'مهمان عزیز')
const customerMobile = computed(() => normalizeMobile(customer.value.mobile || ''))
const coachInviteUrl = computed(() => {
  const code = String(club.value?.referral_code || '').trim()
  return code && typeof window !== 'undefined'
    ? `${window.location.origin}/customer/login?ref=${encodeURIComponent(code)}`
    : ''
})
const inviteCopied = ref(false)
const inviteCopyError = ref('')
const recentOrders = computed(() => orders.value.slice(0, 3))
const avatarLetter = computed(() => {
  const name = customerName.value
  return name !== 'مهمان عزیز' ? name.slice(0, 1) : 'ک'
})

async function copyCoachInvite() {
  if (!coachInviteUrl.value) return
  inviteCopyError.value = ''
  try {
    await navigator.clipboard.writeText(coachInviteUrl.value)
    inviteCopied.value = true
    window.setTimeout(() => { inviteCopied.value = false }, 2200)
  } catch {
    inviteCopyError.value = 'کپی خودکار در دسترس نیست؛ پیوند را انتخاب و دستی کپی کنید.'
  }
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

function surveyHref(invite = {}) {
  return '/survey?invitation=' + encodeURIComponent(invite.name || '')
}

async function loadCustomerVoices() {
  if (!customerMobile.value) return
  voiceLoading.value = true
  voiceHistoryError.value = ''
  try {
    const result = await listMyCustomerVoices()
    customerVoices.value = result?.voices || []
  } catch (err) {
    voiceHistoryError.value = err?.message || 'تاریخچه پیام‌های شما دریافت نشد.'
  } finally {
    voiceLoading.value = false
  }
}

async function submitVoice() {
  if (voiceSaving.value || !voiceForm.value.subject || !voiceForm.value.message) return
  voiceSaving.value = true
  voiceError.value = ''
  voiceMessage.value = ''
  try {
    await submitMyCustomerVoice({ ...voiceForm.value })
    voiceForm.value = { type: 'پیشنهاد', subject: '', order_code: '', message: '' }
    voiceMessage.value = 'پیام شما با موفقیت ثبت شد.'
    await loadCustomerVoices()
  } catch (err) {
    voiceError.value = err?.message || 'ثبت پیام انجام نشد؛ دوباره تلاش کنید.'
  } finally {
    voiceSaving.value = false
  }
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
  getMenuBoot('').then((boot) => { if (boot?.currency) currency.value = boot.currency }).catch(() => {})
  void loadWalletSummary()
  if (auth.mobile) {
    voiceLoading.value = true
    voiceHistoryError.value = ''
    const [invitationResult, reviewResult, voiceResult] = await Promise.allSettled([
      getMySurveyInvitations(),
      listMyCustomerReviews(),
      listMyCustomerVoices(),
    ])
    if (invitationResult.status === 'fulfilled') surveyInvitations.value = invitationResult.value?.invitations || []
    if (reviewResult.status === 'fulfilled') {
      feedbackReplies.value = (reviewResult.value?.reviews || []).filter((review) => String(review.manager_reply || '').trim()).slice(0, 5)
    }
    if (voiceResult.status === 'fulfilled') customerVoices.value = voiceResult.value?.voices || []
    else voiceHistoryError.value = voiceResult.reason?.message || 'تاریخچه پیام‌های شما دریافت نشد.'
    voiceLoading.value = false
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

.survey-invitations {
  display: grid;
  gap: .7rem;
  padding: 1rem;
  border: 1px solid color-mix(in srgb, var(--ds-color-action-accent) 36%, var(--ds-color-border));
  border-radius: var(--ds-radius-lg);
  background: linear-gradient(135deg, var(--ds-color-action-accent-soft), var(--ds-color-surface-raised) 62%);
}
.survey-invitations__heading { display: flex; align-items: flex-start; gap: .7rem; }
.survey-invitations__icon { flex: 0 0 auto; background: var(--ds-color-action-accent-soft); color: var(--ds-color-action-accent-foreground); }
.survey-invitations__heading h2, .survey-replies h2 { margin: 0; font-size: .98rem; }
.survey-invitations__heading p, .survey-replies .customer-section__head p { margin: .2rem 0 0; color: var(--ds-color-text-muted); font-size: .78rem; line-height: 1.7; }
.survey-invitation-row { display: flex; align-items: center; justify-content: space-between; gap: .6rem; min-height: 58px; padding: .65rem .75rem; border: 1px solid var(--ds-color-border); border-radius: 14px; background: var(--ds-color-surface); color: inherit; text-decoration: none; }
.survey-invitation-row > span:first-child { display: grid; gap: .18rem; }
.survey-invitation-row strong { font-size: .82rem; }
.survey-invitation-row small { color: var(--ds-color-text-muted); font-size: .72rem; }
.survey-invitation-action { display: inline-flex; align-items: center; gap: .2rem; flex: 0 0 auto; color: var(--ds-color-action-primary); font-size: .76rem; font-weight: 800; }
.survey-replies { display: grid; gap: .55rem; padding: 1rem; }
.survey-reply-row { display: flex; align-items: flex-start; gap: .65rem; padding: .7rem 0; border-top: 1px solid var(--ds-color-border); }
.survey-reply-row img, .survey-reply-placeholder { flex: 0 0 42px; width: 42px; height: 42px; border-radius: 12px; object-fit: cover; background: var(--ds-color-action-primary-soft); color: var(--ds-color-action-primary); }
.survey-reply-placeholder { display: grid; place-items: center; }
.survey-reply-row > div { min-width: 0; }
.survey-reply-row strong { font-size: .8rem; }
.survey-reply-row p { margin: .25rem 0; color: var(--ds-color-text-secondary); font-size: .83rem; line-height: 1.8; }
.survey-reply-row small { color: var(--ds-color-text-muted); font-size: .7rem; }

.customer-voice { display: grid; gap: 1rem; padding: 1rem; }
.customer-voice__icon { color: var(--ds-color-action-accent); }
.customer-voice__form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .75rem; }
.customer-voice__form label { display: grid; gap: .35rem; color: var(--ds-color-text-secondary); font-size: .78rem; font-weight: 700; }
.customer-voice__form input, .customer-voice__form select, .customer-voice__form textarea { width: 100%; min-height: 44px; padding: .65rem .75rem; border: 1px solid var(--ds-color-border); border-radius: 12px; background: var(--ds-color-surface); color: var(--ds-color-text-primary); font: inherit; font-size: .82rem; }
.customer-voice__form textarea { min-height: 108px; resize: vertical; line-height: 1.8; }
.customer-voice__form input:focus, .customer-voice__form select:focus, .customer-voice__form textarea:focus { outline: 3px solid color-mix(in srgb, var(--ds-color-action-accent) 28%, transparent); border-color: var(--ds-color-action-accent); }
.customer-voice__message-field, .customer-voice__submit, .customer-voice__feedback { grid-column: 1 / -1; }
.customer-voice__submit { justify-self: start; min-width: 148px; }
.customer-voice__feedback { margin: 0; font-size: .78rem; }
.customer-voice__feedback--error { color: var(--ds-color-status-danger); }
.customer-voice__feedback--success { color: var(--ds-color-status-success); }
.customer-voice__history { display: grid; gap: .65rem; padding-top: .9rem; border-top: 1px solid var(--ds-color-border); }
.customer-voice__history-head { display: flex; align-items: center; justify-content: space-between; gap: .75rem; }
.customer-voice__history-head h3 { margin: 0; font-size: .92rem; }
.customer-voice__history-head button { min-height: 36px; padding: .35rem .65rem; font-size: .72rem; }
.customer-voice__empty { margin: 0; color: var(--ds-color-text-muted); font-size: .8rem; }
.customer-voice__item { display: grid; gap: .45rem; padding: .8rem; border: 1px solid var(--ds-color-border); border-radius: 14px; background: var(--ds-color-surface); }
.customer-voice__item-head { display: flex; align-items: flex-start; justify-content: space-between; gap: .7rem; }
.customer-voice__item-head > div { display: grid; gap: .2rem; min-width: 0; }
.customer-voice__item-head strong { font-size: .83rem; overflow-wrap: anywhere; }
.customer-voice__item-head small, .customer-voice__order { color: var(--ds-color-text-muted); font-size: .7rem; }
.customer-voice__status { flex: 0 0 auto; padding: .25rem .5rem; border-radius: 999px; background: var(--ds-color-action-primary-soft); color: var(--ds-color-action-primary); font-size: .68rem; font-weight: 800; }
.customer-voice__item > p { margin: 0; color: var(--ds-color-text-secondary); font-size: .8rem; line-height: 1.8; white-space: pre-wrap; }
.customer-voice__response { display: grid; gap: .2rem; margin-top: .2rem; padding: .6rem .7rem; border-right: 3px solid var(--ds-color-action-accent); background: var(--ds-color-action-accent-soft); border-radius: 10px; }
.customer-voice__response strong { font-size: .75rem; }
.customer-voice__response p { margin: 0; color: var(--ds-color-text-secondary); font-size: .78rem; line-height: 1.8; white-space: pre-wrap; }
@media (max-width: 600px) { .customer-voice__form { grid-template-columns: 1fr; } .customer-voice__message-field, .customer-voice__submit, .customer-voice__feedback { grid-column: auto; } .customer-voice__submit { width: 100%; } }

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

.wallet-overview { display: grid; gap: .85rem; padding: 1rem; border-color: color-mix(in srgb, var(--ds-color-action-primary) 24%, var(--ds-color-border)); }
.wallet-overview__heading { display: flex; align-items: center; gap: .7rem; }
.wallet-overview__heading h2 { margin: 0; font-size: .98rem; }
.wallet-overview__heading p { margin: .2rem 0 0; color: var(--ds-color-text-muted); font-size: .76rem; line-height: 1.7; }
.wallet-overview__icon { flex: 0 0 auto; color: var(--ds-color-action-primary); background: var(--ds-color-action-primary-soft); }
.wallet-overview__balances { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .65rem; }
.wallet-overview__balances > div { display: grid; gap: .35rem; min-width: 0; padding: .8rem; border: 1px solid var(--ds-color-border); border-radius: 14px; background: var(--ds-color-surface); }
.wallet-overview__balances > div small { color: var(--ds-color-text-muted); font-size: .73rem; }
.wallet-overview__balances strong { color: var(--ds-color-text-primary); font-size: .94rem; overflow-wrap: anywhere; }
.wallet-overview__balances strong small { font-weight: 500; }
.wallet-overview__link { display: flex; align-items: center; justify-content: space-between; gap: .5rem; min-height: 44px; color: var(--ds-color-action-primary); font-size: .82rem; font-weight: 800; text-decoration: none; }
.wallet-overview__link:focus-visible, .wallet-overview__error button:focus-visible { outline: 3px solid var(--ds-color-action-accent); outline-offset: 3px; border-radius: 8px; }
.wallet-overview__error { display: flex; align-items: center; justify-content: space-between; gap: .75rem; color: var(--ds-color-text-secondary); font-size: .82rem; }
.wallet-overview__error button { border: 0; background: transparent; color: var(--ds-color-action-primary); font: inherit; font-weight: 800; cursor: pointer; }
@media (max-width: 480px) { .wallet-overview__balances { grid-template-columns: 1fr; } }

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

.coach-invites {
  display: grid;
  gap: 0.9rem;
  padding: 1rem;
}

.coach-invites__copy {
  display: flex;
  align-items: flex-start;
  gap: 0.8rem;
}

.coach-invites__copy h2 {
  margin: 0;
  font-size: 1rem;
}

.coach-invites__copy p {
  margin: 0.3rem 0 0;
  color: var(--ds-color-text-muted);
  font-size: 0.82rem;
  line-height: 1.7;
}

.coach-badge {
  flex: 0 0 auto;
  background: var(--ds-color-action-accent-soft, rgb(236 128 53 / 0.14));
  color: var(--ds-color-action-accent, #b8722d);
}

.coach-invites__terms {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.coach-invites__terms span {
  padding: 0.45rem 0.65rem;
  border: 1px solid var(--ds-color-border);
  border-radius: 999px;
  background: var(--surface-soft, rgba(255, 255, 255, 0.55));
  color: var(--ds-color-text-muted);
  font-size: 0.75rem;
}

.coach-invites__terms strong {
  color: var(--ds-color-text-primary);
}

.coach-invites__label {
  margin-bottom: -0.55rem;
  color: var(--ds-color-text-muted);
  font-size: 0.76rem;
  font-weight: 700;
}

.coach-invites__link-row {
  display: flex;
  gap: 0.5rem;
}

.coach-invites__link-row input {
  flex: 1;
  width: 0;
  min-width: 0;
  min-height: 44px;
  padding: 0.55rem 0.7rem;
  border: 1px solid var(--ds-color-border);
  border-radius: 12px;
  background: var(--surface-soft, rgba(255, 255, 255, 0.55));
  color: var(--ds-color-text-primary);
  font: inherit;
  font-size: 0.76rem;
}

.coach-invites__copy-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  min-height: 44px;
  padding: 0.55rem 0.8rem;
  border: 0;
  border-radius: 12px;
  background: var(--ds-color-action-accent, #b8722d);
  color: var(--ds-color-action-accent-foreground, #fff);
  font: inherit;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
}

.coach-invites__copy-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
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

  .coach-invites__link-row {
    flex-direction: column;
  }
}
</style>
