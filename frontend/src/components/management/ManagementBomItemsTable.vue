<template>
  <ManagementEditableTable
    v-model="localRows"
    title="جدول آیتم های BOM"
    subtitle="افزودن/ویرایش آیتم ها از طریق پنجره Pop-up"
    tone="accent"
    add-button-label="افزودن آیتم"
    popup-title-add="افزودن آیتم BOM"
    popup-title-edit="ویرایش آیتم BOM"
    :columns="columns"
    :disabled="disabled"
    :create-empty-row="createEmptyRow"
    :normalize-row="normalizeRow"
    :validate-row="validateRow"
    empty-text="هنوز آیتمی برای BOM ثبت نشده است."
  >
    <template #cell-item_code="{ value }">
      {{ resolveItemLabel(value) }}
    </template>

    <template #cell-qty="{ value }">
      {{ formatNumber(value) }}
    </template>

    <template #cell-rate="{ value }">
      {{ formatNumber(value) }}
    </template>

    <template #cell-show_in_website="{ row }">
      <span :class="['visibility-chip', toBool(row.show_in_website, true) ? 'is-on' : 'is-off']">
        {{ toBool(row.show_in_website, true) ? 'نمایش در پرینت' : 'عدم نمایش در پرینت' }}
      </span>
    </template>

    <template #cell-nutrition="{ row }">
      <div class="nutrition-chips">
        <span class="chip" v-if="toNumeric(row.restaurant_nutrition_kcal, 0) > 0">Kcal {{ formatNumber(row.restaurant_nutrition_kcal) }}</span>
        <span class="chip" v-if="toNumeric(row.restaurant_nutrition_sugar_g, 0) > 0">Sugar {{ formatNumber(row.restaurant_nutrition_sugar_g) }}g</span>
      </div>
    </template>

    <template #cell-flags="{ row }">
      <div class="flag-chips">
        <span :class="['chip', toBool(row.show_in_website, true) ? '' : 'chip-muted']">
          {{ toBool(row.show_in_website, true) ? 'پرینت' : 'عدم نمایش در پرینت' }}
        </span>
        <span class="chip" v-if="toBool(row.allow_alternative_item)">
          {{ toNumeric(row.alternatives_count, 0) > 0 ? `جایگزین ${formatNumber(row.alternatives_count)}` : 'جایگزینی ماده' }}
        </span>
        <span class="chip" v-if="toBool(row.restaurant_is_required)">اجباری</span>
        <span class="chip" v-if="toBool(row.restaurant_is_editable_qty, false)">تغییر مقدار</span>
      </div>
    </template>

    <template #editor="{ draft }">
      <div class="editor-shell">
        <div class="editor-grid">
          <label class="field span-2">
            <span>آیتم</span>
            <SearchableDropdown
              :model-value="draft.item_code"
              :options="resolvedItemOptions"
              placeholder="انتخاب آیتم"
              search-placeholder="جستجوی آیتم..."
              @update:model-value="setDraftItem(draft, $event)"
            />
          </label>

          <label class="field">
            <span>نام نمایشی مشتری</span>
            <input class="input" v-model="draft.restaurant_customer_label" />
          </label>

          <label class="field">
            <span>واحد</span>
            <input class="input" v-model="draft.uom" />
          </label>

          <label class="field">
            <span>مقدار</span>
            <NumericInput v-model="draft.qty" input-class="input" />
          </label>

          <label class="field">
            <span>نرخ</span>
            <NumericInput v-model="draft.rate" input-class="input" />
          </label>

          <label class="field span-2">
            <span>انبار مبدا</span>
            <input class="input" v-model="draft.source_warehouse" />
          </label>
        </div>

        <div
          v-if="String(draft.item_code || '').trim()"
          class="selected-item-summary"
        >
          <strong>{{ resolveDraftItemLabel(draft) }}</strong>
          <small>{{ String(draft.item_code || '').trim() }}</small>
        </div>

        <section class="editor-section">
          <header class="editor-section__head">
            <strong>تنظیمات نمایش و سفارشی‌سازی</strong>
            <small>رفتار این ماده داخل فرمول و برای مشتری را مشخص کنید.</small>
          </header>

          <div class="checks-grid">
            <ManagementCheckboxField
              v-model="draft.allow_alternative_item"
              label="اجازه جایگزینی ماده اولیه"
              hint="اگر در ERP جایگزین تعریف شده باشد، مشتری می‌تواند آن را انتخاب کند."
              compact
            />
            <ManagementCheckboxField
              v-model="draft.show_in_website"
              label="نمایش در پرینت"
              hint="این ردیف در چاپ و نمایش رسپی دیده شود."
              compact
            />
            <ManagementCheckboxField
              v-model="draft.restaurant_is_included_by_default"
              label="پیش‌فرض در فرمول"
              hint="این ماده در حالت پایه محصول حضور داشته باشد."
              compact
            />
            <ManagementCheckboxField
              v-model="draft.restaurant_can_remove"
              label="قابل حذف توسط مشتری"
              hint="مشتری بتواند این ماده را از سفارش حذف کند."
              compact
            />
            <ManagementCheckboxField
              v-model="draft.restaurant_is_required"
              label="اجباری"
              hint="این ماده همیشه باید در محصول بماند."
              compact
            />
            <ManagementCheckboxField
              v-model="draft.restaurant_is_editable_qty"
              label="قابل تغییر مقدار"
              hint="مقدار این ماده برای مشتری یا فرمول قابل تنظیم باشد."
              compact
            />
          </div>
        </section>

        <div class="alt-summary" v-if="toBool(draft.allow_alternative_item)">
          <template v-if="toNumeric(draft.alternatives_count, 0) > 0">
            <p class="alt-summary__title">جایگزین‌های ثبت‌شده در ERP</p>
            <div class="alt-summary__chips">
              <span class="chip" v-for="option in normalizeAlternatives(draft.alternatives)" :key="option.alternative_item">
                {{ option.item_name || option.alternative_item }}
              </span>
            </div>
            <a
              v-if="String(draft.item_code || '').trim()"
              class="alt-summary__link"
              :href="`/app/item/${encodeURIComponent(String(draft.item_code || '').trim())}`"
              target="_blank"
              rel="noreferrer"
            >
              مدیریت جایگزین‌ها در ERP
            </a>
          </template>
          <p v-else class="alt-summary__warning">
            این ماده اجازه جایگزینی دارد ولی هنوز هیچ Item Alternative برای آن ثبت نشده است.
          </p>
        </div>

        <section class="editor-section">
          <header class="editor-section__head">
            <strong>قواعد مقدار و هزینه</strong>
            <small>محدوده تغییر و هزینه اضافه این ماده را مشخص کنید.</small>
          </header>

          <div class="editor-grid compact">
            <label class="field">
              <span>حداقل ضریب</span>
              <NumericInput v-model="draft.restaurant_min_multiplier" input-class="input" />
            </label>
            <label class="field">
              <span>حداکثر ضریب</span>
              <NumericInput v-model="draft.restaurant_max_multiplier" input-class="input" />
            </label>
            <label class="field">
              <span>گام تغییر ضریب</span>
              <NumericInput v-model="draft.restaurant_step_multiplier" input-class="input" />
            </label>
            <label class="field">
              <span>مقدار ضریب</span>
              <NumericInput v-model="draft.restaurant_multiplier_qty" input-class="input" />
            </label>
            <label class="field">
              <span>هزینه اضافه</span>
              <NumericInput v-model="draft.restaurant_extra_when_added" input-class="input" />
            </label>
          </div>
        </section>

        <section class="editor-section">
          <header class="editor-section__head">
            <strong>ارزش غذایی</strong>
            <small>اگر داده دقیق داری این بخش را پر کن، وگرنه می‌تواند خالی بماند.</small>
          </header>

          <div class="editor-grid compact">
            <label class="field">
              <span>کالری</span>
              <NumericInput v-model="draft.restaurant_nutrition_kcal" input-class="input" />
            </label>
            <label class="field">
              <span>پروتئین (g)</span>
              <NumericInput v-model="draft.restaurant_nutrition_protein_g" input-class="input" />
            </label>
            <label class="field">
              <span>کربوهیدرات (g)</span>
              <NumericInput v-model="draft.restaurant_nutrition_carb_g" input-class="input" />
            </label>
            <label class="field">
              <span>قند (g)</span>
              <NumericInput v-model="draft.restaurant_nutrition_sugar_g" input-class="input" />
            </label>
            <label class="field">
              <span>چربی (g)</span>
              <NumericInput v-model="draft.restaurant_nutrition_fat_g" input-class="input" />
            </label>
          </div>
        </section>
      </div>
    </template>
  </ManagementEditableTable>
