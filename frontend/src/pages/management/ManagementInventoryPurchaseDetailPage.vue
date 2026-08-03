<template>
  <InventorySectionShell
    :title="isNew ? 'سفارش خرید جدید' : order?.name || 'جزئیات سفارش خرید'"
    subtitle="اقلام خرید، نرخ‌ها و دریافت مرحله‌ای"
  >
    <template #actions>
      <button type="button" class="secondary-btn" @click="goBack">بازگشت به لیست خرید</button>
    </template>

    <div v-if="loading" class="detail-loading" role="status" aria-live="polite">
      <span class="loading-orb" aria-hidden="true"></span>
      <strong>در حال آماده‌سازی سفارش خرید...</strong>
      <small>اطلاعات سفارش و اقلام در حال دریافت است.</small>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="message" class="success">{{ message }}</p>

    <ManagementSurfaceCard
      v-if="!loading && (isNew || editing)"
      title="فرم سفارش خرید"
      subtitle="مقدار، واحد و نرخ هر قلم را ریزبه‌ریز ثبت کنید."
    >
      <div class="form-grid">
        <label>
          تأمین‌کننده
          <select class="input" v-model="form.supplier">
            <option value="">بدون تأمین‌کننده</option>
            <option v-for="supplier in boot?.suppliers || []" :key="supplier.name" :value="supplier.name">
              {{ supplier.supplier_name || supplier.name }}
            </option>
          </select>
        </label>
        <label>
          انبار مقصد
          <SearchableDropdown
            v-model="form.target_warehouse"
            :options="warehouseOptions"
            placeholder="انتخاب انبار"
            search-placeholder="جستجوی انبار..."
          />
        </label>
        <label>
          تاریخ سفارش
          <PersianDateInput v-model="form.posting_date" />
        </label>
        <label>
          تاریخ تحویل
          <PersianDateInput v-model="form.expected_date" />
        </label>
        <ManagementNoteField
          v-model="form.note"
          class="full"
          label="یادداشت"
          rows="2"
          placeholder="توضیحات تکمیلی سفارش خرید..."
        />
      </div>

      <div class="purchase-lines">
        <header class="purchase-lines-head">
          <div>
            <strong>اقلام خرید</strong>
            <small>{{ qty(form.items.length) }} ردیف</small>
          </div>
          <span>واحد و مقدار هر ردیف قابل ویرایش است.</span>
        </header>

        <div v-for="(line, index) in form.items" :key="index" class="purchase-line">
          <SearchableDropdown
            v-model="line.item_code"
            allow-item-create
            :item-create-defaults="{ opening_warehouse: form.target_warehouse }"
            :options="materialOptions"
            placeholder="انتخاب ماده..."
            search-placeholder="جستجوی ماده..."
            @update:model-value="syncLine(line, $event)"
            @item-created="applyCreatedItem(line, $event)"
          />
          <SearchableDropdown
            v-model="line.uom"
            :options="uomOptions"
            placeholder="واحد"
            search-placeholder="جستجوی واحد..."
          />
          <input
            class="input"
            type="number"
            min="0.001"
            step="0.001"
            v-model.number="line.qty"
            placeholder="مقدار"
          />
          <input
            class="input"
            type="number"
            min="0"
            step="1"
            v-model.number="line.rate"
            placeholder="نرخ واحد"
          />
          <button
            type="button"
            class="tertiary-btn danger"
            @click="removeLine(index)"
            :disabled="form.items.length === 1"
          >
            حذف
          </button>
        </div>

        <button type="button" class="secondary-btn add-line-btn" @click="addLine">
          + افزودن ردیف
        </button>
      </div>

      <footer class="actions">
        <button type="button" class="primary-btn" @click="save" :disabled="saving">
          {{ saving ? 'در حال ذخیره...' : 'ذخیره پیش‌نویس' }}
        </button>
      </footer>
    </ManagementSurfaceCard>

    <template v-else-if="!loading && order">
      <ManagementSurfaceCard title="خلاصه سفارش خرید" subtitle="وضعیت سفارش و دریافت واقعی انبار">
        <div class="detail-meta">
          <div><small>تأمین‌کننده</small><strong>{{ order.supplier_name || '—' }}</strong></div>
          <div><small>وضعیت</small><strong :class="statusClass(order.status)">{{ order.status }}</strong></div>
          <div><small>تاریخ سفارش</small><strong>{{ formatPersianDate(order.posting_date) }}</strong></div>
          <div><small>درصد دریافت</small><strong>{{ qty(order.received_pct) }}٪</strong></div>
          <div><small>مبلغ کل</small><strong>{{ money(order.grand_total) }}</strong></div>
        </div>

        <p v-if="order.note" class="order-note">{{ order.note }}</p>

        <section class="purchase-checklist" aria-label="چک‌لیست خرید اقلام">
          <header class="checklist-head">
            <div>
              <span class="section-kicker">ثبت خرید واقعی</span>
              <h3>چک‌لیست خرید اقلام</h3>
              <p>برای هر ماده مقدار خریدشده و قیمت واقعی را وارد کنید؛ با تیک‌زدن، ورود کالا به انبار نیز ثبت می‌شود.</p>
            </div>
            <label class="checklist-warehouse">
              <span>انبار دریافت</span>
              <SearchableDropdown
                v-model="receiveWarehouse"
                :options="warehouseOptions"
                placeholder="انتخاب انبار"
                search-placeholder="جستجوی انبار..."
              />
            </label>
          </header>

          <div class="checklist-list">
            <article
              v-for="(line, index) in checklist"
              :key="line.item_code + '-' + index"
              class="checklist-row"
              :class="{ complete: isFullyReceived(line) }"
            >
              <div class="checklist-row-head">
                <label class="check-toggle">
                  <input
                    type="checkbox"
                    :checked="isFullyReceived(line)"
                    :disabled="isFullyReceived(line) || receivingIndex === index || line.remaining_qty <= 0"
                    @change="toggleChecklist(index, $event)"
                  />
                  <span class="checkmark" aria-hidden="true">✓</span>
                  <span>{{ isFullyReceived(line) ? 'خرید کامل' : 'خریدم' }}</span>
                </label>
                <div class="checklist-item-name">
                  <strong>{{ line.item_name }}</strong>
                  <small>{{ line.item_code }}</small>
                </div>
                <span class="checklist-status">
                  خریدشده: {{ qty(line.received_qty) }} از {{ qty(line.ordered_qty) }} {{ line.uom || '' }}
                </span>
              </div>

              <div class="checklist-fields">
                <label>
                  مقدار خریدشده
                  <input
                    class="input"
                    type="number"
                    min="0"
                    step="0.001"
                    :max="line.remaining_qty"
                    v-model.number="line.actual_qty"
                    :disabled="isFullyReceived(line) || receivingIndex === index"
                    @input="scheduleProgressSave"
                  />
                </label>
                <label>
                  قیمت واقعی واحد
                  <input
                    class="input"
                    type="number"
                    min="0"
                    step="1"
                    v-model.number="line.rate"
                    :disabled="isFullyReceived(line) || receivingIndex === index"
                    @input="scheduleProgressSave"
                  />
                </label>
                <div class="checklist-amount">
                  <small>مبلغ این خرید</small>
                  <strong>{{ money(Number(line.actual_qty || 0) * Number(line.rate || 0)) }}</strong>
                </div>
                <button
                  type="button"
                  class="primary-btn checklist-save-btn"
                  :disabled="isFullyReceived(line) || receivingIndex === index || Number(line.actual_qty) <= 0 || !receiveWarehouse"
                  @click="receiveChecklistLine(index)"
                >
                  {{ receivingIndex === index ? 'در حال ثبت...' : 'ثبت خرید' }}
                </button>
              </div>
            </article>
          </div>
          <p class="autosave-state" :class="{ saving: progressSaving }">
            <span class="autosave-dot" aria-hidden="true"></span>
            {{ progressState }}
          </p>
        </section>

        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>قلم</th><th>سفارش</th><th>دریافت</th><th>باقی‌مانده</th><th>نرخ</th><th>مبلغ</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="line in order.items" :key="line.idx">
                <td><strong>{{ line.item_name }}</strong><small>{{ line.item_code }}</small></td>
                <td>{{ qty(line.qty) }} {{ line.uom }}</td>
                <td>{{ qty(line.received_qty) }}</td>
                <td :class="line.remaining_qty > 0 ? 'warning' : 'success'">{{ qty(line.remaining_qty) }}</td>
                <td>{{ money(line.rate) }}</td>
                <td>{{ money(line.amount) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <footer class="actions">
          <button v-if="order.status === 'پیش‌نویس'" type="button" class="secondary-btn" @click="editing = true">
            ویرایش اقلام
          </button>
          <button v-if="order.status === 'پیش‌نویس'" type="button" class="primary-btn" @click="changeStatus('ارسال‌شده')">
            ارسال به تأمین‌کننده
          </button>
          <button v-if="['پیش‌نویس', 'ارسال‌شده'].includes(order.status)" type="button" class="tertiary-btn danger" @click="changeStatus('لغوشده')">
            لغو سفارش
          </button>
          <button type="button" class="secondary-btn" @click="print">چاپ فیش</button>
        </footer>
        <p v-if="order.receipts?.length" class="sub">اسناد دریافت: {{ order.receipts.join('، ') }}</p>
      </ManagementSurfaceCard>
    </template>
  </InventorySectionShell>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import InventorySectionShell from '@/components/management/inventory/InventorySectionShell.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementNoteField from '@/components/management/ManagementNoteField.vue'
import PersianDateInput from '@/components/PersianDateInput.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import {
  getManagementInventoryPurchasePrint,
  getManagementPurchaseOrder,
  listManagementRawMaterials,
  listManagementSuppliers,
  listManagementUOMs,
  listManagementWarehouses,
  receiveManagementPurchaseOrder,
  saveManagementPurchaseOrder,
  saveManagementPurchaseOrderProgress,
  updateManagementPurchaseOrderStatus,
} from '@/utils/api'
import { formatMoney } from '@/utils/format'
import { formatPersianDate } from '@/utils/persianDate'

const params = new URLSearchParams(window.location.search)
const orderName = params.get('name') || ''
const isNew = params.get('new') === '1' || !orderName
const order = ref(null)
const boot = ref(null)
const editing = ref(isNew)
const loading = ref(true)
const saving = ref(false)
const receivingIndex = ref(-1)
const progressSaving = ref(false)
const progressState = ref('با تغییر قیمت، اطلاعات به‌صورت خودکار ذخیره می‌شود.')
const error = ref('')
const message = ref('')
const receiveWarehouse = ref('')
const checklist = ref([])
const form = reactive({
  name: '',
  supplier: '',
  target_warehouse: '',
  posting_date: today(),
  expected_date: '',
  note: '',
  items: [newLine()],
})
let progressTimer = null

const materialOptions = computed(() =>
  (boot.value?.materials || []).map((item) => ({
    value: item.name,
    label: `${item.item_name || item.name} (${item.name})`,
  })),
)
const uomOptions = computed(() => (boot.value?.uoms || []).map((value) => ({ value, label: value })))
const warehouseOptions = computed(() =>
  (boot.value?.leaf_warehouses || []).map((value) => ({ value, label: value })),
)

function today() {
  return new Date().toISOString().slice(0, 10)
}

function newLine() {
  return { item_code: '', qty: 1, uom: '', rate: 0 }
}

function qty(value) {
  return Number(value || 0).toLocaleString('fa-IR', { maximumFractionDigits: 3 })
}

function money(value) {
  return formatMoney(Number(value || 0), 'IRR')
}

function statusClass(value) {
  return value === 'دریافت کامل' ? 'success' : value === 'لغوشده' ? 'danger' : 'primary'
}

function goBack() {
  window.location.href = '/management/inventory/purchases'
}

function addLine() {
  form.items.push(newLine())
}

function removeLine(index) {
  if (form.items.length > 1) form.items.splice(index, 1)
}

function syncLine(line, code = line.item_code) {
  line.item_code = code
  const meta = (boot.value?.materials || []).find((item) => item.name === code)
  if (meta) {
    line.uom = line.uom || meta.stock_uom || 'Nos'
    if (!boot.value.uoms.includes(line.uom)) boot.value.uoms.unshift(line.uom)
  }
}

function applyCreatedItem(line, item) {
  line.item_code = item.item_code || item.name
  line.uom = item.stock_uom || line.uom || 'Nos'
  if (boot.value?.materials && !boot.value.materials.some((row) => row.name === line.item_code)) {
    boot.value.materials.unshift({ name: line.item_code, item_name: item.item_name, stock_uom: line.uom })
  }
  if (line.uom && !boot.value.uoms.includes(line.uom)) boot.value.uoms.unshift(line.uom)
}

function buildChecklist(value) {
  checklist.value = (value?.items || []).map((line) => {
    const received = Number(line.received_qty || 0)
    const remaining = Math.max(Number(line.remaining_qty ?? Number(line.qty || 0) - received), 0)
    return {
      item_code: line.item_code,
      item_name: line.item_name || line.item_code,
      uom: line.uom || '',
      ordered_qty: Number(line.qty || 0),
      received_qty: received,
      remaining_qty: remaining,
      actual_qty: remaining,
      rate: Number(line.rate || 0),
    }
  })
}

function apply(value) {
  order.value = value
  editing.value = false
  Object.assign(form, {
    name: value.name,
    supplier: value.supplier || '',
    target_warehouse: value.target_warehouse || '',
    posting_date: value.posting_date || today(),
    expected_date: value.expected_date || '',
    note: value.note || '',
    items: (value.items || []).map((line) => ({ ...line })),
  })
  receiveWarehouse.value = value.target_warehouse || boot.value?.settings?.default_warehouse || boot.value?.leaf_warehouses?.[0] || ''
  buildChecklist(value)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [materialsPayload, supplierPayload, uomPayload, warehousePayload, orderPayload] = await Promise.all([
      listManagementRawMaterials({ limit: 500, include_all_stock: 1, options_only: 1 }),
      listManagementSuppliers({ limit: 500 }),
      listManagementUOMs({ limit: 500 }),
      listManagementWarehouses({ options_only: 1 }),
      isNew ? Promise.resolve(null) : getManagementPurchaseOrder(orderName),
    ])
    const warehouseRows = warehousePayload?.warehouses || []
    const leafWarehouses = warehousePayload?.leaf_warehouses?.length
      ? warehousePayload.leaf_warehouses
      : warehouseRows
          .filter((row) => Number(row?.is_group || 0) !== 1 && Number(row?.disabled || 0) !== 1)
          .map((row) => row.name || row.warehouse_name)
          .filter(Boolean)
    boot.value = {
      materials: materialsPayload?.items || [],
      suppliers: supplierPayload?.suppliers || [],
      uoms: uomPayload?.uoms || [],
      leaf_warehouses: leafWarehouses,
      settings: { default_warehouse: warehousePayload?.default_warehouse || '' },
    }
    if (!form.target_warehouse) form.target_warehouse = boot.value.settings.default_warehouse || leafWarehouses[0] || ''
    if (isNew) {
      receiveWarehouse.value = form.target_warehouse
    } else if (orderPayload?.order) {
      apply(orderPayload.order)
    }
  } catch (err) {
    error.value = err.message || 'دریافت سفارش خرید ناموفق بود.'
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    const items = form.items.filter((line) => line.item_code && Number(line.qty) > 0)
    if (!items.length) throw new Error('حداقل یک قلم معتبر لازم است.')
    const result = await saveManagementPurchaseOrder({ ...form, items })
    window.location.href = `/management/inventory/purchases/detail?name=${encodeURIComponent(result.order.name)}`
  } catch (err) {
    error.value = err.message || 'ذخیره خرید ناموفق بود.'
  } finally {
    saving.value = false
  }
}

