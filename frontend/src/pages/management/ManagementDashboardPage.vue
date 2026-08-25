<template>
  <ManagementPageScaffold title="داشبورد مدیریتی و BI" subtitle="فروش، مشتری، کانال‌ها، مهندسی منو و کنترل عملیات">
    <template #actions>
      <button type="button" class="secondary-btn" @click="loadDashboard" :disabled="loading">
        {{ loading ? 'در حال بروزرسانی...' : 'بروزرسانی اطلاعات' }}
      </button>
      <button type="button" class="secondary-btn" @click="customizeOpen = !customizeOpen">شخصی سازی گزارش ها</button>
    </template>

    <ManagementSurfaceCard tone="accent">
      <div class="global-controls">
        <div class="control-meta">
          <strong>داشبورد</strong>
          <small>{{ todayLabel }}</small>
        </div>

        <label>
          از تاریخ
          <PersianDateInput v-model="filters.date_from" />
        </label>

        <label>
          تا تاریخ
          <PersianDateInput v-model="filters.date_to" />
        </label>

        <button type="button" class="primary-btn" @click="loadDashboard" :disabled="loading">اجرای فیلتر</button>
      </div>
      <p class="window-line">{{ rangeLabel }}</p>

      <div class="widget-toggle-grid" v-if="customizeOpen">
        <label v-for="widget in widgetOptions" :key="widget.key">
          <input type="checkbox" v-model="widgetState[widget.key]" />
          {{ widget.label }}
        </label>
      </div>

      <div class="menu-highlight-control">
        <label class="check-row">
          <input type="checkbox" v-model="menuHighlightEnabled" :disabled="menuHighlightLoading || menuHighlightSaving" />
          فعال بودن سکشن «ویژه و پرفروش» در منوی عمومی
        </label>
        <button
          type="button"
          class="secondary-btn"
          :disabled="menuHighlightLoading || menuHighlightSaving"
          @click="saveMenuHighlightSettings"
        >
          {{ menuHighlightSaving ? 'در حال ذخیره...' : 'ذخیره تنظیم سکشن منو' }}
        </button>
        <span class="hint-line" v-if="menuHighlightMessage">{{ menuHighlightMessage }}</span>
        <span class="error" v-if="menuHighlightError">{{ menuHighlightError }}</span>
      </div>
    </ManagementSurfaceCard>

    <p class="muted" v-if="loading">در حال بارگذاری داشبورد...</p>
    <p class="error" v-if="error">{{ error }}</p>
    <p class="hint" v-if="warningText">{{ warningText }}</p>

    <template v-if="!loading && !error">
      <ManagementSurfaceCard
        title="تنظیمات افتتاحیه/اختتامیه POS"
        subtitle="تنظیم پیش‌فرض‌های شروع و پایان شیفت صندوق"
        v-if="widgetState.pos_shift"
      >
        <div class="pos-shift-grid">
          <article class="pos-shift-box">
            <h4>افتتاحیه POS</h4>
            <label class="check-row">
              <input type="checkbox" v-model="posShiftForm.opening.enabled" />
              فعال بودن فرآیند افتتاحیه
            </label>
            <label>
              ساعت پیش‌فرض افتتاحیه
              <input class="input" type="time" v-model="posShiftForm.opening.time" />
            </label>
            <label>
              موجودی اولیه صندوق
              <input class="input" type="number" min="0" v-model.number="posShiftForm.opening.cash_float" />
            </label>
            <label class="check-row">
              <input type="checkbox" v-model="posShiftForm.opening.checklist_required" />
              چک‌لیست افتتاحیه اجباری باشد
            </label>
            <ManagementNoteField
              v-model="posShiftForm.opening.note_template"
              label="متن پیش‌فرض افتتاحیه"
              rows="3"
              placeholder="متن چاپ یا توضیح افتتاحیه..."
            />
          </article>

          <article class="pos-shift-box">
            <h4>اختتامیه POS</h4>
            <label class="check-row">
              <input type="checkbox" v-model="posShiftForm.closing.enabled" />
              فعال بودن فرآیند اختتامیه
            </label>
            <label>
              ساعت پیش‌فرض اختتامیه
              <input class="input" type="time" v-model="posShiftForm.closing.time" />
            </label>
            <label>
              موجودی هدف اختتامیه
              <input class="input" type="number" min="0" v-model.number="posShiftForm.closing.expected_cash" />
            </label>
            <label>
              تلرانس اختلاف صندوق
              <input class="input" type="number" min="0" v-model.number="posShiftForm.closing.tolerance" />
            </label>
            <label class="check-row">
              <input type="checkbox" v-model="posShiftForm.closing.checklist_required" />
              چک‌لیست اختتامیه اجباری باشد
            </label>
            <ManagementNoteField
              v-model="posShiftForm.closing.note_template"
              label="متن پیش‌فرض اختتامیه"
              rows="3"
              placeholder="متن چاپ یا توضیح اختتامیه..."
            />
          </article>
        </div>

        <div class="pos-shift-actions">
          <button type="button" class="primary-btn" :disabled="posShiftSaving" @click="savePosShiftSettings">
            {{ posShiftSaving ? 'در حال ذخیره...' : 'ذخیره تنظیمات شیفت POS' }}
          </button>
          <span class="hint-line" v-if="posShiftMessage">{{ posShiftMessage }}</span>
          <span class="error" v-if="posShiftError">{{ posShiftError }}</span>
        </div>
      </ManagementSurfaceCard>

      <section class="kpi-grid" v-if="widgetState.kpis">
        <ManagementSurfaceCard class="kpi-card" tone="soft" v-for="kpi in kpis" :key="kpi.key">
          <small>{{ kpi.label }}</small>
          <strong>{{ formatKpiValue(kpi) }}</strong>
          <div class="kpi-foot">
            <span class="delta" :class="deltaClass(kpi.change)">{{ formatDelta(kpi.change) }}</span>
            <small>{{ kpi.subtitle || 'نسبت به بازه قبل' }}</small>
          </div>
          <a v-if="kpi.action" class="mini-link" :href="kpi.action">{{ kpi.actionLabel || 'مشاهده' }}</a>
        </ManagementSurfaceCard>
      </section>

      <ManagementSurfaceCard
        v-if="widgetState.kpis"
        title="پیک‌ها و ناوگان"
        subtitle="ورود سریع به مدیریت پیک‌ها و خلاصه ظرفیت فعال"
      >
        <div class="mini-matrix">
          <article>
            <small>پیک فعال</small>
            <strong>{{ Number(courierFleet.active_courier_count || 0).toLocaleString('fa-IR') }}</strong>
            <a href="/management/couriers">مدیریت پیک‌ها</a>
          </article>
          <article>
            <small>کل پیک‌ها</small>
            <strong>{{ Number(courierFleet.courier_count || 0).toLocaleString('fa-IR') }}</strong>
            <a href="/management/couriers">جزئیات</a>
          </article>
          <article>
            <small>وسیله فعال</small>
            <strong>{{ Number(courierFleet.active_vehicle_count || 0).toLocaleString('fa-IR') }}</strong>
            <a href="/management/couriers">ناوگان</a>
          </article>
          <article>
            <small>کل وسیله‌ها</small>
            <strong>{{ Number(courierFleet.vehicle_count || 0).toLocaleString('fa-IR') }}</strong>
            <a href="/management/couriers">نمایش همه</a>
          </article>
        </div>
      </ManagementSurfaceCard>

      <section class="panel-grid" v-if="widgetState.sales_financial || widgetState.time_trend || widgetState.cost_control">
        <ManagementSurfaceCard title="فروش/هزینه" subtitle="فروش کل، هزینه، فروش بازگشتی و انتظار فروش" v-if="widgetState.sales_financial">
          <div class="legend-checks">
            <label v-for="entry in salesLegendOptions" :key="entry.key">
              <input type="checkbox" v-model="salesLegendState[entry.key]" />
              {{ entry.label }}
            </label>
          </div>
          <ManagementLineChart :labels="salesChart.labels" :series="salesChart.series" />
        </ManagementSurfaceCard>

        <ManagementSurfaceCard title="روند زمانی فروش" subtitle="تغییر بین روز فروش و ساعت فروش" v-if="widgetState.time_trend">
          <div class="toggle-row">
            <button type="button" :class="{ active: timeTrendMode === 'day' }" @click="timeTrendMode = 'day'">روز فروش</button>
            <button type="button" :class="{ active: timeTrendMode === 'hour' }" @click="timeTrendMode = 'hour'">ساعت فروش</button>
          </div>
          <ManagementLineChart :labels="timeTrendChart.labels" :series="timeTrendChart.series" />
        </ManagementSurfaceCard>

        <ManagementSurfaceCard title="کاست کنترل" subtitle="Cost % = Total Item Costs / Total Sales * 100" v-if="widgetState.cost_control">
          <ManagementLineChart :labels="costControlChart.labels" :series="costControlChart.series" />
          <p class="hint-line" v-if="!hasCostData">داده بهای تمام‌شده ثبت نشده است.</p>
        </ManagementSurfaceCard>
      </section>

      <section class="panel-grid" v-if="widgetState.performers || widgetState.channels">
        <ManagementSurfaceCard title="برترین ها" subtitle="تحلیل دسته بندی ها، جایگاه ها و کارکنان" v-if="widgetState.performers">
          <div class="toggle-row">
            <button type="button" :class="{ active: performerMode === 'category' }" @click="performerMode = 'category'">
              دسته بندی ها
            </button>
            <button type="button" :class="{ active: performerMode === 'place' }" @click="performerMode = 'place'">
              جایگاه ها
            </button>
            <button type="button" :class="{ active: performerMode === 'staff' }" @click="performerMode = 'staff'">
              کارکنان
            </button>
          </div>
          <ManagementBarList :rows="performerRows" mode="money" :currency="currency" />
        </ManagementSurfaceCard>

        <ManagementSurfaceCard title="تحلیل کانال های فروش" subtitle="نمایش بر اساس مبلغ یا تعداد فروش" v-if="widgetState.channels">
          <div class="toggle-row">
            <button type="button" :class="{ active: channelMode === 'money' }" @click="channelMode = 'money'">مبلغ فروش</button>
            <button type="button" :class="{ active: channelMode === 'count' }" @click="channelMode = 'count'">تعداد فروش</button>
          </div>
          <ManagementBarList :rows="channelRows" :mode="channelMode" :currency="currency" />
        </ManagementSurfaceCard>
      </section>

      <section class="crm-grid" v-if="widgetState.crm">
        <ManagementSurfaceCard title="مشتریان جدید / بازگشتی" :subtitle="`کل مشتریان: ${customerAnalytics.totalCustomers} نفر`">
          <ManagementLineChart :labels="customerLineChart.labels" :series="customerLineChart.series" />
        </ManagementSurfaceCard>

        <ManagementSurfaceCard title="تحلیل مشتریان" subtitle="بیشترین تخفیف / بیشترین بدهی">
          <div class="toggle-row">
            <button type="button" :class="{ active: specialCustomerMode === 'discount' }" @click="specialCustomerMode = 'discount'">
              بیشترین تخفیف
            </button>
            <button type="button" :class="{ active: specialCustomerMode === 'debt' }" @click="specialCustomerMode = 'debt'">
              بیشترین بدهی
            </button>
          </div>
          <ManagementDataTable :columns="specialColumns" :rows="specialRows" row-key="key">
            <template #cell-total_spent="{ value }">{{ formatMoney(value, currency) }}</template>
            <template #cell-focus_value="{ value }">{{ formatMoney(value, currency) }}</template>
          </ManagementDataTable>
        </ManagementSurfaceCard>

        <ManagementSurfaceCard title="وفاداری مشتریان" subtitle="بر اساس Recency و طول ارتباط">
          <div class="mini-matrix">
            <article v-for="item in loyaltyCards" :key="item.key">
              <small>{{ item.label }}</small>
              <strong>{{ item.value }} نفر</strong>
              <a href="/management/customers">مشاهده جزییات</a>
            </article>
          </div>
          <p class="hint-line">
            مشتریان وفادار بر اساس طول ارتباط مشتری و تازگی خرید محاسبه می‌شود.
          </p>
        </ManagementSurfaceCard>

        <ManagementSurfaceCard title="ارزش مشتریان" subtitle="بر اساس تکرار خرید و مبلغ خرید">
          <div class="mini-matrix">
            <article v-for="item in valueCards" :key="item.key">
              <small>{{ item.label }}</small>
              <strong>{{ item.value }} نفر</strong>
              <a href="/management/customers">مشاهده جزییات</a>
            </article>
          </div>
        </ManagementSurfaceCard>
      </section>

      <section class="menu-grid" v-if="widgetState.menu">
        <ManagementSurfaceCard title="خلاصه ارزش غذایی فروش" subtitle="مجموع کالری و درشت‌مغذی‌های محصولات پرفروش">
          <div class="nutrition-summary-grid">
            <article v-for="card in nutritionCards" :key="card.key">
              <small>{{ card.label }}</small>
              <strong>{{ card.value }}</strong>
            </article>
          </div>
        </ManagementSurfaceCard>

        <ManagementSurfaceCard title="پرفروش ترین ها / کم فروش ترین ها" subtitle="مبلغ فروش و تعداد فروش">
          <div class="toggle-row">
            <button type="button" :class="{ active: salesListMode === 'top' }" @click="salesListMode = 'top'">پرفروش ترین ها</button>
            <button type="button" :class="{ active: salesListMode === 'low' }" @click="salesListMode = 'low'">کم فروش ترین ها</button>
          </div>
          <ManagementDataTable :columns="menuColumns" :rows="salesListRows" row-key="product">
            <template #cell-amount="{ value }">{{ formatMoney(value, currency) }}</template>
          </ManagementDataTable>
        </ManagementSurfaceCard>

        <ManagementSurfaceCard title="محبوب ترین ها / غیر محبوب ترین ها" subtitle="تعداد فروش">
          <div class="toggle-row">
            <button type="button" :class="{ active: popularityListMode === 'popular' }" @click="popularityListMode = 'popular'">
              محبوب ترین ها
            </button>
            <button type="button" :class="{ active: popularityListMode === 'unpopular' }" @click="popularityListMode = 'unpopular'">
              غیر محبوب ترین ها
            </button>
          </div>
          <ManagementDataTable :columns="menuColumns" :rows="popularityRows" row-key="product">
            <template #cell-amount="{ value }">{{ formatMoney(value, currency) }}</template>
          </ManagementDataTable>
        </ManagementSurfaceCard>

        <ManagementSurfaceCard title="مهندسی منو" subtitle="محبوبیت و سودآوری">
          <div class="mini-matrix">
            <article>
              <small>محبوبیت بالا و سودآوری بالا</small>
              <strong>{{ menuEngineering.matrix.stars }}</strong>
              <a href="/management/reports/top-products">مشاهده جزییات</a>
            </article>
            <article>
              <small>محبوبیت پایین و سودآوری بالا</small>
              <strong>{{ menuEngineering.matrix.puzzles }}</strong>
              <a href="/management/reports/top-products">مشاهده جزییات</a>
            </article>
            <article>
              <small>محبوبیت بالا و سودآوری پایین</small>
              <strong>{{ menuEngineering.matrix.plowhorses }}</strong>
              <a href="/management/reports/top-products">مشاهده جزییات</a>
            </article>
            <article>
              <small>محبوبیت پایین و سودآوری پایین</small>
              <strong>{{ menuEngineering.matrix.dogs }}</strong>
              <a href="/management/reports/top-products">مشاهده جزییات</a>
            </article>
          </div>
        </ManagementSurfaceCard>
      </section>

      <ManagementSurfaceCard
        title="انبارداری هوشمند"
        subtitle="هشدار نقطه سفارش، ارزش موجودی و سوخت ۳۰ روز اخیر"
        v-if="widgetState.inventory_alerts && inventoryAlerts"
      >
        <section class="lost-kpis">
          <article>
            <small>اقلام زیر نقطه سفارش</small>
            <strong :class="{ 'danger-text': inventoryAlerts.below_reorder > 0 }">{{ inventoryAlerts.below_reorder }}</strong>
          </article>
          <article>
            <small>ارزش کل موجودی</small>
            <strong>{{ formatMoney(inventoryAlerts.stock_value_total, currency) }}</strong>
          </article>
          <article>
            <small>ضایعات/خسارت ۳۰ روز</small>
            <strong>{{ formatMoney(inventoryAlerts.waste_damage_30d_value, currency) }}</strong>
          </article>
          <article>
            <small>سفارش‌های خرید باز</small>
            <strong>{{ inventoryAlerts.open_purchase_orders }}</strong>
          </article>
        </section>
        <p class="hint-line">
          <a href="/management/inventory">رفتن به انبارداری هوشمند ←</a>
        </p>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        title="سفارش های از دست رفته"
        :subtitle="`کل سفارش ها: ${lostOrders.summary.total}`"
        v-if="widgetState.lost_orders"
      >
        <section class="lost-kpis">
          <article>
            <small>کل کم شدن سفارش ها</small>
            <strong>{{ lostOrders.summary.lost_total }}</strong>
          </article>
          <article>
            <small>لغو صورتحساب</small>
            <strong>{{ lostOrders.summary.cancelled_invoice }}</strong>
          </article>
          <article>
            <small>کل اوت شدن سفارش ها</small>
            <strong>{{ lostOrders.summary.voided }}</strong>
          </article>
        </section>
        <ManagementLineChart
          :labels="lostOrders.labels"
          :series="[
            {
              key: 'lost',
              label: 'سفارش های از دست رفته',
              color: chartPalette.danger,
              values: lostOrders.values,
            },
          ]"
        />
      </ManagementSurfaceCard>
    </template>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import PersianDateInput from '@/components/PersianDateInput.vue'
