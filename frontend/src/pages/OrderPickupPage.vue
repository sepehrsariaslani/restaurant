<template>
  <section class="order-flow-page order-flow-page--mobile-cta order-flow-page--pickup">
    <header class="order-flow-hero">
      <div>
        <p class="order-flow-eyebrow">{{ pickupMethod === 'car' ? 'تحویل درب ماشین' : 'تحویل حضوری' }}</p>
        <h1 class="order-flow-title">از کدام شعبه تحویل می‌گیرید؟</h1>
        <p class="order-flow-subtitle">شما سفارش را از شعبه انتخاب‌شده تحویل می‌گیرید. هزینه ارسال برای سفارش بیرون‌بر محاسبه نمی‌شود.</p>
      </div>
      <a class="order-flow-secondary" href="/order/type">تغییر نوع سفارش</a>
    </header>

    <nav class="order-flow-steps" aria-label="مراحل سفارش">
      <span class="order-flow-step is-complete">۱. نوع سفارش</span>
      <span class="order-flow-step active" aria-current="step">۲. انتخاب شعبه</span>
      <span class="order-flow-step">۳. منوی شعبه</span>
      <span class="order-flow-step">۴. ثبت سفارش</span>
    </nav>

    <div class="order-flow-layout">
      <main class="order-flow-list">
        <p v-if="loading" class="order-flow-alert">در حال دریافت شعبه‌ها...</p>
        <p v-if="error" class="order-flow-alert danger">{{ error }}</p>
        <p v-if="!loading && !error && !branches.length" class="order-flow-alert">فعلاً شعبهِ باز و فعالی برای تحویل حضوری در دسترس نیست.</p>

        <section v-if="selectedBranch" class="order-flow-card pickup-selected-branch">
          <div class="delivery-branch-heading">
            <div><p class="order-flow-eyebrow">شعبهٔ انتخاب‌شده</p><h2>{{ selectedBranch.title || selectedBranch.name }}</h2><p>{{ selectedBranch.address || 'نشانی شعبه ثبت نشده است.' }}</p></div>
            <button class="order-flow-secondary" type="button" @click="branchPickerOpen = !branchPickerOpen">{{ branchPickerOpen ? 'بستن نقشه' : 'تغییر شعبه' }}</button>
          </div>
        </section>

        <div v-if="!loading && !error && branches.length && (branchPickerOpen || !selectedBranch)" class="pickup-branch-picker order-flow-card" role="group" aria-label="شعبه‌های آماده تحویل بیرون‌بر">
          <h2>از روی نقشه یا فهرست، شعبه را انتخاب کنید</h2>
          <BranchMapPicker v-model="selectedBranchId" :branches="branches" />
          <div class="pickup-branch-grid">
        <button
          v-for="branch in branches"
          :key="branch.id || branch.name"
          type="button"
          class="order-flow-branch-card pickup-branch-card"
          :class="{ active: selectedBranchId === branchKey(branch) }"
          :aria-pressed="selectedBranchId === branchKey(branch)"
          @click="selectBranch(branch)"
        >
          <div class="pickup-branch-card__top">
            <span class="pickup-branch-card__selection" aria-hidden="true">
              <CheckCircle2 v-if="selectedBranchId === branchKey(branch)" :size="21" />
              <Circle v-else :size="21" />
            </span>
            <span class="order-flow-pill" :class="branch.isOpen ? '' : 'warning'">{{ branch.open_label || (branch.isOpen ? 'باز' : 'بسته') }}</span>
          </div>
          <strong class="pickup-branch-card__title">{{ branch.title || branch.name }}</strong>
          <span class="pickup-branch-card__address"><MapPin :size="15" />{{ branch.address || 'نشانی شعبه ثبت نشده است.' }}</span>
          <small v-if="branch.opening_time && branch.closing_time" class="pickup-branch-card__hours">پذیرش سفارش امروز: {{ branch.opening_time }} تا {{ branch.closing_time }}</small>
          <div class="order-flow-branch-meta">
            <span class="order-flow-pill"><Clock3 :size="14" /> حدود {{ branch.prepTime || branch.prep_time_mins || 20 }} دقیقه</span>
            <span class="order-flow-pill">بدون هزینه ارسال</span>
          </div>
          <span class="pickup-branch-card__action">{{ selectedBranchId === branchKey(branch) ? 'این شعبه انتخاب شد' : 'انتخاب این شعبه' }}<ChevronLeft :size="16" /></span>
        </button>
          </div>
        </div>

        <div v-if="selectedBranch && !selectedBranch.isOpen" class="order-flow-alert danger" role="status">
          <strong>پذیرش سفارش این شعبه اکنون بسته است.</strong>
          <span v-if="selectedBranch.opening_time && selectedBranch.closing_time">امروز سفارش‌گیری از {{ selectedBranch.opening_time }} تا {{ selectedBranch.closing_time }} است.</span>
          <button class="order-flow-secondary" type="button" @click="branchPickerOpen = true">انتخاب شعبهٔ باز</button>
        </div>

        <div v-if="branchAvailabilityStatus === 'checking' && hasCartLines" class="order-flow-alert" role="status">در حال بررسی اقلام سبد در این شعبه…</div>
        <div v-else-if="branchAvailabilityStatus === 'unavailable'" class="order-flow-alert danger" role="alert">
          <strong>این شعبه همهٔ اقلام سبد را ندارد.</strong>
          <ul><li v-for="item in unavailableItems" :key="item.id || item.item_slug">{{ item.item_title }} — {{ unavailableReason(item.reason) }}</li></ul>
          <div class="delivery-availability-actions">
            <button class="order-flow-secondary" type="button" @click="removeUnavailableItems">حذف اقلام ناموجود از سبد</button>
            <button class="order-flow-secondary" type="button" @click="branchPickerOpen = true">انتخاب شعبهٔ دیگر</button>
          </div>
        </div>
        <div v-else-if="branchAvailabilityStatus === 'error'" class="order-flow-alert danger" role="alert">
          {{ branchAvailabilityError }}
          <button class="order-flow-secondary" type="button" @click="verifyBranchAvailability">تلاش دوباره</button>
        </div>

        <section v-if="pickupMethod === 'car'" class="order-flow-card pickup-vehicle-card">
          <h2>با کدام خودرو می‌آیید؟</h2>
          <p>مدل، رنگ و پلاک را مشخص کنید تا راحت‌تر پیدایتان کنیم.</p>
          <CustomerVehiclePicker v-model="vehicle" :mobile="mobile" :customer-name="customerName" :signed-in="signedIn" />
        </section>

        <section class="order-flow-card pickup-time-card" v-if="selectedBranch">
          <div class="pickup-time-card__heading">
            <div>
              <p class="order-flow-eyebrow">قدم بعدی · {{ selectedBranch.title || selectedBranch.name }}</p>
              <h2>چه زمانی تحویل می‌گیرید؟</h2>
              <p>زمان تقریبی آماده‌سازی این شعبه {{ selectedBranch.prepTime || selectedBranch.prep_time_mins || 20 }} دقیقه است.</p>
            </div>
            <Clock3 :size="22" aria-hidden="true" />
          </div>
          <div class="order-flow-segmented pickup-time-options">
            <button type="button" :class="{ active: pickupTimeType === 'asap' }" @click="pickupTimeType = 'asap'">هرچه سریع‌تر</button>
            <button type="button" :class="{ active: pickupTimeType === 'scheduled' }" @click="pickupTimeType = 'scheduled'">انتخاب زمان</button>
          </div>
          <label class="order-flow-field pickup-time-field" v-if="pickupTimeType === 'scheduled'">
            <span>ساعت تحویل</span>
            <input class="order-flow-input" type="time" v-model="pickupTime" />
          </label>
          <p v-if="pickupTimeType === 'scheduled' && !pickupTime" class="pickup-time-hint">یک ساعت انتخاب کنید تا ادامه سفارش فعال شود.</p>
          <details class="pickup-note-details">
            <summary>افزودن یادداشت برای شعبه <span>اختیاری</span></summary>
            <label class="order-flow-field">
              <span>یادداشت سفارش</span>
              <textarea class="order-flow-textarea" rows="2" v-model="customerNote" placeholder="مثلاً لطفاً سس جدا باشد" />
            </label>
          </details>
        </section>
      </main>

      <OrderContextSummary class="pickup-order-summary" :next-step="nextStep" :currency="currency">
        <button class="order-flow-primary pickup-summary-cta" type="button" :disabled="!canContinue" @click="continueToMenu">{{ continueLabel }}</button>
      </OrderContextSummary>
    </div>

    <div v-if="selectedBranch" class="order-mobile-cta" role="region" aria-label="ادامه سفارش">
      <div><small>{{ selectedBranch.title || selectedBranch.name }}</small><strong>{{ pickupTimeType === 'scheduled' && pickupTime ? `تحویل ساعت ${pickupTime}` : `آماده‌سازی حدود ${selectedBranch.prepTime || selectedBranch.prep_time_mins || 20} دقیقه` }}</strong></div>
      <button class="order-flow-primary" type="button" :disabled="!canContinue" @click="continueToMenu">{{ continueLabel }}</button>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { CheckCircle2, Circle, Clock3, ChevronLeft, MapPin } from 'lucide-vue-next'