function scheduleProgressSave() {
  progressState.value = 'در حال آماده‌سازی ذخیره خودکار...'
  if (progressTimer) window.clearTimeout(progressTimer)
  progressTimer = window.setTimeout(saveProgress, 650)
}

async function saveProgress() {
  if (!order.value || order.value.status === 'لغوشده' || !checklist.value.length) return
  progressSaving.value = true
  progressState.value = 'در حال ذخیره خودکار قیمت‌ها...'
  try {
    const result = await saveManagementPurchaseOrderProgress({
      name: order.value.name,
      lines: checklist.value.map((line) => ({ item_code: line.item_code, rate: Number(line.rate || 0) })),
    })
    syncOrderAfterProgress(result.order)
    progressState.value = 'آخرین تغییرات ذخیره شد.'
  } catch (err) {
    progressState.value = 'ذخیره خودکار ناموفق بود.'
    error.value = err.message || 'ذخیره خودکار قیمت‌ها ناموفق بود.'
  } finally {
    progressSaving.value = false
  }
}

function syncOrderAfterProgress(value) {
  const localActual = Object.fromEntries(checklist.value.map((line) => [line.item_code, line.actual_qty]))
  order.value = value
  checklist.value = (value.items || []).map((line) => {
    const received = Number(line.received_qty || 0)
    const remaining = Math.max(Number(line.qty || 0) - received, 0)
    return {
      item_code: line.item_code,
      item_name: line.item_name || line.item_code,
      uom: line.uom || '',
      ordered_qty: Number(line.qty || 0),
      received_qty: received,
      remaining_qty: remaining,
      actual_qty: Math.min(Number(localActual[line.item_code] ?? remaining), remaining),
      rate: Number(line.rate || 0),
    }
  })
}

