<template>
  <section class="modifier-groups-settings">
    <ManagementSurfaceCard tone="accent">
      <div class="toolbar">
        <input
          class="input"
          v-model.trim="search"
          placeholder="جستجو گروه مودیفایر..."
          @keydown.enter.prevent="loadGroups"
        />
        <ManagementToggleSwitch
          v-model="includeInactive"
          label="نمایش گروه‌های غیرفعال"
          hint="برای بررسی گروه‌هایی که فعلاً در منو استفاده نمی‌شوند."
        />
        <button class="secondary-btn" type="button" @click="createGroup">گروه جدید</button>
        <button class="primary-btn" type="button" @click="loadGroups">
          {{ loading ? 'در حال بارگذاری...' : 'بروزرسانی' }}
        </button>
      </div>
    </ManagementSurfaceCard>

    <p class="error" v-if="error">{{ error }}</p>
    <p class="success-msg" v-if="successMessage">{{ successMessage }}</p>

    <section class="summary-strip" v-if="!loading">
      <article>
        <small>قیمت‌نامه فعال</small>
        <strong>{{ context.default_price_list || '—' }}</strong>
      </article>
      <article>
        <small>کل گروه‌ها</small>
        <strong>{{ groups.length.toLocaleString('fa-IR') }}</strong>
      </article>
      <article>
        <small>دارای ایراد قیمت</small>
        <strong>{{ groupsWithIssues.toLocaleString('fa-IR') }}</strong>
      </article>
      <article>
        <small>گزینه فعال</small>
        <strong>{{ totalActiveOptions.toLocaleString('fa-IR') }}</strong>
      </article>
    </section>

    <div class="workspace">
      <ManagementSurfaceCard class="groups-pane" title="گروه‌های Modifier" subtitle="انتخاب گروه و بررسی وضعیت قیمت‌ها">
        <div class="groups-list" v-if="groups.length">
          <button
            v-for="group in groups"
            :key="group.name"
            type="button"
            class="group-row"
            :class="{ active: selectedGroupName === group.name }"
            @click="selectGroup(group.name)"
          >
            <div class="group-row__meta">
              <strong>{{ group.title || group.name }}</strong>
              <small>{{ formatGroupSummary(group) }}</small>
            </div>
            <div class="group-row__chips">
              <span class="chip danger" v-if="Number(group.has_pricing_issues) === 1">
                {{ Number(group.unresolved_options_count || 0).toLocaleString('fa-IR') }} ایراد
              </span>
              <span class="chip" :class="Number(group.is_active) === 1 ? 'ok' : 'muted'">
                {{ Number(group.is_active) === 1 ? 'فعال' : 'غیرفعال' }}
              </span>
            </div>
          </button>
        </div>
        <p class="muted" v-else-if="!loading">گروهی برای نمایش پیدا نشد.</p>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        class="editor-pane"
        :title="editorTitle"
        :subtitle="context.default_price_list ? `قیمت‌گذاری از ${context.default_price_list}` : 'قیمت‌گذاری از ERPNext Item Price'"
      >
        <template #actions>
          <div class="editor-actions-top" v-if="groupForm.title">
            <a
              v-if="selectedGroupName"
              class="secondary-btn"
              :href="`/app/restaurant-modifier-group/${encodeURIComponent(selectedGroupName)}`"
              target="_blank"
              rel="noreferrer"
            >
              ERP
            </a>
            <button class="secondary-btn" type="button" @click="deleteGroup" :disabled="saving || !selectedGroupName">
              حذف
            </button>
            <button class="primary-btn" type="button" @click="saveGroup" :disabled="saving">
              {{ saving ? 'در حال ذخیره...' : 'ذخیره گروه' }}
            </button>
          </div>
        </template>

        <div class="editor-grid">
          <label class="field span-2">
            <span>عنوان گروه</span>
            <input class="input" v-model.trim="groupForm.title" placeholder="مثال: افزودنی‌های نوشیدنی" />
          </label>

          <label class="field">
            <span>حالت انتخاب</span>
            <select class="input" v-model="groupForm.selection_mode">
              <option value="single">تک انتخاب</option>
              <option value="multi">چند انتخاب</option>
            </select>
          </label>

          <label class="field">
            <span>ترتیب</span>
            <NumericInput v-model="groupForm.sort_order" input-class="input" />
          </label>

          <label class="field">
            <span>حداقل انتخاب</span>
            <NumericInput v-model="groupForm.min_select" input-class="input" />
          </label>

          <label class="field">
            <span>حداکثر انتخاب</span>
            <NumericInput v-model="groupForm.max_select" input-class="input" />
          </label>

          <label class="field span-2">
            <span>توضیحات</span>
            <textarea class="textarea" v-model.trim="groupForm.description" rows="3" />
          </label>
        </div>

        <div class="toggle-row">
          <ManagementToggleSwitch v-model="groupForm.required" label="اجباری" />
          <ManagementToggleSwitch v-model="groupForm.is_active" label="گروه فعال" />
        </div>

        <ManagementEditableTable
          v-model="groupForm.options"
          title="گزینه‌های گروه"
          subtitle="آیتم اختیاری است و برای مصرف یا تولید استفاده می‌شود."
          tone="accent"
          add-button-label="افزودن گزینه"
          popup-title-add="افزودن گزینه Modifier"
          popup-title-edit="ویرایش گزینه Modifier"
          save-button-label="ذخیره گزینه"
          :columns="optionColumns"
          :create-empty-row="createEmptyOption"
          :normalize-row="normalizeOptionDraft"
          :validate-row="validateOptionDraft"
          empty-text="هنوز گزینه‌ای ثبت نشده است."
        >
          <template #cell-option_name="{ row }">
            <div class="option-name-cell">
              <strong>{{ row.option_name || '—' }}</strong>
              <small>{{ row.option_item_name || row.option_item || row.alternative_bom || 'بدون آیتم' }}</small>
            </div>
          </template>

          <template #cell-action_type="{ value }">
            {{ value === 'bom_variant' ? 'BOM جایگزین' : 'افزودنی' }}
          </template>

          <template #cell-price_status="{ row }">
            <span class="chip" :class="priceStatusClass(row.price_status)">
              {{ priceStatusLabel(row.price_status) }}
            </span>
          </template>

          <template #editor="{ draft }">
            <div class="editor-grid">
              <label class="field span-2">
                <span>نام گزینه</span>
                <input class="input" v-model.trim="draft.option_name" placeholder="مثال: شیر بادام" />
              </label>

              <label class="field">
                <span>نوع گزینه</span>
                <select class="input" v-model="draft.action_type">
                  <option value="add_on">افزودنی</option>
                  <option value="bom_variant">BOM جایگزین</option>
                </select>
              </label>

              <label class="field">
                <span>ترتیب</span>
                <NumericInput v-model="draft.sort_order" input-class="input" />
              </label>

              <label class="field" v-if="draft.action_type === 'add_on'">
                <span>آیتم مصرف/تولید</span>
                <SearchableDropdown
                  v-model="draft.option_item"
                  :options="context.item_options || []"
                  placeholder="انتخاب آیتم"
                  search-placeholder="جستجوی آیتم..."
                  no-results-text="آیتمی پیدا نشد"
                  clearable
                />
                <small class="field-note">اگر خالی بماند، سیستم موقع ذخیره یک آیتم خدماتی با نام گزینه می‌سازد.</small>
              </label>

              <label class="field" v-else>
                <span>BOM جایگزین</span>
                <SearchableDropdown
                  v-model="draft.alternative_bom"
                  :options="context.bom_options || []"
                  placeholder="انتخاب BOM"
                  search-placeholder="جستجوی BOM..."
                  no-results-text="BOMی پیدا نشد"
                  clearable
                />
              </label>

              <label class="field">
                <span>مقدار مصرف</span>
                <NumericInput v-model="draft.option_qty" input-class="input" />
              </label>

              <label class="field" v-if="draft.action_type === 'add_on'">
                <span>واحد انتخاب مشتری</span>
                <SearchableDropdown
                  v-model="draft.option_uom"
                  :options="context.uom_options || []"
                  placeholder="انتخاب واحد"
                  search-placeholder="جستجوی واحد..."
                  no-results-text="واحدی پیدا نشد"
                  clearable
                />
              </label>

              <label class="field">
                <span>حداقل مقدار</span>
                <NumericInput v-model="draft.min_qty" input-class="input" />
              </label>

              <label class="field">
                <span>حداکثر مقدار</span>
                <NumericInput v-model="draft.max_qty" input-class="input" />
              </label>

              <label class="field">
                <span>گام تغییر</span>
                <NumericInput v-model="draft.qty_step" input-class="input" />
              </label>

              <label class="field">
                <span>ضریب دستور</span>
                <NumericInput v-model="draft.recipe_multiplier" input-class="input" />
              </label>
            </div>

            <div class="toggle-grid">
              <ManagementToggleSwitch
                v-model="draft.is_default"
                label="انتخاب پیش‌فرض"
                hint="اگر کاربر چیزی انتخاب نکند، این گزینه از قبل انتخاب شده باشد."
              />
              <ManagementToggleSwitch
                v-model="draft.is_active"
                label="فعال برای مشتری"
                hint="اگر خاموش باشد، این گزینه در سایت و منو به مشتری نمایش داده نمی‌شود."
              />
            </div>
          </template>
        </ManagementEditableTable>
      </ManagementSurfaceCard>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import NumericInput from '@/components/NumericInput.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import ManagementEditableTable from '@/components/management/ManagementEditableTable.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementToggleSwitch from '@/components/management/ManagementToggleSwitch.vue'
