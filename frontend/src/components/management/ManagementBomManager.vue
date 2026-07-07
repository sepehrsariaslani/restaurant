<template>
  <section class="bom-manager">
    <div class="toolbar" v-if="!detailOnly">
      <label v-if="!hasFixedItem" class="field">
        <span>محصول BOM</span>
        <SearchableDropdown
          v-model="selectedItemCode"
          :options="itemSelectOptions"
          placeholder="انتخاب محصول"
          search-placeholder="جستجوی محصول..."
          include-empty-option
          empty-label="همه محصولات"
        />
      </label>

      <label class="field">
        <span>جستجو BOM</span>
        <input ref="searchInputRef" class="input" v-model.trim="searchQuery" placeholder="کد BOM یا نام محصول" @keydown.enter.prevent="loadBoms" />
      </label>

      <div class="toolbar-actions">
        <button type="button" class="secondary-btn" @click="loadBoms" :disabled="loading">
          {{ loading ? 'در حال بارگذاری...' : 'بروزرسانی لیست' }}
        </button>
        <button v-if="!readOnly" type="button" class="primary-btn" @click="handleCreateClick">ایجاد BOM جدید</button>
        <button type="button" class="secondary-btn" @click="shortcutsOpen = true">میانبرها</button>
      </div>
    </div>

    <p class="hint" v-if="hasFixedItem">مدیریت BOM فقط برای محصول {{ fixedItemCode }} فعال است.</p>
    <p class="error" v-if="error">{{ error }}</p>
    <p class="success" v-if="success">{{ success }}</p>

    <ManagementCollectionView v-if="!detailOnly" v-model="viewMode" :modes="viewModes" class="bom-collection">
      <template #list>
        <ManagementListView
          class="desktop-table"
          :columns="columns"
          :rows="boms"
          row-key="name"
          :row-clickable="true"
          @row-click="handleEditClick"
        >
          <template #cell-item="{ row }">{{ row.item_name || row.item || '-' }}</template>
          <template #cell-status="{ row }">
            <div class="status-pills">
              <span :class="['pill', Number(row.is_active) ? 'active' : 'inactive']">
                {{ Number(row.is_active) ? 'فعال' : 'غیرفعال' }}
              </span>
              <span class="pill default" v-if="Number(row.is_default)">پیش فرض</span>
              <span class="pill docstatus" v-if="Number(row.docstatus) === 0">پیش نویس</span>
              <span class="pill docstatus submitted" v-else-if="Number(row.docstatus) === 1">ثبت شده</span>
            </div>
          </template>
          <template #cell-quantity="{ value }">{{ formatQty(value) }}</template>
          <template #cell-modified="{ value }">{{ formatDateTime(value) }}</template>
          <template #cell-actions="{ row }">
            <div class="row-actions">
              <button
                v-if="!readOnly"
                type="button"
                class="secondary-btn mini"
                @click="makeDefault(row)"
                :disabled="saving || Number(row.is_default)"
              >
                پیش فرض
              </button>
              <button
                v-if="!readOnly"
                type="button"
                class="secondary-btn mini"
                @click="submitDraft(row)"
                :disabled="saving || Number(row.docstatus) !== 0"
              >
                ثبت BOM
              </button>
              <a class="secondary-btn mini" :href="`/app/bom/${encodeURIComponent(row.name)}`" target="_blank" rel="noreferrer">ERP</a>
            </div>
          </template>
          <template #empty>برای این فیلتر BOMی پیدا نشد.</template>
        </ManagementListView>

        <ManagementMobileCardList
          class="mobile-cards"
          :rows="boms"
          row-key="name"
          card-class="bom-card"
          empty-text="برای این فیلتر BOMی پیدا نشد."
          :card-clickable="true"
          @card-click="handleEditClick"
        >
          <template #card="{ row }">
            <div class="bom-card__head">
              <div class="bom-card__meta">
                <p class="bom-card__title">{{ row.name || '-' }}</p>
                <p class="bom-card__sub">{{ row.item_name || row.item || '-' }}</p>
              </div>
              <span :class="['pill', Number(row.is_active) ? 'active' : 'inactive']">
                {{ Number(row.is_active) ? 'فعال' : 'غیرفعال' }}
              </span>
            </div>

            <div class="bom-card__totals">
              <p>تعداد: {{ formatQty(row.quantity) }}</p>
              <p>بروزرسانی: {{ formatDateTime(row.modified) }}</p>
            </div>

            <div class="status-pills">
              <span class="pill default" v-if="Number(row.is_default)">پیش فرض</span>
              <span class="pill docstatus" v-if="Number(row.docstatus) === 0">پیش نویس</span>
              <span class="pill docstatus submitted" v-else-if="Number(row.docstatus) === 1">ثبت شده</span>
            </div>

            <div class="row-actions">
              <button
                v-if="!readOnly"
                type="button"
                class="secondary-btn mini"
                @click.stop="makeDefault(row)"
                :disabled="saving || Number(row.is_default)"
              >
                پیش فرض
              </button>
              <button
                v-if="!readOnly"
                type="button"
                class="secondary-btn mini"
                @click.stop="submitDraft(row)"
                :disabled="saving || Number(row.docstatus) !== 0"
              >
                ثبت BOM
              </button>
              <a class="secondary-btn mini" :href="`/app/bom/${encodeURIComponent(row.name)}`" target="_blank" rel="noreferrer">ERP</a>
            </div>
          </template>
        </ManagementMobileCardList>
      </template>

      <template #gallery>
        <ManagementGalleryView
          :rows="boms"
          row-key="name"
          title-field="name"
          subtitle-field="item_name"
          fallback-text="BOM"
          :clickable="true"
          @click-item="handleEditClick"
        >
          <template #caption="{ row }">
            {{ formatQty(row.quantity) }} عدد • {{ formatDateTime(row.modified) }}
          </template>
          <template #overlay="{ row }">
            <span class="gallery-status" :class="Number(row.is_active) ? 'on' : 'off'">
              {{ Number(row.is_active) ? 'فعال' : 'غیرفعال' }}
            </span>
          </template>
          <template #actions="{ row }">
            <div class="row-actions" @click.stop>
              <button
                v-if="!readOnly"
                type="button"
                class="secondary-btn mini"
                @click="makeDefault(row)"
                :disabled="saving || Number(row.is_default)"
              >
                پیش فرض
              </button>
              <button
                v-if="!readOnly"
                type="button"
                class="secondary-btn mini"
                @click="submitDraft(row)"
                :disabled="saving || Number(row.docstatus) !== 0"
              >
                ثبت BOM
              </button>
              <a class="secondary-btn mini" :href="`/app/bom/${encodeURIComponent(row.name)}`" target="_blank" rel="noreferrer">ERP</a>
            </div>
          </template>
        </ManagementGalleryView>
      </template>

      <template #tree>
        <ManagementTreeView
          :nodes="bomTreeNodes"
          empty-text="برای این فیلتر BOMی پیدا نشد."
          :node-clickable="canOpenBomTreeNode"
          @node-click="handleBomTreeNodeClick"
        >
          <template #actions="{ node }">
            <div class="row-actions" v-if="String(node?.key || '').startsWith('bom:')">
              <button
                v-if="!readOnly"
                type="button"
                class="secondary-btn mini"
                @click="makeDefault(node)"
                :disabled="saving || Number(node.is_default)"
              >
                پیش فرض
              </button>
              <button
                v-if="!readOnly"
                type="button"
                class="secondary-btn mini"
                @click="submitDraft(node)"
                :disabled="saving || Number(node.docstatus) !== 0"
              >
                ثبت BOM
              </button>
              <a class="secondary-btn mini" :href="`/app/bom/${encodeURIComponent(node.name)}`" target="_blank" rel="noreferrer">ERP</a>
            </div>
          </template>
        </ManagementTreeView>
      </template>
    </ManagementCollectionView>

    <p class="hint" v-if="detailOnly && loading">در حال بارگذاری جزئیات BOM...</p>

    <section v-if="editorOpen && !readOnly && detailOnly" class="editor-shell">
      <header class="editor-head">
        <div>
          <strong>{{ editorMode === 'create' ? 'ایجاد BOM جدید' : `ویرایش ${form.name}` }}</strong>
          <small class="muted" v-if="Number(form.docstatus) === 1">این BOM ثبت شده است و به صورت مستقیم ویرایش می‌شود.</small>
        </div>
        <div class="editor-head-actions">
          <button type="button" class="secondary-btn" @click="shortcutsOpen = true">میانبرها</button>
          <button type="button" class="secondary-btn" @click="closeEditor">بستن</button>
        </div>
      </header>

      <article class="section-box section-accent">
        <header class="section-head">
          <strong>اطلاعات پایه BOM</strong>
          <small>بخش تنظیمات اصلی فرمول ساخت</small>
        </header>

        <div class="editor-grid">
          <label class="field">
            <span>محصول</span>
            <SearchableDropdown
              v-model="form.item"
              :options="itemSelectOptions"
              placeholder="انتخاب محصول"
              search-placeholder="جستجوی محصول..."
              :disabled="hasFixedItem"
            />
          </label>

          <label class="field">
            <span>مبنای هزینه مواد اولیه (rm_cost_as_per)</span>
            <SearchableDropdown
              v-model="form.rm_cost_as_per"
              :options="rmCostAsPerOptions"
              placeholder="انتخاب مبنا"
              search-placeholder="جستجوی مبنا..."
            />
          </label>

          <label class="field">
            <span>تعداد تولید</span>
            <NumericInput v-model="form.quantity" input-class="input" />
          </label>

          <label class="field">
            <span>شرکت</span>
            <SearchableDropdown
              v-model="form.company"
              :options="companyOptions"
              placeholder="انتخاب شرکت"
              search-placeholder="جستجوی شرکت..."
            />
          </label>

          <label class="field">
            <span>ارز</span>
            <input class="input" v-model="form.currency" />
          </label>
        </div>

        <div class="checks">
          <label class="check"><input type="checkbox" v-model="form.is_active" /> فعال</label>
          <label class="check"><input type="checkbox" v-model="form.is_default" /> پیش فرض محصول</label>
        </div>

        <div class="editor-grid">
          <label class="field">
            <span>کالری BOM</span>
            <NumericInput v-model="form.restaurant_nutrition_kcal" input-class="input" />
          </label>
          <label class="field">
            <span>پروتئین BOM (g)</span>
            <NumericInput v-model="form.restaurant_nutrition_protein_g" input-class="input" />
          </label>
          <label class="field">
            <span>کربوهیدرات BOM (g)</span>
            <NumericInput v-model="form.restaurant_nutrition_carb_g" input-class="input" />
          </label>
          <label class="field">
            <span>قند BOM (g)</span>
            <NumericInput v-model="form.restaurant_nutrition_sugar_g" input-class="input" />
          </label>
          <label class="field">
            <span>چربی BOM (g)</span>
            <NumericInput v-model="form.restaurant_nutrition_fat_g" input-class="input" />
          </label>
        </div>
      </article>

      <ManagementBomItemsTable
        v-model="form.items"
        :item-options="itemSelectOptions"
        :item-catalog="itemCatalog"
      />

      <ManagementBomModifiersTable
        v-model="form.restaurant_modifier_rows"
        :modifier-group-options="modifierGroupOptions"
        :item-options="itemSelectOptions"
        :bom-options="alternativeBomOptions"
      />

      <footer class="editor-actions">
        <button type="button" class="secondary-btn" @click="updateBomCost" :disabled="saving || !form.name">
          {{ saving ? 'در حال بروزرسانی...' : 'بروزرسانی هزینه' }}
        </button>
        <button type="button" class="primary-btn" @click="saveBom(false)" :disabled="saving">
          {{ saving ? 'در حال ذخیره...' : 'ذخیره BOM' }}
        </button>
        <button type="button" class="secondary-btn" @click="saveBom(true)" :disabled="saving">
          ذخیره و ثبت BOM
        </button>
      </footer>
    </section>

    <ManagementPopup
      v-model:open="shortcutsOpen"
      title="میانبرهای کیبورد BOM"
      subtitle="برای سرعت بیشتر در مدیریت BOM از این کلیدها استفاده کنید."
    >
      <ul class="shortcut-list">
        <li><kbd>Ctrl / Cmd + N</kbd><span>ایجاد BOM جدید</span></li>
        <li><kbd>Ctrl / Cmd + K</kbd><span>فوکوس روی جستجو BOM</span></li>
        <li><kbd>Ctrl / Cmd + S</kbd><span>ذخیره BOM</span></li>
        <li><kbd>Ctrl / Cmd + Shift + S</kbd><span>ذخیره و ثبت BOM</span></li>
        <li><kbd>Ctrl / Cmd + Enter</kbd><span>بروزرسانی هزینه BOM</span></li>
        <li><kbd>Ctrl / Cmd + Z</kbd><span>برگشت به تغییر قبلی</span></li>
        <li><kbd>Ctrl / Cmd + Shift + Z</kbd><span>بازگردانی تغییر برگشت‌خورده</span></li>
      </ul>
    </ManagementPopup>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import NumericInput from '@/components/NumericInput.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import ManagementPopup from '@/components/management/ManagementPopup.vue'
