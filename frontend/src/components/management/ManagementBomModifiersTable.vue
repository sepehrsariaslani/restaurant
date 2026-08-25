<template>
  <section class="modifier-groups-shell">
    <header class="group-toolbar">
      <div class="toolbar-meta">
        <strong>گروه‌های انتخاب مشتری</strong>
        <small>تعریف اصلی گروه‌ها و قیمت‌هایشان در صفحه مدیریت Modifier انجام می‌شود.</small>
      </div>

      <div class="toolbar-actions">
        <SearchableDropdown
          v-model="selectedModifierGroup"
          :options="modifierGroupOptions"
          placeholder="انتخاب گروه مودیفایر"
          search-placeholder="جستجوی گروه..."
          :disabled="disabled"
        />
        <button type="button" class="primary-btn" @click="importGroup" :disabled="disabled || importing || !selectedModifierGroup">
          {{ importing ? 'در حال افزودن...' : 'افزودن گروه' }}
        </button>
      </div>
    </header>

    <p class="error" v-if="importError">{{ importError }}</p>

    <ManagementDataTable :columns="groupColumns" :rows="groupRecords" row-key="group_key">
      <template #cell-group_title="{ row }">
        <div class="group-name-cell">
          <strong>{{ row.group_title || row.modifier_group || row.group_key }}</strong>
          <small>{{ row.modifier_group }}</small>
        </div>
      </template>

      <template #cell-selection_mode="{ value }">
        {{ selectionModeLabel(value) }}
      </template>

      <template #cell-required="{ value }">
        <span :class="['pill', toBool(value) ? 'active' : 'inactive']">
          {{ toBool(value) ? 'اجباری' : 'اختیاری' }}
        </span>
      </template>

      <template #cell-range="{ row }">
        {{ Number(row.min_select || 0).toLocaleString('fa-IR') }} تا {{ Number(row.max_select || 1).toLocaleString('fa-IR') }}
      </template>

      <template #cell-options_count="{ value }">
        {{ Number(value || 0).toLocaleString('fa-IR') }} گزینه
      </template>

      <template #cell-actions="{ row }">
        <div class="row-actions">
          <a
            class="secondary-btn mini"
            :href="`/management/modifier-groups?group=${encodeURIComponent(row.modifier_group || row.group_key || '')}`"
          >
            مدیریت Modifier
          </a>
          <button type="button" class="secondary-btn mini" @click="openGroupOptions(row)" :disabled="disabled">گزینه‌ها</button>
          <button type="button" class="secondary-btn mini danger" @click="removeGroup(row)" :disabled="disabled">حذف گروه</button>
        </div>
      </template>

      <template #empty>هنوز گروهی برای این BOM ثبت نشده است.</template>
    </ManagementDataTable>

    <ManagementPopup v-model:open="groupMetaOpen" title="ویرایش تنظیمات گروه" subtitle="تنظیمات اصلی یک گروه مودیفایر">
      <div class="editor-grid">
        <label class="field span-2">
          <span>گروه مودیفایر</span>
          <SearchableDropdown
            v-model="groupMetaDraft.modifier_group"
            :options="modifierGroupOptions"
            placeholder="انتخاب گروه"
            search-placeholder="جستجوی گروه..."
            :disabled="disabled"
          />
        </label>

        <label class="field">
          <span>عنوان گروه (نمایش)</span>
          <input class="input" v-model="groupMetaDraft.group_title" :disabled="disabled" />
        </label>

        <label class="field">
          <span>حالت انتخاب</span>
          <select class="input" v-model="groupMetaDraft.selection_mode" :disabled="disabled">
            <option value="single">تک انتخاب</option>
            <option value="multi">چند انتخاب</option>
          </select>
        </label>

        <label class="field inline-check">
          <input type="checkbox" v-model="groupMetaDraft.required" :disabled="disabled" />
          <span>اجباری</span>
        </label>

        <label class="field">
          <span>حداقل انتخاب</span>
          <NumericInput v-model="groupMetaDraft.min_select" input-class="input" :disabled="disabled" />
        </label>

        <label class="field">
          <span>حداکثر انتخاب</span>
          <NumericInput v-model="groupMetaDraft.max_select" input-class="input" :disabled="disabled" />
        </label>
      </div>

      <p class="error" v-if="groupMetaError">{{ groupMetaError }}</p>

      <template #footer>
        <div class="popup-actions">
          <button type="button" class="secondary-btn" @click="groupMetaOpen = false">انصراف</button>
          <button type="button" class="primary-btn" @click="saveGroupMeta" :disabled="disabled">ذخیره تنظیمات گروه</button>
        </div>
      </template>
    </ManagementPopup>

    <ManagementPopup
      v-model:open="groupOptionsOpen"
      :title="activeGroupTitle"
      subtitle="گزینه‌های این گروه را اضافه/ویرایش/حذف کنید"
      :close-on-backdrop="false"
    >
      <ManagementEditableTable
        v-if="activeGroupKey"
        v-model="activeGroupRowsProxy"
        title="جدول گزینه‌های گروه"
        subtitle="مدیریت جزئیات هر گزینه"
        tone="accent"
        add-button-label="افزودن گزینه"
        popup-title-add="افزودن گزینه جدید"
        popup-title-edit="ویرایش گزینه"
        save-button-label="ذخیره گزینه"
        :columns="optionColumns"
        :disabled="disabled"
        :create-empty-row="createActiveGroupOptionRow"
        :normalize-row="normalizeOptionRow"
        :validate-row="validateOptionRow"
        empty-text="برای این گروه هنوز گزینه‌ای ثبت نشده است."
      >
        <template #cell-modifier_type="{ value }">
          {{ modifierTypeLabel(value) }}
        </template>

        <template #cell-option_item="{ value }">
          {{ resolveItemLabel(value) }}
        </template>

        <template #cell-price_delta="{ row }">
          <div class="price-cell">
            <strong>{{ formatNumber(row.price_delta) }}</strong>
            <small>{{ row.price_list || 'بدون price list' }}</small>
          </div>
        </template>

        <template #cell-price_status="{ row }">
          <span :class="['chip', priceStatusClass(row.price_status)]">
            {{ priceStatusLabel(row.price_status) }}
          </span>
        </template>

        <template #cell-state="{ row }">
          <div class="flag-chips">
            <span class="chip" v-if="toBool(row.is_default)">پیش‌فرض</span>
            <span class="chip" v-if="toBool(row.is_active, true)">فعال</span>
            <span class="chip warning" v-if="String(row.price_status || 'ok') !== 'ok'">
              نیازمند بررسی
            </span>
          </div>
        </template>

        <template #editor="{ draft }">
          <div class="editor-grid">
            <label class="field span-2">
              <span>عنوان گزینه</span>
              <input class="input" v-model="draft.option_label" />
            </label>

            <label class="field">
              <span>کلید گزینه</span>
              <input class="input" v-model="draft.option_key" placeholder="مثال: extra-cheese" />
            </label>

            <label class="field">
              <span>نوع گزینه</span>
              <select class="input" v-model="draft.modifier_type">
                <option value="add_on">افزودنی</option>
                <option value="replacement">جایگزینی</option>
                <option value="bom_variant">BOM جایگزین</option>
              </select>
            </label>

            <label class="field">
              <span>آیتم گزینه</span>
              <SearchableDropdown
                :model-value="draft.option_item"
                :options="itemOptions"
                allow-item-create
                placeholder="انتخاب آیتم"
                search-placeholder="جستجوی آیتم..."
                @update:model-value="draft.option_item = $event"
              />
            </label>

            <label class="field">
              <span>آیتم قابل جایگزینی</span>
              <SearchableDropdown
                :model-value="draft.replacement_for_item"
                :options="itemOptions"
                allow-item-create
                placeholder="انتخاب آیتم"
                search-placeholder="جستجوی آیتم..."
                @update:model-value="draft.replacement_for_item = $event"
              />
            </label>

            <label class="field">
              <span>BOM جایگزین</span>
              <SearchableDropdown
                :model-value="draft.alternative_bom"
                :options="bomOptions"
                placeholder="انتخاب BOM"
                search-placeholder="جستجوی BOM..."
                @update:model-value="draft.alternative_bom = $event"
              />
            </label>

            <label class="field">
              <span>تعداد گزینه</span>
              <NumericInput v-model="draft.option_qty" input-class="input" />
            </label>

            <div class="field span-2 read-only-price">
              <span>قیمت فروش</span>
              <strong>{{ formatNumber(draft.price_delta) }}</strong>
              <small>
                {{ priceStatusLabel(draft.price_status) }}
                <template v-if="draft.unavailable_reason"> - {{ draft.unavailable_reason }}</template>
              </small>
              <a
                class="secondary-btn mini inline-link"
                :href="`/management/modifier-groups?group=${encodeURIComponent(activeGroupRecord?.modifier_group || activeGroupRecord?.group_key || '')}`"
              >
                ویرایش در مدیریت Modifier
              </a>
            </div>

            <label class="field">
              <span>ضریب دستور</span>
              <NumericInput v-model="draft.recipe_multiplier" input-class="input" />
            </label>

            <label class="field">
              <span>ترتیب</span>
              <NumericInput v-model="draft.sort_order" input-class="input" />
            </label>
          </div>

          <div class="checks-grid">
            <label class="check"><input type="checkbox" v-model="draft.is_default" /> گزینه پیش‌فرض</label>
            <label class="check"><input type="checkbox" v-model="draft.is_active" /> فعال</label>
          </div>
        </template>
      </ManagementEditableTable>

      <template #footer>
        <div class="popup-actions">
          <button type="button" class="secondary-btn" @click="groupOptionsOpen = false">بستن</button>
        </div>
      </template>
    </ManagementPopup>
  </section>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import NumericInput from '@/components/NumericInput.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import ManagementDataTable from '@/components/management/ManagementDataTable.vue'