import {
  deleteManagementModifierGroup,
  getManagementModifierGroupDetail,
  getManagementModifierGroupsContext,
  listManagementModifierGroupsOverview,
  saveManagementModifierGroup,
} from '@/utils/api'

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const successMessage = ref('')
const search = ref('')
const includeInactive = ref(true)
const groups = ref([])
const selectedGroupName = ref('')
const context = reactive({
  default_price_list: '',
  price_lists: [],
  item_options: [],
  bom_options: [],
  uom_options: [],
  action_type_options: [],
})

const groupForm = reactive(createEmptyGroupDraft())

const optionColumns = [
  { key: 'option_name', label: 'گزینه' },
  { key: 'action_type', label: 'نوع' },
  { key: 'price_status', label: 'وضعیت قیمت' },
]

const groupsWithIssues = computed(() =>
  groups.value.filter((row) => Number(row.has_pricing_issues || 0) === 1).length,
)

const totalActiveOptions = computed(() =>
  groups.value.reduce((sum, row) => sum + Number(row.active_options_count || 0), 0),
)

const editorTitle = computed(() =>
  groupForm.title ? `ویرایش ${groupForm.title}` : 'گروه Modifier جدید',
)

function createEmptyGroupDraft() {
  return {
    name: '',
    title: '',
    selection_mode: 'single',
    required: false,
    min_select: 0,
    max_select: 1,
    description: '',
    sort_order: 0,
    is_active: true,
    options: [],
  }
}