import ManagementCollectionView from '@/components/management/ManagementCollectionView.vue'
import ManagementGalleryView from '@/components/management/ManagementGalleryView.vue'
import ManagementBomItemsTable from '@/components/management/ManagementBomItemsTable.vue'
import ManagementBomModifiersTable from '@/components/management/ManagementBomModifiersTable.vue'
import ManagementListView from '@/components/management/ManagementListView.vue'
import ManagementMobileCardList from '@/components/management/ManagementMobileCardList.vue'
import ManagementTreeView from '@/components/management/ManagementTreeView.vue'
import {
  createManagementBom,
  getManagementBomContext,
  getManagementBomDoc,
  listManagementBomItems,
  listManagementBoms,
  listManagementModifierGroups,
  setManagementBomDefault,
  submitManagementBom,
  updateManagementBomCost,
  updateManagementBom,
} from '@/utils/api'

const props = defineProps({
  fixedItemCode: {
    type: String,
    default: '',
  },
  initialItemCode: {
    type: String,
    default: '',
  },
  initialBomName: {
    type: String,
    default: '',
  },
  readOnly: {
    type: Boolean,
    default: false,
  },
  detailOnly: {
    type: Boolean,
    default: false,
  },
})

const detailOnly = computed(() => Boolean(props.detailOnly))
const hasFixedItem = computed(() => Boolean(String(props.fixedItemCode || '').trim()))
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const searchQuery = ref('')
const searchInputRef = ref(null)
const selectedItemCode = ref(String(props.fixedItemCode || props.initialItemCode || '').trim())
const boms = ref([])
const itemCatalog = ref([])
const companies = ref([])
const modifierGroups = ref([])
const shortcutsOpen = ref(false)
const bomContextDefaults = reactive({
  default_company: '',
  default_currency: '',
})
const undoHistory = ref([])
const redoHistory = ref([])
const historyLocked = ref(false)
const editorOpen = ref(false)
const editorMode = ref('create')
const pendingOpenBomName = ref(String(props.initialBomName || '').trim())
const viewMode = ref(readStoredViewMode())

