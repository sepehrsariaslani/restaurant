<template>
  <section class="native-product-panel" dir="rtl">
    <div v-if="loading" class="native-state">در حال دریافت تنظیمات پایه کالا...</div>
    <div v-else>
      <div v-if="visibleSections.length" class="native-section-tabs" role="tablist" aria-label="بخش‌های پایه کالا">
        <button
          v-for="section in visibleSections"
          :key="`native-tab-${section.id}`"
          type="button"
          class="native-section-tab"
          :class="{ active: activeSection === section.id }"
          role="tab"
          :aria-selected="activeSection === section.id"
          @click="activeSection = section.id"
        >
          {{ section.title }}
        </button>
      </div>

      <div v-if="activeSectionConfig" class="native-sections">
      <ManagementSurfaceCard
        :key="activeSectionConfig.id"
        :title="activeSectionConfig.title"
        :subtitle="activeSectionConfig.description"
        class="native-section-card"
      >
        <div v-if="visibleFields(activeSectionConfig).length" class="native-fields-grid">
          <div
            v-for="fieldConfig in visibleFields(activeSectionConfig)"
            :key="fieldConfig.key"
            class="native-field"
            :class="{ 'native-field--check': fieldConfig.type === 'check' }"
          >
            <label v-if="fieldConfig.type === 'check'" class="native-check-field">
              <input
                type="checkbox"
                :checked="Boolean(state.fields[fieldConfig.key])"
                :disabled="fieldConfig.readOnly"
                @change="updateField(fieldConfig.key, $event.target.checked)"
              />
              <span>{{ fieldConfig.label }}</span>
            </label>

            <template v-else>
              <label class="native-field-label">{{ fieldConfig.label }}</label>

              <SearchableDropdown
                v-if="fieldConfig.type === 'link'"
                :model-value="state.fields[fieldConfig.key] || ''"
                :search-fn="query => searchLink(fieldConfig, query)"
                :resolve-fn="value => resolveLink(fieldConfig, value)"
                label-field="label"
                value-field="name"
                :disabled="fieldConfig.readOnly"
                :placeholder="`${fieldConfig.label} را انتخاب کنید`"
                    search-placeholder="جستجو..."
                fixed-panel
                    :create-config="getCreateConfig(fieldConfig.doctype)"
                    @update:modelValue="value => updateField(fieldConfig.key, value)"
              />

              <select
                v-else-if="fieldConfig.type === 'select'"
                class="native-field-input"
                :value="state.fields[fieldConfig.key] ?? ''"
                :disabled="fieldConfig.readOnly"
                @change="updateField(fieldConfig.key, $event.target.value)"
              >
                <option v-for="option in fieldConfig.options || []" :key="option" :value="option">{{ selectOptionLabel(option) }}</option>
              </select>

              <input
                v-else-if="fieldConfig.type === 'number'"
                class="native-field-input native-field-input--number"
                type="number"
                inputmode="decimal"
                :value="state.fields[fieldConfig.key] ?? 0"
                :disabled="fieldConfig.readOnly"
                @input="updateField(fieldConfig.key, numericValue($event.target.value))"
              />

              <textarea
                v-else-if="fieldConfig.type === 'textarea'"
                class="native-field-input native-field-input--textarea"
                rows="2"
                :value="state.fields[fieldConfig.key] || ''"
                :disabled="fieldConfig.readOnly"
                @input="updateField(fieldConfig.key, $event.target.value)"
              />

              <input
                v-else
                class="native-field-input"
                :type="fieldConfig.type === 'date' ? 'date' : 'text'"
                :value="state.fields[fieldConfig.key] || ''"
                :disabled="fieldConfig.readOnly"
                @input="updateField(fieldConfig.key, $event.target.value)"
              />
            </template>
            <small v-if="fieldConfig.suffix" class="native-field-suffix">{{ fieldConfig.suffix }}</small>
          </div>
        </div>

        <div v-for="table in visibleTables(activeSectionConfig)" :key="table.key" class="native-table-block">
          <ManagementEditableTable
            :model-value="state.tables[table.key] || []"
            :columns="table.columns"
            :title="table.title"
            :subtitle="'ردیف‌های متصل به سند مرجع سیستم'"
            :storage-key="`management-product-native-${table.key}`"
            row-key="name"
            max-height="420px"
            :disabled="saving"
            :create-empty-row="() => createEmptyRow(table)"
            @update:modelValue="rows => updateTable(table.key, rows)"
          >
            <template #editor="{ draft }">
              <div class="native-editor-grid">
                <label v-for="column in table.columns" :key="`editor-${table.key}-${column.key}`">
                  <span class="native-field-label">{{ column.label }}</span>
                  <SearchableDropdown
                    v-if="column.fieldtype === 'Link'"
                    :model-value="draft[column.key] || ''"
                    :search-fn="query => searchLink({ doctype: column.options, labelField: linkLabelField(column.options) }, query)"
                    :resolve-fn="value => resolveLink({ doctype: column.options, labelField: linkLabelField(column.options) }, value)"
                    label-field="label"
                    value-field="name"
                    :placeholder="`${column.label} را انتخاب کنید`"
                    search-placeholder="جستجو..."
                    fixed-panel
                    :create-config="getCreateConfig(column.options)"
                    @update:modelValue="value => { draft[column.key] = value }"
                  />
                  <select
                    v-else-if="column.fieldtype === 'Select'"
                    class="native-field-input"
                    v-model="draft[column.key]"
                  >
                    <option v-for="option in selectOptions(column.options)" :key="option" :value="option">{{ selectOptionLabel(option) }}</option>
                  </select>
                  <label v-else-if="column.fieldtype === 'Check'" class="native-check-field">
                    <input type="checkbox" v-model="draft[column.key]" />
                    <span>{{ column.label }}</span>
                  </label>
                  <input
                    v-else
                    class="native-field-input"
                    :type="column.fieldtype === 'Float' || column.fieldtype === 'Currency' ? 'number' : 'text'"
                    v-model="draft[column.key]"
                  />
                </label>
              </div>
            </template>
          </ManagementEditableTable>
        </div>
      </ManagementSurfaceCard>
      </div>
    </div>

    <p v-if="!loading && !visibleSections.length" class="native-state">فیلد پایه قابل نمایشی برای این نسخه پیدا نشد.</p>
    <button v-if="!loading" type="button" class="primary-btn native-save-button" :disabled="saving" @click="$emit('save')">
      {{ saving ? 'در حال ذخیره تنظیمات پایه...' : 'ذخیره تنظیمات پایه کالا' }}
    </button>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { callMethodByPath } from '@/utils/api'