import ManagementDataTable from '@/components/management/ManagementDataTable.vue'
import ManagementLineChart from '@/components/management/bi/ManagementLineChart.vue'
import ManagementBarList from '@/components/management/bi/ManagementBarList.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementNoteField from '@/components/management/ManagementNoteField.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import {
  getManagementDashboard,
  getManagementDashboardLayout,
  getManagementInventoryAlertsSummary,
  setManagementDashboardLayout,
  getManagementPOSBoot,
  getManagementPOSShiftSettings,
  getManagementReportCashierPerformance,
  getManagementReportCancellations,
  getManagementReportChannelSplit,
  getManagementReportOrderStatus,
  getManagementReportSalesHourly,
  getManagementReportSalesTrend,
  getManagementReportTopProducts,
  getManagementSiteSettings,
  listManagementCustomers,
  listManagementOrders,
  listManagementProducts,
  setManagementPOSShiftSettings,
  setManagementSiteSettings,
} from '@/utils/api'
import { formatMoney } from '@/utils/format'
import {
  buildChannelDistribution,
  buildCustomerAnalytics,
  buildHourlySeries,
  buildKpiSet,
  buildLostOrderDataset,
  buildMenuEngineering,
  buildPerformerRows,
  buildSalesFinancialSeries,
  getPreviousWindow,
} from '@/utils/managementBi'