import ManagementEditableTable from '@/components/management/ManagementEditableTable.vue'
import ManagementPopup from '@/components/management/ManagementPopup.vue'
import { getManagementModifierGroupDetail } from '@/utils/api'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
  modifierGroupOptions: {
    type: Array,
    default: () => [],
  },
  itemOptions: {
    type: Array,
    default: () => [],
  },
  bomOptions: {
    type: Array,
    default: () => [],
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const groupColumns = [
  { key: 'group_title', label: 'گروه' },
  { key: 'selection_mode', label: 'حالت انتخاب' },
  { key: 'required', label: 'الزام' },
  { key: 'range', label: 'محدوده' },
  { key: 'options_count', label: 'تعداد گزینه' },
  { key: 'actions', label: 'عملیات' },
]

const optionColumns = [
  { key: 'option_label', label: 'عنوان گزینه' },
  { key: 'modifier_type', label: 'نوع' },
  { key: 'price_delta', label: 'قیمت فروش' },
  { key: 'price_status', label: 'وضعیت قیمت' },
  { key: 'state', label: 'وضعیت' },
]

const selectedModifierGroup = ref('')
const importError = ref('')
const importing = ref(false)

const groupMetaOpen = ref(false)
const groupMetaError = ref('')
const groupMetaDraft = reactive({
  group_key: '',
  modifier_group: '',
  group_title: '',
  selection_mode: 'single',
  required: false,
  min_select: 0,
  max_select: 1,
})

const groupOptionsOpen = ref(false)
const activeGroupKey = ref('')

const localRows = computed({
  get: () => (Array.isArray(props.modelValue) ? props.modelValue : []),
  set: (next) => emit('update:modelValue', next),
})

const groupRecords = computed(() => {
  const map = new Map()

  for (const rawRow of localRows.value) {
    const row = normalizeOptionRow(rawRow)
    const key = groupKeyOf(row)
    if (!key) {
      continue
    }

    if (!map.has(key)) {
      map.set(key, {
        group_key: key,
        modifier_group: row.modifier_group || key,
        group_title: row.group_title || resolveGroupLabel(row.modifier_group || key),
        selection_mode: row.selection_mode || 'single',
        required: toBool(row.required),
        min_select: Number(row.min_select || 0),
        max_select: Number(row.max_select || 1),
        rows: [],
      })
    }

    map.get(key).rows.push(row)
  }

  const records = Array.from(map.values()).map((record) => ({
    ...record,
    options_count: record.rows.length,
  }))

  return records.sort((left, right) =>
    String(left.group_title || left.group_key).localeCompare(String(right.group_title || right.group_key), 'fa'),
  )
})

const activeGroupRecord = computed(() => groupRecords.value.find((row) => row.group_key === activeGroupKey.value) || null)

const activeGroupTitle = computed(() => {
  if (!activeGroupRecord.value) {
    return 'مدیریت گزینه‌های گروه'
  }
  return `گزینه‌های ${activeGroupRecord.value.group_title || activeGroupRecord.value.modifier_group}`
})

const activeGroupRowsProxy = computed({
  get: () => (activeGroupRecord.value ? activeGroupRecord.value.rows : []),
  set: (nextRows) => {
    if (!activeGroupRecord.value) {
      return
    }
    const prepared = (Array.isArray(nextRows) ? nextRows : []).map((row) =>
      normalizeOptionRow({
        ...row,
        group_key: activeGroupRecord.value.group_key,
        modifier_group: activeGroupRecord.value.modifier_group,
        group_title: activeGroupRecord.value.group_title,
        selection_mode: activeGroupRecord.value.selection_mode,
        required: activeGroupRecord.value.required,
        min_select: activeGroupRecord.value.min_select,
        max_select: activeGroupRecord.value.max_select,
      }),
    )

    if (!prepared.length) {
      prepared.push(createEmptyOptionRow(activeGroupRecord.value))
    }

    replaceGroupRows(activeGroupRecord.value.group_key, prepared)
  },
})

function groupKeyOf(row) {
  return String(row?.group_key || row?.modifier_group || '').trim()
}

function toBool(value, defaultValue = false) {
  if (value === '' || value === null || value === undefined) {
    return defaultValue
  }
  return Number(value) === 1 || value === true
}

function toNumeric(value, fallback = 0) {
  const numeric = Number(value)
  if (Number.isFinite(numeric)) {
    return numeric
  }
  return fallback
}

function resolveGroupLabel(groupName) {
  const normalized = String(groupName || '').trim()
  if (!normalized) {
    return '-'
  }
  const found = (props.modifierGroupOptions || []).find((row) => String(row?.value || '').trim() === normalized)
  if (found?.label) {
    return String(found.label).split(' (')[0] || found.label
  }
  return normalized
}

function resolveItemLabel(itemCode) {
  const normalized = String(itemCode || '').trim()
  if (!normalized) {
    return '-'
  }
  const found = (props.itemOptions || []).find((row) => String(row?.value || '').trim() === normalized)
  return found?.label || normalized
}

function selectionModeLabel(value) {
  const normalized = String(value || '').trim()
  if (normalized === 'multi') {
    return 'چند انتخاب'
  }
  return 'تک انتخاب'
}

function modifierTypeLabel(value) {
  const normalized = String(value || '').trim()
  if (normalized === 'replacement') {
    return 'جایگزینی'
  }
  if (normalized === 'bom_variant') {
    return 'BOM جایگزین'
  }
  return 'افزودنی'
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('fa-IR', { maximumFractionDigits: 2 })
}

function createEmptyOptionRow(groupMeta = {}) {
  const groupKey = String(groupMeta.group_key || groupMeta.modifier_group || '').trim()
  const groupName = String(groupMeta.modifier_group || groupKey).trim()

  return {
    modifier_group: groupName,
    group_key: groupKey || groupName,
    group_title: String(groupMeta.group_title || resolveGroupLabel(groupName)).trim(),
    selection_mode: String(groupMeta.selection_mode || 'single').trim() || 'single',
    required: toBool(groupMeta.required),
    min_select: Math.max(0, Math.floor(toNumeric(groupMeta.min_select, 0))),
    max_select: Math.max(1, Math.floor(toNumeric(groupMeta.max_select, 1))),
    modifier_type: 'add_on',
    option_key: '',
    option_label: '',
    option_item: '',
    replacement_for_item: '',
    alternative_bom: '',
    option_qty: 1,
    price_delta: 0,
    price_status: 'missing_item',
    price_list: '',
    unavailable_reason: '',
    is_selectable: false,
    disabled: true,
    recipe_multiplier: 1,
    is_default: false,
    sort_order: 0,
    is_active: true,
  }
}

function normalizeOptionRow(row) {
  const normalizedGroup = String(row?.modifier_group || row?.group_key || '').trim()
  const normalizedGroupKey = String(row?.group_key || normalizedGroup).trim()
  const normalizedLabel = String(row?.option_label || '').trim()

  return {
    modifier_group: normalizedGroup,
    group_key: normalizedGroupKey || normalizedGroup,
    group_title: String(row?.group_title || resolveGroupLabel(normalizedGroup)).trim(),
    selection_mode: String(row?.selection_mode || 'single').trim() || 'single',
    required: toBool(row?.required),
    min_select: Math.max(0, Math.floor(toNumeric(row?.min_select, 0))),
    max_select: Math.max(1, Math.floor(toNumeric(row?.max_select, 1))),
    modifier_type: String(row?.modifier_type || 'add_on').trim() || 'add_on',
    option_key: String(row?.option_key || normalizedLabel).trim(),
    option_label: normalizedLabel,
    option_item: String(row?.option_item || '').trim(),
    replacement_for_item: String(row?.replacement_for_item || '').trim(),
    alternative_bom: String(row?.alternative_bom || '').trim(),
    option_qty: toNumeric(row?.option_qty, 1),
    price_delta: toNumeric(row?.price_delta, 0),
    price_status: String(row?.price_status || 'ok').trim() || 'ok',
    price_list: String(row?.price_list || '').trim(),
    unavailable_reason: String(row?.unavailable_reason || '').trim(),
    is_selectable: toBool(row?.is_selectable, true),
    disabled: toBool(row?.disabled),
    recipe_multiplier: toNumeric(row?.recipe_multiplier, 1),
    is_default: toBool(row?.is_default),
    sort_order: Math.floor(toNumeric(row?.sort_order, 0)),
    is_active: toBool(row?.is_active, true),
  }
}

function validateOptionRow(row) {
  if (!String(row?.option_label || '').trim() && !String(row?.option_item || '').trim() && !String(row?.alternative_bom || '').trim()) {
    return 'حداقل عنوان گزینه یا آیتم گزینه یا BOM جایگزین را وارد کنید.'
  }
  if (toNumeric(row?.option_qty, 0) <= 0) {
    return 'تعداد گزینه باید بیشتر از صفر باشد.'
  }
  return ''
}

function replaceGroupRows(groupKey, nextGroupRows) {
  const normalizedKey = String(groupKey || '').trim()
  const others = localRows.value.filter((row) => groupKeyOf(row) !== normalizedKey)
  localRows.value = [...others, ...(nextGroupRows || [])]
}

function openGroupMeta(groupRecord) {
  groupMetaError.value = ''
  groupMetaDraft.group_key = String(groupRecord?.group_key || '').trim()
  groupMetaDraft.modifier_group = String(groupRecord?.modifier_group || '').trim()
  groupMetaDraft.group_title = String(groupRecord?.group_title || '').trim()
  groupMetaDraft.selection_mode = String(groupRecord?.selection_mode || 'single').trim() || 'single'
  groupMetaDraft.required = toBool(groupRecord?.required)
  groupMetaDraft.min_select = Number(groupRecord?.min_select || 0)
  groupMetaDraft.max_select = Number(groupRecord?.max_select || 1)
  groupMetaOpen.value = true
}

function saveGroupMeta() {
  const currentKey = String(groupMetaDraft.group_key || '').trim()
  const nextModifierGroup = String(groupMetaDraft.modifier_group || '').trim()
  if (!currentKey || !nextModifierGroup) {
    groupMetaError.value = 'گروه مودیفایر را انتخاب کنید.'
    return
  }

  const sourceRows = localRows.value.filter((row) => groupKeyOf(row) === currentKey)
  const nextRows = sourceRows.map((row) =>
    normalizeOptionRow({
      ...row,
      modifier_group: nextModifierGroup,
      group_key: nextModifierGroup,
      group_title: String(groupMetaDraft.group_title || resolveGroupLabel(nextModifierGroup)).trim(),
      selection_mode: String(groupMetaDraft.selection_mode || 'single').trim() || 'single',
      required: toBool(groupMetaDraft.required),
      min_select: Math.max(0, Math.floor(toNumeric(groupMetaDraft.min_select, 0))),
      max_select: Math.max(1, Math.floor(toNumeric(groupMetaDraft.max_select, 1))),
    }),
  )

  replaceGroupRows(currentKey, nextRows)
  groupMetaOpen.value = false
}

function openGroupOptions(groupRecord) {
  activeGroupKey.value = String(groupRecord?.group_key || '').trim()
  groupOptionsOpen.value = true
}

function removeGroup(groupRecord) {
  const key = String(groupRecord?.group_key || '').trim()
  if (!key) {
    return
  }
  replaceGroupRows(key, [])
}

function createActiveGroupOptionRow() {
  if (!activeGroupRecord.value) {
    return createEmptyOptionRow({})
  }
  return createEmptyOptionRow(activeGroupRecord.value)
}

async function importGroup() {
  const groupName = String(selectedModifierGroup.value || '').trim()
  if (!groupName) {
    return
  }

  importing.value = true
  importError.value = ''
  try {
    const groupDoc = await getManagementModifierGroupDetail(groupName)

    const groupMeta = {
      group_key: String(groupDoc?.name || groupName).trim(),
      modifier_group: String(groupDoc?.name || groupName).trim(),
      group_title: String(groupDoc?.title || resolveGroupLabel(groupName)).trim(),
      selection_mode: String(groupDoc?.selection_mode || 'single').trim() || 'single',
      required: toBool(groupDoc?.required),
      min_select: Math.max(0, Math.floor(toNumeric(groupDoc?.min_select, 0))),
      max_select: Math.max(1, Math.floor(toNumeric(groupDoc?.max_select, 1))),
    }

    const options = Array.isArray(groupDoc?.options) ? groupDoc.options : []
    const preparedRows = []

    if (!options.length) {
      preparedRows.push(createEmptyOptionRow(groupMeta))
    } else {
      for (const option of options) {
        preparedRows.push(
          normalizeOptionRow({
            ...createEmptyOptionRow(groupMeta),
            ...groupMeta,
            modifier_type: String(option?.action_type || 'add_on').trim() || 'add_on',
            option_key: String(option?.option_name || option?.name || '').trim(),
            option_label: String(option?.option_name || option?.label || option?.name || '').trim(),
            option_item: String(option?.option_item || '').trim(),
            alternative_bom: String(option?.alternative_bom || '').trim(),
            option_qty: toNumeric(option?.option_qty, 1),
            price_delta: toNumeric(option?.price_delta, 0),
            price_status: String(option?.price_status || 'ok').trim() || 'ok',
            price_list: String(option?.price_list || '').trim(),
            unavailable_reason: String(option?.unavailable_reason || '').trim(),
            is_selectable: toBool(option?.is_selectable, true),
            disabled: toBool(option?.disabled),
            recipe_multiplier: toNumeric(option?.recipe_multiplier, 1),
            is_default: toBool(option?.is_default),
            sort_order: Math.floor(toNumeric(option?.sort_order, 0)),
            is_active: toBool(option?.is_active, true),
          }),
        )
      }
    }

    replaceGroupRows(groupMeta.group_key, preparedRows)
    selectedModifierGroup.value = ''
    openGroupOptions({ group_key: groupMeta.group_key })
  } catch (groupErr) {
    importError.value = groupErr.message || 'دریافت اطلاعات گروه ناموفق بود.'
  } finally {
    importing.value = false
  }
}

function priceStatusLabel(status = '') {
  const normalized = String(status || '').trim()
  if (normalized === 'missing_price') return 'بدون قیمت'
  if (normalized === 'missing_item') return 'بدون آیتم'
  if (normalized === 'inactive') return 'غیرفعال'
  return 'آماده'
}

function priceStatusClass(status = '') {
  const normalized = String(status || '').trim()
  if (normalized === 'missing_price' || normalized === 'missing_item') return 'warning'
  if (normalized === 'inactive') return 'inactive'
  return 'active'
}
</script>

<style scoped>
.modifier-groups-shell {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 14px;
  background: rgb(var(--palette-eggshell-rgb) / 0.58);
  padding: 0.56rem;
  display: grid;
  gap: 0.5rem;
}

.group-toolbar {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 0.55rem;
}

.toolbar-meta {
  display: grid;
  gap: 0.15rem;
}

.toolbar-meta strong {
  font-size: 0.88rem;
}

.toolbar-meta small {
  color: var(--text-muted);
  font-size: 0.76rem;
  line-height: 1.7;
}

.toolbar-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.toolbar-actions :deep(.searchable-dropdown) {
  min-width: 240px;
}

.group-name-cell {
  display: grid;
  gap: 0.1rem;
}

.group-name-cell strong {
  font-size: 0.79rem;
}

.group-name-cell small {
  color: var(--text-muted);
  font-size: 0.72rem;
}

.row-actions {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.24rem;
}

.mini {
  padding: 0.34rem 0.5rem;
  font-size: 0.7rem;
}

.danger {
  color: var(--danger);
  border-color: rgb(var(--palette-deep-saffron-rgb) / 0.3);
}

.pill {
  border-radius: 999px;
  padding: 0.11rem 0.45rem;
  font-size: 0.69rem;
}

.pill.active {
  background: rgb(var(--palette-june-bud-rgb) / 0.42);
  color: var(--accent-green);
}

.pill.inactive {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.18);
  color: var(--accent-gold);
}