const form = reactive({
  name: '',
  docstatus: 0,
  item: '',
  rm_cost_as_per: 'Valuation Rate',
  quantity: 1,
  company: '',
  currency: '',
  is_active: true,
  is_default: false,
  restaurant_nutrition_kcal: 0,
  restaurant_nutrition_protein_g: 0,
  restaurant_nutrition_carb_g: 0,
  restaurant_nutrition_sugar_g: 0,
  restaurant_nutrition_fat_g: 0,
  items: [],
  restaurant_modifier_rows: [],
})

const columns = [
  { key: 'name', label: 'BOM' },
  { key: 'item', label: 'محصول' },
  { key: 'quantity', label: 'تعداد' },
  { key: 'status', label: 'وضعیت' },
  { key: 'modified', label: 'آخرین بروزرسانی' },
  { key: 'actions', label: 'عملیات' },
]

const viewModes = [
  { value: 'list', label: 'لیست', icon: '≡' },
  { value: 'gallery', label: 'گالری', icon: '▦' },
  { value: 'tree', label: 'درخت', icon: '⋰' },
]

const rmCostAsPerOptions = [
  { value: 'Valuation Rate', label: 'نرخ ارزش‌گذاری (Valuation Rate)' },
  { value: 'Last Purchase Rate', label: 'آخرین نرخ خرید (Last Purchase Rate)' },
  { value: 'Price List', label: 'لیست قیمت (Price List)' },
]

const itemSelectOptions = computed(() =>
  itemCatalog.value.map((row) => ({
    value: row.name || row.item_code,
    label: `${row.item_name || row.item_code || row.name} (${row.item_code || row.name})`,
  })),
)

