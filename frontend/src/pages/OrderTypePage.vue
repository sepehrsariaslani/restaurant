<template>
  <section class="order-flow-page order-type-page">
    <header class="order-flow-hero">
      <div><p class="order-flow-eyebrow">سفارش به سلیقه شما</p><h1 class="order-flow-title">کجا تحویل بگیرید؟</h1><p class="order-flow-subtitle">روش دریافت را انتخاب کنید؛ بعد سراغ غذاهای خوشمزه می‌رویم.</p></div>
      <a class="order-flow-secondary" :href="cartState.lines.length ? '/cart' : '/menu'">{{ cartState.lines.length ? 'بازگشت به سبد' : 'دیدن منو' }}</a>
    </header>
    <section class="order-branch-context" aria-label="شعبه سفارش">
      <label class="order-branch-context__select">
        <span>شعبهٔ سفارش شما</span>
        <select v-model="selectedBranchId" :disabled="branchesLoading" @change="saveBranchSelection">
          <option value="">{{ branchesLoading ? 'در حال دریافت شعبه‌ها…' : 'شعبه را انتخاب کنید' }}</option>
          <option v-for="branch in branches" :key="branch.id || branch.name" :value="branch.id || branch.name">
            {{ branch.title || branch.name }}{{ branch.isOpen === false ? ' · بسته' : '' }}
          </option>
        </select>
      </label>
      <a class="order-branch-context__link" href="/customer/branches?return=%2Forder%2Ftype">دیدن آدرس و ساعت شعب</a>
      <p v-if="selectedBranch" class="order-branch-context__saved" role="status">این انتخاب روی همین دستگاه ذخیره می‌شود.</p>
      <p v-else-if="!branchesLoading && branchesError" class="order-flow-alert danger" role="alert">{{ branchesError }}</p>
    </section>

    <div class="receiving-grid">
      <button v-for="choice in choices" :key="choice.id" class="receiving-choice" :disabled="!selectedBranch || !isChoiceAvailable(choice)" type="button" @click="choose(choice)">
        <span class="receiving-icon"><component :is="choice.icon" :size="28" aria-hidden="true" /></span>
        <span class="receiving-copy"><strong>{{ choice.title }}</strong><small>{{ choice.description }}</small><span>{{ choiceRequirement(choice) || choice.hint }}</span></span>
        <ChevronLeft :size="20" class="receiving-arrow" aria-hidden="true" />
      </button>
    </div>
    <p class="receiving-note">روش دریافت و جزئیات آن را تا پیش از ثبت سفارش می‌توانید تغییر دهید.</p>
  </section>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { Bike, CarFront, ChevronLeft, Store, UtensilsCrossed } from 'lucide-vue-next'
import { cartState, saveOrderContext } from '@/stores/cartStore'
import { resetOrderContextForType } from '@/utils/orderFlow'
import { getBranches } from '@/utils/api'
import { isCustomerCompany } from '@/utils/orderBranches'
import './orderFlow.css'
const branches = ref([])
const branchesLoading = ref(true)
const branchesError = ref('')
const selectedBranchId = ref(cartState.orderContext.branch || '')
const selectedBranch = computed(() => branches.value.find((row) => (row.id || row.name) === selectedBranchId.value) || null)
const choices = [
  { id: 'delivery', type: 'delivery', title: 'درب منزل', description: 'غذای شما را به نشانی دلخواه می‌رسانیم.', hint: 'انتخاب روی نقشه یا آدرس‌های من', icon: Bike, href: '/order/delivery' },
  { id: 'car', type: 'pickup', title: 'درب ماشین', description: 'نزدیک شعبه بمانید؛ سفارش را تا خودرو می‌آوریم.', hint: 'انتخاب شعبه و مشخصات خودرو', icon: CarFront, href: '/order/pickup?method=car' },
  { id: 'walk', type: 'pickup', title: 'تحویل حضوری', description: 'سفارش آماده را از پیشخوان تحویل بگیرید.', hint: 'انتخاب شعبه و زمان تحویل', icon: Store, href: '/order/pickup?method=walk' },
  { id: 'dine_in', type: 'dine_in', title: 'سر میز', description: 'در رستوران هستید یا برای بعد میز می‌خواهید؟', hint: 'انتخاب میز یا رزرو برای بعد', icon: UtensilsCrossed, href: '/order/dine-in' },
]
function choose(choice) {
  if (!selectedBranch.value || !isChoiceAvailable(choice)) return
  // Reopening the current method should not discard a completed address or vehicle.
  if (cartState.orderContext.order_type !== choice.type) resetOrderContextForType(choice.type)
  saveBranchSelection()
  if (choice.type === 'pickup') saveOrderContext({ pickup_method: choice.id })
  window.location.href = choice.href
}