.flag-chips {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.24rem;
}

.chip {
  border-radius: 999px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  color: rgb(var(--palette-deep-sapphire-rgb) / 1);
  font-size: 0.68rem;
  padding: 0.1rem 0.42rem;
}

.chip.warning {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.18);
  color: var(--accent-gold);
}

.price-cell,
.read-only-price {
  display: grid;
  gap: 0.14rem;
}

.price-cell small,
.read-only-price small {
  color: var(--text-muted);
}

.inline-link {
  width: fit-content;
}

.editor-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.42rem;
}

.field {
  display: grid;
  gap: 0.2rem;
}

.field > span {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.field.inline-check {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  margin-top: 1.2rem;
}

.span-2 {
  grid-column: span 2;
}

.checks-grid {
  margin-top: 0.36rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.38rem;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 0.28rem;
  font-size: 0.77rem;
}

.popup-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.4rem;
}

.error {
  margin: 0;
  color: var(--danger);
  font-size: 0.76rem;
}

@media (max-width: 980px) {
  .group-toolbar,
  .toolbar-actions,
  .editor-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
  }

  .toolbar-actions :deep(.searchable-dropdown) {
    min-width: 0;
  }

  .span-2 {
    grid-column: auto;
  }

  .field.inline-check {
    margin-top: 0;
  }
}
</style>