import CustomerVehiclePicker from '@/components/customer/CustomerVehiclePicker.vue'
import BranchMapPicker from '@/components/checkout/BranchMapPicker.vue'
import { vehicleComplete } from '@/utils/customerOrderValidation'
import OrderContextSummary from '@/components/OrderContextSummary.vue'
import { cartState, saveOrderContext } from '@/stores/cartStore'
import { consumeNutritionScheduleReturn } from '@/utils/orderFlow'
import { isCustomerPickupCompany, resolvePickupCompanySelection } from '@/utils/orderBranches'
import { getBranches, getMenuBoot } from '@/utils/api'
import { useBranchCartAvailability } from '@/composables/useBranchCartAvailability'
import './orderFlow.css'

const query = new URLSearchParams(window.location.search)
const pickupMethod = ref(query.get('method') === 'car' ? 'car' : query.get('method') === 'walk' ? 'walk' : cartState.orderContext.pickup_method || 'walk')
const vehicle = ref(cartState.orderContext.pickup_vehicle || {})
let auth = {}
try { auth = JSON.parse(localStorage.getItem('restaurant-customer-auth-v1') || '{}') } catch {}
const signedIn = Boolean(auth.mobile && auth.customer_token)
const mobile = auth.mobile || ''
const customerName = auth.customer_name || ''
const branches = ref([])
const loading = ref(false)
const error = ref('')
const currency = ref('IRR')
const selectedBranchId = ref(cartState.orderContext.branch || '')
const branchPickerOpen = ref(!selectedBranchId.value)
const {
  status: branchAvailabilityStatus,
  unavailableItems,
  error: branchAvailabilityError,
  verify: verifyBranchAvailability,
  removeUnavailable: removeUnavailableItems,
} = useBranchCartAvailability(selectedBranchId)
const pickupTimeType = ref(cartState.orderContext.pickup_time_type || 'asap')
const pickupTime = ref(cartState.orderContext.pickup_time || '')
const customerNote = ref(cartState.orderContext.customer_note || '')