const loading = ref(false)
const error = ref('')
const warnings = ref([])
const customizeOpen = ref(false)
const currency = ref('IRR')

const today = new Date()
const start = new Date(today)
start.setDate(today.getDate() - 17)

const filters = reactive({
  date_from: start.toISOString().slice(0, 10),
  date_to: today.toISOString().slice(0, 10),
})

const widgetState = reactive({
  pos_shift: true,
  kpis: true,
  sales_financial: true,
  time_trend: true,
  cost_control: true,
  performers: true,
  channels: true,
  crm: true,
  menu: true,
  inventory_alerts: true,
  lost_orders: true,
})

const widgetOptions = [
  { key: 'pos_shift', label: 'تنظیمات شیفت POS' },
  { key: 'kpis', label: 'KPI ها' },
  { key: 'sales_financial', label: 'فروش/هزینه' },
  { key: 'time_trend', label: 'روند زمانی فروش' },
  { key: 'cost_control', label: 'کاست کنترل' },
  { key: 'performers', label: 'برترین ها' },
  { key: 'channels', label: 'کانال های فروش' },
  { key: 'crm', label: 'تحلیل مشتریان' },
  { key: 'menu', label: 'مهندسی منو' },
  { key: 'inventory_alerts', label: 'هشدارهای انبار' },
  { key: 'lost_orders', label: 'سفارش های از دست رفته' },
]