const companyOptions = computed(() =>
  companies.value.map((row) => ({
    value: row.name,
    label: row.name,
  })),
)

const modifierGroupOptions = computed(() =>
  modifierGroups.value.map((row) => ({
    value: row.name,
    label: `${row.title || row.name} (${row.name})`,
  })),
)

const alternativeBomOptions = computed(() => {
  const seen = new Set()
  const rows = []

  for (const bom of boms.value) {
    const name = String(bom?.name || '').trim()
    if (!name || seen.has(name)) {
      continue
    }
    seen.add(name)
    rows.push({ value: name, label: `${name} (${bom.item_name || bom.item || '-'})` })
  }

  const currentName = String(form.name || '').trim()
  if (currentName && !seen.has(currentName)) {
    rows.unshift({ value: currentName, label: currentName })
  }

  return rows
})

const bomTreeNodes = computed(() => {
  const grouped = new Map()

  for (const row of boms.value || []) {
    const itemCode = String(row?.item || '').trim() || 'بدون محصول'
    const itemLabel = String(row?.item_name || itemCode || '-').trim() || '-'
    const key = `item:${itemCode}`

    if (!grouped.has(key)) {
      grouped.set(key, {
        key,
        label: itemLabel,
        caption: '',
        badge: 'محصول',
        children: [],
      })
    }

    const bucket = grouped.get(key)
    bucket.children.push({
      ...row,
      key: `bom:${row?.name || `${key}-${bucket.children.length}`}`,
      label: String(row?.name || '-').trim(),
      caption: `${formatQty(row?.quantity || 0)} عدد • ${formatDateTime(row?.modified || '')}`,
      badge: Number(row?.is_default || 0) ? 'پیش فرض' : 'BOM',
      status: {
        label: Number(row?.is_active || 0) ? 'فعال' : 'غیرفعال',
        tone: Number(row?.is_active || 0) ? 'success' : 'warning',
      },
      children: [],
    })
    bucket.caption = `${formatQty(bucket.children.length)} BOM`
  }

  return Array.from(grouped.values()).sort((left, right) =>
    String(left?.label || '').localeCompare(String(right?.label || ''), 'fa'),
  )
})

watch(
  () => props.fixedItemCode,
  (next) => {
    selectedItemCode.value = String(next || '').trim()
    loadBoms()
  },
)

watch(
  () => props.initialItemCode,
  (next) => {
    if (hasFixedItem.value) {
      return
    }
    const normalized = String(next || '').trim()
    if (normalized) {
      selectedItemCode.value = normalized
    }
  },
)

watch(
  () => props.initialBomName,
  (next) => {
    pendingOpenBomName.value = String(next || '').trim()
    tryOpenPendingBom()
  },
)

watch(
  () => selectedItemCode.value,
  () => {
    if (hasFixedItem.value) {
      return
    }
    loadBoms()
  },
)

function clearMessages() {
  error.value = ''
  success.value = ''
}

function snapshotFormState() {
  return JSON.stringify({
    name: form.name,
    docstatus: Number(form.docstatus || 0),
    item: form.item,
    rm_cost_as_per: form.rm_cost_as_per,
    quantity: form.quantity,
    company: form.company,
    currency: form.currency,
    is_active: Boolean(form.is_active),
    is_default: Boolean(form.is_default),
    restaurant_nutrition_kcal: form.restaurant_nutrition_kcal,
    restaurant_nutrition_protein_g: form.restaurant_nutrition_protein_g,
    restaurant_nutrition_carb_g: form.restaurant_nutrition_carb_g,
    restaurant_nutrition_sugar_g: form.restaurant_nutrition_sugar_g,
    restaurant_nutrition_fat_g: form.restaurant_nutrition_fat_g,
    items: Array.isArray(form.items) ? form.items : [],
    restaurant_modifier_rows: Array.isArray(form.restaurant_modifier_rows) ? form.restaurant_modifier_rows : [],
  })
}

function applySnapshot(snapshot) {
  if (!snapshot) {
    return
  }
  let payload = null
  try {
    payload = JSON.parse(snapshot)
  } catch (snapshotErr) {
    return
  }
  historyLocked.value = true
  form.name = String(payload?.name || '').trim()
  form.docstatus = Number(payload?.docstatus || 0)
  form.item = String(payload?.item || '').trim()
  form.rm_cost_as_per = String(payload?.rm_cost_as_per || 'Valuation Rate').trim() || 'Valuation Rate'
  form.quantity = Number(payload?.quantity || 1) || 1
  form.company = String(payload?.company || '').trim()
  form.currency = String(payload?.currency || 'IRR').trim() || 'IRR'
  form.is_active = Boolean(payload?.is_active)
  form.is_default = Boolean(payload?.is_default)
  form.restaurant_nutrition_kcal = Number(payload?.restaurant_nutrition_kcal || 0)
  form.restaurant_nutrition_protein_g = Number(payload?.restaurant_nutrition_protein_g || 0)
  form.restaurant_nutrition_carb_g = Number(payload?.restaurant_nutrition_carb_g || 0)
  form.restaurant_nutrition_sugar_g = Number(payload?.restaurant_nutrition_sugar_g || 0)
  form.restaurant_nutrition_fat_g = Number(payload?.restaurant_nutrition_fat_g || 0)
  form.items = Array.isArray(payload?.items) ? payload.items : []
  form.restaurant_modifier_rows = Array.isArray(payload?.restaurant_modifier_rows) ? payload.restaurant_modifier_rows : []
  nextTick(() => {
    historyLocked.value = false
  })
}

