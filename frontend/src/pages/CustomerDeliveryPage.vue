<template>
  <div class="customer-page delivery-page" dir="rtl">
    <section class="customer-page__hero">
      <div class="customer-page__topbar">
        <button class="customer-page__back" @click="goBack" aria-label="بازگشت">
          <ChevronRight :size="20" />
        </button>
        <div class="customer-page__titles">
          <p class="customer-page__eyebrow"><Truck :size="14" /> انتخاب روش سفارش</p>
          <h1 class="customer-page__title">نوع سفارش</h1>
          <p class="customer-page__subtitle">تحویل درب منزل یا بیرون‌بر را متناسب با نیازتان انتخاب کنید.</p>
        </div>
        <span class="hero-side-placeholder"></span>
      </div>
    </section>

    <div class="customer-page__body">
      <section class="customer-section">
        <div class="delivery-tabs customer-glass-card">
          <button class="delivery-tab" :class="{ 'is-active': orderType === 'delivery' }" @click="orderType = 'delivery'">
            <Bike :size="18" />
            تحویل درب منزل
          </button>
          <button class="delivery-tab" :class="{ 'is-active': orderType === 'pickup' }" @click="orderType = 'pickup'">
            <PackageCheck :size="18" />
            بیرون‌بر
          </button>
        </div>
      </section>

      <section v-if="orderType === 'delivery'" class="customer-stack">
        <article class="customer-glass-card customer-list-card info-card">
          <span class="customer-icon-badge"><MapPin :size="20" /></span>
          <div class="info-card__body">
            <strong>آدرس تحویل</strong>
            <p v-if="selectedAddress">{{ selectedAddress.address }}</p>
            <p v-else class="customer-muted-text">هنوز آدرسی انتخاب نشده است.</p>
          </div>
          <a href="/customer/addresses" class="customer-page__ghost-action info-link">تغییر</a>
        </article>

        <article class="customer-glass-card customer-list-card estimate-card">
          <div class="estimate-row">
            <span><Clock3 :size="16" /> زمان تحویل</span>
            <strong>۳۰–۴۵ دقیقه</strong>
          </div>
          <div class="estimate-row">
            <span><Bike :size="16" /> هزینه ارسال</span>
            <strong>رایگان (بالای ۱۵۰,۰۰۰ تومان)</strong>
          </div>
        </article>

        <article class="customer-glass-card customer-list-card">
          <div class="customer-field">
            <label>یادداشت برای پیک</label>
            <textarea v-model="deliveryNote" class="customer-textarea" rows="3" placeholder="مثلاً: زنگ نزنید، در را باز بگذارید..."></textarea>
          </div>
        </article>
      </section>

      <section v-else class="customer-stack">
        <div class="customer-section__head">
          <div>
            <h2>انتخاب شعبه</h2>
            <p>سفارش شما از این شعبه آماده می‌شود.</p>
          </div>
        </div>

        <label
          v-for="b in branches"
          :key="b.id"
          class="branch-card customer-glass-card"
          :class="{ 'is-active': selectedBranch === b.id }"
        >
          <input type="radio" :value="b.id" v-model="selectedBranch" hidden />
          <span class="branch-card__radio" :class="{ 'is-active': selectedBranch === b.id }"></span>
          <div class="branch-card__body">
            <div class="branch-card__head">
              <strong>{{ b.name }}</strong>
              <span class="branch-badge" :class="b.isOpen ? 'branch-badge--open' : 'branch-badge--closed'">
                {{ b.isOpen ? 'باز' : 'بسته' }}
              </span>
            </div>
            <p>{{ b.address }}</p>
            <small>آماده در {{ b.prepTime }} دقیقه</small>
          </div>
        </label>
      </section>
    </div>

    <div class="customer-bottom-cta">
      <button class="customer-primary-cta" @click="confirm" :disabled="!canConfirm">
        ادامه و مشاهده منو
        <ArrowLeft :size="18" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ArrowLeft, Bike, ChevronRight, Clock3, MapPin, PackageCheck, Truck } from 'lucide-vue-next'