function createEmptyOption() {
  return {
    option_name: '',
    action_type: 'add_on',
    option_item: '',
    option_item_name: '',
    alternative_bom: '',
    option_qty: 1,
    option_uom: '',
    stock_uom: '',
    min_qty: 0,
    max_qty: 4,
    qty_step: 1,
    recipe_multiplier: 1,
    sort_order: 0,
    is_default: false,
    is_active: true,
    price_delta: 0,
    base_price: 0,
    unit_rate: 0,
    conversion_factor: 1,
    price_status: 'missing_item',
    price_list: context.default_price_list || '',
    unavailable_reason: '',
  }
}

function resetGroupForm(next = createEmptyGroupDraft()) {
  Object.assign(groupForm, createEmptyGroupDraft(), {
    ...next,
    required: Number(next?.required || 0) === 1 || next?.required === true,
    is_active: Number(next?.is_active ?? 1) === 1 || next?.is_active === true,
    options: (next?.options || []).map((row) => normalizeOptionDraft(row)),
  })
}

function normalizeOptionDraft(row = {}) {
  return {
    ...createEmptyOption(),
    ...row,
    option_name: String(row?.option_name || row?.name || '').trim(),
    action_type: String(row?.action_type || 'add_on').trim() || 'add_on',
    option_item: String(row?.option_item || '').trim(),
    option_item_name: String(row?.option_item_name || '').trim(),
    alternative_bom: String(row?.alternative_bom || '').trim(),
    option_qty: Number(row?.option_qty || 1) || 1,
    option_uom: String(row?.option_uom || '').trim(),
    stock_uom: String(row?.stock_uom || '').trim(),
    min_qty: Number(row?.min_qty ?? 0) || 0,
    max_qty: Number(row?.max_qty ?? 4) || 4,
    qty_step: Number(row?.qty_step || row?.option_qty || 1) || 1,
    recipe_multiplier: Number(row?.recipe_multiplier || 1) || 1,
    sort_order: Number(row?.sort_order || 0) || 0,
    is_default: Number(row?.is_default || 0) === 1 || row?.is_default === true,
    is_active: Number(row?.is_active ?? 1) === 1 || row?.is_active === true,
    price_delta: Number(row?.price_delta || 0) || 0,
    base_price: Number(row?.base_price || row?.price_delta || 0) || 0,
    unit_rate: Number(row?.unit_rate || 0) || 0,
    conversion_factor: Number(row?.conversion_factor || 1) || 1,
    price_status: String(row?.price_status || 'ok').trim() || 'ok',
    price_list: String(row?.price_list || context.default_price_list || '').trim(),
    unavailable_reason: String(row?.unavailable_reason || '').trim(),
  }
}

