<template>
  <ManagementPageScaffold
    title="تنظیم شیفت صندوق"
    subtitle="پیش‌فرض‌های آغاز و پایان کار صندوق را یک‌جا مدیریت کنید."
  >
    <p v-if="loading" class="state-message" role="status">در حال دریافت تنظیمات شیفت...</p>
    <div v-else-if="loadError" class="load-error" role="alert">
      <p class="state-message state-message--error">{{ loadError }}</p>
      <button class="secondary-btn" type="button" @click="loadSettings">تلاش دوباره</button>
    </div>

    <template v-else>
      <div class="shift-grid">
        <ManagementSurfaceCard title="افتتاحیه صندوق" subtitle="مقادیر پیش‌فرض هنگام شروع شیفت">
          <div class="shift-fields">
            <label class="check-row">
              <input v-model="form.opening.enabled" type="checkbox" :disabled="saving" />
              فعال بودن فرآیند افتتاحیه
            </label>
            <label class="field">
              <span>ساعت پیش‌فرض افتتاحیه</span>
              <input v-model="form.opening.time" class="input" type="time" :disabled="saving" />
            </label>
            <label class="field">
              <span>موجودی اولیه صندوق</span>
              <input v-model.number="form.opening.cash_float" class="input" type="number" min="0" inputmode="decimal" :disabled="saving" />
            </label>
            <label class="check-row">
              <input v-model="form.opening.checklist_required" type="checkbox" :disabled="saving" />
              چک‌لیست افتتاحیه اجباری باشد
            </label>
            <ManagementNoteField
              v-model="form.opening.note_template"
              label="متن پیش‌فرض افتتاحیه"
              rows="3"
              placeholder="متن چاپ یا توضیح افتتاحیه..."
              :disabled="saving"
            />
          </div>
        </ManagementSurfaceCard>

        <ManagementSurfaceCard title="اختتامیه صندوق" subtitle="مقادیر پیش‌فرض هنگام بستن شیفت">
          <div class="shift-fields">
            <label class="check-row">
              <input v-model="form.closing.enabled" type="checkbox" :disabled="saving" />
              فعال بودن فرآیند اختتامیه
            </label>
            <label class="field">
              <span>ساعت پیش‌فرض اختتامیه</span>
              <input v-model="form.closing.time" class="input" type="time" :disabled="saving" />
            </label>
            <label class="field">
              <span>موجودی هدف اختتامیه</span>
              <input v-model.number="form.closing.expected_cash" class="input" type="number" min="0" inputmode="decimal" :disabled="saving" />
            </label>
            <label class="field">
              <span>تلرانس اختلاف صندوق</span>
              <input v-model.number="form.closing.tolerance" class="input" type="number" min="0" inputmode="decimal" :disabled="saving" />
            </label>
            <label class="check-row">
              <input v-model="form.closing.checklist_required" type="checkbox" :disabled="saving" />
              چک‌لیست اختتامیه اجباری باشد
            </label>
            <ManagementNoteField
              v-model="form.closing.note_template"
              label="متن پیش‌فرض اختتامیه"
              rows="3"
              placeholder="متن چاپ یا توضیح اختتامیه..."
              :disabled="saving"
            />
          </div>
        </ManagementSurfaceCard>
      </div>

      <ManagementSurfaceCard class="save-card" tone="soft">
        <div class="save-card__content">
          <div class="save-card__messages" aria-live="polite">
            <p v-if="saveError" class="state-message state-message--error" role="alert">{{ saveError }}</p>
            <p v-if="saveMessage" class="state-message" role="status">{{ saveMessage }}</p>
          </div>
          <button class="primary-btn" type="button" :disabled="saving" @click="saveSettings">
            {{ saving ? 'در حال ذخیره...' : 'ذخیره تنظیمات شیفت' }}
          </button>
        </div>
      </ManagementSurfaceCard>
    </template>
  </ManagementPageScaffold>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import ManagementNoteField from '@/components/management/ManagementNoteField.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { getManagementPOSShiftSettings, setManagementPOSShiftSettings } from '@/utils/api'