</template>

<script setup>
import { computed } from 'vue'
import NumericInput from '@/components/NumericInput.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import ManagementCheckboxField from '@/components/management/ManagementCheckboxField.vue'
import ManagementEditableTable from '@/components/management/ManagementEditableTable.vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
  itemOptions: {
    type: Array,
    default: () => [],
  },
  itemCatalog: {
    type: Array,
    default: () => [],
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const columns = [
  { key: 'item_code', label: 'آیتم' },
  { key: 'restaurant_customer_label', label: 'نام نمایشی' },
  { key: 'qty', label: 'مقدار' },
  { key: 'show_in_website', label: 'نمایش در پرینت' },
  { key: 'uom', label: 'واحد' },
  { key: 'rate', label: 'نرخ' },
  { key: 'nutrition', label: 'تغذیه' },
  { key: 'flags', label: 'ویژگی ها' },
]

const localRows = computed({
  get: () => (Array.isArray(props.modelValue) ? props.modelValue : []),
  set: (next) => emit('update:modelValue', next),
})

const itemMetaMap = computed(() => {
  const map = new Map()
  for (const row of props.itemCatalog || []) {
    const keys = [row?.name, row?.item_code]
      .map((value) => String(value || '').trim())
      .filter(Boolean)
    for (const key of keys) {
      map.set(key, row)
    }
  }
  return map
})

const resolvedItemOptions = computed(() => {
  const map = new Map()

  for (const option of props.itemOptions || []) {
    const value = String(option?.value || '').trim()
    if (!value) {
      continue
    }
    map.set(value, {
      value,
      label: String(option?.label || value).trim() || value,
      stock_uom: String(option?.stock_uom || '').trim(),
    })
  }

  for (const row of props.modelValue || []) {
    const itemCode = String(row?.item_code || '').trim()
    if (!itemCode) {
      continue
    }
    const itemName = String(
      row?.item_name ||
      itemMetaMap.value.get(itemCode)?.item_name ||
      row?.restaurant_customer_label ||
      itemCode,
    ).trim()
    if (!map.has(itemCode)) {
      map.set(itemCode, {
        value: itemCode,
        label: itemName && itemName !== itemCode ? `${itemName} (${itemCode})` : itemCode,
        stock_uom: String(row?.uom || row?.stock_uom || '').trim(),
      })
    }
  }

  return [...map.values()]
})

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

function createEmptyRow() {
  return {
    item_code: '',
    item_name: '',
    qty: 1,
    uom: '',
    rate: 0,
    source_warehouse: '',
    allow_alternative_item: false,
    show_in_website: true,
    restaurant_customer_label: '',
    restaurant_is_included_by_default: true,
    restaurant_can_remove: false,
    restaurant_is_required: false,
    restaurant_is_editable_qty: false,
    restaurant_min_multiplier: 0,
    restaurant_max_multiplier: 3,
    restaurant_step_multiplier: 0.5,
    restaurant_multiplier_qty: 0,
    restaurant_extra_when_added: 0,
    restaurant_nutrition_kcal: 0,
    restaurant_nutrition_protein_g: 0,
    restaurant_nutrition_carb_g: 0,
    restaurant_nutrition_sugar_g: 0,
    restaurant_nutrition_fat_g: 0,
    alternatives_count: 0,
    alternatives: [],
  }
}

function normalizeRow(row) {
  return {
    item_code: String(row?.item_code || '').trim(),
    item_name: String(
      row?.item_name ||
      itemMetaMap.value.get(String(row?.item_code || '').trim())?.item_name ||
      '',
    ).trim(),
    qty: toNumeric(row?.qty, 1),
    uom: String(row?.uom || '').trim(),
    rate: toNumeric(row?.rate, 0),
    source_warehouse: String(row?.source_warehouse || '').trim(),
    allow_alternative_item: toBool(row?.allow_alternative_item),
    show_in_website: toBool(row?.show_in_website ?? row?.show_in_print, true),
    restaurant_customer_label: String(row?.restaurant_customer_label || '').trim(),
    restaurant_is_included_by_default: toBool(row?.restaurant_is_included_by_default, true),
    restaurant_can_remove: toBool(row?.restaurant_can_remove, false),
    restaurant_is_required: toBool(row?.restaurant_is_required),
    restaurant_is_editable_qty: toBool(row?.restaurant_is_editable_qty, false),
    restaurant_min_multiplier: toNumeric(row?.restaurant_min_multiplier, 0),
    restaurant_max_multiplier: toNumeric(row?.restaurant_max_multiplier, 3),
    restaurant_step_multiplier: toNumeric(row?.restaurant_step_multiplier, 0.5),
    restaurant_multiplier_qty: toNumeric(row?.restaurant_multiplier_qty, 0),
    restaurant_extra_when_added: toNumeric(row?.restaurant_extra_when_added, 0),
    restaurant_nutrition_kcal: toNumeric(row?.restaurant_nutrition_kcal, 0),
    restaurant_nutrition_protein_g: toNumeric(row?.restaurant_nutrition_protein_g, 0),
    restaurant_nutrition_carb_g: toNumeric(row?.restaurant_nutrition_carb_g, 0),
    restaurant_nutrition_sugar_g: toNumeric(row?.restaurant_nutrition_sugar_g, 0),
    restaurant_nutrition_fat_g: toNumeric(row?.restaurant_nutrition_fat_g, 0),
    alternatives_count: toNumeric(row?.alternatives_count, 0),
    alternatives: normalizeAlternatives(row?.alternatives),
  }
}

function validateRow(row) {
  const itemCode = String(row?.item_code || '').trim()
  if (!itemCode) {
    return 'لطفا آیتم را انتخاب کنید.'
  }
  if (toNumeric(row?.qty, 0) <= 0) {
    return 'مقدار باید بیشتر از صفر باشد.'
  }
  if (!String(row?.uom || '').trim()) {
    return 'واحد را وارد کنید.'
  }
  return ''
}

function normalizeAlternatives(value) {
  if (!Array.isArray(value)) return []
  return value
    .map((row) => ({
      alternative_item: String(row?.alternative_item || '').trim(),
      item_name: String(row?.item_name || '').trim(),
      stock_uom: String(row?.stock_uom || '').trim(),
    }))
    .filter((row) => row.alternative_item)
}

function setDraftItem(draft, itemCode) {
  const normalized = String(itemCode || '').trim()
  draft.item_code = normalized
  const meta = itemMetaMap.value.get(normalized)
  if (meta) {
    draft.item_name = String(meta.item_name || meta.name || normalized).trim()
  }
  if (meta && !String(draft.uom || '').trim()) {
    draft.uom = String(meta.stock_uom || '').trim()
  }
}

function resolveItemLabel(value) {
  const key = String(value || '').trim()
  if (!key) {
    return '-'
  }
  const option = resolvedItemOptions.value.find((row) => String(row?.value || '').trim() === key)
  if (option?.label) {
    return option.label
  }
  return key
}

function resolveDraftItemLabel(draft) {
  const itemCode = String(draft?.item_code || '').trim()
  if (!itemCode) {
    return 'آیتم انتخاب نشده'
  }
  const explicit = String(draft?.item_name || '').trim()
  if (explicit) {
    return explicit
  }
  const option = resolvedItemOptions.value.find((row) => String(row?.value || '').trim() === itemCode)
  if (option?.label) {
    return option.label
  }
  const meta = itemMetaMap.value.get(itemCode)
  return String(meta?.item_name || itemCode).trim()
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('fa-IR', { maximumFractionDigits: 4 })
}
</script>

<style scoped>
.editor-shell {
  display: grid;
  gap: 0.7rem;
}

.editor-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.42rem;
}

