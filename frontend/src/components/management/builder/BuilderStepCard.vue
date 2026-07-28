<template>
  <ManagementSurfaceCard class="builder-step-card" :class="{ 'is-invalid': hasError }">
    <template #title>
      <div class="step-header">
        <span class="step-badge">{{ stepIndex + 1 }}</span>
        <input
          class="input step-name-input"
          v-model="localStep.step_title"
          placeholder="نام مرحله"
          :class="{ 'is-invalid': errors.step_title }"
          @input="emitUpdate"
        />
        <div class="step-actions">
          <button
            type="button"
            class="icon-btn"
            :disabled="stepIndex === 0"
            title="انتقال به بالا"
            @click="$emit('move-up')"
          >
            <ChevronUpIcon class="icon-sm" />
          </button>
          <button
            type="button"
            class="icon-btn"
            :disabled="stepIndex === stepsLength - 1"
            title="انتقال به پایین"
            @click="$emit('move-down')"
          >
            <ChevronDownIcon class="icon-sm" />
          </button>
          <button
            type="button"
            class="icon-btn danger"
            title="حذف مرحله"
            @click="$emit('delete')"
          >
            <TrashIcon class="icon-sm" />
          </button>
        </div>
      </div>
    </template>

    <div class="step-settings-grid">
      <ManagementToggleSwitch
        v-model="localStep.is_required"
        label="مرحله اجباری"
        hint="مشتری باید حداقل پورشن لازم از این مرحله را کامل کند"
        @update:model-value="emitUpdate"
      />
      <label>
        حداقل پورشن مرحله
        <PersianNumberInput v-model="localStep.min_select" :min="0" @input="emitUpdate" />
      </label>
      <label>
        حداکثر پورشن مرحله
        <PersianNumberInput v-model="localStep.max_select" :min="1" @input="emitUpdate" />
      </label>
      <label>
        حالت انتخاب
        <select class="input" v-model="localStep.selection_mode" @change="emitUpdate">
          <option value="single">تک انتخاب</option>
          <option value="multiple">چند انتخاب پورشنی</option>
          <option value="quantity">پورشن افزایشی</option>
        </select>
      </label>
    </div>

    <p v-if="errors.min_max" class="error-text">{{ errors.min_max }}</p>
    <p v-if="errors.required_min" class="error-text">{{ errors.required_min }}</p>

    <label class="step-desc-label">
      توضیح مرحله (اختیاری)
      <textarea
        class="textarea"
        v-model="localStep.step_description"
        placeholder="راهنمای انتخاب برای مشتری"
        rows="2"
        @input="emitUpdate"
      />
    </label>

    <section class="options-section">
      <header class="options-head">
        <strong>گزینه‌ها</strong>
        <button type="button" class="secondary-btn sm" @click="showAddOption = true">
          + افزودن گزینه
        </button>
      </header>

      <p v-if="!localStep.options.length" class="muted empty-options">
        این مرحله هیچ گزینه‌ای ندارد.
      </p>

      <ManagementEditableTable
        v-else
        :columns="optionColumns"
        v-model="optionsProxy"
        :popup-title-add="'افزودن گزینه جدید'"
        :popup-title-edit="'ویرایش گزینه'"
        empty-text="داده ای برای نمایش وجود ندارد."
        :create-empty-row="createEmptyOption"
        :normalize-row="normalizeOptionRow"
        :validate-row="validateOptionRow"
      >
        <template #cell.item="{ row }">
          <SearchableDropdown
            v-model="row.item"
            :options="itemOptions"
            placeholder="انتخاب محصول"
            search-placeholder="جستجوی محصول..."
            @update:model-value="onRowItemSelected(row, $event)"
          />
        </template>
        <template #cell.base_price_delta="{ row }">
          <PersianNumberInput v-model="row.base_price_delta" :min="0" @input="emitUpdate" />
        </template>
        <template #cell.portion_qty="{ row }">
          <PersianNumberInput v-model="row.portion_qty" :min="0.01" @input="emitUpdate" />
        </template>
        <template #cell.portion_uom="{ row }">
          <input class="input table-input" v-model="row.portion_uom" placeholder="مثلاً گرم" @input="emitUpdate" />
        </template>
        <template #cell.portion_limits="{ row }">
          <span class="item-detail">
            {{ formatPortionLimit(row.min_portions, row.max_portions, row.portion_step) }}
          </span>
        </template>
        <template #cell.is_default="{ row }">
          <input type="checkbox" v-model="row.is_default" @change="toggleDefault(row)" />
        </template>
        <template #cell.image="{ row }">
          <img v-if="row.image" :src="row.image" alt="" class="option-thumb" />
          <button v-else type="button" class="icon-btn" @click="uploadOptionImage(row)">
            <ImageIcon class="icon-sm" />
          </button>
        </template>
        <template #cell.item_detail="{ row }">
          <span v-if="getLinkedItem(row.item)" class="item-detail">
            {{ formatPrice(getLinkedItem(row.item).standard_rate || 0) }}
            <small v-if="getLinkedItem(row.item).stock_uom" class="uom">
              / {{ getLinkedItem(row.item).stock_uom }}
            </small>
          </span>
          <span v-else class="muted">—</span>
        </template>
        <template #editor="{ draft, mode }">
          <div class="option-editor-grid">
            <label>
              محصول
              <SearchableDropdown
                v-model="draft.item"
                :options="itemOptions"
                placeholder="انتخاب محصول"
                search-placeholder="جستجو..."
                @update:model-value="onDraftItemPicked(draft, $event)"
              />
            </label>
            <label>
              نام گزینه
              <input class="input" v-model="draft.option_label" placeholder="نام گزینه" />
            </label>
            <label>
              افزودن قیمت دستی
              <PersianNumberInput v-model="draft.base_price_delta" :min="0" />
            </label>
            <label>
              مقدار هر پورشن
              <PersianNumberInput v-model="draft.portion_qty" :min="0.01" />
            </label>
            <label>
              واحد پورشن
              <input class="input" v-model="draft.portion_uom" placeholder="مثلاً گرم، عدد، میلی‌لیتر" />
            </label>
            <label>
              حداقل پورشن این گزینه
              <PersianNumberInput v-model="draft.min_portions" :min="0" />
            </label>
            <label>
              حداکثر پورشن این گزینه
              <PersianNumberInput v-model="draft.max_portions" :min="1" />
            </label>
            <label>
              گام پورشن
              <PersianNumberInput v-model="draft.portion_step" :min="0.01" />
            </label>
            <label>
              برچسب آلرژی
              <input class="input" v-model="draft.allergen_tags" placeholder="مثلاً: گلوتن، لبنیات" />
            </label>
            <p v-if="!draft.item" class="muted small">
              یک محصول انتخاب کنید تا اطلاعات آن به‌صورت خودکار پر شود.
            </p>
            <p v-else-if="getLinkedItem(draft.item)" class="muted small">
              نرخ لیست قیمت پیش‌فرض: {{ formatPrice(getLinkedItem(draft.item).standard_rate || 0) }}
              <span v-if="getLinkedItem(draft.item).stock_uom">
                / {{ getLinkedItem(draft.item).stock_uom }}
              </span>
            </p>
            <p v-if="draft.item && getLinkedItem(draft.item)?.price_status && getLinkedItem(draft.item)?.price_status !== 'ok'" class="error-text">
              {{ getLinkedItem(draft.item)?.unavailable_reason || 'برای این آیتم قیمت یا تبدیل واحد معتبر پیدا نشد.' }}
            </p>
          </div>
        </template>
      </ManagementEditableTable>
    </section>

    <ManagementPopup
      :open="showAddOption"
      title="افزودن گزینه سریع"
      size="sm"
      @update:open="showAddOption = $event"
    >
      <div class="add-option-form">
        <p v-if="!itemOptions.length" class="empty-picker-note">
          آیتمی برای انتخاب پیدا نشد. اگر آیتم‌ها را تازه ساخته‌اید، صفحه را یک‌بار رفرش کنید.
        </p>
        <label>
          محصول
          <SearchableDropdown
            v-model="newOption.item"
            :options="itemOptions"
            placeholder="انتخاب محصول"
            search-placeholder="جستجو..."
            @update:model-value="onNewOptionItemSelected"
          />
        </label>
        <label>
          نام گزینه
          <input class="input" v-model="newOption.option_label" placeholder="نام گزینه" />
        </label>
        <label>
          افزودن قیمت دستی
          <PersianNumberInput v-model="newOption.base_price_delta" :min="0" />
        </label>
        <label>
          مقدار هر پورشن
          <PersianNumberInput v-model="newOption.portion_qty" :min="0.01" />
        </label>
        <label>
          واحد پورشن
          <input class="input" v-model="newOption.portion_uom" placeholder="مثلاً گرم، عدد، میلی‌لیتر" />
        </label>
        <label>
          حداقل پورشن این گزینه
          <PersianNumberInput v-model="newOption.min_portions" :min="0" />
        </label>
        <label>
          حداکثر پورشن این گزینه
          <PersianNumberInput v-model="newOption.max_portions" :min="1" />
        </label>
        <label>
          گام پورشن
          <PersianNumberInput v-model="newOption.portion_step" :min="0.01" />
        </label>
        <label>
          برچسب آلرژی
          <input class="input" v-model="newOption.allergen_tags" placeholder="مثلاً: گلوتن، لبنیات" />
        </label>
        <p v-if="newOption.item && getLinkedItem(newOption.item)" class="muted small">
          نرخ لیست قیمت پیش‌فرض: {{ formatPrice(getLinkedItem(newOption.item).standard_rate || 0) }}
          <span v-if="getLinkedItem(newOption.item).stock_uom">
            / {{ getLinkedItem(newOption.item).stock_uom }}
          </span>
        </p>
        <p v-if="newOption.item && getLinkedItem(newOption.item)?.price_status && getLinkedItem(newOption.item)?.price_status !== 'ok'" class="error-text">
          {{ getLinkedItem(newOption.item)?.unavailable_reason || 'برای این آیتم قیمت یا تبدیل واحد معتبر پیدا نشد.' }}
        </p>
        <div class="popup-actions">
          <button class="primary-btn" type="button" @click="addOption">افزودن</button>
          <button class="secondary-btn" type="button" @click="showAddOption = false">انصراف</button>
        </div>
      </div>
    </ManagementPopup>
  </ManagementSurfaceCard>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementToggleSwitch from '@/components/management/ManagementToggleSwitch.vue'