function branchKey(branch = {}) {
  return branch.id || branch.name || ''
}

const selectedBranch = computed(() => branches.value.find((branch) => branchKey(branch) === selectedBranchId.value) || null)
const hasCartLines = computed(() => cartState.lines.length > 0)
const continueLabel = computed(() => hasCartLines.value ? 'تکمیل سفارش' : 'ادامه به منوی این شعبه')
const nextStep = computed(() => hasCartLines.value ? 'تکمیل سفارش' : 'مشاهده منو و انتخاب غذا')
const canContinue = computed(() => Boolean(selectedBranch.value && selectedBranch.value.isOpen !== false && (pickupTimeType.value !== 'scheduled' || pickupTime.value) && (pickupMethod.value !== 'car' || vehicleComplete(vehicle.value)) && (!hasCartLines.value || branchAvailabilityStatus.value === 'available')))

watch([selectedBranch, pickupTimeType, pickupTime, customerNote, pickupMethod, vehicle], persistPickup, { deep: true })

function persistPickup() {
  if (!selectedBranch.value) return
  saveOrderContext({
    order_type: 'pickup',
    pickup_method: pickupMethod.value,
    pickup_vehicle: pickupMethod.value === 'car' ? { ...vehicle.value } : null,
    branch: selectedBranch.value.id || selectedBranch.value.name,
    branch_title: selectedBranch.value.title || selectedBranch.value.name,
    prep_time_mins: Number(selectedBranch.value.prepTime || selectedBranch.value.prep_time_mins || 20),
    pickup_time_type: pickupTimeType.value,
    pickup_time: pickupTimeType.value === 'scheduled' ? pickupTime.value : '',
    delivery_fee: 0,
    customer_note: customerNote.value,
    courier_note: '',
    address: null,
  })
}

function selectBranch(branch) {
  selectedBranchId.value = branchKey(branch)
  branchPickerOpen.value = false
}