function isFullyReceived(line) {
  return Number(line.remaining_qty || 0) <= 0
}

function toggleChecklist(index, event) {
  if (!event.target.checked) {
    event.target.checked = true
    return
  }
  receiveChecklistLine(index)
}

async function receiveChecklistLine(index) {
  const line = checklist.value[index]
  if (!line || isFullyReceived(line) || receivingIndex.value !== -1) return
  const actualQty = Number(line.actual_qty || 0)
  if (actualQty <= 0) {
    error.value = 'مقدار خریدشده را وارد کنید.'
    return
  }
  if (!receiveWarehouse.value) {
    error.value = 'انبار دریافت را انتخاب کنید.'
    return
  }
  receivingIndex.value = index
  error.value = ''
  try {
    const result = await receiveManagementPurchaseOrder({
      name: order.value.name,
      warehouse: receiveWarehouse.value,
      lines: [{ item_code: line.item_code, qty: actualQty, rate: Number(line.rate || 0) }],
    })
    apply(result.order)
    message.value = `خرید «${line.item_name}» ثبت و موجودی انبار به‌روزرسانی شد.`
  } catch (err) {
    error.value = err.message || 'ثبت خرید این قلم ناموفق بود.'
  } finally {
    receivingIndex.value = -1
  }
}

async function changeStatus(status) {
  try {
    const result = await updateManagementPurchaseOrderStatus({ name: order.value.name, status })
    apply(result.order)
    message.value = 'وضعیت سفارش به‌روزرسانی شد.'
  } catch (err) {
    error.value = err.message || 'تغییر وضعیت سفارش ناموفق بود.'
  }
}

