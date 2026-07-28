<template>
  <ManagementPageScaffold title="کاست کنترل" subtitle="بودجه‌بندی، سود و زیان ماهانه، نقطه سربه‌سر و بازگشت سرمایه">
    <template #actions>
      <select class="input year-input" v-model.number="fiscalYear" @change="loadAll">
        <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
      </select>
      <button type="button" class="secondary-btn" @click="loadAll" :disabled="loadingAny">
        {{ loadingAny ? 'در حال بروزرسانی...' : 'بروزرسانی' }}
      </button>
    </template>

    <div v-if="boot" class="totals-grid boot-kpis">
      <div class="total-box"><small>فروش سال</small><strong>{{ formatMoneyValue(boot.kpis.year_revenue) }}</strong></div>
      <div class="total-box"><small>سود خالص سال</small><strong :class="boot.kpis.year_net >= 0 ? 'ok-text' : 'warn-text'">{{ formatMoneyValue(boot.kpis.year_net) }}</strong></div>
      <div class="total-box"><small>نسبت بهای تمام‌شده</small><strong>{{ formatQty(boot.kpis.cogs_ratio_pct) }}٪</strong></div>
      <div class="total-box"><small>سود خالص ماه جاری</small><strong :class="boot.kpis.current_month_net >= 0 ? 'ok-text' : 'warn-text'">{{ formatMoneyValue(boot.kpis.current_month_net) }}</strong></div>
      <div class="total-box" :class="{ 'warn-border': boot.kpis.current_month_revenue > 0 && boot.kpis.safety_margin_pct < 0 }">
        <small>نقطه سربه‌سر (فروش ماهانه)</small><strong>{{ formatMoneyValue(boot.kpis.breakeven_monthly_sales) }}</strong>
      </div>
      <div class="total-box"><small>حاشیه امنیت ماه جاری</small><strong :class="boot.kpis.safety_margin_pct >= 0 ? 'ok-text' : 'warn-text'">{{ formatQty(boot.kpis.safety_margin_pct) }}٪</strong></div>
      <div class="total-box" :class="{ 'warn-border': boot.kpis.monthly_budget_amount && boot.kpis.monthly_budget_used_pct > 100 }">
        <small>مصرف بودجه ماه</small>
        <strong :class="boot.kpis.monthly_budget_amount && boot.kpis.monthly_budget_used_pct > 100 ? 'warn-text' : 'ok-text'">
          {{ boot.kpis.monthly_budget_amount ? formatQty(boot.kpis.monthly_budget_used_pct) + '٪' : '—' }}
        </strong>
      </div>
    </div>
    <p class="error" v-if="bootError">{{ bootError }}</p>

    <nav class="tabs-bar">
      <button v-for="tab in tabs" :key="tab.key" type="button" :class="['tab-btn', { active: activeTab === tab.key }]" @click="activeTab = tab.key">
        {{ tab.label }}
      </button>
    </nav>

    <!-- ======================= سود و زیان ======================= -->
    <section v-if="activeTab === 'pl'" class="tab-body">
      <ManagementSurfaceCard :title="`سود و زیان ماهانه سال ${formatQty(fiscalYear)}`" subtitle="بهای تمام‌شده از بهای دستور پخت (BOM) و ضایعات از گردش‌های انبار محاسبه می‌شود">
        <p class="muted" v-if="!boot">در حال محاسبه...</p>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>ماه</th><th>سفارش‌ها</th><th>فروش</th><th>بهای تمام‌شده</th><th>سود ناخالص</th><th>هزینه‌های ثابت</th><th>ضایعات/خسارت</th><th>سود خالص</th><th>حاشیه</th></tr>
            </thead>
            <tbody>
              <tr v-for="row in boot.pl_rows" :key="row.month" :class="{ 'current-month': row.month === currentMonthHighlight }">
                <td><strong>{{ monthName(row.month) }}</strong></td>
                <td>{{ formatQty(row.orders) }}</td>
                <td>{{ formatMoneyValue(row.revenue) }}</td>
                <td>{{ formatMoneyValue(row.cogs) }}</td>
                <td>{{ formatMoneyValue(row.gross_profit) }}</td>
                <td>{{ formatMoneyValue(row.fixed_costs) }}</td>
                <td>{{ formatMoneyValue(row.waste) }}</td>
                <td :class="row.net_profit >= 0 ? 'ok-text' : 'warn-text'"><strong>{{ formatMoneyValue(row.net_profit) }}</strong></td>
                <td>{{ formatQty(row.margin_pct) }}٪</td>
              </tr>
            </tbody>
            <tfoot v-if="boot">
              <tr>
                <td><strong>جمع سال</strong></td>
                <td>{{ formatQty(totalOrders) }}</td>
                <td><strong>{{ formatMoneyValue(totals.revenue) }}</strong></td>
                <td>{{ formatMoneyValue(totals.cogs) }}</td>
                <td>{{ formatMoneyValue(totals.gross) }}</td>
                <td>{{ formatMoneyValue(totals.fixed) }}</td>
                <td>{{ formatMoneyValue(totals.waste) }}</td>
                <td :class="totals.net >= 0 ? 'ok-text' : 'warn-text'"><strong>{{ formatMoneyValue(totals.net) }}</strong></td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
        <p class="muted hint-line">ضایعات و خروج/خسارت ثبت‌شده در انبارداری هوشمند به ارزش ریالی در این جدول لحاظ می‌شود.</p>
      </ManagementSurfaceCard>
    </section>

    <!-- ======================= بودجه ======================= -->
    <section v-if="activeTab === 'budgets'" class="tab-body">
      <ManagementSurfaceCard title="بودجه‌بندی" subtitle="بودجه ماهانه و سالانه برای دسته‌های هزینه‌ای؛ درصد مصرف بودجه ماه جاری بالای صفحه نمایش داده می‌شود">
        <div class="btn-row"><button type="button" class="primary-btn" @click="openBudgetForm()">بودجه جدید</button></div>
        <p class="muted" v-if="budgetsLoading">در حال دریافت بودجه‌ها...</p>
        <div v-else-if="budgets.length" class="table-wrap">
          <table class="data-table">
            <thead><tr><th>عنوان</th><th>دسته</th><th>دوره</th><th>سال</th><th>ماه</th><th>مبلغ</th><th>وضعیت</th><th></th></tr></thead>
            <tbody>
              <tr v-for="b in budgets" :key="b.name" :class="{ inactive: !b.is_active }">
                <td><strong>{{ b.title }}</strong><br><small class="muted">{{ b.name }}</small></td>
                <td>{{ b.category || '—' }}</td>
                <td><span class="pill">{{ b.period }}</span></td>
                <td>{{ formatQty(b.fiscal_year) }}</td>
                <td>{{ b.period === 'ماهانه' ? monthName(b.month) : '—' }}</td>
                <td>{{ formatMoneyValue(b.planned_amount) }}</td>
                <td><span class="pill" :class="{ ok: b.is_active, warn: !b.is_active }">{{ b.is_active ? 'فعال' : 'غیرفعال' }}</span></td>
                <td class="row-actions">
                  <button type="button" class="tertiary-btn" @click="openBudgetForm(b)">ویرایش</button>
                  <button type="button" class="tertiary-btn danger" @click="removeBudget(b)">حذف</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="muted" v-else-if="!budgetsLoading">بودجه‌ای برای این سال ثبت نشده است.</p>
      </ManagementSurfaceCard>

      <div v-if="budgetForm" class="popup-backdrop" @click.self="budgetForm = null">
        <div class="popup">
          <h3>{{ budgetForm.name ? 'ویرایش بودجه' : 'بودجه جدید' }}</h3>
          <div class="form-grid">
            <label>عنوان <span class="req">*</span><input class="input" v-model.trim="budgetForm.title" placeholder="مثلاً بودجه خرید مواد اولیه" /></label>
            <label>دسته هزینه<input class="input" v-model.trim="budgetForm.category" placeholder="مواد اولیه / مارکتینگ / پرسنل ..." /></label>
            <label>دوره
              <select class="input" v-model="budgetForm.period"><option value="ماهانه">ماهانه</option><option value="سالانه">سالانه</option></select>
            </label>
            <label>سال مالی<input class="input" type="number" min="1400" v-model.number="budgetForm.fiscal_year" /></label>
            <label v-if="budgetForm.period === 'ماهانه'">ماه
              <select class="input" v-model.number="budgetForm.month">
                <option v-for="m in 12" :key="m" :value="m">{{ monthName(m) }}</option>
              </select>
            </label>
            <label>مبلغ بودجه (ریال) <span class="req">*</span><input class="input" type="number" min="0" v-model.number="budgetForm.planned_amount" /></label>
            <label class="check-row full-row"><input type="checkbox" v-model="budgetForm.is_active" /> فعال</label>
          </div>
          <p class="error" v-if="budgetFormError">{{ budgetFormError }}</p>
          <div class="btn-row">
            <button type="button" class="primary-btn" @click="saveBudget" :disabled="budgetSaving">{{ budgetSaving ? '...' : 'ذخیره بودجه' }}</button>
            <button type="button" class="tertiary-btn" @click="budgetForm = null">انصراف</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ======================= نقطه سربه‌سر و ROI ======================= -->
    <section v-if="activeTab === 'breakeven'" class="tab-body">
      <ManagementSurfaceCard title="نقطه سربه‌سر" subtitle="حداقل فروشی که هزینه‌های ثابت و متغیر را پوشش می‌دهد">
        <div class="totals-grid" v-if="boot">
          <div class="total-box"><small>هزینه‌های ثابت ماهانه</small><strong>{{ formatMoneyValue(boot.kpis.fixed_monthly_cost) }}</strong></div>
          <div class="total-box"><small>نسبت هزینه متغیر (بهای تمام‌شده)</small><strong>{{ formatQty(boot.kpis.cogs_ratio_pct) }}٪</strong></div>
          <div class="total-box"><small>سربه‌سر ماهانه</small><strong>{{ formatMoneyValue(boot.kpis.breakeven_monthly_sales) }}</strong></div>
          <div class="total-box"><small>سربه‌سر روزانه</small><strong>{{ formatMoneyValue(boot.kpis.breakeven_daily_sales) }}</strong></div>
        </div>
        <p class="muted hint-line">
          فرمول: هزینه‌های ثابت ÷ (۱ − نسبت بهای تمام‌شده). هزینه‌های ثابت از بخش «هزینه‌های جاری» داشبورد و بهای تمام‌شده از دستور پخت محصولات محاسبه می‌شود؛ برای دقت بیشتر، هزینه‌های ثابت و قیمت مواد اولیه را به‌روز نگه دارید.
        </p>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="محاسبه بازگشت سرمایه (ROI)" subtitle="بر اساس میانگین سود خالص ماهانه سال جاری مالی">
        <div class="form-grid">
          <label>مبلغ سرمایه‌گذاری (ریال) <span class="req">*</span><input class="input" type="number" min="0" v-model.number="roiForm.investment" placeholder="مثلاً 500,000,000" /></label>
          <label>سال مالی
            <select class="input" v-model.number="roiForm.fiscal_year">
              <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
            </select>
          </label>
        </div>
        <div class="btn-row">
          <button type="button" class="primary-btn" @click="computeRoi" :disabled="roiBusy">{{ roiBusy ? '...' : 'محاسبه' }}</button>
        </div>
        <p class="error" v-if="roiError">{{ roiError }}</p>
        <div class="totals-grid result-block" v-if="roiResult">
          <div class="total-box"><small>میانگین سود خالص ماهانه</small><strong>{{ formatMoneyValue(roiResult.avg_monthly_net_profit) }}</strong></div>
          <div class="total-box"><small>ماه‌های دارای فروش</small><strong>{{ formatQty(roiResult.months_with_sales) }}</strong></div>
          <div class="total-box"><small>دوره بازگشت سرمایه</small><strong>{{ roiResult.payback_months ? formatQty(roiResult.payback_months) + ' ماه' : '—' }}</strong></div>
          <div class="total-box"><small>ROI سالانه</small><strong :class="roiResult.roi_annual_pct > 0 ? 'ok-text' : 'warn-text'">{{ formatQty(roiResult.roi_annual_pct) }}٪</strong></div>
        </div>
      </ManagementSurfaceCard>
    </section>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import {
  getManagementCostControlBoot,
  listManagementBudgets,
  saveManagementBudget,
  deleteManagementBudget,
  computeManagementRoi,
} from '@/utils/api'
import { formatMoney as formatMoneyUtil } from '@/utils/format'

