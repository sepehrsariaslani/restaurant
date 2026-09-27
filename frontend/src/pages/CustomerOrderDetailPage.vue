<template>
  <div class="order-detail-page" dir="rtl">
    <CustomerPageHeader eyebrow="تاریخچه خرید" title="جزئیات سفارش" fallback-href="/customer/orders">
      <template #eyebrow-icon><ReceiptText :size="14" aria-hidden="true" /></template>
      <template #action><a class="customer-page__action" href="/customer/orders">سفارش‌ها</a></template>
    </CustomerPageHeader>

    <section class="code-card customer-glass-card">
      <div><p>کد سفارش</p><h2>{{ orderCode || '-' }}</h2></div>
      <span v-if="order" class="status-pill">{{ formatStatus(order.status) }}</span>
    </section>

    <section v-if="!mobile" class="lookup-card">
      <label>
        <span>شماره موبایل سفارش</span>
        <input v-model="mobileInput" class="input" dir="ltr" inputmode="numeric" placeholder="09123456789" />
      </label>
      <button class="primary-btn" type="button" @click="loadOrder">نمایش سفارش</button>
    </section>

    <p v-if="loading" class="state muted">در حال دریافت سفارش...</p>
    <p v-else-if="error" class="state error">{{ error }}</p>

    <template v-else-if="order">
      <section class="facts-grid customer-order-facts" aria-label="خلاصه سفارش">
        <article>
          <span>مشتری</span>
          <strong>{{ order.customer_name || '-' }}</strong>
        </article>
        <article>
          <span>مبلغ</span>
          <strong>{{ formatMoney(order.grand_total || 0, currency) }}</strong>
        </article>
        <article>
          <span>نوع سفارش</span>
          <strong>{{ order.delivery_mode || order.order_type || '-' }}</strong>
        </article>
        <article>
          <span>تاریخ</span>
          <strong>{{ formatDate(order.created_at || order.creation || order.transaction_date) }}</strong>
        </article>
      </section>

      <CustomerOrderSurveySummary
        :summary="surveySummary"
        :requesting="requestingSurvey"
        @request="requestSurvey"
      />
      <p v-if="surveyError" class="state error" role="alert">{{ surveyError }}</p>

      <section v-if="timeline.length" class="timeline-card customer-glass-card">
        <h3><Clock3 :size="19" /> روند سفارش</h3>
        <ol class="timeline">
          <li v-for="row in timeline" :key="row.status" :class="{ done: row.done }">
            <i></i>
            <span>{{ formatStatus(row.status) }}</span>
          </li>
        </ol>
      </section>

      <section class="items-card customer-glass-card">
        <header>
          <h3><ShoppingBag :size="19" /> آیتم‌های سفارش</h3>
          <span>{{ items.length.toLocaleString('fa-IR') }} مورد</span>
        </header>
        <div v-if="items.length" class="items-list">
          <article v-for="(line, index) in items" :key="`${line.menu_item}-${index}`" class="item-row">
            <span class="item-number">{{ (index + 1).toLocaleString('fa-IR') }}</span>
            <div>
              <strong>{{ line.title || line.item_name || '-' }}</strong>
              <small>تعداد {{ Number(line.qty || 0).toLocaleString('fa-IR') }}</small>
            </div>
            <span>{{ formatMoney(line.line_total || 0, currency) }}</span>
          </article>
        </div>
        <p v-else class="muted">آیتمی برای این سفارش دریافت نشد.</p>
      </section>

      <section v-if="order.address || order.delivery_address" class="address-card customer-glass-card">
        <h3><MapPin :size="18" /> آدرس تحویل</h3>
        <p>{{ order.address || order.delivery_address }}</p>
      </section>

      <section v-if="reorderReport" class="reorder-report" :class="{ 'has-unavailable': reorderReport.unavailable.length }" role="status" aria-live="polite">
        <strong>{{ reorderReport.message }}</strong>
        <p v-if="reorderReport.unavailable.length">این موارد به سبد اضافه نشدند:</p>
        <ul v-if="reorderReport.unavailable.length"><li v-for="entry in reorderReport.unavailable" :key="entry.key">{{ entry.title }}: {{ entry.reason }}</li></ul>
        <a v-if="reorderReport.added" href="/cart" class="customer-page__action"><ShoppingBag :size="17" /> رفتن به سبد خرید</a>
      </section>

      <div class="actions-row">
        <a :href="successUrl" class="secondary-btn"><PackageCheck :size="17" /> پیگیری سفارش</a>
        <button type="button" class="primary-btn" :disabled="reordering || !repeatableItems.length" @click="repeatOrder">
          <RotateCcw :size="17" /> {{ reordering ? 'در حال بررسی محصولات…' : 'سفارش دوباره' }}
        </button>
      </div>
    </template>

    <section v-else class="empty-card">
      <Search :size="30" aria-hidden="true" />
      <h3>سفارشی برای نمایش نیست</h3>
      <p>کد سفارش و شماره موبایل را بررسی کنید.</p>
    </section>

    <div class="bottom-spacer"></div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Clock3, MapPin, PackageCheck, ReceiptText, RotateCcw, Search, ShoppingBag } from 'lucide-vue-next'