async function print() {
  try {
    const payload = await getManagementInventoryPurchasePrint(order.value.name)
    const printWindow = window.open('', '_blank', 'width=420,height=760')
    if (!printWindow) throw new Error('پنجره چاپ باز نشد.')
    printWindow.document.write(`<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>${payload.name}</title></head><body>${payload.html}</body></html>`)
    printWindow.document.close()
    printWindow.focus()
    window.setTimeout(() => printWindow.print(), 300)
  } catch (err) {
    error.value = err.message || 'چاپ ناموفق بود.'
  }
}

onMounted(load)
onBeforeUnmount(() => {
  if (progressTimer) window.clearTimeout(progressTimer)
})
</script>

<style scoped>
.detail-loading {
  display: grid;
  justify-items: center;
  gap: 0.45rem;
  min-height: 220px;
  padding: 3.5rem 1rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 18px;
  background: var(--mg-bg-surface);
  color: var(--mg-text-main);
  text-align: center;
}

.detail-loading small,
.autosave-state,
.sub {
  color: var(--mg-text-muted);
  font-size: 0.74rem;
}

.loading-orb {
  width: 2.2rem;
  height: 2.2rem;
  border: 3px solid color-mix(in srgb, var(--mg-primary) 22%, transparent);
  border-top-color: var(--mg-primary);
  border-radius: 50%;
  animation: purchase-spin 0.8s linear infinite;
}