const tabs = [
  { key: 'pl', label: 'سود و زیان' },
  { key: 'budgets', label: 'بودجه‌بندی' },
  { key: 'breakeven', label: 'نقطه سربه‌سر و ROI' },
]
const activeTab = ref('pl')

const currentYear = new Date().getFullYear()
const yearOptions = [currentYear - 1, currentYear, currentYear + 1]
const fiscalYear = ref(currentYear)

const boot = ref(null)
const bootError = ref('')
const bootLoading = ref(false)
const budgets = ref([])
const budgetsLoading = ref(false)
const budgetForm = ref(null)
const budgetFormError = ref('')
const budgetSaving = ref(false)
const roiForm = ref({ investment: null, fiscal_year: currentYear })
const roiBusy = ref(false)
const roiError = ref('')
const roiResult = ref(null)

const loadingAny = computed(() => bootLoading.value || budgetsLoading.value)
const monthNames = ['ژانویه', 'فوریه', 'مارس', 'آوریل', 'مه', 'ژوئن', 'ژوئیه', 'اوت', 'سپتامبر', 'اکتبر', 'نوامبر', 'دسامبر']
const currentMonthHighlight = computed(() => (fiscalYear.value === currentYear ? new Date().getMonth() + 1 : 0))
const totals = computed(() => {
  const rows = boot.value?.pl_rows || []
  return {
    revenue: rows.reduce((a, r) => a + Number(r.revenue || 0), 0),
    cogs: rows.reduce((a, r) => a + Number(r.cogs || 0), 0),
    gross: rows.reduce((a, r) => a + Number(r.gross_profit || 0), 0),
    fixed: rows.reduce((a, r) => a + Number(r.fixed_costs || 0), 0),
    waste: rows.reduce((a, r) => a + Number(r.waste || 0), 0),
    net: rows.reduce((a, r) => a + Number(r.net_profit || 0), 0),
  }
})
const totalOrders = computed(() => (boot.value?.pl_rows || []).reduce((a, r) => a + Number(r.orders || 0), 0))