const chartPalette = Object.freeze({
  primary: 'var(--accent-green)',
  accent: 'var(--accent-gold)',
  danger: 'var(--danger)',
  warning: 'var(--warning)',
  success: 'var(--success)',
})

const salesLegendOptions = [
  { key: 'sales', label: 'فروش کل', color: chartPalette.primary },
  { key: 'cost', label: 'هزینه', color: chartPalette.warning },
  { key: 'returns', label: 'فروش بازگشتی', color: chartPalette.danger },
  { key: 'expected', label: 'انتظار فروش', color: chartPalette.accent },
]

const salesLegendState = reactive({
  sales: true,
  cost: true,
  returns: true,
  expected: true,
})

const timeTrendMode = ref('day')
const performerMode = ref('staff')
const channelMode = ref('money')
const specialCustomerMode = ref('discount')
const salesListMode = ref('top')
const popularityListMode = ref('popular')

const kpis = ref([])
const salesSeries = ref({ labels: [], salesValues: [], expectedValues: [], costValues: [], returnValues: [], costPercentValues: [] })
const hourlySeries = ref({ labels: [], salesValues: [], expectedValues: [] })
const channelRowsRaw = ref([])
const cashierRowsRaw = ref([])
const ordersCurrent = ref([])
const customerAnalytics = ref({
  labels: [],
  newSeries: [],
  returningSeries: [],
  loyalty: { loyal: 0, near_loyal: 0, new_customer: 0, lost: 0 },
  values: { best: 0, high_volume: 0, frequent: 0, at_risk: 0 },
  totalCustomers: 0,
  discountRows: [],
  debtRows: [],
})
const menuEngineering = ref({
  matrix: { stars: 0, puzzles: 0, plowhorses: 0, dogs: 0 },
  bestSelling: [],
  lowSelling: [],
  popular: [],
  unpopular: [],
})
const dashboardNutrition = ref({})
const lostOrders = ref({ summary: { total: 0, lost_total: 0, cancelled_invoice: 0, voided: 0 }, labels: [], values: [] })
const inventoryAlerts = ref(null)

async function loadInventoryAlerts() {
  try {
    inventoryAlerts.value = await getManagementInventoryAlertsSummary()
  } catch (_) {
    inventoryAlerts.value = null
  }
}
const productCategoryMap = ref({})
const courierFleet = ref({ courier_count: 0, active_courier_count: 0, vehicle_count: 0, active_vehicle_count: 0 })

const specialColumns = [
  { key: 'customer_name', label: 'مشتری' },
  { key: 'total_spent', label: 'مبلغ سفارش (ریال)' },
  { key: 'focus_value', label: 'کل تخفیف / بدهی (ریال)' },
]

const menuColumns = [
  { key: 'product', label: 'محصول' },
  { key: 'amount', label: 'مبلغ فروش (ریال)' },
  { key: 'qty', label: 'تعداد فروش' },
  { key: 'status', label: 'وضعیت' },
]

const warningText = computed(() => warnings.value.join(' | '))
const posShiftSaving = ref(false)
const posShiftMessage = ref('')
const posShiftError = ref('')
const menuHighlightEnabled = ref(true)
const menuHighlightLoading = ref(false)
const menuHighlightSaving = ref(false)
const menuHighlightError = ref('')
const menuHighlightMessage = ref('')
const posShiftForm = reactive({
  opening: {
    enabled: true,
    time: '08:00',
    cash_float: 0,
    checklist_required: true,
    note_template: '',
  },
  closing: {
    enabled: true,
    time: '23:00',
    expected_cash: 0,
    tolerance: 0,
    checklist_required: true,
    note_template: '',
  },
})