@keyframes purchase-spin { to { transform: rotate(360deg); } }

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 0.65rem;
}

.form-grid label {
  display: grid;
  gap: 0.25rem;
  font-size: 0.78rem;
  color: var(--mg-text-main);
}

.full { grid-column: 1 / -1; }

.purchase-lines,
.purchase-checklist {
  display: grid;
  gap: 0.65rem;
  margin-top: 1rem;
  padding: 0.85rem;
  border: 1px dashed var(--mg-border);
  border-radius: 16px;
  background: color-mix(in srgb, var(--mg-bg-surface) 88%, var(--mg-bg-page) 12%);
}

.purchase-lines-head,
.checklist-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.7rem;
}

.purchase-lines-head > div,
.checklist-head > div {
  display: grid;
  gap: 0.12rem;
}

.purchase-lines-head small,
.purchase-lines-head > span,
.checklist-head p,
.section-kicker {
  color: var(--mg-text-muted);
  font-size: 0.7rem;
}

.checklist-head h3 {
  margin: 0;
  color: var(--mg-text-main);
  font-size: 0.95rem;
}

.checklist-head p {
  margin: 0.15rem 0 0;
  line-height: 1.65;
}

.section-kicker {
  color: var(--mg-primary);
  font-weight: 800;
}

.purchase-line {
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(110px, 1.2fr) minmax(90px, 1fr) minmax(110px, 1fr) auto;
  gap: 0.45rem;
  align-items: center;
}

