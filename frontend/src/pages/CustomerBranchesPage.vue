<template>
  <div class="customer-page branches-page" dir="rtl">
    <CustomerPageHeader
      eyebrow="پیدا کردن ما"
      title="شعبه‌های ویدرخت"
      subtitle="اطلاعات شعبه را ببینید و منوی همان شعبه را باز کنید."
      fallback-href="/menu"
    >
      <template #eyebrow-icon><MapPin :size="14" aria-hidden="true" /></template>
    </CustomerPageHeader>

    <main class="customer-page__body branches-body">
      <section v-if="loading" class="customer-glass-card branches-state" role="status" aria-live="polite">
        <span class="branches-state__icon"><LoaderCircle :size="22" class="is-spinning" aria-hidden="true" /></span>
        <h2>در حال دریافت شعبه‌ها</h2>
        <p>چند لحظه صبر کنید تا اطلاعات به‌روز شود.</p>
      </section>

      <section v-else-if="error" class="customer-glass-card branches-state" role="alert">
        <span class="branches-state__icon branches-state__icon--warning"><CircleAlert :size="22" aria-hidden="true" /></span>
        <h2>اطلاعات شعبه‌ها دریافت نشد</h2>
        <p>{{ error }}</p>
        <DsButton variant="secondary" :loading="loading" @click="loadBranches">
          <template #leading><RefreshCw :size="16" aria-hidden="true" /></template>
          تلاش دوباره
        </DsButton>
      </section>

      <section v-else-if="customerBranches.length" class="branches-grid" aria-label="فهرست شعبه‌ها">
        <article v-for="branch in customerBranches" :key="branch.id" class="branch-card customer-glass-card">
          <div class="branch-card__media">
            <img
              v-if="branch.image && !imageFailed(branch)"
              :src="branch.image"
              :alt="`نمای ${branch.title || branch.name}`"
              loading="lazy"
              @error="markImageFailed(branch)"
            />
            <div v-else class="branch-card__placeholder" aria-hidden="true">
              <span><Store :size="30" /></span>
              <small>ویدرخت</small>
            </div>
            <DsBadge class="branch-card__status" :tone="branch.isOpen ? 'success' : 'neutral'">
              <span class="status-dot" :class="{ 'status-dot--closed': !branch.isOpen }"></span>
              {{ branch.isOpen ? 'اکنون باز است' : 'اکنون بسته است' }}
            </DsBadge>
          </div>

          <div class="branch-card__content">
            <div class="branch-card__heading">
              <div>
                <p class="branch-card__eyebrow">شعبه ویدرخت</p>
                <h2>{{ branch.title || branch.name }}</h2>
              </div>
              <span v-if="branch.prepTime" class="branch-card__prep">
                <Clock3 :size="15" aria-hidden="true" />
                آماده‌سازی حدود {{ branch.prepTime }} دقیقه
              </span>
            </div>

            <div class="branch-card__details">
              <p v-if="branch.address" class="branch-detail">
                <MapPin :size="17" aria-hidden="true" />
                <span>{{ branch.address }}</span>
              </p>
              <p v-if="hoursLabel(branch)" class="branch-detail">
                <Clock3 :size="17" aria-hidden="true" />
                <span>{{ hoursLabel(branch) }}</span>
              </p>
              <p v-if="branch.phone" class="branch-detail">
                <Phone :size="17" aria-hidden="true" />
                <a :href="`tel:${branch.phone}`" dir="ltr">{{ branch.phone }}</a>
              </p>
            </div>

            <div v-if="branch.pickup_available || branch.delivery_available" class="branch-card__services" aria-label="روش‌های سفارش">
              <DsBadge v-if="branch.pickup_available" tone="primary"><ShoppingBag :size="14" /> بیرون‌بر</DsBadge>
              <DsBadge v-if="branch.delivery_available" tone="warning"><Bike :size="14" /> ارسال</DsBadge>
            </div>

            <div class="branch-card__actions">
              <a
                v-if="mapHref(branch)"
                class="branch-action branch-action--secondary"
                :href="mapHref(branch)"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Navigation :size="17" aria-hidden="true" />
                مسیریابی
              </a>
              <button class="branch-action branch-action--primary" type="button" @click="openBranchMenu(branch)">
                دیدن منوی این شعبه
                <ArrowLeft :size="17" aria-hidden="true" />
              </button>
            </div>
          </div>
        </article>
      </section>

      <section v-else class="customer-glass-card branches-state">
        <span class="branches-state__icon"><Store :size="22" aria-hidden="true" /></span>
        <h2>شعبه‌ای برای نمایش پیدا نشد</h2>
        <p>بعداً دوباره سر بزنید یا منوی آنلاین ویدرخت را ببینید.</p>
        <a href="/menu" class="branch-action branch-action--primary branches-state__link">رفتن به منو <ArrowLeft :size="17" /></a>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  ArrowLeft,
  Bike,
  CircleAlert,
  Clock3,
  LoaderCircle,
  MapPin,
  Navigation,
  Phone,
  RefreshCw,
  ShoppingBag,
  Store,
} from 'lucide-vue-next'
import DsBadge from '@/components/design/DsBadge.vue'
import DsButton from '@/components/design/DsButton.vue'
import CustomerPageHeader from '@/components/customer/CustomerPageHeader.vue'
import { cartState, saveOrderContext } from '@/stores/cartStore'
import { getBranches } from '@/utils/api'
import { isCustomerCompany } from '@/utils/orderBranches'