function monthName(m) {
  return monthNames[Math.max(1, Math.min(12, Number(m) || 1)) - 1]
}
function formatMoneyValue(value) {
  return formatMoneyUtil(Number(value || 0))
}
function formatQty(value) {
  return Number(value || 0).toLocaleString('fa-IR')
}

async function loadBoot() {
  bootLoading.value = true
  bootError.value = ''
  try {
    boot.value = await getManagementCostControlBoot({ fiscal_year: fiscalYear.value })
  } catch (err) {
    bootError.value = err.message || 'محاسبه شاخص‌های هزینه ناموفق بود.'
  } finally {
    bootLoading.value = false
  }
}

async function loadBudgets() {
  budgetsLoading.value = true
  try {
    const payload = await listManagementBudgets({ fiscal_year: fiscalYear.value })
    budgets.value = payload?.budgets || []
  } catch (err) {
    budgets.value = []
  } finally {
    budgetsLoading.value = false
  }
}

function loadAll() {
  loadBoot()
  loadBudgets()
}

function openBudgetForm(b = null) {
  budgetFormError.value = ''
  budgetForm.value = b
    ? { name: b.name, title: b.title, category: b.category || '', period: b.period, fiscal_year: b.fiscal_year, month: b.month || 1, planned_amount: b.planned_amount, is_active: !!b.is_active, notes: b.notes || '' }
    : { name: '', title: '', category: '', period: 'ماهانه', fiscal_year: fiscalYear.value, month: new Date().getMonth() + 1, planned_amount: null, is_active: true, notes: '' }
}

