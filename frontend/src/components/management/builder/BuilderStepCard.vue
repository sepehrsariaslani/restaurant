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
        hint="مشتری باید حداقل یک گزینه از این مرحله انتخاب کند"
        @update:model-value="emitUpdate"
      />
      <label>
        حداقل انتخاب
        <PersianNumberInput v-model="localStep.min_select" :min="0" @input="emitUpdate" />
      </label>
      <label>
        حداکثر انتخاب
        <PersianNumberInput v-model="localStep.max_select" :min="1" @input="emitUpdate" />
      </label>
      <label>
        حالت انتخاب
        <select class="input" v-model="localStep.selection_mode" @change="emitUpdate">
          <option value="single">تک انتخاب</option>
          <option value="multiple">چند انتخاب</option>
          <option value="quantity">تعداد</option>
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
        :rows="localStep.options"
        @add-row="showAddOption = true"
        @delete-row="deleteOption"
      >
        <template #cell.item="{ row }">
          <SearchableDropdown
            v-model="row.item"
            :options="itemOptions"
            placeholder="انتخاب محصول"
            search-placeholder="جستجوی محصول..."
            @update:model-value="emitUpdate"
          />
        </template>
        <template #cell.base_price_delta="{ row }">
          <PersianNumberInput v-model="row.base_price_delta" :min="0" @input="emitUpdate" />
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
      </ManagementEditableTable>
    </section>

    <ManagementPopup v-if="showAddOption" title="افزودن گزینه جدید" @close="showAddOption = false">
      <div class="add-option-form">
        <label>
          محصول
          <SearchableDropdown
            v-model="newOption.item"
            :options="itemOptions"
            placeholder="انتخاب محصول"
            search-placeholder="جستجو..."
          />
        </label>
        <label>
          افزودن قیمت
          <PersianNumberInput v-model="newOption.base_price_delta" :min="0" />
        </label>
        <label>
          توضیح گزینه
          <input class="input" v-model="newOption.option_label" placeholder="نام گزینه" />
        </label>
        <label>
          برچسب آلرژی
          <input class="input" v-model="newOption.allergen_tags" placeholder="مثلاً: گلوتن، لبنیات" />
        </label>
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

watch(
  () => props.step,
  (val) => {
    Object.assign(localStep, JSON.parse(JSON.stringify(val)))
  },
  { deep: true },
)

function emitUpdate() {
  emit('update:step', JSON.parse(JSON.stringify(localStep)))
}

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
  { key: 'base_price_delta', label: 'افزودن قیمت' },
  { key: 'is_default', label: 'پیش‌فرض' },
  { key: 'image', label: 'تصویر' },
]

const showAddOption = ref(false)
const newOption = reactive({
  item: '',
  option_label: '',
  base_price_delta: 0,
  is_default: false,
  allergen_tags: '',
  image: '',
})

function addOption() {
  if (!newOption.item) return
  const opt = {
    option_label: newOption.option_label || newOption.item,
    option_key: `opt-${Date.now()}`,
    item: newOption.item,
    base_price_delta: Number(newOption.base_price_delta) || 0,
    price_type: 'fixed',
    is_default: false,
    is_available: true,
    allergen_tags: newOption.allergen_tags,
    image: '',
    sort_order: localStep.options.length,
  }
  localStep.options.push(opt)
  emitUpdate()
  showAddOption.value = false
  newOption.item = ''
  newOption.option_label = ''
  newOption.base_price_delta = 0
  newOption.allergen_tags = ''
}

function deleteOption(index) {
  localStep.options.splice(index, 1)
  emitUpdate()
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
  background: var(--module-500, #7c5a42);
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
  color: #dc2626;
  border-color: #fca5a5;
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
  border-top: 1px solid #e5e7eb;
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
  background: #f9fafb;
  border-radius: 8px;
}
.option-thumb {
  width: 32px;
  height: 32px;
  object-fit: cover;
  border-radius: 4px;
}
.error-text {
  color: #dc2626;
  font-size: 0.85rem;
  margin: 0.25rem 0;
}
.is-invalid {
  border-color: #fca5a5;
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
</style>