import { getBranches } from '@/utils/api'

const orderType = ref('delivery')
const deliveryNote = ref('')
const selectedBranch = ref('')
const branches = ref([])
const selectedAddress = ref(null)

const selectedBranchObj = computed(() => branches.value.find((b) => b.id === selectedBranch.value))

onMounted(async () => {
  try {
    const addr = localStorage.getItem('selected_address')
    if (addr) selectedAddress.value = JSON.parse(addr)
  } catch {}
  const params = new URLSearchParams(window.location.search)
  if (params.get('type') === 'pickup') orderType.value = 'pickup'
  try {
    const data = await getBranches()
    branches.value = Array.isArray(data?.branches) ? data.branches : []
    selectedBranch.value = branches.value.find((b) => b.isOpen)?.id || branches.value[0]?.id || ''
  } catch {}
})

const canConfirm = computed(() => {
  if (orderType.value === 'delivery') return true
  return Boolean(selectedBranch.value) && (selectedBranchObj.value?.isOpen ?? false)
})

function goBack() { window.history.back() }
function confirm() {
  try {
    localStorage.setItem('order_type', orderType.value)
    if (orderType.value === 'pickup' && selectedBranchObj.value) {
      localStorage.setItem('selected_branch', JSON.stringify(selectedBranchObj.value))
    }
    if (deliveryNote.value) {
      localStorage.setItem('delivery_note', deliveryNote.value)
    }
  } catch {}
  window.location.href = '/menu'
}
</script>

<style scoped>
.hero-side-placeholder {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
}

.delivery-tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem;
  padding: 0.5rem;
}

.delivery-tab {
  min-height: 50px;
  border: 0;
  border-radius: 18px;
  background: transparent;
  color: var(--text-muted);
  font: inherit;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  cursor: pointer;
}

.delivery-tab.is-active {
  background: linear-gradient(135deg, var(--accent-green), var(--accent-gold));
  color: #fff;
  box-shadow: 0 12px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.22);
}

.info-card {
  display: flex;
  align-items: center;
  gap: 0.9rem;
}

.info-card__body {
  flex: 1;
}

.info-card__body strong {
  display: block;
  margin-bottom: 0.25rem;
}

.info-card__body p {
  margin: 0;
  line-height: 1.7;
  color: var(--text-secondary);
}

.info-link {
  text-decoration: none;
}

.estimate-card {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.estimate-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.45rem 0;
}

.estimate-row + .estimate-row {
  border-top: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.08);
}

.estimate-row span {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--text-muted);
}

.branch-card {
  display: flex;
  align-items: flex-start;
  gap: 0.9rem;
  padding: 1rem;
  cursor: pointer;
}

.branch-card.is-active {
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.22);
  box-shadow: 0 12px 28px rgb(var(--palette-deep-sapphire-rgb) / 0.12);
}

.branch-card__radio {
  width: 20px;
  height: 20px;
  border-radius: 999px;
  border: 2px solid rgb(var(--palette-deep-sapphire-rgb) / 0.26);
  margin-top: 0.35rem;
  position: relative;
  flex-shrink: 0;
}

.branch-card__radio.is-active {
  border-color: var(--accent-green);
}

.branch-card__radio.is-active::after {
  content: '';
  position: absolute;
  inset: 3px;
  border-radius: inherit;
  background: var(--accent-green);
}

.branch-card__body {
  flex: 1;
}

.branch-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.branch-card__head strong {
  font-size: 0.95rem;
}

.branch-card__body p {
  margin: 0.35rem 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.branch-card__body small {
  display: block;
  margin-top: 0.35rem;
  color: var(--text-muted);
}

.branch-badge {
  padding: 0.28rem 0.55rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 800;
}

.branch-badge--open {
  background: rgb(var(--success-rgb) / 0.12);
  color: var(--success);
}

.branch-badge--closed {
  background: rgb(var(--danger-rgb) / 0.12);
  color: var(--danger);
}
</style>