.add-line-btn {
  min-height: 38px;
  border-style: dashed;
}

.checklist-warehouse {
  display: grid;
  min-width: 190px;
  gap: 0.25rem;
  color: var(--mg-text-main);
  font-size: 0.73rem;
}

.checklist-list {
  display: grid;
  gap: 0.55rem;
}

.checklist-row {
  display: grid;
  gap: 0.55rem;
  padding: 0.7rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 13px;
  background: color-mix(in srgb, var(--mg-bg-surface) 76%, #ffffff 24%);
}

.checklist-row.complete {
  border-color: color-mix(in srgb, var(--mg-success) 35%, var(--mg-border-light) 65%);
  background: color-mix(in srgb, var(--mg-success-bg) 54%, var(--mg-bg-surface) 46%);
}

.checklist-row-head {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.65rem;
}

.check-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  color: var(--mg-primary);
  font-size: 0.74rem;
  font-weight: 800;
  cursor: pointer;
  white-space: nowrap;
}

.check-toggle input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.checkmark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.4rem;
  height: 1.4rem;
  border: 1.5px solid var(--mg-primary);
  border-radius: 0.45rem;
  color: transparent;
  background: var(--mg-bg-surface);
  transition: all 0.18s ease;
}

.check-toggle input:checked + .checkmark {
  border-color: var(--mg-success);
  background: var(--mg-success);
  color: #fff;
}