import ManagementEditableTable from '@/components/management/ManagementEditableTable.vue'
import ManagementPopup from '@/components/management/ManagementPopup.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import PersianNumberInput from '@/components/PersianNumberInput.vue'
import {
  ChevronUp as ChevronUpIcon,
  ChevronDown as ChevronDownIcon,
  Trash2 as TrashIcon,
  Image as ImageIcon,
} from 'lucide-vue-next'

const props = defineProps({
  step: { type: Object, required: true },
  stepIndex: { type: Number, required: true },
  stepsLength: { type: Number, required: true },
  itemOptions: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:step', 'move-up', 'move-down', 'delete'])

const localStep = reactive(JSON.parse(JSON.stringify(props.step)))
if (!Array.isArray(localStep.options)) {
  localStep.options = []
}

watch(
  () => props.step,
  (val) => {
    Object.assign(localStep, JSON.parse(JSON.stringify(val)))
  },
  { deep: true },
)

function emitUpdate() {
  if (!Array.isArray(localStep.options)) {
    localStep.options = []
  }
  emit('update:step', JSON.parse(JSON.stringify(localStep)))
}

const optionsProxy = computed({
  get: () => (Array.isArray(localStep.options) ? localStep.options : []),
  set: (next) => {
    localStep.options = Array.isArray(next) ? next : []
    emitUpdate()
  },
})

const errors = computed(() => {
  const e = {}
  if (!localStep.step_title || !localStep.step_title.trim()) {
    e.step_title = 'نام مرحله نمی‌تواند خالی باشد.'
  }
  if (Number(localStep.min_select) > Number(localStep.max_select)) {
    e.min_max = 'حداقل انتخاب نمی‌تواند بیشتر از حداکثر باشد.'
  }
  if (localStep.is_required && Number(localStep.min_select) < 1) {
    e.required_min = 'مراحل اجباری حداقل باید یک انتخاب داشته باشند.'
  }
  return e
})

const hasError = computed(() => Object.keys(errors.value).length > 0)

const optionColumns = [
  { key: 'item', label: 'محصول' },
  { key: 'option_label', label: 'نام گزینه' },
  { key: 'portion_qty', label: 'هر پورشن' },
  { key: 'portion_uom', label: 'واحد' },
  { key: 'portion_limits', label: 'محدوده پورشن' },
  { key: 'base_price_delta', label: 'افزودن قیمت' },
  { key: 'is_default', label: 'پیش‌فرض' },
  { key: 'image', label: 'تصویر' },
  { key: 'item_detail', label: 'قیمت پایه / واحد' },
]

const showAddOption = ref(false)
const newOption = reactive({
  item: '',
  option_label: '',
  base_price_delta: 0,
  portion_qty: 1,
  portion_uom: '',
  min_portions: 0,
  max_portions: 1,
  portion_step: 1,
  is_default: false,
  allergen_tags: '',
  image: '',
})

function findItemOption(value) {
  return props.itemOptions.find((item) => String(item.value) === String(value)) || null
}

function getLinkedItem(value) {
  return findItemOption(value)
}

function formatPrice(value) {
  const num = Number(value) || 0
  return num.toLocaleString('fa-IR')
}

function formatPortionLimit(min, max, step) {
  const minValue = Number(min || 0)
  const maxValue = Number(max || 0)
  const stepValue = Number(step || 1)
  return `${minValue.toLocaleString('fa-IR')} تا ${maxValue.toLocaleString('fa-IR')} • گام ${stepValue.toLocaleString('fa-IR')}`
}

function applyItemToOption(option, itemValue) {
  const selectedItem = findItemOption(itemValue)
  option.item = itemValue || ''
  if (!selectedItem) return
  if (!option.option_label) {
    option.option_label = selectedItem.item_name || selectedItem.label || selectedItem.value
  }
  if (!option.image) {
    option.image = selectedItem.image || ''
  }
  if (!option.portion_uom) {
    option.portion_uom = selectedItem.stock_uom || ''
  }
}

function createEmptyOption() {
  return {
    item: '',
    option_label: '',
    option_key: `opt-${Date.now()}`,
    base_price_delta: 0,
    portion_qty: 1,
    portion_uom: '',
    min_portions: 0,
    max_portions: 1,
    portion_step: 1,
    price_type: 'fixed',
    price_percentage: 0,
    is_default: false,
    is_available: true,
    max_qty: 1,
    allergen_tags: '',
    image: '',
    sort_order: Array.isArray(localStep.options) ? localStep.options.length : 0,
  }
}

function normalizeOptionRow(row) {
  const normalized = {
    ...createEmptyOption(),
    ...(row || {}),
  }

  applyItemToOption(normalized, normalized.item)

  normalized.option_label = String(normalized.option_label || '').trim()
  normalized.option_key = String(normalized.option_key || `opt-${Date.now()}`).trim()
  normalized.base_price_delta = Number(normalized.base_price_delta) || 0
  normalized.portion_qty = Math.max(Number(normalized.portion_qty) || 1, 0.01)
  normalized.portion_uom = String(normalized.portion_uom || getLinkedItem(normalized.item)?.stock_uom || '').trim()
  normalized.min_portions = Math.max(Number(normalized.min_portions) || 0, 0)
  normalized.max_portions = Math.max(Number(normalized.max_portions) || 1, 1)
  normalized.portion_step = Math.max(Number(normalized.portion_step) || 1, 0.01)
  normalized.price_percentage = Number(normalized.price_percentage) || 0
  normalized.max_qty = Math.max(Number(normalized.max_qty) || 1, 1)
  normalized.is_default = Boolean(normalized.is_default)
  normalized.is_available = normalized.is_available !== false
  normalized.sort_order = Number(normalized.sort_order)
  if (!Number.isFinite(normalized.sort_order)) {
    normalized.sort_order = Array.isArray(localStep.options) ? localStep.options.length : 0
  }

  if (normalized.is_default) {
    ;(localStep.options || []).forEach((option) => {
      option.is_default = false
    })
  }

  return normalized
}

function validateOptionRow(row) {
  if (!String(row?.item || '').trim()) {
    return 'انتخاب محصول برای گزینه الزامی است.'
  }
  if (!String(row?.option_label || '').trim()) {
    return 'نام گزینه نمی‌تواند خالی باشد.'
  }
  if (Number(row?.portion_qty || 0) <= 0) {
    return 'مقدار هر پورشن باید بیشتر از صفر باشد.'
  }
  if (Number(row?.max_portions || 0) < Number(row?.min_portions || 0)) {
    return 'حداکثر پورشن نمی‌تواند کمتر از حداقل پورشن باشد.'
  }
  if (Number(row?.portion_step || 0) <= 0) {
    return 'گام پورشن باید بیشتر از صفر باشد.'
  }
  return ''
}

function onDraftItemPicked(draft, value) {
  applyItemToOption(draft, value)
}

function onRowItemSelected(row, value) {
  applyItemToOption(row, value)
  emitUpdate()
}

function onNewOptionItemSelected(value) {
  applyItemToOption(newOption, value)
}

function resetNewOption() {
  newOption.item = ''
  newOption.option_label = ''
  newOption.base_price_delta = 0
  newOption.portion_qty = 1
  newOption.portion_uom = ''
  newOption.min_portions = 0
  newOption.max_portions = 1
  newOption.portion_step = 1
  newOption.allergen_tags = ''
  newOption.image = ''
}

function addOption() {
  if (!newOption.item) return
  const selectedItem = findItemOption(newOption.item)
  const opt = {
    option_label: newOption.option_label || selectedItem?.item_name || newOption.item,
    option_key: `opt-${Date.now()}`,
    item: newOption.item,
    base_price_delta: Number(newOption.base_price_delta || 0),
    portion_qty: Number(newOption.portion_qty || 1),
    portion_uom: String(newOption.portion_uom || selectedItem?.stock_uom || '').trim(),
    min_portions: Number(newOption.min_portions || 0),
    max_portions: Math.max(Number(newOption.max_portions || 1), 1),
    portion_step: Number(newOption.portion_step || 1),
    price_type: 'fixed',
    price_percentage: 0,
    is_default: false,
    is_available: true,
    max_qty: 1,
    allergen_tags: newOption.allergen_tags,
    image: selectedItem?.image || '',
    sort_order: localStep.options.length,
  }
  localStep.options.push(opt)
  emitUpdate()
  showAddOption.value = false
  resetNewOption()
}

function toggleDefault(row) {
  if (row.is_default) {
    localStep.options.forEach((o) => {
      if (o !== row) o.is_default = false
    })
  }
  emitUpdate()
}

function uploadOptionImage(row) {
  // Trigger file upload via frappe upload
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch('/api/method/upload_file', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      })
      const data = await res.json()
      if (data.message?.file_url) {
        row.image = data.message.file_url
        emitUpdate()
      }
    } catch {
      // silent fail
    }
  }
  input.click()
}
</script>

