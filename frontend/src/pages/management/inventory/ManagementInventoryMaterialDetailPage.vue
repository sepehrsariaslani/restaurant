<template>
  <InventorySectionShell :title="isNew ? 'ماده اولیه جدید' : detail?.item_name || 'جزئیات ماده اولیه'" subtitle="اطلاعات پایه، واحد، نرخ خرید، نقطه سفارش و گردش اخیر">
    <template #actions>
      <button type="button" class="secondary-btn" @click="goBack">بازگشت به لیست</button>
      <button v-if="detail && !isNew" type="button" class="secondary-btn" @click="load">بروزرسانی</button>
    </template>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="message" class="success">{{ message }}</p>
    <ManagementSurfaceCard title="اطلاعات ماده اولیه">
      <div v-if="loading" class="muted">در حال دریافت جزئیات...</div>
      <template v-else>
        <div class="detail-kpis" v-if="detail">
          <article><small>موجودی کل</small><strong>{{ qty(detail.qty) }} {{ detail.stock_uom }}</strong></article>
          <article><small>ارزش موجودی</small><strong>{{ money(detail.value) }}</strong></article>
          <article><small>نرخ خرید</small><strong>{{ money(form.purchase_rate) }}</strong></article>
        </div>
        <div class="form-grid">
          <label>کد کالا
            <input class="input" v-model.trim="form.item_code" :disabled="!isNew" placeholder="کد ماده" />
          </label>
          <label>نام ماده اولیه <span class="req">*</span>
            <input class="input" v-model.trim="form.item_name" placeholder="مثلاً پنیر موزارلا" />
          </label>
          <label>گروه کالا
            <select class="input" v-model="form.item_group">
              <option v-for="group in boot?.item_groups || []" :key="group.name" :value="group.name">{{ group.name }}</option>
            </select>
          </label>
          <label>واحد اندازه‌گیری
            <input class="input" v-model.trim="form.stock_uom" placeholder="Kg / Gram / Nos" />
          </label>
          <label>نرخ خرید
            <input class="input" type="number" min="0" v-model.number="form.purchase_rate" />
          </label>
          <label>تأمین‌کننده پیش‌فرض
            <select class="input" v-model="form.default_supplier">
              <option value="">بدون تأمین‌کننده</option>
              <option v-for="supplier in boot?.suppliers || []" :key="supplier.name" :value="supplier.name">{{ supplier.supplier_name || supplier.name }}</option>
            </select>
          </label>
          <label class="check"><input type="checkbox" v-model="form.disabled" /> غیرفعال</label>
        </div>
        <section class="reorder-section">
          <header><div><h4>نقطه سفارش</h4><p>برای هر انبار حداقل موجودی و مقدار پیشنهادی خرید را ثبت کنید.</p></div><button type="button" class="secondary-btn" @click="form.reorder_levels.push({ warehouse: '', level: 0, request_qty: 0 })">+ افزودن</button></header>
          <div v-for="(row, index) in form.reorder_levels" :key="index" class="reorder-row">
            <select class="input" v-model="row.warehouse"><option value="">انبار</option><option v-for="warehouse in boot?.leaf_warehouses || []" :key="warehouse" :value="warehouse">{{ warehouse }}</option></select>
            <input class="input" type="number" min="0" step="0.001" v-model.number="row.level" placeholder="حداقل" />
            <input class="input" type="number" min="0" step="0.001" v-model.number="row.request_qty" placeholder="پیشنهاد خرید" />
            <button type="button" class="tertiary-btn danger" @click="form.reorder_levels.splice(index, 1)">حذف</button>
          </div>
        </section>
        <footer class="detail-actions"><button type="button" class="primary-btn" @click="save" :disabled="saving">{{ saving ? 'در حال ذخیره...' : 'ذخیره تغییرات' }}</button></footer>
      </template>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard v-if="detail && !isNew" title="گردش اخیر" subtitle="آخرین ورودها، خروج‌ها و اسناد مرتبط">
      <InventoryResponsiveList :columns="movementColumns" :rows="detail.movements || []" row-key="voucher" :row-clickable="false" empty-text="گردشی ثبت نشده است.">
        <template #cell-qty_change="{ row }"><span :class="row.qty_change >= 0 ? 'success' : 'error'">{{ row.qty_change >= 0 ? '+' : '' }}{{ qty(row.qty_change) }} {{ row.stock_uom }}</span></template>
        <template #card="{ row }"><div class="card-head"><strong>{{ row.voucher || 'سند' }}</strong><span :class="row.qty_change >= 0 ? 'success' : 'error'">{{ qty(row.qty_change) }}</span></div><small class="sub">{{ row.posting_date }} • {{ row.warehouse }}</small></template>
      </InventoryResponsiveList>
    </ManagementSurfaceCard>
  </InventorySectionShell>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import InventoryResponsiveList from '@/components/management/inventory/InventoryResponsiveList.vue'