import CustomerPageHeader from '@/components/customer/CustomerPageHeader.vue'
import CustomerOrderSurveySummary from '@/components/customer/CustomerOrderSurveySummary.vue'
import { computeBuilderPrice, getItemDetail, getMyOrderSurveySummaries, getOrder, requestMyOrderSurvey } from '@/utils/api'
import { cartState, saveOrderContext, upsertLine } from '@/stores/cartStore'
import { buildCustomerReorderLine } from '@/utils/customerOrderRepeat'
import { hasCustomerSession } from '@/utils/customerAuth'
import { formatMoney, formatStatus, normalizeMobile, parseQuery } from '@/utils/format'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
const query = parseQuery()
const order = ref(null)
const items = ref([])
const timeline = ref([])
const loading = ref(false)
const error = ref('')
const currency = ref('TOMAN')
const reordering = ref(false)
const reorderReport = ref(null)
const surveySummary = ref(null)
const requestingSurvey = ref(false)
const surveyError = ref('')
const mobileInput = ref(query.mobile || readAuth().mobile || '')

const orderCode = computed(() => resolveOrderCode())
const mobile = computed(() => normalizeMobile(mobileInput.value || ''))
const successUrl = computed(() => `/order-success/${encodeURIComponent(orderCode.value)}?mobile=${encodeURIComponent(mobile.value)}`)
const repeatableItems = computed(() => items.value.filter((line) => !Number(line.is_auto_added || 0)))

function readAuth() {
  try {
    const auth = JSON.parse(localStorage.getItem(CUSTOMER_AUTH_KEY) || '{}')
    return { mobile: auth.mobile || localStorage.getItem('customer_phone') || '' }
  } catch {
    return { mobile: '' }
  }
}

function resolveOrderCode() {
  const path = window.location.pathname.replace(/^\/+|\/+$/g, '')
  const parts = path.split('/')
  if (parts.length >= 3 && parts[0] === 'customer' && parts[1] === 'orders') {
    return decodeURIComponent(parts.slice(2).join('/'))
  }
  return String(query.order_code || '').trim()
}