function captureHistory(force = false) {
  if (!force && (!editorOpen.value || historyLocked.value)) {
    return
  }
  const snapshot = snapshotFormState()
  const last = undoHistory.value[undoHistory.value.length - 1]
  if (!force && snapshot === last) {
    return
  }
  undoHistory.value.push(snapshot)
  if (undoHistory.value.length > 120) {
    undoHistory.value.shift()
  }
  if (!force) {
    redoHistory.value = []
  }
}

function resetHistory() {
  undoHistory.value = []
  redoHistory.value = []
  captureHistory(true)
}

function undoFormChanges() {
  if (undoHistory.value.length <= 1 || historyLocked.value) {
    return
  }
  const current = undoHistory.value.pop()
  if (current) {
    redoHistory.value.push(current)
  }
  applySnapshot(undoHistory.value[undoHistory.value.length - 1])
  success.value = 'آخرین تغییر با میانبر برگشت داده شد.'
}

function redoFormChanges() {
  if (!redoHistory.value.length || historyLocked.value) {
    return
  }
  const nextSnapshot = redoHistory.value.pop()
  if (!nextSnapshot) {
    return
  }
  undoHistory.value.push(nextSnapshot)
  applySnapshot(nextSnapshot)
  success.value = 'تغییر برگشت‌خورده دوباره اعمال شد.'
}

function focusSearchInput() {
  searchInputRef.value?.focus?.()
  searchInputRef.value?.select?.()
}

function isTypingTarget(target) {
  const tagName = String(target?.tagName || '').toLowerCase()
  return ['input', 'textarea', 'select'].includes(tagName) || Boolean(target?.isContentEditable)
}

function onWindowKeydown(event) {
  const key = String(event?.key || '').toLowerCase()
  const hasModifier = Boolean(event.ctrlKey || event.metaKey)
  if (!hasModifier) {
    return
  }

  if (key === 'k') {
    event.preventDefault()
    focusSearchInput()
    return
  }

  if (key === 'n' && !props.readOnly) {
    event.preventDefault()
    handleCreateClick()
    return
  }

  if (key === 's' && !props.readOnly) {
    event.preventDefault()
    if (editorOpen.value && !saving.value) {
      saveBom(Boolean(event.shiftKey))
    }
    return
  }

  if (key === 'enter' && !props.readOnly) {
    event.preventDefault()
    if (editorOpen.value && form.name && !saving.value) {
      updateBomCost()
    }
    return
  }

  if (key === 'z' && !isTypingTarget(event.target) && editorOpen.value && !props.readOnly) {
    event.preventDefault()
    if (event.shiftKey) {
      redoFormChanges()
    } else {
      undoFormChanges()
    }
    return
  }

  if (key === 'y' && !isTypingTarget(event.target) && editorOpen.value && !props.readOnly) {
    event.preventDefault()
    redoFormChanges()
  }
}

function toBool(value, defaultValue = false) {
  if (value === '' || value === null || value === undefined) {
    return defaultValue
  }
  return Number(value) === 1 || value === true
}

function formatQty(value) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric)) {
    return '0'
  }
  return numeric.toLocaleString('fa-IR', { maximumFractionDigits: 4 })
}

function formatDateTime(value) {
  const raw = String(value || '').trim()
  if (!raw) {
    return '-'
  }
  let normalized = raw
  if (/^\d{4}-\d{2}-\d{2}\s/.test(normalized)) {
    normalized = normalized.replace(' ', 'T')
  }
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(normalized))
  } catch (dateErr) {
    return raw
  }
}

function resolveCompanyCurrency(companyName = '') {
  const normalizedCompany = String(companyName || '').trim()
  const row = companies.value.find((entry) => String(entry?.name || '').trim() === normalizedCompany)
  return String(row?.default_currency || bomContextDefaults.default_currency || '').trim() || 'IRR'
}

function applyCompanyCurrencyDefaults() {
  form.company = String(bomContextDefaults.default_company || companies.value?.[0]?.name || '').trim()
  form.currency = resolveCompanyCurrency(form.company)
}

async function bootstrapContext() {
  const [ctxResult, itemsResult, groupsResult] = await Promise.allSettled([
    getManagementBomContext(),
    listManagementBomItems({ limit: 500 }),
    listManagementModifierGroups({ limit: 500 }),
  ])

  const contextPayload = ctxResult.status === 'fulfilled' ? ctxResult.value : null
  const itemsPayload = itemsResult.status === 'fulfilled' ? itemsResult.value : []
  const groupsPayload = groupsResult.status === 'fulfilled' ? groupsResult.value : []

  companies.value = Array.isArray(contextPayload?.companies) ? contextPayload.companies : []
  itemCatalog.value = Array.isArray(itemsPayload) ? itemsPayload : []
  modifierGroups.value = Array.isArray(groupsPayload) ? groupsPayload : []
  bomContextDefaults.default_company = String(contextPayload?.default_company || companies.value?.[0]?.name || '').trim()
  bomContextDefaults.default_currency =
    String(contextPayload?.default_currency || companies.value.find((row) => row.name === bomContextDefaults.default_company)?.default_currency || '').trim() ||
    'IRR'

  if (!form.company || editorMode.value === 'create') {
    form.company = String(form.company || bomContextDefaults.default_company || companies.value?.[0]?.name || '').trim()
  }
  if (!form.currency || editorMode.value === 'create') {
    form.currency = resolveCompanyCurrency(form.company)
  }
}

