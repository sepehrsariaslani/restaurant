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
        <span class="chip" v-if="toBool(row.allow_alternative_item)">جایگزین</span>
        <span class="chip" v-if="toBool(row.restaurant_is_required)">اجباری</span>
        <span class="chip" v-if="toBool(row.restaurant_is_editable_qty, false)">تغییر مقدار</span>
      </div>
    </template>

    <template #editor="{ draft }">
      <div class="editor-grid">
        <label class="field span-2">
          <span>آیتم</span>
          <SearchableDropdown
            :model-value="draft.item_code"
            :options="itemOptions"
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

      <div class="checks-grid">
        <label class="check"><input type="checkbox" v-model="draft.allow_alternative_item" /> اجازه استفاده از آیتم جایگزین (allow_alternative_item)</label>
        <label class="check"><input type="checkbox" v-model="draft.show_in_website" /> نمایش در پرینت (show_in_website)</label>
        <label class="check"><input type="checkbox" v-model="draft.restaurant_is_included_by_default" /> پیش فرض در فرمول</label>
        <label class="check"><input type="checkbox" v-model="draft.restaurant_can_remove" /> قابل حذف توسط مشتری</label>
        <label class="check"><input type="checkbox" v-model="draft.restaurant_is_required" /> اجباری</label>
        <label class="check"><input type="checkbox" v-model="draft.restaurant_is_editable_qty" /> قابل تغییر مقدار</label>
      </div>

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
    </template>
  </ManagementEditableTable>
</template>

<script setup>
import { computed } from 'vue'
import NumericInput from '@/components/NumericInput.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
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
  }
}

function normalizeRow(row) {
  return {
    item_code: String(row?.item_code || '').trim(),
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

function setDraftItem(draft, itemCode) {
  const normalized = String(itemCode || '').trim()
  draft.item_code = normalized
  const meta = itemMetaMap.value.get(normalized)
  if (meta && !String(draft.uom || '').trim()) {
    draft.uom = String(meta.stock_uom || '').trim()
  }
}

function resolveItemLabel(value) {
  const key = String(value || '').trim()
  if (!key) {
    return '-'
  }
  const option = (props.itemOptions || []).find((row) => String(row?.value || '').trim() === key)
  if (option?.label) {
    return option.label
  }
  return key
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('fa-IR', { maximumFractionDigits: 4 })
}
</script>

<style scoped>
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
  margin-top: 0.35rem;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.35rem;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 0.28rem;
  font-size: 0.77rem;
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