function validateOptionDraft(row = {}) {
  if (!String(row?.option_name || '').trim()) {
    return 'نام گزینه الزامی است.'
  }
  if (String(row?.action_type || '') === 'bom_variant' && !String(row?.alternative_bom || '').trim()) {
    return 'برای BOM Variant باید BOM جایگزین انتخاب شود.'
  }
  if (Number(row?.option_qty || 0) <= 0) {
    return 'مقدار مصرف باید بیشتر از صفر باشد.'
  }
  if (Number(row?.qty_step || 0) <= 0) {
    return 'گام تغییر باید بیشتر از صفر باشد.'
  }
  return ''
}

function formatGroupSummary(group) {
  const count = Number(group.options_count || 0).toLocaleString('fa-IR')
  const mode = String(group.selection_mode || 'single') === 'multi' ? 'چندانتخاب' : 'تک‌انتخاب'
  return `${count} گزینه • ${mode}`
}

function priceStatusLabel(status = '') {
  const normalized = String(status || '').trim()
  if (normalized === 'missing_price') return 'بدون قیمت'
  if (normalized === 'missing_item') return 'بدون آیتم'
  if (normalized === 'missing_conversion') return 'بدون تبدیل واحد'
  if (normalized === 'inactive') return 'غیرفعال'
  return 'آماده'
}

function priceStatusClass(status = '') {
  const normalized = String(status || '').trim()
  if (normalized === 'missing_price' || normalized === 'missing_item' || normalized === 'missing_conversion') return 'danger'
  if (normalized === 'inactive') return 'muted'
  return 'ok'
}

async function loadContext() {
  const payload = await getManagementModifierGroupsContext()
  Object.assign(context, payload || {})
}

async function loadGroups(preferredName = '') {
  loading.value = true
  error.value = ''
  try {
    const payload = await listManagementModifierGroupsOverview({
      search: search.value,
      include_inactive: includeInactive.value ? 1 : 0,
    })
    groups.value = Array.isArray(payload?.groups) ? payload.groups : []
    if (payload?.default_price_list) {
      context.default_price_list = payload.default_price_list
    }
    const targetName =
      String(preferredName || selectedGroupName.value || '').trim() ||
      String(new URLSearchParams(window.location.search).get('group') || '').trim()
    if (targetName && groups.value.some((row) => row.name === targetName)) {
      await selectGroup(targetName)
    } else if (!selectedGroupName.value && groups.value[0]?.name) {
      await selectGroup(groups.value[0].name)
    } else if (!groups.value.length) {
      createGroup()
    }
  } catch (loadErr) {
    error.value = loadErr.message || 'دریافت لیست گروه‌های modifier ناموفق بود.'
  } finally {
    loading.value = false
  }
}

