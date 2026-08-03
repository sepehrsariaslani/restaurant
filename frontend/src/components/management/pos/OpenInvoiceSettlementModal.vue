<template>
  <Teleport to="body">
    <div v-if="open" class="invoice-settlement-backdrop" @click.self="$emit('close')">
      <section class="invoice-settlement-modal" dir="rtl" role="dialog" aria-modal="true" aria-labelledby="invoice-settlement-title" @click.stop>
        <header class="invoice-settlement-head">
          <div>
            <span class="invoice-settlement-kicker">سفارش باز</span>
            <h3 id="invoice-settlement-title">تسویه فاکتور</h3>
            <small>{{ invoice?.order_code || invoice?.name || 'فاکتور' }}</small>
          </div>
          <button type="button" class="invoice-settlement-close" @click="$emit('close')">×</button>
        </header>

        <div class="invoice-settlement-summary">
          <span>{{ invoice?.customer_name || 'مشتری POS' }}</span>
          <strong>{{ formatMoney(invoice?.grand_total || 0, currency) }}</strong>
        </div>

        <label class="invoice-settlement-field">
          روش تسویه
          <SearchableDropdown
            v-model="selectedOptionKey"
            :options="paymentOptions"
            placeholder="انتخاب روش پرداخت"
            search-placeholder="جستجوی روش پرداخت..."
          />
        </label>

        <label v-if="selectedOption?.method !== 'credit'" class="invoice-settlement-field">
          شماره پیگیری / مرجع
          <input v-model.trim="reference" class="input" placeholder="اختیاری" />
        </label>
        <p v-else class="invoice-settlement-credit-hint">این فاکتور به‌صورت اعتباری ثبت می‌شود و مانده آن باز می‌ماند.</p>
        <p v-if="error" class="invoice-settlement-error">{{ error }}</p>

        <footer class="invoice-settlement-actions">
          <button type="button" class="secondary-btn" @click="$emit('close')">انصراف</button>
          <button type="button" class="primary-btn" :disabled="loading || !selectedOption" @click="confirm">
            {{ loading ? 'در حال ثبت...' : 'تأیید تسویه' }}
          </button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import { formatMoney } from '@/utils/format'

const props = defineProps({
  open: { type: Boolean, default: false },
  invoice: { type: Object, default: null },
  paymentOptions: { type: Array, default: () => [] },
  currency: { type: String, default: 'IRR' },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  defaultOptionKey: { type: String, default: '' },
})

const emit = defineEmits(['close', 'confirm'])
const selectedOptionKey = ref('')
const reference = ref('')
const selectedOption = computed(() => props.paymentOptions.find((row) => row.value === selectedOptionKey.value) || null)

watch(
  () => [props.open, props.defaultOptionKey, props.paymentOptions],
  () => {
    if (!props.open) return
    selectedOptionKey.value = props.defaultOptionKey || props.paymentOptions[0]?.value || ''
    reference.value = ''
  },
  { deep: true, immediate: true },
)

function confirm() {
  if (!selectedOption.value) return
  emit('confirm', {
    method: selectedOption.value.method || 'cash',
    mode_of_payment: selectedOption.value.mode_of_payment || selectedOption.value.label || selectedOption.value.value,
    reference_no: reference.value,
  })
}
</script>

<style scoped>
.invoice-settlement-backdrop {
  position: fixed;
  inset: 0;
  z-index: 12500;
  display: grid;
  place-items: center;
  padding: 1rem;
  background: rgb(25 20 14 / 0.58);
  backdrop-filter: blur(4px);
}

.invoice-settlement-modal {
  width: min(430px, 100%);
  display: grid;
  gap: 0.8rem;
  padding: 1rem;
  border: 1px solid var(--mg-border);
  border-radius: 20px;
  background: linear-gradient(180deg, var(--mg-bg-surface), var(--mg-bg-page));
  color: var(--mg-text-main);
  box-shadow: 0 28px 80px rgb(30 20 13 / 0.3);
}

.invoice-settlement-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.7rem;
}

.invoice-settlement-head h3 { margin: 0.1rem 0; font-size: 1rem; font-weight: 900; }
.invoice-settlement-head small { color: var(--mg-text-muted); font-size: 0.7rem; }
.invoice-settlement-kicker { color: var(--mg-primary); font-size: 0.68rem; font-weight: 800; }
.invoice-settlement-close { border: 1px solid var(--mg-border-light); border-radius: 9px; background: var(--mg-bg-surface); color: var(--mg-text-muted); font: inherit; font-size: 1.2rem; width: 34px; height: 34px; cursor: pointer; }

.invoice-settlement-summary {
  display: flex;
  justify-content: space-between;
  gap: 0.7rem;
  padding: 0.7rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  background: color-mix(in srgb, var(--mg-bg-surface) 78%, #fff 22%);
}
.invoice-settlement-summary span { color: var(--mg-text-muted); font-size: 0.75rem; }
.invoice-settlement-summary strong { color: var(--mg-primary); direction: ltr; font-size: 0.85rem; }

.invoice-settlement-field { display: grid; gap: 0.28rem; color: var(--mg-text-main); font-size: 0.76rem; font-weight: 800; }
.invoice-settlement-credit-hint { margin: 0; padding: 0.6rem; border-radius: 10px; background: color-mix(in srgb, var(--mg-primary) 8%, transparent); color: var(--mg-text-muted); font-size: 0.73rem; line-height: 1.7; }
.invoice-settlement-error { margin: 0; color: var(--mg-danger); font-size: 0.74rem; }
.invoice-settlement-actions { display: flex; justify-content: flex-end; gap: 0.45rem; padding-top: 0.4rem; border-top: 1px solid var(--mg-border-light); }

@media (max-width: 520px) {
  .invoice-settlement-backdrop { align-items: end; padding: 0; }
  .invoice-settlement-modal { border-radius: 20px 20px 0 0; padding-bottom: max(1rem, env(safe-area-inset-bottom)); }
  .invoice-settlement-actions > * { flex: 1; }
}
</style>