<style scoped>
.builder-step-card {
  margin-bottom: 1rem;
}
.step-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
}
.step-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--module-500, var(--mg-primary));
  color: #fff;
  font-weight: 600;
  font-size: 0.85rem;
  flex-shrink: 0;
}
.step-name-input {
  flex: 1;
  font-weight: 600;
  font-size: 1rem;
}
.step-actions {
  display: flex;
  gap: 0.25rem;
  flex-shrink: 0;
}
.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  color: #4b5563;
}
.icon-btn:hover:not(:disabled) {
  background: #f3f4f6;
}
.icon-btn.danger {
  color: var(--mg-danger);
  border-color: var(--mg-danger);
}
.icon-btn.danger:hover:not(:disabled) {
  background: #fef2f2;
}
.icon-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.step-settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
  margin: 1rem 0;
}
.step-desc-label {
  display: block;
  margin-top: 0.75rem;
}
.options-section {
  margin-top: 1rem;
  border-top: 1px solid var(--mg-border-light);
  padding-top: 1rem;
}
.options-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}
.empty-options {
  padding: 1rem;
  text-align: center;
  background: var(--mg-bg-page);
  border-radius: 8px;
}
.option-thumb {
  width: 32px;
  height: 32px;
  object-fit: cover;
  border-radius: 4px;
}
.item-detail {
  font-variant-numeric: tabular-nums;
  font-size: 0.9rem;
}
.item-detail .uom {
  color: var(--text-muted, var(--mg-text-muted));
  font-size: 0.75rem;
}
.option-editor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  min-width: 320px;
}
.error-text {
  color: var(--mg-danger);
  font-size: 0.85rem;
  margin: 0.25rem 0;
}
.is-invalid {
  border-color: var(--mg-danger);
}
.add-option-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 320px;
}
.popup-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}
.empty-picker-note {
  margin: 0;
  padding: 0.65rem 0.75rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  border-radius: 10px;
  background: rgb(var(--palette-eggshell-rgb) / 0.72);
  color: var(--text-muted);
  font-size: 0.85rem;
}
</style>