function unavailableReason(reason) {
  if (reason === 'not_in_branch') return 'در این شعبه عرضه نمی‌شود'
  if (reason === 'out_of_stock') return 'فعلاً موجود نیست'
  return 'در فهرست فروش این شعبه نیست'
}

async function loadBranches() {
  loading.value = true
  error.value = ''
  try {
    const [branchPayload, boot] = await Promise.all([getBranches(), getMenuBoot('')])
    branches.value = (Array.isArray(branchPayload?.branches) ? branchPayload.branches : []).filter(isCustomerPickupCompany)
    selectedBranchId.value = resolvePickupCompanySelection(branches.value, selectedBranchId.value)
    branchPickerOpen.value = !selectedBranchId.value
    currency.value = boot?.currency || 'IRR'
  } catch (err) {
    error.value = err.message || 'دریافت شعبه‌ها ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function continueToMenu() {
  if (!canContinue.value) return
  persistPickup()
  if (hasCartLines.value) {
    window.location.href = consumeNutritionScheduleReturn() || '/checkout'
    return
  }
  window.location.href = `/menu?branch=${encodeURIComponent(branchKey(selectedBranch.value))}`
}

onMounted(() => {
  saveOrderContext({ order_type: 'pickup', pickup_method: pickupMethod.value, delivery_fee: 0, address: null, courier_note: '' })
  loadBranches()
})
</script>

<style scoped>
.pickup-vehicle-card > p { margin-bottom: 1rem; }
.pickup-selected-branch { display: grid; gap: .8rem; }
.pickup-selected-branch .delivery-branch-heading h2 { margin: 0; }
.pickup-branch-picker { display: grid; gap: .8rem; }
.pickup-branch-picker > h2 { margin: 0; font-size: 1rem; }
.delivery-branch-heading { display: flex; align-items: start; justify-content: space-between; gap: 1rem; }
.delivery-branch-heading > div { display: grid; gap: .25rem; }
.delivery-branch-heading h2 { margin: 0; }
.delivery-branch-heading p { margin: 0; color: var(--ds-color-text-secondary); font-size: .84rem; }
.delivery-availability-actions { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .65rem; }
.order-flow-alert ul { margin: .5rem 0; padding-inline-start: 1.25rem; }

.order-flow-layout .pickup-branch-grid .order-flow-branch-card,
.order-flow-layout > .order-flow-list > .order-flow-branch-card {
  width: min(100%, 32rem);
  justify-self: center;
}

.order-flow-steps {
  display: flex;
  flex-wrap: nowrap;
  overflow-x: auto;
}

.order-flow-step {
  flex: 0 0 auto;
  white-space: nowrap;
}

.order-flow-hero {
  padding: clamp(1rem, 2vw, 1.3rem);
}

.order-flow-title {
  font-size: clamp(1.55rem, 4vw, 2.25rem);
  line-height: 1.25;
}

.order-flow-hero > .order-flow-secondary {
  width: fit-content;
  max-width: 100%;
  justify-self: start;
  white-space: nowrap;
}

.order-flow-page--pickup .order-flow-title {
  font-size: clamp(1.45rem, 3vw, 1.9rem);
  line-height: 1.3;
}

.order-flow-page--pickup .pickup-branch-card {
  min-height: 0;
  padding: 0.85rem 1rem;
}

.order-flow-page--pickup .pickup-branch-card.active {
  border-color: color-mix(in srgb, var(--ds-color-action-primary) 58%, var(--ds-color-border));
  border-inline-start: 3px solid var(--ds-color-action-primary);
}

.order-flow-page--pickup .pickup-branch-card__action {
  margin-top: 0.1rem;
}

.order-flow-page--pickup .pickup-time-card__heading {
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--ds-color-border);
}

.order-flow-page--pickup .pickup-time-options {
  max-width: 34rem;
}

.order-flow-page--pickup :deep(.pickup-order-summary header > p:last-child),
.order-flow-page--pickup :deep(.pickup-order-summary .order-flow-summary-line:nth-child(-n + 4)) {
  display: none;
}

.order-flow-branch-card.active {
  border-color: color-mix(in srgb, var(--ds-color-action-primary) 64%, var(--ds-color-border));
}

.order-flow-steps {
  scroll-snap-type: x proximity;
  scrollbar-width: thin;
}

.order-flow-step {
  scroll-snap-align: start;
}

@media (max-width: 560px) {
  .order-flow-hero > .order-flow-secondary {
    white-space: normal;
  }
}
</style>