async function loadBoms() {
  loading.value = true
  clearMessages()
  try {
    const rows = await listManagementBoms({
      item_code: hasFixedItem.value ? props.fixedItemCode : selectedItemCode.value,
      search: searchQuery.value,
      limit: 180,
    })
    boms.value = rows || []
    tryOpenPendingBom()
  } catch (loadErr) {
    error.value = loadErr.message || 'دریافت BOMها ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function tryOpenPendingBom() {
  const bomName = String(pendingOpenBomName.value || '').trim()
  if (!bomName || saving.value || props.readOnly) {
    return
  }
  pendingOpenBomName.value = ''
  openEdit({ name: bomName })
}

function resetForm() {
  const baseItem = String(hasFixedItem.value ? props.fixedItemCode : selectedItemCode.value || '').trim()
  form.name = ''
  form.docstatus = 0
  form.item = baseItem
  form.rm_cost_as_per = 'Valuation Rate'
  form.quantity = 1
  form.is_active = true
  form.is_default = false
  form.restaurant_nutrition_kcal = 0
  form.restaurant_nutrition_protein_g = 0
  form.restaurant_nutrition_carb_g = 0
  form.restaurant_nutrition_sugar_g = 0
  form.restaurant_nutrition_fat_g = 0
  applyCompanyCurrencyDefaults()
  form.items = []
  form.restaurant_modifier_rows = []
}

function navigateToBomDetail({ item = '', bom = '' } = {}) {
  const params = new URLSearchParams()
  const normalizedItem = String(item || '').trim()
  const normalizedBom = String(bom || '').trim()
  if (normalizedItem) {
    params.set('item', normalizedItem)
  }
  if (normalizedBom) {
    params.set('bom', normalizedBom)
  }
  const query = params.toString()
  const nextUrl = query ? `/management/bom?${query}` : '/management/bom'
  window.location.href = nextUrl
}

function handleCreateClick() {
  if (detailOnly.value) {
    openCreate()
    return
  }
  const itemCode = String(hasFixedItem.value ? props.fixedItemCode : selectedItemCode.value || '').trim()
  navigateToBomDetail({ item: itemCode })
}

function handleEditClick(row) {
  const fallbackItem = hasFixedItem.value ? props.fixedItemCode : selectedItemCode.value
  const itemCode = String(row?.item || fallbackItem || '').trim()
  const bomName = String(row?.name || '').trim()
  if (detailOnly.value) {
    openEdit({ name: bomName })
    return
  }
  navigateToBomDetail({ item: itemCode, bom: bomName })
}

function canOpenBomTreeNode(node) {
  return String(node?.key || '').startsWith('bom:')
}

function handleBomTreeNodeClick(node) {
  if (!canOpenBomTreeNode(node)) {
    return
  }
  handleEditClick(node)
}

function openCreate() {
  clearMessages()
  editorMode.value = 'create'
  resetForm()
  editorOpen.value = true
  resetHistory()
}

async function openEdit(row) {
  const bomName = String(row?.name || '').trim()
  if (!bomName) {
    return
  }

  saving.value = true
  clearMessages()
  try {
    const doc = await getManagementBomDoc(bomName)
    editorMode.value = 'edit'
    form.name = doc.name || bomName
    form.docstatus = Number(doc.docstatus || 0)
    form.item = String(doc.item || '').trim()
    form.rm_cost_as_per = String(doc.rm_cost_as_per || 'Valuation Rate').trim() || 'Valuation Rate'
    form.quantity = Number(doc.quantity || 1) || 1
    form.company = String(doc.company || form.company || '').trim()
    form.currency = String(doc.currency || form.currency || 'IRR').trim()
    form.is_active = toBool(doc.is_active, true)
    form.is_default = toBool(doc.is_default)
    form.restaurant_nutrition_kcal = Number(doc.restaurant_nutrition_kcal || 0)
    form.restaurant_nutrition_protein_g = Number(doc.restaurant_nutrition_protein_g || 0)
    form.restaurant_nutrition_carb_g = Number(doc.restaurant_nutrition_carb_g || 0)
    form.restaurant_nutrition_sugar_g = Number(doc.restaurant_nutrition_sugar_g || 0)
    form.restaurant_nutrition_fat_g = Number(doc.restaurant_nutrition_fat_g || 0)

    form.items = Array.isArray(doc.items)
      ? doc.items.map((itemRow) => ({
          item_code: String(itemRow.item_code || '').trim(),
          qty: Number(itemRow.qty || 0),
          uom: String(itemRow.uom || itemRow.stock_uom || '').trim(),
          rate: Number(itemRow.rate || 0),
          source_warehouse: String(itemRow.source_warehouse || '').trim(),
          allow_alternative_item: toBool(itemRow.allow_alternative_item),
          show_in_website: toBool(itemRow.show_in_website ?? itemRow.show_in_print, true),
          restaurant_customer_label: String(itemRow.restaurant_customer_label || '').trim(),
          restaurant_is_included_by_default: toBool(itemRow.restaurant_is_included_by_default, true),
          restaurant_can_remove: toBool(itemRow.restaurant_can_remove, false),
          restaurant_is_required: toBool(itemRow.restaurant_is_required),
          restaurant_is_editable_qty: toBool(itemRow.restaurant_is_editable_qty, false),
          restaurant_min_multiplier: Number(itemRow.restaurant_min_multiplier || 0),
          restaurant_max_multiplier: Number(itemRow.restaurant_max_multiplier || 3),
          restaurant_step_multiplier: Number(itemRow.restaurant_step_multiplier || 0.5),
          restaurant_multiplier_qty: Number(itemRow.restaurant_multiplier_qty || 0),
          restaurant_extra_when_added: Number(itemRow.restaurant_extra_when_added || 0),
          restaurant_nutrition_kcal: Number(itemRow.restaurant_nutrition_kcal || 0),
          restaurant_nutrition_protein_g: Number(itemRow.restaurant_nutrition_protein_g || 0),
          restaurant_nutrition_carb_g: Number(itemRow.restaurant_nutrition_carb_g || 0),
          restaurant_nutrition_sugar_g: Number(itemRow.restaurant_nutrition_sugar_g || 0),
          restaurant_nutrition_fat_g: Number(itemRow.restaurant_nutrition_fat_g || 0),
          alternatives_count: Number(itemRow.alternatives_count || 0),
          alternatives: Array.isArray(itemRow.alternatives) ? itemRow.alternatives : [],
        }))
      : []

    form.restaurant_modifier_rows = Array.isArray(doc.restaurant_modifier_rows)
      ? doc.restaurant_modifier_rows.map((modifierRow) => ({
          modifier_group: String(modifierRow.modifier_group || '').trim(),
          group_key: String(modifierRow.group_key || modifierRow.modifier_group || '').trim(),
          group_title: String(modifierRow.group_title || '').trim(),
          selection_mode: String(modifierRow.selection_mode || 'single').trim() || 'single',
          required: toBool(modifierRow.required),
          min_select: Number(modifierRow.min_select || 0),
          max_select: Number(modifierRow.max_select || 1),
          modifier_type: String(modifierRow.modifier_type || 'add_on').trim() || 'add_on',
          option_key: String(modifierRow.option_key || '').trim(),
          option_label: String(modifierRow.option_label || '').trim(),
          option_item: String(modifierRow.option_item || '').trim(),
          replacement_for_item: String(modifierRow.replacement_for_item || '').trim(),
          alternative_bom: String(modifierRow.alternative_bom || '').trim(),
          option_qty: Number(modifierRow.option_qty || 1),
          price_delta: Number(modifierRow.price_delta || 0),
          recipe_multiplier: Number(modifierRow.recipe_multiplier || 1),
          is_default: toBool(modifierRow.is_default),
          sort_order: Number(modifierRow.sort_order || 0),
          is_active: toBool(modifierRow.is_active, true),
        }))
      : []

    editorOpen.value = true
    resetHistory()
  } catch (openErr) {
    error.value = openErr.message || 'دریافت اطلاعات BOM ناموفق بود.'
  } finally {
    saving.value = false
  }
}

function closeEditor() {
  editorOpen.value = false
}

function buildPayload() {
  return {
    name: form.name,
    item: form.item,
    rm_cost_as_per: form.rm_cost_as_per || 'Valuation Rate',
    quantity: Number(form.quantity || 1) || 1,
    company: form.company,
    currency: form.currency || 'IRR',
    is_active: form.is_active ? 1 : 0,
    is_default: form.is_default ? 1 : 0,
    restaurant_nutrition_kcal: Number(form.restaurant_nutrition_kcal || 0),
    restaurant_nutrition_protein_g: Number(form.restaurant_nutrition_protein_g || 0),
    restaurant_nutrition_carb_g: Number(form.restaurant_nutrition_carb_g || 0),
    restaurant_nutrition_sugar_g: Number(form.restaurant_nutrition_sugar_g || 0),
    restaurant_nutrition_fat_g: Number(form.restaurant_nutrition_fat_g || 0),
    items: form.items,
    restaurant_modifier_rows: form.restaurant_modifier_rows,
  }
}

async function updateBomCost() {
  const bomName = String(form.name || '').trim()
  if (!bomName) {
    return
  }
  saving.value = true
  clearMessages()
  try {
    await updateManagementBomCost({
      bom_name: bomName,
      rm_cost_as_per: form.rm_cost_as_per || 'Valuation Rate',
    })
    await openEdit({ name: bomName })
    await loadBoms()
    success.value = `هزینه BOM ${bomName} بروزرسانی شد.`
  } catch (updateErr) {
    error.value = updateErr.message || 'بروزرسانی هزینه BOM ناموفق بود.'
  } finally {
    saving.value = false
  }
}

async function saveBom(submitAfterSave = false) {
  if (!form.item) {
    error.value = 'محصول BOM را انتخاب کنید.'
    return
  }

  saving.value = true
  clearMessages()
  try {
    const payload = buildPayload()
    let result = null
    if (editorMode.value === 'create') {
      result = await createManagementBom(payload)
    } else {
      result = await updateManagementBom(payload)
    }

    const bomName = String(result?.name || payload.name || '').trim()
    if (payload.is_default && bomName && payload.item) {
      await setManagementBomDefault({
        bom_name: bomName,
        item_code: payload.item,
      })
    }
    if (submitAfterSave && bomName) {
      await submitManagementBom(bomName)
    }

    await loadBoms()
    if (bomName) {
      const row = boms.value.find((entry) => entry.name === bomName) || { name: bomName }
      await openEdit(row)
    }
    success.value = submitAfterSave ? 'BOM ذخیره و ثبت شد.' : 'BOM با موفقیت ذخیره شد.'
  } catch (saveErr) {
    error.value = saveErr.message || 'ذخیره BOM ناموفق بود.'
  } finally {
    saving.value = false
  }
}

async function makeDefault(row) {
  const bomName = String(row?.name || '').trim()
  const itemCode = String(row?.item || '').trim()
  if (!bomName || !itemCode) {
    return
  }

  saving.value = true
  clearMessages()
  try {
    await setManagementBomDefault({ bom_name: bomName, item_code: itemCode })
    await loadBoms()
    success.value = `BOM ${bomName} به عنوان پیش فرض تنظیم شد.`
  } catch (setErr) {
    error.value = setErr.message || 'تنظیم BOM پیش فرض ناموفق بود.'
  } finally {
    saving.value = false
  }
}

async function submitDraft(row) {
  const bomName = String(row?.name || '').trim()
  if (!bomName) {
    return
  }
  saving.value = true
  clearMessages()
  try {
    await submitManagementBom(bomName)
    await loadBoms()
    success.value = `BOM ${bomName} ثبت شد.`
    if (detailOnly.value) {
      await openEdit({ name: bomName })
    }
  } catch (submitErr) {
    error.value = submitErr.message || 'ثبت BOM ناموفق بود.'
  } finally {
    saving.value = false
  }
}

function readStoredViewMode() {
  try {
    const raw = localStorage.getItem('management-boms-view-mode')
    if (raw === 'grid') {
      return 'gallery'
    }
    if (['list', 'gallery', 'tree'].includes(raw)) {
      return raw
    }
  } catch (storageError) {
    // Ignore storage errors and keep default mode.
  }
  return 'list'
}

watch(
  () => form.company,
  (nextCompany) => {
    const normalizedCompany = String(nextCompany || '').trim()
    if (!normalizedCompany) {
      form.currency = String(bomContextDefaults.default_currency || form.currency || 'IRR').trim() || 'IRR'
      return
    }
    form.currency = resolveCompanyCurrency(normalizedCompany)
  },
)

watch(
  form,
  () => {
    captureHistory()
  },
  { deep: true },
)

watch(
  () => viewMode.value,
  (nextMode) => {
    try {
      localStorage.setItem('management-boms-view-mode', nextMode)
    } catch (storageError) {
      // Ignore storage failures.
    }
  },
)

onMounted(async () => {
  window.addEventListener('keydown', onWindowKeydown)
  resetForm()
  await bootstrapContext()
  await loadBoms()
  if (detailOnly.value) {
    const bomName = String(props.initialBomName || '').trim()
    if (bomName) {
      await openEdit({ name: bomName })
    } else if (!props.readOnly) {
      openCreate()
    }
    return
  }
  tryOpenPendingBom()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onWindowKeydown)
})
</script>