const todayLabel = computed(() => {
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long',
    }).format(new Date())
  } catch (dateErr) {
    return 'امروز'
  }
})

const rangeLabel = computed(() => {
  const from = formatPersianDate(filters.date_from)
  const to = formatPersianDate(filters.date_to)
  return `${from} تا ${to}`
})

const salesChart = computed(() => {
  const series = []
  if (salesLegendState.sales) {
    series.push({ key: 'sales', label: 'فروش کل', color: chartPalette.primary, values: salesSeries.value.salesValues })
  }
  if (salesLegendState.cost && hasCostData.value) {
    series.push({ key: 'cost', label: 'هزینه', color: chartPalette.warning, values: salesSeries.value.costValues })
  }
  if (salesLegendState.returns) {
    series.push({ key: 'returns', label: 'فروش بازگشتی', color: chartPalette.danger, values: salesSeries.value.returnValues })
  }
  if (salesLegendState.expected) {
    series.push({ key: 'expected', label: 'انتظار فروش', color: chartPalette.accent, values: salesSeries.value.expectedValues })
  }

  return {
    labels: salesSeries.value.labels,
    series,
  }
})

const hasCostData = computed(() => Boolean(salesSeries.value.hasCostData))

const timeTrendChart = computed(() => {
  if (timeTrendMode.value === 'hour') {
    return {
      labels: hourlySeries.value.labels,
      series: [
        { key: 'sales_hour', label: 'مبلغ فروش', color: chartPalette.primary, values: hourlySeries.value.salesValues },
        { key: 'expected_hour', label: 'انتظار فروش', color: chartPalette.accent, values: hourlySeries.value.expectedValues },
      ],
    }
  }

  return {
    labels: salesSeries.value.labels,
    series: [
      { key: 'sales_day', label: 'مبلغ فروش', color: chartPalette.primary, values: salesSeries.value.salesValues },
      { key: 'expected_day', label: 'انتظار فروش', color: chartPalette.accent, values: salesSeries.value.expectedValues },
    ],
  }
})

const costControlChart = computed(() => ({
  labels: salesSeries.value.labels,
  series: hasCostData.value
    ? [
        {
          key: 'cost_percent',
          label: 'درصد کاست',
          color: chartPalette.warning,
          values: salesSeries.value.costPercentValues,
        },
      ]
    : [],
}))

const performerRows = computed(() =>
  buildPerformerRows({
    mode: performerMode.value,
    orders: ordersCurrent.value,
    cashierRows: cashierRowsRaw.value,
    productMap: productCategoryMap.value,
  }),
)

const channelRows = computed(() => buildChannelDistribution(channelRowsRaw.value, channelMode.value).slice(0, 10))

const customerLineChart = computed(() => ({
  labels: customerAnalytics.value.labels,
  series: [
    { key: 'new', label: 'مشتریان جدید', color: chartPalette.success, values: customerAnalytics.value.newSeries },
    { key: 'returning', label: 'مشتریان بازگشتی', color: chartPalette.accent, values: customerAnalytics.value.returningSeries },
  ],
}))

const specialRows = computed(() => {
  const source = specialCustomerMode.value === 'discount' ? customerAnalytics.value.discountRows : customerAnalytics.value.debtRows
  return source.map((row) => ({
    key: row.key,
    customer_name: row.customer_name,
    total_spent: row.total_spent,
    focus_value: specialCustomerMode.value === 'discount' ? row.discount_total : row.debt_total,
  }))
})

const loyaltyCards = computed(() => [
  { key: 'loyal', label: 'مشتریان وفادار', value: customerAnalytics.value.loyalty.loyal },
  { key: 'near_loyal', label: 'مشتری نزدیک به وفاداری', value: customerAnalytics.value.loyalty.near_loyal },
  { key: 'new_customer', label: 'مشتری جدید', value: customerAnalytics.value.loyalty.new_customer },
  { key: 'lost', label: 'مشتری از دست رفته', value: customerAnalytics.value.loyalty.lost },
])

const valueCards = computed(() => [
  { key: 'best', label: 'بهترین مشتریان', value: customerAnalytics.value.values.best },
  { key: 'high_volume', label: 'مشتری با حجم خرید بالا', value: customerAnalytics.value.values.high_volume },
  { key: 'frequent', label: 'مشتری متناوب', value: customerAnalytics.value.values.frequent },
  { key: 'at_risk', label: 'مشتری نامطمئن', value: customerAnalytics.value.values.at_risk },
])

const salesListRows = computed(() => {
  const source = salesListMode.value === 'top' ? menuEngineering.value.bestSelling : menuEngineering.value.lowSelling
  return source.map((row) => ({
    product: row.product,
    amount: row.amount,
    qty: row.qty,
    status: row.amount > 0 ? 'فعال' : 'بدون فروش',
  }))
})

const popularityRows = computed(() => {
  const source = popularityListMode.value === 'popular' ? menuEngineering.value.popular : menuEngineering.value.unpopular
  return source.map((row) => ({
    product: row.product,
    amount: row.amount,
    qty: row.qty,
    status: row.qty > 0 ? 'دارای تقاضا' : 'بدون تقاضا',
  }))
})

const nutritionCards = computed(() => {
  const totals = dashboardNutrition.value || {}
  const toMacro = (value) => {
    const numeric = Number(value || 0)
    if (!Number.isFinite(numeric) || numeric <= 0) {
      return '0'
    }
    if (Math.abs(numeric - Math.round(numeric)) < 1e-8) {
      return Number(Math.round(numeric)).toLocaleString('fa-IR')
    }
    return Number(numeric.toFixed(1)).toLocaleString('fa-IR')
  }

  return [
    { key: 'kcal', label: 'کالری کل', value: `${toMacro(totals.kcal)} kcal` },
    { key: 'protein', label: 'پروتئین کل', value: `${toMacro(totals.protein_g)} g` },
    { key: 'carb', label: 'کربوهیدرات کل', value: `${toMacro(totals.carb_g)} g` },
    { key: 'sugar', label: 'قند کل', value: `${toMacro(totals.sugar_g)} g` },
    { key: 'fat', label: 'چربی کل', value: `${toMacro(totals.fat_g)} g` },
  ]
})