import ManagementEditableTable from '@/components/management/ManagementEditableTable.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import { getSearchableCreateConfig } from '@/utils/managementSearchableCreate'
import {
  nativeFieldSections,
  nativeTableConfigs,
  isNativeFieldVisible,
  isNativeSectionVisible,
  isNativeTableVisible,
} from '@/utils/managementProductNative'

const props = defineProps({
  modelValue: { type: Object, default: () => ({ fields: {}, tables: {} }) },
  loading: { type: Boolean, default: false },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'save'])
const state = computed(() => ({ fields: props.modelValue?.fields || {}, tables: props.modelValue?.tables || {} }))
const visibleSections = computed(() => nativeFieldSections.filter((section) => isNativeSectionVisible(section, state.value)))
const activeSection = ref('classification')
const activeSectionConfig = computed(() => visibleSections.value.find((section) => section.id === activeSection.value) || visibleSections.value[0] || null)

watch(
  visibleSections,
  (sections) => {
    if (!sections.some((section) => section.id === activeSection.value)) {
      activeSection.value = sections[0]?.id || ''
    }
  },
  { immediate: true },
)

function visibleFields(section) {
  return (section.fields || []).filter((fieldConfig) => isNativeFieldVisible(fieldConfig, state.value))
}

function visibleTables(section) {
  return nativeTableConfigs.filter((table) => isNativeTableVisible(table, state.value) && table.section === section.id)
}

function nextState(fields = state.value.fields, tables = state.value.tables) {
  return {
    fields: { ...fields },
    tables: JSON.parse(JSON.stringify(tables || {})),
  }
}

function updateField(key, value) {
  emit('update:modelValue', nextState({ ...state.value.fields, [key]: value }))
}

function updateTable(key, rows) {
  emit('update:modelValue', nextState(state.value.fields, { ...state.value.tables, [key]: rows }))
}