<style scoped>
.bom-manager {
  display: grid;
  gap: 0.65rem;
}

.bom-collection {
  display: grid;
  gap: 0.55rem;
}

.toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto;
  gap: 0.45rem;
  align-items: end;
}

.field {
  display: grid;
  gap: 0.2rem;
  min-width: 0;
}

.field > span {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.toolbar-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.desktop-table {
  display: block;
}

.mobile-cards {
  display: none;
}

.bom-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.55rem;
}

.bom-card__meta {
  min-width: 0;
  flex: 1;
}

.bom-card__title {
  margin: 0;
  font-size: 0.86rem;
  font-weight: 800;
}

.bom-card__sub {
  margin: 0.16rem 0 0;
  font-size: 0.77rem;
  color: var(--text-muted);
}

.bom-card__totals {
  display: grid;
  gap: 0.12rem;
  font-size: 0.79rem;
  color: rgb(16 24 40 / 0.86);
}

.bom-card__totals p {
  margin: 0;
}

.shortcut-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.45rem;
}

.shortcut-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  border-radius: 10px;
  padding: 0.45rem 0.6rem;
}

.shortcut-list kbd {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  border-bottom-width: 2px;
  border-radius: 8px;
  padding: 0.1rem 0.35rem;
  background: rgb(var(--palette-eggshell-rgb) / 0.9);
  font-size: 0.72rem;
  line-height: 1.4;
  color: var(--text-primary);
  direction: ltr;
}