function formatPersianDate(value) {
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value))
  } catch (dateErr) {
    return value
  }
}

function normalizeTimeInput(value, fallback = '00:00') {
  const raw = String(value || '').trim()
  if (!raw) {
    return fallback
  }
  const parts = raw.split(':')
  if (parts.length < 2) {
    return fallback
  }
  const hour = String(parts[0] || '').padStart(2, '0')
  const minute = String(parts[1] || '').padStart(2, '0')
  return `${hour}:${minute}`
}

function normalizeTimePayload(value, fallback = '00:00:00') {
  const raw = String(value || '').trim()
  if (!raw) {
    return fallback
  }
  if (/^\d{2}:\d{2}:\d{2}$/.test(raw)) {
    return raw
  }
  if (/^\d{2}:\d{2}$/.test(raw)) {
    return `${raw}:00`
  }
  return fallback
}

function applyPosShiftSettings(payload = {}) {
  const opening = payload?.opening || {}
  const closing = payload?.closing || {}

  posShiftForm.opening.enabled = Boolean(opening.enabled)
  posShiftForm.opening.time = normalizeTimeInput(opening.time, '08:00')
  posShiftForm.opening.cash_float = Number(opening.cash_float || 0)
  posShiftForm.opening.checklist_required = Boolean(opening.checklist_required)
  posShiftForm.opening.note_template = String(opening.note_template || '')

  posShiftForm.closing.enabled = Boolean(closing.enabled)
  posShiftForm.closing.time = normalizeTimeInput(closing.time, '23:00')
  posShiftForm.closing.expected_cash = Number(closing.expected_cash || 0)
  posShiftForm.closing.tolerance = Number(closing.tolerance || 0)
  posShiftForm.closing.checklist_required = Boolean(closing.checklist_required)
  posShiftForm.closing.note_template = String(closing.note_template || '')
}

async function savePosShiftSettings() {
  posShiftSaving.value = true
  posShiftError.value = ''
  posShiftMessage.value = ''
  try {
    const payload = {
      opening: {
        enabled: posShiftForm.opening.enabled ? 1 : 0,
        time: normalizeTimePayload(posShiftForm.opening.time, '08:00:00'),
        cash_float: Math.max(Number(posShiftForm.opening.cash_float || 0), 0),
        checklist_required: posShiftForm.opening.checklist_required ? 1 : 0,
        note_template: String(posShiftForm.opening.note_template || '').trim(),
      },
      closing: {
        enabled: posShiftForm.closing.enabled ? 1 : 0,
        time: normalizeTimePayload(posShiftForm.closing.time, '23:00:00'),
        expected_cash: Math.max(Number(posShiftForm.closing.expected_cash || 0), 0),
        tolerance: Math.max(Number(posShiftForm.closing.tolerance || 0), 0),
        checklist_required: posShiftForm.closing.checklist_required ? 1 : 0,
        note_template: String(posShiftForm.closing.note_template || '').trim(),
      },
    }
    const result = await setManagementPOSShiftSettings(payload)
    applyPosShiftSettings(result)
    posShiftMessage.value = 'تنظیمات افتتاحیه/اختتامیه با موفقیت ذخیره شد.'
  } catch (saveErr) {
    posShiftError.value = saveErr.message || 'ذخیره تنظیمات شیفت POS ناموفق بود.'
  } finally {
    posShiftSaving.value = false
  }
}

async function loadMenuHighlightSettings() {
  menuHighlightLoading.value = true
  menuHighlightError.value = ''
  menuHighlightMessage.value = ''
  try {
    const payload = await getManagementSiteSettings()
    const settings = payload?.web_settings || {}
    menuHighlightEnabled.value = Number(settings.restaurant_menu_highlight_enabled || 0) === 1
  } catch (loadErr) {
    menuHighlightError.value = loadErr.message || 'خواندن تنظیم سکشن ویژه/پرفروش ناموفق بود.'
  } finally {
    menuHighlightLoading.value = false
  }
}

async function saveMenuHighlightSettings() {
  menuHighlightSaving.value = true
  menuHighlightError.value = ''
  menuHighlightMessage.value = ''
  try {
    await setManagementSiteSettings({
      web_settings: {
        restaurant_menu_highlight_enabled: menuHighlightEnabled.value ? 1 : 0,
      },
    })
    menuHighlightMessage.value = 'تنظیم سکشن ویژه/پرفروش ذخیره شد.'
  } catch (saveErr) {
    menuHighlightError.value = saveErr.message || 'ذخیره تنظیم سکشن ویژه/پرفروش ناموفق بود.'
  } finally {
    menuHighlightSaving.value = false
  }
}

function formatKpiValue(kpi) {
  if (kpi.value === null || kpi.value === undefined || kpi.value === '') {
    return 'ناموجود'
  }
  if (kpi.unit === 'money') {
    return formatMoney(kpi.value || 0, currency.value)
  }
  if (kpi.unit === 'count') {
    return `${Number(kpi.value || 0).toLocaleString('fa-IR')}`
  }
  if (kpi.unit === 'minutes') {
    return `${Number(kpi.value || 0).toLocaleString('fa-IR')} دقیقه`
  }
  if (kpi.unit === 'score') {
    return `${Number(kpi.value || 0).toLocaleString('fa-IR')}`
  }
  return String(kpi.value || 0)
}

function formatDelta(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '-'
  }
  const numeric = Number(value || 0)
  const sign = numeric > 0 ? '+' : ''
  return `${sign}${numeric.toFixed(1)}%`
}