function numericValue(value) {
  if (value === '' || value === null) return 0
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function createEmptyRow(table) {
  return Object.fromEntries((table.columns || []).map((column) => [column.key, column.fieldtype === 'Check' ? false : '']))
}

function selectOptions(value = '') {
  return ['', ...String(value || '').split('\n').map((option) => option.trim()).filter(Boolean)]
}

function getCreateConfig(doctype) {
  return getSearchableCreateConfig(doctype)
}

function selectOptionLabel(value) {
  return ({
    'Item Attribute': 'ویژگی کالا', Manufacturer: 'تولیدکننده', FIFO: 'اولین ورود، اولین خروج',
    'Moving Average': 'میانگین متحرک', LIFO: 'آخرین ورود، اولین خروج', Purchase: 'خرید',
    'Material Transfer': 'انتقال مواد', 'Material Issue': 'خروج مواد', Manufacture: 'تولید',
    'Customer Provided': 'تأمین‌شده توسط مشتری', Transfer: 'انتقال',
  })[value] || value || 'پیش‌فرض سیستم'
}

function linkLabelField(doctype = '') {
  return {
    Item: 'item_name',
    Brand: 'brand_name',
    Customer: 'customer_name',
    Supplier: 'supplier_name',
    Warehouse: 'warehouse_name',
    Company: 'company_name',
    Manufacturer: 'short_name',
  }[doctype] || 'name'
}

async function searchLink(fieldConfig, query = '') {
  const doctype = String(fieldConfig?.doctype || '').trim()
  if (!doctype) return []
  const term = String(query || '').trim()
  try {
    const rows = await callMethodByPath('frappe.desk.search.search_link', {
      doctype,
      txt: term,
      page_length: 30,
      ...(fieldConfig?.searchField ? { searchfield: fieldConfig.searchField } : {}),
    })
    return (Array.isArray(rows) ? rows : []).map((row) => ({
      ...row,
      name: row.name || row.value,
      label: row.label || row.description || row.name || row.value,
      value: row.value || row.name,
    }))
  } catch {
    return []
  }
}

async function resolveLink(fieldConfig, value) {
  const name = String(value || '').trim()
  if (!name) return null
  const rows = await searchLink(fieldConfig, name)
  return rows.find((row) => row.name === name) || { name, label: name }
}
</script>

<style scoped>
.native-product-panel { display: grid; gap: 1rem; }
.native-section-tabs { display: flex; gap: .55rem; overflow-x: auto; padding: .3rem; border: 1px solid var(--mg-border); border-radius: var(--mg-radius-md); background: var(--mg-bg-surface-soft); scrollbar-width: thin; }
.native-section-tab { flex: 0 0 auto; border: 1px solid transparent; border-radius: var(--mg-radius-sm); background: transparent; color: var(--mg-text-muted); padding: .6rem .85rem; font: inherit; font-size: .78rem; font-weight: 800; cursor: pointer; white-space: nowrap; }
.native-section-tab:hover { color: var(--mg-text-main); background: color-mix(in srgb, var(--mg-primary) 7%, transparent); }
.native-section-tab.active { border-color: color-mix(in srgb, var(--mg-primary) 42%, var(--mg-border)); background: color-mix(in srgb, var(--mg-primary) 12%, var(--mg-bg-surface)); color: var(--mg-primary); }
.native-sections { display: grid; gap: 1rem; }
.native-section-card { min-width: 0; }
.native-fields-grid, .native-editor-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .85rem; }
.native-field { position: relative; min-width: 0; }
.native-field--check { display: flex; align-items: end; }
.native-field-label { display: block; margin-bottom: .35rem; color: var(--mg-text-muted); font-size: .76rem; font-weight: 800; }
.native-field-input { width: 100%; min-height: 42px; border: 1px solid var(--mg-border); border-radius: var(--mg-radius-sm); background: var(--mg-bg-surface); color: var(--mg-text-main); padding: .55rem .7rem; outline: none; }
.native-field-input:focus { border-color: var(--mg-primary); box-shadow: 0 0 0 3px color-mix(in srgb, var(--mg-primary) 14%, transparent); }
.native-field-input--number { direction: ltr; text-align: left; }
.native-field-input--textarea { resize: vertical; }
.native-field-suffix { position: absolute; left: .65rem; bottom: .72rem; color: var(--mg-text-muted); font-size: .68rem; }
.native-check-field { width: 100%; min-height: 42px; display: flex; align-items: center; gap: .55rem; border: 1px solid var(--mg-border); border-radius: var(--mg-radius-sm); padding: .55rem .7rem; color: var(--mg-text-main); font-size: .78rem; font-weight: 800; cursor: pointer; }
.native-check-field input { accent-color: var(--mg-primary); }
.native-table-block { min-width: 0; margin-top: .8rem; }
.native-state { padding: 2rem; border: 1px dashed var(--mg-border); border-radius: var(--mg-radius-md); color: var(--mg-text-muted); text-align: center; }
.native-save-button { justify-self: start; }
@media (max-width: 980px) { .native-fields-grid, .native-editor-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 640px) { .native-fields-grid, .native-editor-grid { grid-template-columns: 1fr; } .native-save-button { width: 100%; } }
</style>
