<template>
  <Teleport to="body">
    <div v-if="open" class="final-amount-backdrop" @click.self="$emit('close')">
      <section class="final-amount-modal" dir="rtl" role="dialog" aria-modal="true" aria-labelledby="final-amount-title" @click.stop>
        <header class="final-amount-head">
          <div class="final-amount-icon" aria-hidden="true"><Target :size="20" :stroke-width="2.2" /></div>
          <div>
            <span class="final-amount-kicker">کنترل مبلغ فاکتور</span>
            <h3 id="final-amount-title">تعیین مبلغ نهایی</h3>
          </div>
          <button type="button" class="final-amount-close" aria-label="بستن" @click="$emit('close')">×</button>
        </header>

        <p class="final-amount-description">مبلغ نهایی را وارد کنید؛ تخفیف لازم به‌صورت خودکار محاسبه می‌شود.</p>

        <div class="final-amount-summary">
          <div><small>مبلغ فعلی فاکتور</small><strong>{{ formatMoney(currentTotal, currency) }}</strong></div>
          <div><small>تخفیف فعلی</small><strong>{{ formatMoney(discountAmount, currency) }}</strong></div>
        </div>

        <label class="final-amount-field">
          مبلغ نهایی فاکتور
          <PersianNumberInput
            v-model="draft"
            :suffix="currency === 'IRR' ? 'ریال' : currency"
            placeholder="مثلاً ۵۴۹۰۰۰"
            :min="0"
            show-words
          />
        </label>

        <p class="final-amount-hint">این مبلغ، مبلغ قابل پرداخت فاکتور است و نه مبلغ قبل از تخفیف.</p>

        <footer class="final-amount-actions">
          <button type="button" class="final-amount-clear" @click="$emit('clear')">حذف مبلغ نهایی</button>
          <div>
            <button type="button" class="final-amount-cancel" @click="$emit('close')">انصراف</button>
            <button type="button" class="final-amount-confirm" :disabled="draft <= 0" @click="$emit('confirm', draft)">اعمال مبلغ</button>
          </div>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Target } from 'lucide-vue-next'
import PersianNumberInput from '@/components/PersianNumberInput.vue'
import { formatMoney } from '@/utils/format'

const props = defineProps({
  open: { type: Boolean, default: false },
  modelValue: { type: Number, default: 0 },
  currentTotal: { type: Number, default: 0 },
  discountAmount: { type: Number, default: 0 },
  currency: { type: String, default: 'IRR' },
})

defineEmits(['close', 'confirm', 'clear'])
const draft = ref(0)

watch(
  () => [props.open, props.modelValue],
  () => {
    if (props.open) draft.value = Number(props.modelValue || props.currentTotal || 0)
  },
  { immediate: true },
)
</script>

<style scoped>
.final-amount-backdrop {
  position: fixed;
  inset: 0;
  z-index: 13000;
  display: grid;
  place-items: center;
  padding: 1rem;
  background: rgb(31 21 14 / 0.55);
  backdrop-filter: blur(5px);
}

.final-amount-modal {
  width: min(440px, 100%);
  display: grid;
  gap: 0.85rem;
  padding: 1rem;
  border: 1px solid color-mix(in srgb, var(--mg-border) 82%, transparent);
  border-radius: 22px;
  background: linear-gradient(180deg, var(--mg-bg-surface), var(--mg-bg-page));
  color: var(--mg-text-main);
  box-shadow: 0 28px 80px rgb(30 20 13 / 0.3);
}

.final-amount-head {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.final-amount-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border: 1px solid color-mix(in srgb, var(--mg-primary) 30%, transparent);
  border-radius: 13px;
  background: color-mix(in srgb, var(--mg-primary) 11%, var(--mg-bg-surface) 89%);
  color: var(--mg-primary);
}

.final-amount-head > div:nth-child(2) { min-width: 0; flex: 1; }
.final-amount-kicker { color: var(--mg-primary); font-size: 0.68rem; font-weight: 800; }
.final-amount-head h3 { margin: 0.12rem 0 0; font-size: 1rem; font-weight: 900; }

.final-amount-close {
  width: 34px;
  height: 34px;
  border: 1px solid var(--mg-border-light);
  border-radius: 10px;
  background: var(--mg-bg-surface);
  color: var(--mg-text-muted);
  font: inherit;
  font-size: 1.2rem;
  cursor: pointer;
}

.final-amount-description,
.final-amount-hint {
  margin: 0;
  color: var(--mg-text-muted);
  font-size: 0.76rem;
  line-height: 1.75;
}

.final-amount-summary {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.final-amount-summary > div {
  display: grid;
  gap: 0.2rem;
  padding: 0.6rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  background: color-mix(in srgb, var(--mg-bg-surface) 78%, #ffffff 22%);
}

.final-amount-summary small { color: var(--mg-text-muted); font-size: 0.67rem; }
.final-amount-summary strong { color: var(--mg-text-main); font-size: 0.82rem; }

.final-amount-field {
  display: grid;
  gap: 0.3rem;
  font-size: 0.78rem;
  font-weight: 800;
}

.final-amount-field :deep(.input) {
  min-height: 48px;
  border-color: color-mix(in srgb, var(--mg-primary) 35%, var(--mg-border) 65%);
  background: color-mix(in srgb, var(--mg-bg-surface) 78%, #ffffff 22%);
  color: var(--mg-text-main);
  font-size: 1rem;
  font-weight: 800;
}

.final-amount-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  padding-top: 0.35rem;
  border-top: 1px solid var(--mg-border-light);
}

.final-amount-actions > div { display: flex; gap: 0.4rem; }
.final-amount-clear,
.final-amount-cancel,
.final-amount-confirm {
  min-height: 38px;
  border-radius: 10px;
  padding: 0.42rem 0.7rem;
  font: inherit;
  font-size: 0.74rem;
  font-weight: 800;
  cursor: pointer;
}
.final-amount-clear { border: 0; background: transparent; color: var(--mg-danger); }
.final-amount-cancel { border: 1px solid var(--mg-border); background: var(--mg-bg-surface); color: var(--mg-text-muted); }
.final-amount-confirm { border: 1px solid var(--mg-primary); background: var(--mg-primary); color: #fff; }
.final-amount-confirm:disabled { opacity: 0.5; cursor: not-allowed; }

@media (max-width: 480px) {
  .final-amount-backdrop { align-items: end; padding: 0; }
  .final-amount-modal { border-radius: 22px 22px 0 0; padding-bottom: max(1rem, env(safe-area-inset-bottom)); }
  .final-amount-actions { align-items: stretch; flex-direction: column; }
  .final-amount-actions > div { display: grid; grid-template-columns: 1fr 1fr; }
  .final-amount-clear { align-self: flex-start; }
}
</style>