async function selectGroup(groupName = '') {
  const normalized = String(groupName || '').trim()
  if (!normalized) {
    return
  }
  error.value = ''
  selectedGroupName.value = normalized
  try {
    const detail = await getManagementModifierGroupDetail(normalized)
    resetGroupForm(detail)
    syncUrlGroup(normalized)
  } catch (detailErr) {
    error.value = detailErr.message || 'دریافت جزئیات گروه ناموفق بود.'
  }
}

function createGroup() {
  selectedGroupName.value = ''
  resetGroupForm({
    ...createEmptyGroupDraft(),
    options: [createEmptyOption()],
  })
  syncUrlGroup('')
}

function syncUrlGroup(groupName = '') {
  try {
    const url = new URL(window.location.href)
    if (groupName) {
      url.searchParams.set('group', groupName)
    } else {
      url.searchParams.delete('group')
    }
    window.history.replaceState({}, '', url.toString())
  } catch (syncErr) {
    // noop
  }
}

async function saveGroup() {
  saving.value = true
  error.value = ''
  successMessage.value = ''
  try {
    const payload = {
      name: String(groupForm.name || '').trim(),
      title: String(groupForm.title || '').trim(),
      selection_mode: String(groupForm.selection_mode || 'single').trim() || 'single',
      required: groupForm.required ? 1 : 0,
      min_select: Number(groupForm.min_select || 0) || 0,
      max_select: Math.max(Number(groupForm.max_select || 1) || 1, 1),
      description: String(groupForm.description || '').trim(),
      sort_order: Number(groupForm.sort_order || 0) || 0,
      is_active: groupForm.is_active ? 1 : 0,
      options: (groupForm.options || []).map((row) => ({
        option_name: String(row.option_name || '').trim(),
        action_type: String(row.action_type || 'add_on').trim() || 'add_on',
        option_item: String(row.option_item || '').trim(),
        alternative_bom: String(row.alternative_bom || '').trim(),
        option_qty: Number(row.option_qty || 1) || 1,
        option_uom: String(row.option_uom || '').trim(),
        min_qty: Number(row.min_qty ?? 0) || 0,
        max_qty: Number(row.max_qty ?? 4) || 4,
        qty_step: Number(row.qty_step || row.option_qty || 1) || 1,
        recipe_multiplier: Number(row.recipe_multiplier || 1) || 1,
        is_default: row.is_default ? 1 : 0,
        sort_order: Number(row.sort_order || 0) || 0,
        is_active: row.is_active ? 1 : 0,
      })),
    }
    const saved = await saveManagementModifierGroup(payload)
    successMessage.value = 'گروه modifier ذخیره شد.'
    resetGroupForm(saved)
    selectedGroupName.value = String(saved?.name || '').trim()
    await loadGroups(selectedGroupName.value)
  } catch (saveErr) {
    error.value = saveErr.message || 'ذخیره گروه modifier ناموفق بود.'
  } finally {
    saving.value = false
  }
}

async function deleteGroup() {
  if (!selectedGroupName.value) {
    return
  }
  if (!window.confirm('این گروه modifier حذف شود؟')) {
    return
  }
  saving.value = true
  error.value = ''
  successMessage.value = ''
  try {
    await deleteManagementModifierGroup(selectedGroupName.value)
    successMessage.value = 'گروه modifier حذف شد.'
    const deletedName = selectedGroupName.value
    createGroup()
    await loadGroups()
    if (selectedGroupName.value === deletedName) {
      selectedGroupName.value = ''
    }
  } catch (deleteErr) {
    error.value = deleteErr.message || 'حذف گروه modifier ناموفق بود.'
  } finally {
    saving.value = false
  }
}