const branches = ref([])
const failedImages = ref(new Set())
const loading = ref(true)
const error = ref('')

const customerBranches = computed(() => branches.value.filter(isCustomerCompany))

function branchKey(branch) {
  return String(branch?.id || branch?.name || '')
}

function imageFailed(branch) {
  return failedImages.value.has(branchKey(branch))
}

function markImageFailed(branch) {
  const next = new Set(failedImages.value)
  next.add(branchKey(branch))
  failedImages.value = next
}

function hoursLabel(branch) {
  if (branch?.opening_time && branch?.closing_time) {
    return `پذیرش سفارش امروز از ${branch.opening_time} تا ${branch.closing_time}`
  }
  return ''
}

function mapHref(branch) {
  const rawUrl = String(branch?.mapUrl || '').trim()
  if (!rawUrl || rawUrl === 'https://maps.google.com') return ''
  try {
    const url = new URL(rawUrl, window.location.origin)
    return ['https:', 'http:'].includes(url.protocol) ? url.href : ''
  } catch {
    return ''
  }
}

function openBranchMenu(branch) {
  const id = branchKey(branch)
  if (!id) return
  saveOrderContext({ branch: id, branch_title: branch.title || branch.name || id })

  const returnTo = new URLSearchParams(window.location.search).get('return') || ''
  const safeReturn = ['/order/type', '/order/delivery', '/cart'].includes(returnTo)
    || /^\/order\/pickup(?:\?method=(?:car|walk))?$/.test(returnTo)
  if (safeReturn) {
    window.location.href = returnTo
    return
  }
  if (cartState.lines.length && cartState.orderContext.order_type) {
    window.location.href = '/cart'
    return
  }
  window.location.href = `/menu?branch=${encodeURIComponent(id)}`
}

async function loadBranches() {
  loading.value = true
  error.value = ''
  try {
    const payload = await getBranches()
    branches.value = Array.isArray(payload?.branches) ? payload.branches : []
  } catch (err) {
    error.value = err?.message || 'اتصال را بررسی کنید و دوباره تلاش کنید.'
  } finally {
    loading.value = false
  }
}

onMounted(loadBranches)
</script>

<style scoped>
.branches-page {
  min-height: 100vh;
}

.branches-body {
  width: min(100%, 1120px);
  margin-inline: auto;
}

.branches-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 340px), 1fr));
  align-items: stretch;
  gap: var(--ds-space-5);
}

.branch-card {
  display: flex;
  min-width: 0;
  flex-direction: column;
  border-color: var(--ds-color-border);
  background: var(--ds-color-surface-raised);
  box-shadow: var(--ds-shadow-sm);
  transition: transform var(--ds-motion-normal) var(--ds-motion-ease), box-shadow var(--ds-motion-normal) ease;
}

.branch-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--ds-shadow-md);
}

.branch-card__media {
  position: relative;
  overflow: hidden;
  aspect-ratio: 16 / 8;
  background: var(--ds-color-action-primary-soft);
}

.branch-card__media > img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.branch-card__placeholder {
  display: grid;
  width: 100%;
  height: 100%;
  place-content: center;
  justify-items: center;
  gap: var(--ds-space-2);
  background:
    radial-gradient(circle at 20% 20%, var(--ds-color-action-accent-soft), transparent 42%),
    linear-gradient(135deg, var(--ds-color-action-primary-soft), var(--ds-color-surface-muted));
  color: var(--ds-color-action-primary);
}

.branch-card__placeholder > span {
  display: grid;
  width: 58px;
  height: 58px;
  place-items: center;
  border: 1px solid var(--ds-color-border);
  border-radius: 50%;
  background: var(--ds-color-surface-raised);
}

.branch-card__placeholder small {
  color: var(--ds-color-text-secondary);
  font-size: 0.8rem;
  font-weight: 700;
}

.branch-card__status {
  position: absolute;
  inset-block-start: var(--ds-space-3);
  inset-inline-start: var(--ds-space-3);
  border: 1px solid var(--ds-color-surface-raised);
  box-shadow: var(--ds-shadow-sm);
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--ds-color-status-success);
}