.checklist-item-name {
  display: grid;
  min-width: 0;
  gap: 0.12rem;
}

.checklist-item-name strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.checklist-item-name small {
  color: var(--mg-text-muted);
  font-size: 0.68rem;
}

.checklist-status {
  color: var(--mg-text-muted);
  font-size: 0.7rem;
  white-space: nowrap;
}

.checklist-fields {
  display: grid;
  grid-template-columns: minmax(110px, 1fr) minmax(120px, 1fr) minmax(120px, 1fr) auto;
  gap: 0.5rem;
  align-items: end;
}

.checklist-fields label {
  display: grid;
  gap: 0.22rem;
  color: var(--mg-text-muted);
  font-size: 0.68rem;
}

.checklist-amount {
  display: grid;
  gap: 0.18rem;
  min-height: 38px;
  align-content: center;
  padding: 0.35rem 0.5rem;
  border-radius: 9px;
  background: var(--mg-bg-page);
}

.checklist-amount small {
  color: var(--mg-text-muted);
  font-size: 0.65rem;
}

.checklist-amount strong {
  color: var(--mg-success);
  font-size: 0.78rem;
}

.checklist-save-btn {
  min-height: 38px;
  white-space: nowrap;
}

.autosave-state {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  margin: 0;
}

.autosave-state.saving { color: var(--mg-primary); }

.autosave-dot {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 50%;
  background: var(--mg-success);
}

.autosave-state.saving .autosave-dot {
  background: var(--mg-primary);
  animation: purchase-pulse 0.8s ease-in-out infinite alternate;
}

@keyframes purchase-pulse { to { opacity: 0.35; transform: scale(0.7); } }

.detail-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0.55rem;
}

.detail-meta > div {
  display: grid;
  gap: 0.18rem;
  padding: 0.6rem;
  border-radius: 12px;
  background: var(--mg-bg-page);
}

.detail-meta strong { font-size: 0.8rem; }
.success { color: var(--mg-success); }
.danger, .error { color: var(--mg-danger); }
.primary { color: var(--mg-primary); }
.warning { color: var(--mg-danger); }

.order-note {
  margin: 0.9rem 0 0;
  padding: 0.7rem;
  border: 1px solid color-mix(in srgb, var(--mg-primary) 22%, var(--mg-border-light) 78%);
  border-radius: 12px;
  background: color-mix(in srgb, var(--mg-bg-surface) 82%, #ffffff 18%);
  color: var(--mg-text-main);
  white-space: pre-line;
}

.table-wrap { overflow-x: auto; margin-top: 1rem; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th,
.data-table td { padding: 0.5rem; border-bottom: 1px solid var(--mg-border-light); text-align: right; vertical-align: top; white-space: nowrap; }
.data-table td small { display: block; color: var(--mg-text-muted); font-size: 0.67rem; }
.actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem; padding-top: 0.7rem; border-top: 1px solid var(--mg-border-light); }
.sub { display: block; margin-top: 0.5rem; }

@media (max-width: 760px) {
  .purchase-lines-head,
  .checklist-head { flex-direction: column; }
  .checklist-warehouse { width: 100%; min-width: 0; }
  .purchase-line { grid-template-columns: 1fr 1fr; }
  .purchase-line :deep(.searchable-dropdown:first-child),
  .purchase-line :deep(.searchable-dropdown:nth-child(2)),
  .purchase-line .tertiary-btn { grid-column: 1 / -1; }
  .checklist-row-head { grid-template-columns: auto minmax(0, 1fr); }
  .checklist-status { grid-column: 2; }
  .checklist-fields { grid-template-columns: 1fr 1fr; }
  .checklist-amount,
  .checklist-save-btn { grid-column: 1 / -1; }
  .actions > * { flex: 1 1 100%; }
}
</style>