const loading = ref(true)
const saving = ref(false)
const loadError = ref('')
const saveError = ref('')
const saveMessage = ref('')
const form = reactive({
  opening: { enabled: true, time: '08:00', cash_float: 0, checklist_required: true, note_template: '' },
  closing: { enabled: true, time: '23:00', expected_cash: 0, tolerance: 0, checklist_required: true, note_template: '' },
})

function normalizeTimeInput(value, fallback) {
  const raw = String(value || '').trim()
  const match = raw.match(/^(\d{1,2}):(\d{1,2})/)
  return match ? `${match[1].padStart(2, '0')}:${match[2].padStart(2, '0')}` : fallback
}

function normalizeTimePayload(value, fallback) {
  const raw = String(value || '').trim()
  if (/^\d{2}:\d{2}:\d{2}$/.test(raw)) return raw
  if (/^\d{2}:\d{2}$/.test(raw)) return `${raw}:00`
  return fallback
}

function applySettings(payload = {}) {
  const opening = payload?.opening || {}
  const closing = payload?.closing || {}
  Object.assign(form.opening, {
    enabled: Boolean(opening.enabled),
    time: normalizeTimeInput(opening.time, '08:00'),
    cash_float: Number(opening.cash_float || 0),
    checklist_required: Boolean(opening.checklist_required),
    note_template: String(opening.note_template || ''),
  })
  Object.assign(form.closing, {
    enabled: Boolean(closing.enabled),
    time: normalizeTimeInput(closing.time, '23:00'),
    expected_cash: Number(closing.expected_cash || 0),
    tolerance: Number(closing.tolerance || 0),
    checklist_required: Boolean(closing.checklist_required),
    note_template: String(closing.note_template || ''),
  })
}

async function loadSettings() {
  loading.value = true
  loadError.value = ''
  try {
    applySettings(await getManagementPOSShiftSettings())
  } catch (error) {
    loadError.value = error?.message || 'دریافت تنظیمات شیفت صندوق ناموفق بود.'
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  saveError.value = ''
  saveMessage.value = ''
  try {
    const payload = {
      opening: {
        enabled: form.opening.enabled ? 1 : 0,
        time: normalizeTimePayload(form.opening.time, '08:00:00'),
        cash_float: Math.max(Number(form.opening.cash_float || 0), 0),
        checklist_required: form.opening.checklist_required ? 1 : 0,
        note_template: String(form.opening.note_template || '').trim(),
      },
      closing: {
        enabled: form.closing.enabled ? 1 : 0,
        time: normalizeTimePayload(form.closing.time, '23:00:00'),
        expected_cash: Math.max(Number(form.closing.expected_cash || 0), 0),
        tolerance: Math.max(Number(form.closing.tolerance || 0), 0),
        checklist_required: form.closing.checklist_required ? 1 : 0,
        note_template: String(form.closing.note_template || '').trim(),
      },
    }
    applySettings(await setManagementPOSShiftSettings(payload))
    saveMessage.value = 'تنظیمات شیفت با موفقیت ذخیره شد.'
  } catch (error) {
    saveError.value = error?.message || 'ذخیره تنظیمات شیفت ناموفق بود.'
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>

<style scoped>
.shift-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--ds-space-3, .75rem); }
.shift-fields { display: grid; gap: var(--ds-space-3, .75rem); }
.field { display: grid; gap: var(--ds-space-1, .25rem); color: var(--ds-color-text-secondary); font-size: .84rem; }
.check-row { display: flex; align-items: center; gap: var(--ds-space-2, .5rem); min-height: 44px; color: var(--ds-color-text-primary); font-size: .84rem; }
.check-row input { width: 18px; height: 18px; accent-color: var(--ds-color-action-primary); }
.save-card__content, .load-error { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: var(--ds-space-3, .75rem); }
.save-card__content { width: 100%; }
.save-card__messages { display: grid; gap: var(--ds-space-1, .25rem); }
.state-message { margin: 0; color: var(--ds-color-text-secondary); font-size: .88rem; }
.state-message--error { color: var(--ds-color-status-danger, var(--danger)); }
@media (max-width: 760px) { .shift-grid { grid-template-columns: minmax(0, 1fr); } }
</style>