import InventorySectionShell from '@/components/management/inventory/InventorySectionShell.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { getManagementInventoryBoot, getManagementRawMaterialDetail, saveManagementRawMaterial } from '@/utils/api'
import { formatMoney } from '@/utils/format'

const params = new URLSearchParams(window.location.search)
const itemCode = params.get('item') || ''
const isNew = !itemCode || params.get('new') === '1'
const detail = ref(null)
const boot = ref(null)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const message = ref('')
const form = reactive({ name: '', item_code: itemCode, item_name: '', item_group: '', stock_uom: 'Nos', purchase_rate: 0, default_supplier: '', disabled: false, reorder_levels: [] })
const movementColumns = [
  { key: 'posting_date', label: 'تاریخ' },
  { key: 'warehouse', label: 'انبار' },
  { key: 'qty_change', label: 'تغییر مقدار' },
  { key: 'voucher', label: 'سند' },
]
function qty(value) { return Number(value || 0).toLocaleString('fa-IR', { maximumFractionDigits: 3 }) }
function money(value) { return formatMoney(Number(value || 0), 'IRR') }
function goBack() { window.location.href = '/management/inventory/materials' }
function applyDetail(value) {
  detail.value = value
  Object.assign(form, { name: value.name, item_code: value.name, item_name: value.item_name, item_group: value.item_group || '', stock_uom: value.stock_uom || 'Nos', purchase_rate: value.purchase_rate || 0, default_supplier: value.default_supplier || '', disabled: !!value.disabled, reorder_levels: (value.reorder_levels || []).map((row) => ({ ...row })) })
}
async function load() {
  loading.value = true; error.value = ''
  try {
    boot.value = await getManagementInventoryBoot()
    if (isNew) { form.item_group = boot.value?.item_groups?.[0]?.name || ''; return }
    const payload = await getManagementRawMaterialDetail(itemCode)
    applyDetail(payload)
  } catch (err) { error.value = err.message || 'دریافت جزئیات ماده ناموفق بود.' }
  finally { loading.value = false }
}
async function save() {
  saving.value = true; error.value = ''; message.value = ''
  try {
    const result = await saveManagementRawMaterial({ ...form, disabled: form.disabled ? 1 : 0, reorder_levels: form.reorder_levels.filter((row) => row.warehouse) })
    message.value = 'ماده اولیه ذخیره شد.'
    window.history.replaceState({}, '', `/management/inventory/materials/detail?item=${encodeURIComponent(result.name || form.item_code)}`)
    window.setTimeout(() => { window.location.href = '/management/inventory/materials' }, 450)
  } catch (err) { error.value = err.message || 'ذخیره ماده ناموفق بود.' }
  finally { saving.value = false }
}
onMounted(load)
</script>

<style scoped>
.detail-kpis { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.6rem; margin-bottom: 0.8rem; }
.detail-kpis article { display: grid; gap: 0.2rem; padding: 0.65rem; border: 1px solid var(--mg-border-light); border-radius: 13px; background: var(--mg-bg-page); }
.detail-kpis small, .sub { color: var(--mg-text-muted); font-size: 0.7rem; }
.detail-kpis strong { color: var(--mg-primary); }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 0.65rem; }
.form-grid label { display: grid; gap: 0.25rem; color: var(--mg-text-main); font-size: 0.78rem; }
.check { display: inline-flex !important; align-items: center; grid-template-columns: auto 1fr; }
.reorder-section { display: grid; gap: 0.55rem; margin-top: 1rem; padding: 0.8rem; border: 1px dashed var(--mg-border); border-radius: 15px; }
.reorder-section header { display: flex; justify-content: space-between; gap: 0.5rem; align-items: flex-start; }
.reorder-section h4, .reorder-section p { margin: 0; }
.reorder-section p { color: var(--mg-text-muted); font-size: 0.7rem; margin-top: 0.15rem; }
.reorder-row { display: grid; grid-template-columns: minmax(0, 2fr) minmax(90px, 1fr) minmax(90px, 1fr) auto; gap: 0.45rem; }
.detail-actions { display: flex; justify-content: flex-end; margin-top: 0.8rem; }
.success { color: var(--mg-success); }
.error { color: var(--mg-danger); }
.card-head { display: flex; justify-content: space-between; gap: 0.5rem; }
@media (max-width: 620px) { .detail-kpis { grid-template-columns: 1fr; } .reorder-row { grid-template-columns: 1fr 1fr; } .reorder-row button { grid-column: 1 / -1; } .detail-actions .primary-btn { width: 100%; } }
</style>