.status-pills {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.pill {
  border-radius: 999px;
  padding: 0.12rem 0.46rem;
  font-size: 0.69rem;
}

.pill.active {
  background: rgb(var(--palette-june-bud-rgb) / 0.44);
  color: var(--accent-green);
}

.pill.inactive {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.17);
  color: var(--accent-gold);
}

.pill.default {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  color: rgb(var(--palette-deep-sapphire-rgb) / 1);
}

.pill.docstatus {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  color: var(--text-muted);
}

.pill.docstatus.submitted {
  background: rgb(var(--palette-june-bud-rgb) / 0.24);
  color: rgb(var(--palette-deep-sapphire-rgb) / 0.9);
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

.gallery-status {
  position: absolute;
  top: 0.45rem;
  inset-inline-start: 0.45rem;
  border-radius: 999px;
  padding: 0.12rem 0.44rem;
  font-size: 0.66rem;
  font-weight: 700;
}

.gallery-status.on {
  background: rgb(var(--palette-june-bud-rgb) / 0.72);
  color: var(--accent-green);
}

.gallery-status.off {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.24);
  color: var(--accent-gold);
}

.editor-shell {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 16px;
  background: rgb(var(--palette-eggshell-rgb) / 0.66);
  padding: 0.6rem;
  display: grid;
  gap: 0.55rem;
}

.editor-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 0.45rem;
}

.editor-head-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.section-box {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 14px;
  background: rgb(var(--palette-eggshell-rgb) / 0.62);
  padding: 0.5rem;
  display: grid;
  gap: 0.45rem;
}

.section-box.section-accent {
  border-color: rgb(var(--palette-deep-saffron-rgb) / 0.35);
  background: linear-gradient(180deg, rgb(var(--palette-deep-saffron-rgb) / 0.06), rgb(var(--palette-eggshell-rgb) / 0.62));
}

.section-head {
  display: grid;
  gap: 0.14rem;
}

.section-head strong {
  font-size: 0.86rem;
}

.section-head small {
  color: var(--text-muted);
  font-size: 0.76rem;
}

.editor-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.45rem;
}

.checks {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.78rem;
}

.editor-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.hint {
  margin: 0;
  font-size: 0.78rem;
  color: var(--text-muted);
}

.error {
  margin: 0;
  color: var(--danger);
}

.success {
  margin: 0;
  color: var(--accent-green);
}

@media (max-width: 1100px) {
  .toolbar,
  .editor-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .toolbar,
  .editor-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .toolbar-actions {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
  }

  .desktop-table {
    display: none;
  }

  .mobile-cards {
    display: block;
  }
}
</style>