async function saveBudget() {
  budgetSaving.value = true
  budgetFormError.value = ''
  try {
    await saveManagementBudget({ ...budgetForm.value, is_active: budgetForm.value.is_active ? 1 : 0 })
    budgetForm.value = null
    await loadBudgets()
    await loadBoot()
  } catch (err) {
    budgetFormError.value = err.message || 'ذخیره بودجه ناموفق بود.'
  } finally {
    budgetSaving.value = false
  }
}

async function removeBudget(b) {
  if (!window.confirm(`بودجه «${b.title}» حذف شود؟`)) return
  try {
    await deleteManagementBudget(b.name)
    await loadBudgets()
    await loadBoot()
  } catch (err) {}
}

async function computeRoi() {
  roiBusy.value = true
  roiError.value = ''
  roiResult.value = null
  try {
    roiResult.value = await computeManagementRoi({ investment: roiForm.value.investment, fiscal_year: roiForm.value.fiscal_year })
  } catch (err) {
    roiError.value = err.message || 'محاسبه بازگشت سرمایه ناموفق بود.'
  } finally {
    roiBusy.value = false
  }
}

onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.boot-kpis {
  margin-bottom: 0.9rem;
}
.year-input {
  width: 110px;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.65rem;
  margin-bottom: 0.7rem;
}
.form-grid label {
  display: grid;
  gap: 0.3rem;
  font-size: 0.86rem;
}
.full-row {
  grid-column: 1 / -1;
}
.input {
  width: 100%;
  box-sizing: border-box;
}
.btn-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.6rem;
  margin-bottom: 0.6rem;
}
.table-wrap {
  overflow-x: auto;
  margin-top: 0.7rem;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.86rem;
}
.data-table th,
.data-table td {
  text-align: right;
  padding: 0.45rem 0.55rem;
  border-bottom: 1px solid var(--border-color, #e5dfd2);
  vertical-align: top;
  white-space: nowrap;
}
.data-table th {
  color: var(--text-muted, #6b7a72);
  font-weight: 600;
}
.data-table tr.inactive td {
  opacity: 0.55;
}
.data-table tfoot td {
  border-top: 2px solid var(--border-color, #e5dfd2);
  border-bottom: 0;
}
tr.current-month td {
  background: rgba(47, 111, 92, 0.06);
}
.row-actions {
  white-space: nowrap;
}
.pill {
  display: inline-block;
  border-radius: 999px;
  padding: 0.12rem 0.6rem;
  font-size: 0.76rem;
  background: var(--surface-soft, #f0ede4);
  margin-inline-end: 0.25rem;
  white-space: nowrap;
}
.pill.ok {
  background: rgba(47, 111, 92, 0.14);
  color: var(--accent-green, #2f6f5c);
}
.pill.warn {
  background: rgba(184, 79, 79, 0.14);
  color: #b84f4f;
}
.check-row {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.88rem;
}
.popup-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(20, 24, 22, 0.45);
  display: grid;
  place-items: center;
  z-index: 60;
  padding: 1rem;
}
.popup {
  background: var(--surface-bg, #fff);
  border-radius: 16px;
  padding: 1rem 1.1rem;
  width: min(620px, 100%);
  max-height: 88vh;
  overflow-y: auto;
  display: grid;
  gap: 0.65rem;
}
.popup h3 {
  margin: 0;
}
.muted {
  color: var(--text-muted, #6b7a72);
}
.error {
  color: #b84f4f;
}
.ok-text {
  color: var(--accent-green, #2f6f5c);
}
.warn-text {
  color: #b84f4f;
}
.tertiary-btn.danger {
  color: #b84f4f;
}
.req {
  color: #b84f4f;
}
.hint-line {
  font-size: 0.78rem;
  margin-top: 0.5rem;
}
.result-block {
  margin-top: 0.8rem;
  margin-bottom: 0;
}
</style>