function deltaClass(value) {
  const numeric = Number(value || 0)
  if (numeric > 0) {
    return 'up'
  }
  if (numeric < 0) {
    return 'down'
  }
  return 'flat'
}

async function safeCall(fn, args, fallback, warningsList) {
  try {
    return await fn(args)
  } catch (callErr) {
    warningsList.push(callErr.message || 'بخشی از داده‌ها قابل دریافت نبود.')
    return fallback
  }
}

async function loadDashboard() {
  loading.value = true
  error.value = ''
  const localWarnings = []

  try {
    const prevRange = getPreviousWindow(filters.date_from, filters.date_to)

    const [
      dashboardCurrent,
      dashboardPrev,
      salesTrendCurrent,
      salesTrendPrev,
      salesHourlyCurrent,
      topProductsCurrent,
      channelCurrent,
      cashierCurrent,
      orderStatusCurrent,
      cancellationsCurrent,
      ordersCurrentPayload,
      ordersPrevPayload,
      customersCurrent,
      posBoot,
      posShiftBoot,
      managementProducts,
    ] = await Promise.all([
      safeCall(getManagementDashboard, { date_from: filters.date_from, date_to: filters.date_to }, {}, localWarnings),
      safeCall(getManagementDashboard, prevRange, {}, localWarnings),
      safeCall(getManagementReportSalesTrend, { date_from: filters.date_from, date_to: filters.date_to }, { rows: [] }, localWarnings),
      safeCall(getManagementReportSalesTrend, prevRange, { rows: [] }, localWarnings),
      safeCall(getManagementReportSalesHourly, { date_from: filters.date_from, date_to: filters.date_to }, { rows: [] }, localWarnings),
      safeCall(getManagementReportTopProducts, { date_from: filters.date_from, date_to: filters.date_to }, { rows: [] }, localWarnings),
      safeCall(getManagementReportChannelSplit, { date_from: filters.date_from, date_to: filters.date_to }, { rows: [] }, localWarnings),
      safeCall(getManagementReportCashierPerformance, { date_from: filters.date_from, date_to: filters.date_to }, { rows: [] }, localWarnings),
      safeCall(getManagementReportOrderStatus, { date_from: filters.date_from, date_to: filters.date_to }, { rows: [] }, localWarnings),
      safeCall(getManagementReportCancellations, { date_from: filters.date_from, date_to: filters.date_to }, { rows: [] }, localWarnings),
      safeCall(listManagementOrders, { date_from: filters.date_from, date_to: filters.date_to }, { orders: [] }, localWarnings),
      safeCall(listManagementOrders, prevRange, { orders: [] }, localWarnings),
      safeCall(listManagementCustomers, { date_from: filters.date_from, date_to: filters.date_to }, { customers: [] }, localWarnings),
      safeCall(getManagementPOSBoot, {}, { items: [], currency: 'IRR' }, localWarnings),
      safeCall(getManagementPOSShiftSettings, {}, { opening: {}, closing: {} }, localWarnings),
      safeCall(listManagementProducts, {}, { products: [] }, localWarnings),
    ])

    currency.value = dashboardCurrent.currency || posBoot.currency || 'IRR'

    const currentSales = buildSalesFinancialSeries({
      salesTrendRows: salesTrendCurrent.rows || [],
      cancellationRows: cancellationsCurrent.rows || [],
      dateFrom: filters.date_from,
      dateTo: filters.date_to,
    })

    const previousSales = buildSalesFinancialSeries({
      salesTrendRows: salesTrendPrev.rows || [],
      cancellationRows: [],
      dateFrom: prevRange.date_from,
      dateTo: prevRange.date_to,
    })

    const currentOrders = ordersCurrentPayload.orders || []
    const prevOrders = ordersPrevPayload.orders || []

    const products = managementProducts.products || []
    const stockThreshold = Number(managementProducts.stock?.low_threshold || 5)
    const lowStockCount = products.filter((row) => {
      const qty = Number(row.stock_qty || 0)
      return qty > 0 && qty <= stockThreshold
    }).length
    const outStockCount = products.filter((row) => Number(row.stock_qty || 0) <= 0).length

    salesSeries.value = currentSales
    hourlySeries.value = buildHourlySeries(salesHourlyCurrent.rows || [])
    ordersCurrent.value = currentOrders
    channelRowsRaw.value = channelCurrent.rows || []
    cashierRowsRaw.value = cashierCurrent.rows || []

    const map = {}
    for (const item of posBoot.items || []) {
      if (item.title) {
        map[item.title] = item.category_title || 'بدون دسته بندی'
      }
    }
    productCategoryMap.value = map
    applyPosShiftSettings(posShiftBoot || {})
    posShiftError.value = ''

    kpis.value = buildKpiSet({
      orders: currentOrders,
      salesSeries: currentSales,
      previousOrders: prevOrders,
      previousSalesSeries: previousSales,
      operationalMetrics: dashboardCurrent.operational || {},
      previousOperationalMetrics: dashboardPrev.operational || {},
      lowStockCount,
      outStockCount,
    })

    customerAnalytics.value = buildCustomerAnalytics({
      orders: currentOrders,
      customers: customersCurrent.customers || [],
      dateFrom: filters.date_from,
      dateTo: filters.date_to,
    })

    const dashboardTopProducts = Array.isArray(dashboardCurrent?.top_products) ? dashboardCurrent.top_products : []
    menuEngineering.value = buildMenuEngineering((topProductsCurrent.rows || []).length ? topProductsCurrent.rows || [] : dashboardTopProducts)
    dashboardNutrition.value = dashboardCurrent?.nutrition || {}
    courierFleet.value = dashboardCurrent?.courier_fleet || { courier_count: 0, active_courier_count: 0, vehicle_count: 0, active_vehicle_count: 0 }

    lostOrders.value = buildLostOrderDataset({
      orderStatusRows: orderStatusCurrent.rows || [],
      cancellationRows: cancellationsCurrent.rows || [],
    })

    warnings.value = localWarnings
  } catch (errObj) {
    error.value = errObj.message || 'بارگذاری داشبورد ناموفق بود.'
  } finally {
    loading.value = false
  }
}