.status-dot--closed {
  background: var(--ds-color-text-muted);
}

.branch-card__content {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: var(--ds-space-4);
  padding: var(--ds-space-5);
}

.branch-card__heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--ds-space-3);
}

.branch-card__eyebrow {
  margin: 0 0 var(--ds-space-1);
  color: var(--ds-color-text-muted);
  font-size: 0.76rem;
  font-weight: 600;
}

.branch-card__heading h2 {
  margin: 0;
  color: var(--ds-color-text-primary);
  font-size: 1.18rem;
  font-weight: 800;
}

.branch-card__prep {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  gap: var(--ds-space-1);
  padding: 0.45rem 0.6rem;
  border-radius: var(--ds-radius-pill);
  background: var(--ds-color-surface-muted);
  color: var(--ds-color-text-secondary);
  font-size: 0.73rem;
  font-weight: 600;
}

.branch-card__details {
  display: grid;
  gap: var(--ds-space-3);
}

.branch-detail {
  display: flex;
  align-items: flex-start;
  gap: var(--ds-space-2);
  margin: 0;
  color: var(--ds-color-text-secondary);
  font-size: 0.88rem;
  line-height: 1.7;
}

.branch-detail > :first-child {
  flex: 0 0 auto;
  margin-top: 0.2rem;
  color: var(--ds-color-action-primary);
}

.branch-detail a {
  color: var(--ds-color-action-primary);
  font-weight: 700;
  text-decoration: none;
}

.branch-detail a:hover {
  text-decoration: underline;
}

.branch-card__services,
.branch-card__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--ds-space-2);
}

.branch-card__actions {
  margin-top: auto;
  padding-top: var(--ds-space-2);
}

.branch-card__services :deep(svg) {
  width: 14px;
  height: 14px;
}

.branch-action {
  display: inline-flex;
  min-height: 44px;
  align-items: center;
  justify-content: center;
  gap: var(--ds-space-2);
  border: 1px solid transparent;
  border-radius: var(--ds-radius-pill);
  padding: 0 var(--ds-space-4);
  font: inherit;
  font-size: 0.84rem;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  transition: transform var(--ds-motion-fast) var(--ds-motion-ease), background-color var(--ds-motion-fast) ease;
}

.branch-action:hover {
  transform: translateY(-1px);
}

.branch-action:focus-visible {
  outline: 3px solid var(--ds-color-focus-ring);
  outline-offset: 2px;
}

.branch-action--primary {
  flex: 1 1 auto;
  border-color: var(--ds-color-action-accent);
  background: var(--ds-color-action-accent);
  color: var(--ds-color-action-accent-foreground, var(--ds-color-text-inverse));
}

.branch-action--primary:hover {
  background: color-mix(in srgb, var(--ds-color-action-accent) 88%, var(--ds-color-text-primary));
}

.branch-action--secondary {
  border-color: var(--ds-color-border);
  background: var(--ds-color-surface-raised);
  color: var(--ds-color-action-primary);
}

.branch-action--secondary:hover {
  background: var(--ds-color-action-primary-soft);
}

.branches-state {
  display: grid;
  max-width: 520px;
  justify-items: center;
  gap: var(--ds-space-3);
  margin: 0 auto;
  padding: clamp(1.5rem, 5vw, 2.5rem);
  text-align: center;
}

.branches-state h2 {
  margin: 0;
  color: var(--ds-color-text-primary);
  font-size: 1.1rem;
}

.branches-state p {
  margin: 0;
  color: var(--ds-color-text-secondary);
  font-size: 0.88rem;
  line-height: 1.8;
}

.branches-state__icon {
  display: grid;
  width: 52px;
  height: 52px;
  place-items: center;
  border-radius: 50%;
  background: var(--ds-color-action-primary-soft);
  color: var(--ds-color-action-primary);
}

.branches-state__icon--warning {
  background: var(--ds-color-status-warning-soft);
  color: var(--ds-color-status-warning);
}

.branches-state__link {
  margin-top: var(--ds-space-2);
}

.is-spinning {
  animation: branch-spin 0.8s linear infinite;
}

@keyframes branch-spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 600px) {
  .branches-body {
    padding: var(--ds-space-4);
  }

  .branch-card__content {
    gap: var(--ds-space-3);
    padding: var(--ds-space-4);
  }

  .branch-card__heading {
    flex-direction: column;
  }

  .branch-card__prep {
    align-self: flex-start;
  }

  .branch-card__actions {
    display: grid;
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .branch-card,
  .branch-action {
    transition: none;
  }

  .branch-card:hover,
  .branch-action:hover {
    transform: none;
  }

  .is-spinning {
    animation: none;
  }
}
</style>