function isChoiceAvailable(choice) {
  if (choice.type === 'delivery') return selectedBranch.value?.delivery_available !== false
  if (choice.type === 'pickup') return selectedBranch.value?.pickup_available !== false
  return true
}

function choiceRequirement(choice) {
  if (!selectedBranch.value) return 'ابتدا شعبه را انتخاب کنید.'
  if (isChoiceAvailable(choice)) return ''
  return choice.type === 'delivery'
    ? 'این شعبه ارسال ندارد؛ شعبهٔ دیگری انتخاب کنید.'
    : 'این شعبه تحویل حضوری ندارد؛ شعبهٔ دیگری انتخاب کنید.'
}

function saveBranchSelection() {
  const branch = selectedBranch.value
  if (branch) saveOrderContext({ branch: branch.id || branch.name, branch_title: branch.title || branch.name })
}

onMounted(async () => {
  try {
    const payload = await getBranches()
    branches.value = (payload?.branches || []).filter(isCustomerCompany)
    if (!branches.value.some((row) => (row.id || row.name) === selectedBranchId.value)) {
      selectedBranchId.value = selectedBranchId.value
        ? ''
        : branches.value.length === 1
          ? branches.value[0].id || branches.value[0].name
          : ''
    }
    saveBranchSelection()
  } catch (err) {
    branchesError.value = err.message || 'دریافت شعبه‌ها ناموفق بود.'
  } finally {
    branchesLoading.value = false
  }
})
</script>
<style scoped>
.order-type-page { max-width: 900px; }
.order-branch-context { display: flex; flex-wrap: wrap; align-items: end; gap: .75rem 1rem; margin: 1rem 0 1.25rem; padding: 1rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-lg); background: var(--ds-color-surface-raised); }
.order-branch-context__select { display: grid; gap: .4rem; flex: 1 1 16rem; color: var(--ds-color-text-secondary); font-size: .82rem; }
.order-branch-context__select select { min-height: 46px; padding: .6rem .8rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-sm); background: var(--ds-color-surface); color: var(--ds-color-text-primary); font: inherit; }
.order-branch-context__link { min-height: 44px; display: inline-flex; align-items: center; color: var(--ds-color-action-primary); font-size: .85rem; font-weight: 700; text-decoration: none; }
.order-branch-context__saved { flex-basis: 100%; margin: 0; color: var(--ds-color-text-muted); font-size: .78rem; }
.receiving-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
.receiving-choice { display: grid; grid-template-columns: 56px minmax(0, 1fr) 20px; align-items: center; gap: 1rem; padding: 1.5rem 1.25rem; min-height: 160px; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-lg); background: var(--ds-color-surface-raised); color: var(--ds-color-text-primary); text-align: start; font: inherit; cursor: pointer; transition: border-color var(--ds-motion-fast); }
.receiving-choice:hover { border-color: var(--ds-color-action-primary); }
.receiving-choice:disabled { opacity: .55; cursor: not-allowed; }
.receiving-icon { display: grid; place-items: center; width: 56px; height: 56px; border-radius: var(--ds-radius-md); color: var(--ds-color-action-primary); background: var(--ds-color-action-primary-soft); }
.receiving-copy { display: grid; gap: .45rem; }
.receiving-copy strong { font-size: 1.12rem; }
.receiving-copy small { color: var(--ds-color-text-secondary); font-size: .85rem; line-height: 1.8; }
.receiving-copy > span { font-size: .75rem; color: var(--ds-color-text-muted); }
.receiving-arrow { color: var(--ds-color-action-accent); }
.receiving-note { color: var(--ds-color-text-muted); font-size: .85rem; text-align: center; margin: 1.5rem 0; }
@media (max-width: 680px) { .receiving-grid { grid-template-columns: 1fr; gap: .75rem; } .receiving-choice { min-height: 120px; padding: 1.15rem 1rem; gap: .8rem; } }
</style>