watch(includeInactive, () => {
  loadGroups(selectedGroupName.value)
})

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    await loadContext()
    await loadGroups()
  } catch (mountErr) {
    error.value = mountErr.message || 'آماده‌سازی مدیریت modifier ناموفق بود.'
    loading.value = false
  }
})
</script>

<style scoped>
.modifier-groups-settings {
  display: grid;
  gap: 0.9rem;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  align-items: center;
}

.toolbar .input {
  flex: 1 1 18rem;
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.7rem;
}

.summary-strip article {
  border: 1px solid var(--border-soft, rgba(120, 92, 62, 0.16));
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.78);
  padding: 0.85rem 1rem;
  display: grid;
  gap: 0.16rem;
}

.summary-strip small {
  color: var(--muted, var(--mg-text-muted));
}

.summary-strip strong {
  font-size: 0.95rem;
}

.workspace {
  display: grid;
  grid-template-columns: minmax(18rem, 22rem) minmax(0, 1fr);
  gap: 0.9rem;
  align-items: start;
}

.groups-list {
  display: grid;
  gap: 0.45rem;
}

.group-row {
  width: 100%;
  border: 1px solid var(--border-soft, rgba(120, 92, 62, 0.16));
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.72);
  padding: 0.8rem 0.9rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  text-align: right;
}

.group-row.active {
  border-color: rgba(120, 82, 52, 0.44);
  background: rgba(255, 251, 245, 0.98);
}

.group-row__meta {
  display: grid;
  gap: 0.14rem;
}

.group-row__meta small,
.option-name-cell small,
.price-cell small {
  color: var(--muted, var(--mg-text-muted));
}

.group-row__chips {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  justify-content: end;
}

.chip {
  border-radius: 999px;
  padding: 0.24rem 0.55rem;
  font-size: 0.72rem;
  border: 1px solid rgba(120, 92, 62, 0.14);
  background: rgba(255, 255, 255, 0.85);
}

.chip.ok {
  color: var(--mg-success);
  background: rgba(220, 252, 231, 0.8);
}

.chip.danger {
  color: #9a3412;
  background: rgba(255, 237, 213, 0.92);
}

.chip.muted {
  color: var(--mg-text-muted);
  background: rgba(243, 244, 246, 0.92);
}

.editor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.field {
  display: grid;
  gap: 0.32rem;
}

.field span {
  font-size: 0.78rem;
  color: var(--muted, var(--mg-text-muted));
}

.field-note {
  font-size: 0.72rem;
  color: var(--muted, var(--mg-text-muted));
  line-height: 1.7;
}

.field.span-2 {
  grid-column: span 2;
}

.textarea {
  min-height: 5.5rem;
}

.toggle-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.9rem;
  margin: 0.9rem 0;
}

.toggle-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 0.9rem;
}

.option-name-cell,
.price-cell {
  display: grid;
  gap: 0.14rem;
}

.price-editor {
  margin-top: 0.9rem;
  padding: 0.8rem;
  border: 1px dashed rgba(120, 92, 62, 0.22);
  border-radius: 14px;
  background: rgba(255, 250, 244, 0.82);
  display: grid;
  gap: 0.7rem;
}

.price-editor__meta {
  display: grid;
  gap: 0.16rem;
}

.price-editor__meta small {
  color: var(--muted, var(--mg-text-muted));
}

.price-editor__stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.55rem;
}

.price-editor__stats article {
  border-radius: 12px;
  border: 1px solid rgba(120, 92, 62, 0.14);
  background: rgba(255, 255, 255, 0.84);
  padding: 0.65rem 0.7rem;
  display: grid;
  gap: 0.18rem;
}

.price-editor__stats small {
  color: var(--muted, var(--mg-text-muted));
}

.editor-actions-top {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

@media (max-width: 1100px) {
  .workspace {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .summary-strip,
  .editor-grid,
  .toggle-grid,
  .price-editor__stats {
    grid-template-columns: 1fr;
  }

  .field.span-2 {
    grid-column: auto;
  }
}
</style>