.editor-grid.compact {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.field {
  display: grid;
  gap: 0.2rem;
}

.field > span {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.span-2 {
  grid-column: span 2;
}

.checks-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem;
}

.selected-item-summary {
  display: inline-grid;
  gap: 0.1rem;
  padding: 0.65rem 0.8rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 139 94 52) / 0.14);
  border-radius: 12px;
  background: rgb(var(--palette-eggshell-rgb, 251 248 244) / 0.72);
}

.selected-item-summary strong {
  font-size: 0.84rem;
}

.selected-item-summary small {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.editor-section {
  display: grid;
  gap: 0.55rem;
}

.editor-section__head {
  display: grid;
  gap: 0.12rem;
}

.editor-section__head strong {
  font-size: 0.82rem;
}

.editor-section__head small {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.alt-summary {
  margin-top: 0.45rem;
  padding: 0.7rem 0.8rem;
  border-radius: 14px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.14);
  background: rgb(var(--palette-eggshell-rgb, 251 248 244) / 0.72);
  display: grid;
  gap: 0.4rem;
}

.alt-summary__title,
.alt-summary__warning {
  margin: 0;
  font-size: 0.78rem;
  color: var(--text-muted);
}

.alt-summary__warning {
  color: var(--warning, #9a6700);
}

.alt-summary__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.alt-summary__link {
  width: fit-content;
  font-size: 0.76rem;
  color: var(--accent-brown, #6f4a31);
  text-decoration: none;
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

.chip-muted {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.06);
  color: rgb(var(--palette-deep-sapphire-rgb) / 0.74);
}

.visibility-chip {
  border-radius: 999px;
  padding: 0.1rem 0.42rem;
  font-size: 0.68rem;
  line-height: 1.5;
  display: inline-flex;
  align-items: center;
  border: 1px solid transparent;
}

.visibility-chip.is-on {
  color: rgb(var(--success-rgb) / 1);
  background: rgb(var(--success-rgb) / 0.14);
  border-color: rgb(var(--success-rgb) / 0.3);
}

.visibility-chip.is-off {
  color: rgb(var(--danger-rgb) / 0.96);
  background: rgb(var(--danger-rgb) / 0.12);
  border-color: rgb(var(--danger-rgb) / 0.3);
}

.nutrition-chips {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.24rem;
}

@media (max-width: 920px) {
  .editor-grid,
  .editor-grid.compact,
  .checks-grid {
    grid-template-columns: 1fr;
  }

  .span-2 {
    grid-column: auto;
  }
}
</style>