let layoutSaveTimer = null
let layoutDirty = false
let layoutAppliedFromServer = false

async function loadDashboardLayoutPreferences() {
  try {
    const payload = await getManagementDashboardLayout()
    const widgets = payload?.layout?.widgets || {}
    for (const key of Object.keys(widgetState)) {
      if (widgets[key] && typeof widgets[key].visible === 'boolean') {
        widgetState[key] = widgets[key].visible
      }
    }
    layoutAppliedFromServer = true
  } catch (_) {
    layoutAppliedFromServer = false
  }
}

function queueDashboardLayoutSave() {
  if (!layoutAppliedFromServer || layoutDirty) {
    return
  }
  window.clearTimeout(layoutSaveTimer)
  layoutSaveTimer = window.setTimeout(async () => {
    try {
      layoutDirty = true
      const widgets = {}
      Object.keys(widgetState).forEach((key, index) => {
        widgets[key] = { visible: Boolean(widgetState[key]), order: index }
      })
      await setManagementDashboardLayout({ widgets })
    } catch (_) {
      // Layout persistence is best-effort; never block the dashboard.
    } finally {
      layoutDirty = false
    }
  }, 600)
}

watch(widgetState, () => {
  queueDashboardLayoutSave()
})

async function initDashboardPage() {
  await Promise.all([loadDashboard(), loadMenuHighlightSettings(), loadDashboardLayoutPreferences(), loadInventoryAlerts()])
}

initDashboardPage()
</script>

<style scoped>
.global-controls {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) 170px 170px auto;
  gap: 0.6rem;
  align-items: end;
}

.control-meta {
  display: grid;
  gap: 0.2rem;
}

.control-meta strong {
  font-size: 0.95rem;
}

.control-meta small {
  color: var(--text-muted);
  font-size: 0.78rem;
}

.global-controls label {
  display: grid;
  gap: 0.2rem;
  font-size: 0.78rem;
}

.window-line {
  margin: 0.55rem 0 0;
  color: var(--text-muted);
  font-size: 0.78rem;
}

.widget-toggle-grid {
  margin-top: 0.7rem;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.45rem;
}

.widget-toggle-grid label {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.78rem;
}

.menu-highlight-control {
  margin-top: 0.7rem;
  padding-top: 0.7rem;
  border-top: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.menu-highlight-control .check-row {
  display: inline-flex;
  align-items: center;
  gap: 0.38rem;
  font-size: 0.78rem;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.6rem;
}

.kpi-card {
  display: grid;
  gap: 0.22rem;
}

.kpi-card small {
  color: var(--text-muted);
  font-size: 0.74rem;
}

.kpi-card strong {
  font-size: 0.95rem;
}

.kpi-foot {
  display: flex;
  justify-content: space-between;
  gap: 0.35rem;
  align-items: center;
}

.delta {
  font-size: 0.74rem;
  font-weight: 600;
}

.delta.up {
  color: var(--success);
}

.delta.down {
  color: var(--danger);
}

.delta.flat {
  color: var(--text-muted);
}

.mini-link {
  justify-self: start;
  font-size: 0.72rem;
  color: var(--accent);
}

.pos-shift-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.7rem;
}

.pos-shift-box {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.17);
  border-radius: 14px;
  background: rgb(var(--palette-eggshell-rgb) / 0.52);
  padding: 0.6rem;
  display: grid;
  gap: 0.42rem;
}

.pos-shift-box h4 {
  margin: 0;
  font-size: 0.88rem;
}

.pos-shift-box label {
  display: grid;
  gap: 0.18rem;
  font-size: 0.76rem;
}

.pos-shift-box .check-row {
  display: inline-flex;
  align-items: center;
  gap: 0.38rem;
}

.pos-shift-actions {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.58rem;
}

.panel-grid,
.crm-grid,
.menu-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.7rem;
}

.legend-checks,
.toggle-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.5rem;
}

.legend-checks label,
.toggle-row button {
  font-size: 0.76rem;
}

.toggle-row button {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  background: #fff;
  border-radius: 999px;
  padding: 0.28rem 0.7rem;
  cursor: pointer;
}

.toggle-row button.active {
  background: var(--accent-green);
  color: #fff;
}

.mini-matrix {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem;
}

.mini-matrix article {
  border-radius: 12px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  background: rgb(var(--palette-eggshell-rgb) / 0.48);
  padding: 0.45rem;
  display: grid;
  gap: 0.2rem;
}

.mini-matrix small {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.mini-matrix strong {
  font-size: 0.9rem;
}

.mini-matrix a {
  font-size: 0.72rem;
  color: var(--accent);
}

.nutrition-summary-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.5rem;
}

.nutrition-summary-grid article {
  border-radius: 12px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  background: rgb(var(--palette-eggshell-rgb) / 0.48);
  padding: 0.45rem;
  display: grid;
  gap: 0.2rem;
}

.nutrition-summary-grid small {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.nutrition-summary-grid strong {
  font-size: 0.9rem;
}

.lost-kpis {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.5rem;
  margin-bottom: 0.6rem;
}

.lost-kpis article {
  border-radius: 12px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.15);
  background: rgb(var(--palette-eggshell-rgb) / 0.5);
  padding: 0.45rem;
}

.lost-kpis small {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.lost-kpis strong.danger-text {
  color: var(--danger, #b84f4f);
}
.lost-kpis strong {
  display: block;
  margin-top: 0.2rem;
}

.hint,
.hint-line {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.76rem;
}

.error {
  margin: 0;
  color: var(--danger);
}

@media (max-width: 1120px) {
  .kpi-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .global-controls {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .nutrition-summary-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 880px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .panel-grid,
  .crm-grid,
  .menu-grid,
  .nutrition-summary-grid,
  .pos-shift-grid,
  .widget-toggle-grid,
  .lost-kpis,
  .mini-matrix {
    grid-template-columns: 1fr;
  }

  .global-controls {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 520px) {
  .kpi-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