function formatDate(value = '') {
  if (!value) return '-'
  try {
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return date.toLocaleString('fa-IR', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return value
  }
}

async function loadOrder() {
  if (!orderCode.value || !mobile.value) return
  loading.value = true
  error.value = ''
  try {
    const data = await getOrder(orderCode.value, mobile.value)
    order.value = data?.order || null
    items.value = Array.isArray(data?.items) ? data.items : []
    timeline.value = Array.isArray(data?.status_timeline) ? data.status_timeline : []
    reorderReport.value = null
    if (data?.currency) currency.value = data.currency
    surveySummary.value = null
    surveyError.value = ''
    if (hasCustomerSession()) {
      try {
        const orderName = String(order.value?.name || '')
        if (orderName) {
          const payload = await getMyOrderSurveySummaries([orderName])
          surveySummary.value = payload?.summaries?.[orderName] || null
        }
      } catch (_) {}
    }
  } catch (err) {
    error.value = err?.message || 'دریافت جزئیات سفارش ناموفق بود.'
  } finally {
    loading.value = false
  }
}

async function requestSurvey() {
  const orderName = String(order.value?.name || '')
  if (!orderName || requestingSurvey.value) return
  requestingSurvey.value = true
  surveyError.value = ''
  try {
    const result = await requestMyOrderSurvey(orderName)
    if (result?.href) window.location.assign(result.href)
  } catch (err) {
    surveyError.value = err?.message || 'آماده‌سازی فرم نظرخواهی انجام نشد.'
  } finally {
    requestingSurvey.value = false
  }
}

function builderSelections(line) {
  const customization = line?.customization && typeof line.customization === 'object' ? line.customization : {}
  const nested = customization.builder_selection || {}
  return Array.isArray(nested.selections)
    ? nested.selections
    : Array.isArray(customization.builder_portion_rows)
      ? customization.builder_portion_rows
      : []
}

async function repeatOrder() {
  if (reordering.value || !repeatableItems.value.length) return
  reordering.value = true
  reorderReport.value = null
  const currentContext = cartState.orderContext || {}
  const orderContext = order.value?.order_context || {}
  const branch = currentContext.branch || orderContext.branch || ''
  const addedLines = []
  const unavailable = []

  for (const [index, line] of repeatableItems.value.entries()) {
    const title = line.title || line.item_name || line.menu_item || 'محصول'
    try {
      if (!line.item_slug) throw new Error('این سفارش پیش از ثبت شناسهٔ منو انجام شده است.')
      const detail = await getItemDetail(line.item_slug, branch)
      const item = detail?.item || {}
      let builderPrice = null
      if (Number(item.restaurant_builder_active || 0) === 1) {
        const selections = builderSelections(line)
        if (!selections.length) throw new Error('ترکیب سفارشی این محصول در سفارش قبلی موجود نیست.')
        const pricing = await computeBuilderPrice(item.name || item.item_code, selections)
        const currentPricing = pricing?.data || pricing || {}
        if (currentPricing.final_price == null) throw new Error('قیمت فعلی این ترکیب دریافت نشد.')
        builderPrice = Number(currentPricing.final_price)
      }
      addedLines.push({ index, title, line: buildCustomerReorderLine(line, detail, builderPrice) })
    } catch (err) {
      unavailable.push({ key: `${line.menu_item || title}-${index}`, title, reason: err?.message || 'محصول در دسترس نیست.' })
    }
  }

  if (branch && !currentContext.branch) {
    saveOrderContext({ branch, branch_title: orderContext.branch_title || branch })
  }
  for (const entry of addedLines) upsertLine(entry.line)

  reorderReport.value = {
    added: addedLines.length,
    unavailable,
    message: addedLines.length
      ? `${addedLines.length.toLocaleString('fa-IR')} قلم با قیمت و موجودی فعلی به سبد اضافه شد.`
      : 'هیچ‌کدام از محصولات سفارش قبلی در حال حاضر قابل افزودن نبودند.',
  }
  reordering.value = false
}

onMounted(() => {
  if (orderCode.value && mobile.value) loadOrder()
})
</script>

<style scoped>
.order-detail-page { min-height: 100vh; padding: 0 0 7rem; background: var(--ds-color-bg-page); color: var(--ds-color-text-primary); }
.code-card, .lookup-card, .timeline-card, .items-card, .address-card, .empty-card { margin: 1rem; padding: 1.15rem; border: 1px solid var(--ds-color-border); border-radius: 22px; }
.code-card { display: flex; align-items: center; justify-content: space-between; gap: 1rem; background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground); }
.code-card p { margin: 0 0 .35rem; color: var(--ds-color-action-primary-foreground); opacity: .78; font-size: .78rem; }
.code-card h2 { margin: 0; direction: ltr; font-size: 1.35rem; letter-spacing: .03em; }
.status-pill { flex: 0 0 auto; border: 1px solid color-mix(in srgb, var(--ds-color-action-primary-foreground) 34%, transparent); border-radius: 999px; padding: .4rem .75rem; font-size: .78rem; font-weight: 800; }
.lookup-card label { display: grid; gap: .4rem; color: var(--ds-color-text-secondary); font-size: .85rem; font-weight: 700; }
.input { width: 100%; box-sizing: border-box; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); padding: .85rem 1rem; font: inherit; background: var(--ds-color-surface); color: var(--ds-color-text-primary); }
.primary-btn, .secondary-btn { min-height: 48px; gap: .5rem; border: 1px solid transparent; border-radius: var(--ds-radius-md); padding: .75rem 1rem; text-decoration: none; font: inherit; font-weight: 800; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; }
.primary-btn { background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground); }
.secondary-btn { background: var(--ds-color-surface-raised); color: var(--ds-color-text-primary); border-color: var(--ds-color-border); }
.primary-btn:disabled { opacity: .55; cursor: not-allowed; }
.lookup-card .primary-btn { width: 100%; margin-top: .8rem; }
.state { margin: 1rem; text-align: center; line-height: 1.8; }
.muted { color: var(--ds-color-text-muted); }
.error { color: var(--ds-color-status-danger); }
.facts-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .7rem; margin: 0 1rem 1rem; }
.facts-grid article { min-width: 0; padding: .9rem; border: 1px solid var(--ds-color-border); border-radius: 18px; background: var(--ds-color-surface-raised); }
.facts-grid span { display: block; color: var(--ds-color-text-muted); font-size: .75rem; margin-bottom: .3rem; }
.facts-grid strong { font-size: .9rem; overflow-wrap: anywhere; }
.timeline-card h3, .items-card h3, .address-card h3 { display: flex; align-items: center; gap: .5rem; margin: 0; font-size: 1rem; }
.timeline { list-style: none; margin: 1rem 0 0; padding: 0; display: grid; gap: .7rem; }
.timeline li { display: flex; align-items: center; gap: .65rem; color: var(--ds-color-text-muted); font-weight: 700; }
.timeline i { width: 12px; height: 12px; border-radius: 50%; background: var(--ds-color-border); }
.timeline li.done { color: var(--ds-color-status-success); }
.timeline li.done i { background: var(--ds-color-status-success); box-shadow: 0 0 0 4px var(--ds-color-status-success-soft); }
.items-card header { display: flex; align-items: center; justify-content: space-between; gap: .75rem; border-bottom: 1px solid var(--ds-color-border); padding-bottom: .8rem; margin-bottom: .8rem; }
.items-card header span { color: var(--ds-color-text-muted); font-size: .78rem; }
.items-list { display: grid; gap: .55rem; }
.item-row { display: flex; align-items: center; gap: .7rem; padding: .75rem; border: 1px solid var(--ds-color-border); border-radius: 16px; background: var(--ds-color-surface); }
.item-number { display: grid; flex: 0 0 32px; width: 32px; height: 32px; place-items: center; border-radius: 11px; background: var(--ds-color-action-accent-soft); color: var(--ds-color-action-accent-foreground); font-size: .82rem; font-weight: 800; }
.item-row > div { flex: 1; min-width: 0; }
.item-row strong { display: block; font-size: .88rem; }
.item-row small { display: block; margin-top: .2rem; color: var(--ds-color-text-muted); }
.item-row > span:last-child { color: var(--ds-color-action-primary); font-weight: 800; white-space: nowrap; }
.address-card p { color: var(--ds-color-text-secondary); line-height: 1.8; margin: .6rem 0 0; }
.reorder-report { display: grid; gap: .55rem; margin: 1rem; padding: 1rem; border: 1px solid var(--ds-color-status-success); border-radius: 18px; background: var(--ds-color-status-success-soft); }
.reorder-report.has-unavailable { border-color: var(--ds-color-status-warning); }
.reorder-report p, .reorder-report ul { margin: 0; color: var(--ds-color-text-secondary); line-height: 1.8; }
.reorder-report ul { padding-inline-start: 1.2rem; }
.actions-row { display: grid; grid-template-columns: 1fr 1fr; gap: .7rem; margin: 1rem; }
.empty-card { display: grid; justify-items: center; gap: .55rem; text-align: center; }
.empty-card h3, .empty-card p { margin: 0; }
.empty-card p { color: var(--ds-color-text-secondary); }
.bottom-spacer { height: 2rem; }
.survey-detail-cta { display: flex; align-items: center; gap: .7rem; margin: 0 1rem 1rem; padding: .8rem .9rem; border: 1px solid color-mix(in srgb, var(--ds-color-action-accent) 36%, var(--ds-color-border)); border-radius: 18px; background: var(--ds-color-action-accent-soft); color: var(--ds-color-text-primary); text-decoration: none; }
.survey-detail-cta > span:first-child { display: grid; flex: 0 0 40px; width: 40px; height: 40px; place-items: center; border-radius: 13px; background: var(--ds-color-surface); color: var(--ds-color-action-primary); }
.survey-detail-cta > span:nth-child(2) { display: grid; flex: 1; gap: .18rem; }
.survey-detail-cta strong { font-size: .84rem; }
.survey-detail-cta small { color: var(--ds-color-text-muted); font-size: .73rem; }
@media (min-width: 720px) { .order-detail-page { max-width: 760px; margin: 0 auto; } .code-card, .lookup-card, .timeline-card, .items-card, .address-card, .empty-card { margin-inline: 0; } .facts-grid, .actions-row, .reorder-report { margin-inline: 0; } }
@media (max-width: 430px) { .actions-row { grid-template-columns: 1fr; } .status-pill { font-size: .72rem; } }
</style>
