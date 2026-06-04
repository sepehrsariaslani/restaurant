<template>
  <ManagementPageScaffold class="pos-theme" title="POS مدیریت" subtitle="فروشگاه ساده با BOM، بارکد وزنی و اتصال سخت افزار">
    <section class="ticket-tabs">
      <div
        v-for="(ticket, index) in ticketSessions"
        :key="ticket.id"
        :class="{ active: activeTicketId === ticket.id }"
        class="ticket-tab-group"
      >
        <button type="button" class="ticket-tab" @click="switchToTicket(ticket.id)">
          {{ ticketLabel(ticket, index) }}
        </button>
        <button type="button" class="ticket-tab-close" title="بستن فاکتور" @click.stop="closeTicketTab(ticket.id)">×</button>
      </div>
      <button type="button" class="ticket-tab new" @click="createNewTicketTab">+ فاکتور جدید</button>
    </section>

    <section class="pos-status-bar">
      <div class="pos-status-left">
        <span class="shift-dot" :class="posProfileSummary.has_open_shift ? 'shift-open' : 'shift-closed'"></span>
        <strong class="pos-status-name">{{ posProfileSummary.title || posProfileSummary.name || 'POS' }}</strong>
        <span class="pos-status-sep">|</span>
        <span class="pos-status-shift">{{ posProfileSummary.has_open_shift ? 'شیفت باز' : 'شیفت بسته' }}</span>
        <span class="pos-status-method">{{ payment.method === 'card' ? '💳 کارت' : '💵 نقد' }}</span>
      </div>
      <div class="pos-status-right">
        <button type="button" class="pos-info-toggle" @click="posInfoExpanded = !posInfoExpanded">
          {{ posInfoExpanded ? '▲ بستن' : '▼ جزئیات POS' }}
        </button>
        <a class="pos-settings-link" href="/management/pos_profile">⚙</a>
      </div>
    </section>

    <section class="pos-info-panel" v-if="posInfoExpanded">
      <div class="pos-info-item" v-if="posProfileSummary.company">
        <span class="pos-info-label">شرکت</span>
        <strong>{{ posProfileSummary.company }}</strong>
      </div>
      <div class="pos-info-item" v-if="posProfileSummary.warehouse">
        <span class="pos-info-label">انبار</span>
        <strong>{{ posProfileSummary.warehouse }}</strong>
      </div>
      <div class="pos-info-item" v-if="posProfileSummary.selling_price_list">
        <span class="pos-info-label">لیست قیمت</span>
        <strong>{{ posProfileSummary.selling_price_list }}</strong>
      </div>
      <div class="pos-info-item">
        <span class="pos-info-label">درگاه</span>
        <strong>{{ paymentBoot.provider_label }}</strong>
      </div>
      <div class="pos-info-item" v-if="paymentBoot.terminal_id">
        <span class="pos-info-label">دستگاه</span>
        <strong>{{ paymentBoot.terminal_id }}</strong>
      </div>
      <div class="pos-info-item" v-if="posProfileSummary.shift_name">
        <span class="pos-info-label">شیفت</span>
        <strong>{{ posProfileSummary.shift_name }}</strong>
      </div>
      <div class="pos-info-item" v-if="posProfileSummary.shift_opened_at">
        <span class="pos-info-label">شروع</span>
        <strong>{{ formatInvoiceDateTime(posProfileSummary.shift_opened_at) }}</strong>
      </div>
    </section>

    <section class="table-session-preview">
      <header class="table-session-head" @click="tableExpanded = !tableExpanded">
        <div class="table-head-title">
          <strong>میزهای سالن</strong>
          <span class="count-badge">{{ tableOptions.length }}</span>
          <span class="occupied-badge" v-if="occupiedTableCount">{{ occupiedTableCount }} اشغال</span>
        </div>
        <div class="table-head-right">
          <button type="button" class="icon-refresh-btn" @click.stop="loadPOSBoot" title="بروزرسانی">↻</button>
          <span class="collapse-arrow">{{ tableExpanded ? '▲' : '▼' }}</span>
        </div>
      </header>

      <template v-if="tableExpanded">
        <div class="table-grid">
          <article
            v-for="table in tableOptions"
            :key="table.name"
            class="table-cell"
            :class="[
              `status-${String(table.status || '').toLowerCase()}`,
              { active: selectedDineInTable?.name === table.name },
            ]"
            @click="selectDineInTable(table)"
          >
            <span class="table-cell-name">{{ table.label }}</span>
            <span class="table-cell-time" v-if="table.occupied_minutes">{{ formatOccupiedMinutes(table.occupied_minutes) }}</span>
            <span class="table-cell-orders" v-if="table.pending_orders">{{ toFaDigits(table.pending_orders) }} سفارش</span>
            <span class="table-cell-empty" v-else-if="table.status === 'empty'">آزاد</span>
          </article>
        </div>

        <p class="muted" v-if="tablePreviewLoading">در حال دریافت سفارش‌های میز...</p>
        <p class="error" v-else-if="tablePreviewError">{{ tablePreviewError }}</p>
        <template v-else-if="selectedDineInTable">
          <div class="table-detail-bar">
            <div class="table-detail-info">
              <strong>{{ selectedDineInTable.label }}</strong>
              <span v-if="selectedTablePreview?.totals?.session_grand_total">
                جمع: {{ formatMoney(selectedTablePreview.totals.session_grand_total, currency) }}
              </span>
              <span v-if="selectedTableCustomer.name">👤 {{ selectedTableCustomer.name }}</span>
              <span v-if="selectedTableCustomer.guest_count">{{ toFaDigits(selectedTableCustomer.guest_count) }} نفر</span>
            </div>
            <div class="table-detail-actions">
              <button type="button" class="secondary-btn" @click="assignCustomerToSelectedTable">
                ثبت مشتری
              </button>
              <button
                type="button"
                class="secondary-btn danger"
                :disabled="!selectedTablePreview?.session?.name"
                @click="clearSelectedTableSession"
              >
                خالی کردن میز
              </button>
              <template v-if="selectedTablePreview?.session?.name">
                <SearchableDropdown
                  v-model="moveTableTarget"
                  :options="movableTableDropdownOptions"
                  placeholder="انتقال به میز..."
                  search-placeholder="جستجوی میز..."
                  include-empty-option
                  empty-label="انتقال به میز..."
                  tone="dark"
                />
                <button type="button" class="primary-btn" :disabled="!moveTableTarget" @click="moveSelectedTableSession">
                  انتقال
                </button>
                <template v-if="mergeableTableDropdownOptions.length">
                  <SearchableDropdown
                    v-model="mergeTableTarget"
                    :options="mergeableTableDropdownOptions"
                    placeholder="ترکیب با میز..."
                    search-placeholder="جستجوی میز..."
                    include-empty-option
                    empty-label="ترکیب با میز..."
                    tone="dark"
                  />
                  <button type="button" class="primary-btn merge-btn" :disabled="!mergeTableTarget" @click="mergeSelectedTableSession">
                    ترکیب
                  </button>
                </template>
                <button
                  v-if="confirmedDineInOrders.length"
                  type="button"
                  class="secondary-btn split-bill-btn"
                  @click="showSplitBill = true"
                >
                  تقسیم صورتحساب
                </button>
              </template>
            </div>
          </div>
        </template>
        <p class="muted" v-else-if="!tablePreviewLoading && !tablePreviewError">یک میز را انتخاب کنید.</p>
      </template>
    </section>

    <PosHeaderBar
      ref="headerBarRef"
      :customer-query="form.customer_query"
      :customer-type="form.customer_type"
      :customer-options="customerOptions"
      :guest-count="form.guest_count"
      :date-label="dateLabel"
      :hardware-status="hardwareStatus"
      :hardware-loading="hardwareLoading"
      :is-offline="isOffline"
      @close="closePOS"
      @add-customer="addQuickCustomer"
      @update:customer-query="setCustomerQuery"
      @select-customer="selectCustomerFromHistory"
      @create-customer="createCustomerFromQuery"
      @update:customer-type="form.customer_type = $event"
      @update:guest-count="form.guest_count = $event"
      @refresh-hardware="refreshHardwareStatus"
    />

    <p class="offline-banner" v-if="isOffline">اینترنت قطع است. بعد از وصل شدن اینترنت، همگام سازی را بررسی کنید.</p>
    <p class="sync-banner" v-if="syncReminder">{{ syncReminder }}</p>
    <p class="error" v-if="error">{{ error }}</p>
    <p class="success" v-if="successMessage">{{ successMessage }}</p>

    <section class="open-invoices-panel">
      <header class="open-invoices-head" @click="openInvoicesExpanded = !openInvoicesExpanded">
        <div class="open-invoices-title">
          <strong>فاکتورهای باز</strong>
          <span class="count-badge" v-if="openInvoices.length">{{ openInvoices.length }}</span>
          <span class="count-badge empty" v-else-if="!openInvoicesLoading">صفر</span>
        </div>
        <div class="open-inv-head-right">
          <button type="button" class="icon-refresh-btn" @click.stop="loadOpenInvoices" title="بروزرسانی">↻</button>
          <span class="collapse-arrow">{{ openInvoicesExpanded ? '▲' : '▼' }}</span>
        </div>
      </header>

      <template v-if="openInvoicesExpanded">
      <p class="muted" v-if="openInvoicesLoading">در حال دریافت فاکتورهای باز...</p>
      <p class="error" v-else-if="openInvoiceError">{{ openInvoiceError }}</p>
      <p class="muted" v-else-if="!openInvoices.length">فاکتور بازی وجود ندارد.</p>

      <template v-else>
        <div class="open-invoice-strip">
          <article
            v-for="invoice in openInvoices"
            :key="invoice.invoice_key"
            class="open-invoice-card"
            :class="{ active: selectedOpenInvoice?.invoice_key === invoice.invoice_key }"
            @click="selectOpenInvoice(invoice)"
          >
            <strong>{{ invoice.order_code }}</strong>
            <small>{{ invoice.customer_name || 'POS Customer' }}</small>
            <small>{{ formatMoney(invoice.grand_total || 0, currency) }}</small>
            <small>{{ formatInvoiceDateTime(invoice.created_at) }}</small>
          </article>
        </div>

        <div class="open-invoice-detail" v-if="selectedOpenInvoiceDetail?.order">
          <header>
            <div>
              <strong>جزئیات {{ selectedOpenInvoiceDetail.order.order_code }}</strong>
              <small>
                وضعیت: {{ formatStatus(selectedOpenInvoiceDetail.order.status) }} | پرداخت:
                {{ selectedOpenInvoiceDetail.order.payment_status || 'pending' }}
              </small>
            </div>
            <div class="open-invoice-actions">
              <button type="button" class="secondary-btn" @click="applySelectedOpenInvoiceProfile">
                انتخاب فاکتور
              </button>
              <button type="button" class="primary-btn" :disabled="settlingOpenInvoice" @click="settleSelectedOpenInvoice">
                {{ settlingOpenInvoice ? 'در حال ثبت پرداخت...' : 'ثبت پرداخت فاکتور' }}
              </button>
            </div>
          </header>

          <ul>
            <li v-for="(item, idx) in selectedOpenInvoiceDetail.order.items || []" :key="`${idx}-${item.title}`">
              <span>{{ item.title }}</span>
              <span>{{ formatCompactNumber(item.qty, 2) }}</span>
              <span>{{ formatMoney(item.line_total || 0, currency) }}</span>
            </li>
          </ul>
        </div>
      </template>
      </template>
    </section>

    <section class="pos-shell" dir="rtl">
      <PosCategorySidebar
        class="categories-col"
        :categories="categories"
        :selected-category="selectedCategory"
        :loading="loading"
        @update:selected-category="selectedCategory = $event"
      />

      <PosProductPanel
        class="products-col"
        :products="filteredProducts"
        :loading="loading"
        :error="loading ? '' : productError"
        :search-term="search"
        :scanner-input="scannerInput"
        :scanner-feedback="scannerFeedback"
        :product-view="productView"
        :quantity-map="productQtyMap"
        :fallback-image="fallbackImage"
        :currency="currency"
        @update:search-term="search = $event"
        @update:product-view="productView = $event"
        @update:scanner-input="scannerInput = $event"
        @scan-scale="handleScaleBarcodeScan"
        @increment-product="incrementProduct"
        @decrement-product="decrementProduct"
        @open-bom="openCustomizationSheet"
      />

      <PosCartPanel
        ref="cartPanelRef"
        class="cart-col"
        :cart-lines="cart"
        :selected-line-id="selectedCartLineId"
        :currency="currency"
        :order-mode="form.order_mode"
        :place="form.place"
        :place-options="placeOptions"
        :table-orders="selectedDineInOrders"
        :table-preview-loading="tablePreviewLoading"
        :selected-table-label="selectedDineInTable?.label || ''"
        :can-print-table-orders="confirmedDineInOrders.length > 0"
        :note="form.note"
        :payment-method="payment.method"
        :payment-reference="payment.reference_no"
        :payment-rrn="payment.rrn"
        :payment-boot="paymentBoot"
        :financial="financial"
        :totals="totals"
        :submitting="submitting"
        @update:selected-line-id="selectedCartLineId = $event"
        @update:order-mode="setOrderMode"
        @update:place="form.place = $event"
        @update:note="form.note = $event"
        @update:payment-method="payment.method = $event"
        @update:payment-reference="payment.reference_no = $event"
        @update:payment-rrn="payment.rrn = $event"
        @patch-financial="patchFinancial"
        @increment-line="setCartQty($event, Number($event.qty || 0) + 1)"
        @decrement-line="setCartQty($event, Number($event.qty || 0) - 1)"
        @remove-line="setCartQty($event, 0)"
        @edit-line-note="editLineNote"
        @edit-line-customization="openLineCustomizationEditor"
        @clear-cart="clearCart"
        @verify-credit="verifyCreditCard"
        @verify-coupon="verifyCoupon"
        @update-table-order-item="changeTableOrderItemQty($event.order, $event.item, $event.delta)"
        @print-confirmed-table="printConfirmedTableOrders"
        @submit-order="submitPOSOrder(false)"
        @submit-and-pay="submitPOSOrder(true)"
        @print-ticket="openPrintEditor"
      />
    </section>

    <PosBomSheet
      :open="customizationSheet.open"
      :loading="customizationSheet.loading"
      :error="customizationSheet.error"
      :item="customizationSheet.item"
      :ingredients="customizationSheet.ingredients"
      :modifier-groups="customizationSheet.modifierGroups"
      :customization="customizationSheet.customization"
      :qty="customizationSheet.qty"
      :preview="sheetPreview"
      :currency="currency"
      :confirm-label="customizationSheet.editing_line_id ? 'ذخیره تغییرات' : 'افزودن به سبد'"
      @close="closeCustomizationSheet"
      @update:qty="customizationSheet.qty = $event"
      @update-customization="setSheetCustomization"
      @update-modifiers="setSheetModifiers"
      @confirm="confirmCustomizationAdd"
    />

    <div v-if="printEditorOpen" class="print-editor-backdrop" @click.self="closePrintEditor">
      <section class="print-editor-sheet">
        <header class="print-editor-head">
          <div>
            <h3>پیش نمایش چاپ + cart-list</h3>
            <p>از همین صفحه می توانید آیتم ها را ویرایش کنید و بعد چاپ بگیرید.</p>
          </div>
          <div class="print-editor-actions">
            <button type="button" class="secondary-btn" @click="closePrintEditor">بستن</button>
            <button type="button" class="primary-btn" :disabled="!cart.length" @click="printCurrentTicket">چاپ نهایی</button>
          </div>
        </header>

        <div class="print-meta-editor">
          <label>
            نام فروشگاه
            <input
              class="input dark-input"
              :value="receiptSettings.store_name"
              @input="updateReceiptSetting('store_name', $event.target.value)"
              placeholder="مثال: وی درخت"
            />
          </label>
          <label>
            شماره تماس فروشگاه
            <input
              class="input dark-input"
              :value="receiptSettings.store_phone"
              @input="updateReceiptSetting('store_phone', $event.target.value)"
              placeholder="مثال: 021xxxxxxx"
            />
          </label>
          <label>
            شماره فاکتور (اختیاری)
            <input
              class="input dark-input"
              :value="receiptSettings.manual_invoice_no"
              @input="receiptSettings.manual_invoice_no = $event.target.value"
              placeholder="خالی بگذارید تا خودکار ساخته شود"
            />
          </label>
        </div>

        <div class="print-editor-grid">
          <aside class="print-editor-cart">
            <h4>cart-list</h4>
            <p class="muted" v-if="!cart.length">سبد خرید خالی است.</p>
            <div v-else class="print-editor-list">
              <article v-for="line in cart" :key="line.line_id" class="print-editor-row">
                <div class="print-editor-row-main">
                  <strong>{{ line.title }}</strong>
                  <small>{{ formatMoney((Number(line.qty || 0) * Number(line.price || 0)), currency) }}</small>
                  <small v-if="line.note">یادداشت: {{ line.note }}</small>
                </div>
                <div class="print-editor-row-actions">
                  <button type="button" @click="setCartQty(line, Number(line.qty || 0) - 1)">-</button>
                  <span>{{ formatCompactNumber(line.qty, 3) }}</span>
                  <button type="button" @click="setCartQty(line, Number(line.qty || 0) + 1)">+</button>
                  <button
                    v-if="canEditCustomizationLine(line)"
                    type="button"
                    class="ghost-btn"
                    @click="openLineCustomizationEditor(line)"
                  >
                    BOM
                  </button>
                  <button type="button" class="ghost-btn" @click="editLineNote(line)">یادداشت</button>
                  <button type="button" class="danger-btn" @click="setCartQty(line, 0)">حذف</button>
                </div>
              </article>
            </div>
          </aside>

          <section class="print-editor-preview">
            <div class="receipt-preview-host" v-html="receiptPreviewHtml"></div>
          </section>
        </div>
      </section>
    </div>

    <TableSplitBillSheet
      :open="showSplitBill"
      :orders="confirmedDineInOrders"
      :currency="currency"
      :table-label="selectedDineInTable?.label || ''"
      @close="showSplitBill = false"
    />
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import PosHeaderBar from '@/components/management/pos/PosHeaderBar.vue'
import PosCategorySidebar from '@/components/management/pos/PosCategorySidebar.vue'
import PosProductPanel from '@/components/management/pos/PosProductPanel.vue'
import PosCartPanel from '@/components/management/pos/PosCartPanel.vue'
import PosBomSheet from '@/components/management/pos/PosBomSheet.vue'
import TableSplitBillSheet from '@/components/management/TableSplitBillSheet.vue'
import {
  assignTableSessionCustomer,
  closeTableSession,
  createManagementTableOrderFromPOS,
  createManagementPOSOrder,
  getManagementOrderDetail,
  getTableDetail,
  getTableOverview,
  getItemDetail,
  listManagementOrders,
  markManagementOrderPaid,
  mergeTableSessions,
  moveTableSession,
  getManagementPOSBoot,
  getManagementPOSHardwareStatus,
  reportManagementPOSHardwareEvent,
  updateTableOrderItem,
} from '@/utils/api'
import { formatMoney, formatStatus } from '@/utils/format'
import { createDefaultCustomization, estimateLine, sanitizeCustomization } from '@/utils/itemConfig'
import { calculatePosTotals } from '@/utils/posPricingEngine'

let bootWalletBalance = 0
let bootDefaultPaymentMethod = 'cash'
const RECEIPT_SETTINGS_STORAGE_KEY = 'restaurant-pos-receipt-settings-v1'

function defaultFormState() {
  return {
    customer_query: '',
    customer_name: 'POS Customer',
    mobile: '09120000000',
    customer_type: 'normal',
    guest_count: 1,
    order_mode: 'dine_in',
    place: '',
    note: '',
  }
}

function defaultPaymentState() {
  return {
    method: bootDefaultPaymentMethod,
    reference_no: '',
    rrn: '',
  }
}

function defaultFinancialState() {
  return {
    useWallet: false,
    walletBalance: bootWalletBalance,
    creditCardCode: '',
    couponCode: '',
    discountType: 'fixed',
    discountValue: 0,
    taxExempt: false,
    taxAmount: 0,
    tipAmount: 0,
    serviceType: 'fixed',
    serviceValue: 0,
    printProduction: true,
    createNextInvoice: true,
  }
}

const loading = ref(false)
const submitting = ref(false)
const hardwareLoading = ref(false)
const error = ref('')
const successMessage = ref('')
const scannerFeedback = ref('')
const syncReminder = ref('')
const categories = ref([])
const products = ref([])
const currency = ref('IRR')
const search = ref('')
const selectedCategory = ref('')
const productView = ref('grid')
const scannerInput = ref('')
const selectedCartLineId = ref('')
const customerOptions = ref([])
const printEditorOpen = ref(false)
const receiptSettings = reactive({
  store_name: 'وی درخت',
  store_phone: '',
  manual_invoice_no: '',
})
const ticketSessions = reactive([{ id: 'ticket-1', snapshot: null }])
const activeTicketId = ref('ticket-1')
let ticketCounter = 1
const tableOptions = ref([])
const posInfoExpanded = ref(false)
const openInvoicesExpanded = ref(false)
const tableExpanded = ref(false)
const posProfileSummary = reactive({
  name: '',
  title: '',
  company: '',
  warehouse: '',
  selling_price_list: '',
  currency: 'IRR',
  has_open_shift: false,
  shift_name: '',
  shift_opened_at: '',
  shift_status: '',
})
const selectedTablePreview = ref(null)
const tablePreviewLoading = ref(false)
const tablePreviewError = ref('')
const moveTableTarget = ref('')
const mergeTableTarget = ref('')
const showSplitBill = ref(false)
const openInvoices = ref([])
const openInvoicesLoading = ref(false)
const openInvoiceError = ref('')
const selectedOpenInvoiceKey = ref('')
const selectedOpenInvoiceDetail = ref(null)
const settlingOpenInvoice = ref(false)
const isOffline = ref(typeof navigator !== 'undefined' ? !navigator.onLine : false)
const cart = reactive([])
const detailCache = new Map()
const reminderTimer = ref(null)

const headerBarRef = ref(null)
const cartPanelRef = ref(null)

const hardwareStatus = reactive({
  connected: false,
  message: 'وضعیت سخت افزار بررسی نشده است.',
  latency_ms: 0,
})

const scaleConfig = reactive({
  enabled: true,
  prefix: '20',
  item_code_digits: 5,
  weight_digits: 5,
  checksum_digits: 1,
  weight_divisor: 1000,
})

const paymentBoot = reactive({
  enabled: false,
  supports_card: false,
  provider: 'manual',
  provider_label: 'حالت دستی',
  terminal_id: '',
})

const payment = reactive(defaultPaymentState())

const form = reactive(defaultFormState())

const financial = reactive(defaultFinancialState())

const customizationSheet = reactive({
  open: false,
  loading: false,
  error: '',
  item: null,
  ingredients: [],
  modifierGroups: [],
  customization: {
    ingredient_adjustments: [],
    selected_modifiers: [],
    selected_alternatives: [],
  },
  qty: 1,
  editing_line_id: '',
})

const fallbackImage =
  'https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?w=900&auto=format&fit=crop&q=60'

const dateLabel = computed(() => {
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

const placeOptions = computed(() => {
  if (form.order_mode === 'dine_in') {
    if (tableOptions.value.length) {
      return tableOptions.value.map((row) => row.label)
    }
    return ['میز 1', 'میز 2', 'میز 3', 'میز 4', 'میز VIP']
  }
  if (form.order_mode === 'delivery') {
    return ['پیک 1', 'پیک 2', 'پیک 3', 'ارسال اکسپرس']
  }
  return ['بیرون بر حضوری', 'تحویل کنار سالن']
})

const selectedDineInTable = computed(() => {
  if (form.order_mode !== 'dine_in') {
    return null
  }
  return resolveSelectedDineInTable()
})

const selectedDineInOrders = computed(() => selectedTablePreview.value?.orders || [])
const confirmedDineInOrders = computed(() =>
  selectedDineInOrders.value.filter((order) => String(order.status || '').toLowerCase() !== 'pending'),
)
const movableTableOptions = computed(() => {
  if (!selectedDineInTable.value?.name) {
    return []
  }
  return tableOptions.value.filter((table) => {
    if (table.name === selectedDineInTable.value.name) {
      return false
    }
    return !table.active_session
  })
})
const movableTableDropdownOptions = computed(() =>
  movableTableOptions.value.map((table) => ({
    value: table.name,
    label: table.label,
  })),
)
const mergeableTableOptions = computed(() => {
  if (!selectedDineInTable.value?.name) {
    return []
  }
  return tableOptions.value.filter((table) => {
    if (table.name === selectedDineInTable.value.name) {
      return false
    }
    return !!table.active_session
  })
})
const mergeableTableDropdownOptions = computed(() =>
  mergeableTableOptions.value.map((table) => ({
    value: table.name,
    label: `${table.label} (اشغال)`,
  })),
)
const selectedTableCustomer = computed(() => {
  const fromSession = selectedTablePreview.value?.session || {}
  const fromTable = selectedDineInTable.value || {}
  return {
    name: String(fromSession.customer_name || fromTable.customer_name || '').trim(),
    mobile: String(fromSession.customer_mobile || fromTable.customer_mobile || '').trim(),
    customer_type: String(fromSession.customer_type || fromTable.customer_type || '').trim(),
    guest_count: Number(fromSession.guest_count || fromTable.guest_count || 0),
  }
})
const selectedOpenInvoice = computed(() =>
  openInvoices.value.find((row) => row.invoice_key === selectedOpenInvoiceKey.value) || null,
)

const filteredProducts = computed(() => {
  const query = search.value.trim().toLowerCase()
  return products.value.filter((row) => {
    if (selectedCategory.value && row.category_slug !== selectedCategory.value) {
      return false
    }
    if (!query) {
      return true
    }
    const normalizedQuery = query.replace(/\s+/g, '')
    const title = String(row.title || row.item_name || '').toLowerCase()
    const slug = String(row.slug || row.restaurant_slug || '').toLowerCase()
    const name = String(row.name || row.item_code || '').toLowerCase()
    const code = String(row.code || '').toLowerCase()
    return (
      title.includes(query) ||
      slug.includes(query) ||
      name.includes(query) ||
      code.includes(query) ||
      slug.replace(/\s+/g, '').includes(normalizedQuery) ||
      name.replace(/\s+/g, '').includes(normalizedQuery)
    )
  })
})

const productQtyMap = computed(() => {
  return cart.reduce((acc, line) => {
    const slug = String(line.slug || '').trim()
    if (!slug) {
      return acc
    }
    acc[slug] = Number(acc[slug] || 0) + Number(line.qty || 0)
    return acc
  }, {})
})

const occupiedTableCount = computed(() =>
  tableOptions.value.filter((t) => t.status === 'occupied' || t.status === 'waiting').length,
)

const totals = computed(() =>
  calculatePosTotals({
    cartLines: cart.map((line) => ({
      unit_price: line.price,
      qty: line.qty,
    })),
    discountType: financial.discountType,
    discountValue: financial.discountValue,
    serviceType: financial.serviceType,
    serviceValue: financial.serviceValue,
    taxAmount: financial.taxExempt ? 0 : financial.taxAmount,
    tipAmount: financial.tipAmount,
    useWallet: financial.useWallet,
    walletBalance: financial.walletBalance,
  }),
)

const sheetPreview = computed(() => {
  const basePrice = Number(customizationSheet.item?.base_price || 0)
  const breakdown = estimateLine({
    basePrice,
    qty: Number(customizationSheet.qty || 1),
    ingredients: customizationSheet.ingredients || [],
    modifierGroups: customizationSheet.modifierGroups || [],
    customization: customizationSheet.customization || {},
  })
  return {
    unitPrice: Number(breakdown.unitPrice || basePrice),
    lineTotal: Number(breakdown.lineTotal || 0),
  }
})

const productError = computed(() => {
  if (!filteredProducts.value.length && !loading.value) {
    return 'محصولی با این فیلتر پیدا نشد.'
  }
  return ''
})

function cloneLineForSnapshot(line) {
  const customization = line?.customization
    ? {
        ingredient_adjustments: [...(line.customization.ingredient_adjustments || [])],
        selected_modifiers: [...(line.customization.selected_modifiers || [])],
        selected_alternatives: [...(line.customization.selected_alternatives || [])],
      }
    : {
        ingredient_adjustments: [],
        selected_modifiers: [],
        selected_alternatives: [],
      }

  return {
    ...line,
    customization,
    customization_ingredients: Array.isArray(line?.customization_ingredients)
      ? line.customization_ingredients.map((row) => ({
          key: String(row?.key || '').trim(),
          name: String(row?.name || '').trim(),
          customer_label: String(row?.customer_label || '').trim(),
          is_included_by_default: Number(row?.is_included_by_default || 0),
        }))
      : [],
  }
}

function createEmptyTicketSnapshot() {
  return {
    form: defaultFormState(),
    payment: defaultPaymentState(),
    financial: defaultFinancialState(),
    cart: [],
    selectedLineId: '',
    search: '',
    selectedCategory: '',
    productView: 'grid',
    scannerInput: '',
    scannerFeedback: '',
    successMessage: '',
    errorMessage: '',
  }
}

function captureCurrentTicketSnapshot() {
  return {
    form: { ...form },
    payment: { ...payment },
    financial: { ...financial },
    cart: cart.map((line) => cloneLineForSnapshot(line)),
    selectedLineId: selectedCartLineId.value,
    search: search.value,
    selectedCategory: selectedCategory.value,
    productView: productView.value,
    scannerInput: scannerInput.value,
    scannerFeedback: scannerFeedback.value,
    successMessage: successMessage.value,
    errorMessage: error.value,
  }
}

function applyTicketSnapshot(snapshot) {
  const next = snapshot || createEmptyTicketSnapshot()
  Object.assign(form, defaultFormState(), next.form || {})
  Object.assign(payment, defaultPaymentState(), next.payment || {})
  Object.assign(financial, defaultFinancialState(), next.financial || {})
  cart.splice(0, cart.length, ...((next.cart || []).map((line) => cloneLineForSnapshot(line))))
  selectedCartLineId.value = next.selectedLineId || cart[0]?.line_id || ''
  search.value = String(next.search || '')
  selectedCategory.value = String(next.selectedCategory || '')
  productView.value = String(next.productView || 'grid')
  scannerInput.value = String(next.scannerInput || '')
  scannerFeedback.value = String(next.scannerFeedback || '')
  successMessage.value = String(next.successMessage || '')
  error.value = String(next.errorMessage || '')
}

function getTicketSessionById(id) {
  return ticketSessions.find((ticket) => ticket.id === id) || null
}

function saveActiveTicketSnapshot() {
  const active = getTicketSessionById(activeTicketId.value)
  if (!active) {
    return
  }
  active.snapshot = captureCurrentTicketSnapshot()
}

function ticketLabel(ticket, index) {
  if (ticket.id === activeTicketId.value) {
    const activeName = String(form.customer_name || '').trim()
    return activeName && activeName !== 'POS Customer' ? activeName : `فاکتور ${index + 1}`
  }
  const ticketName = String(ticket.snapshot?.form?.customer_name || '').trim()
  return ticketName && ticketName !== 'POS Customer' ? ticketName : `فاکتور ${index + 1}`
}

function switchToTicket(ticketId) {
  if (!ticketId || ticketId === activeTicketId.value) {
    return
  }
  saveActiveTicketSnapshot()
  const targetTicket = getTicketSessionById(ticketId)
  if (!targetTicket) {
    return
  }
  activeTicketId.value = ticketId
  applyTicketSnapshot(targetTicket.snapshot || createEmptyTicketSnapshot())
}

function createNewTicketTab() {
  saveActiveTicketSnapshot()
  ticketCounter += 1
  const nextId = `ticket-${ticketCounter}`
  const snapshot = createEmptyTicketSnapshot()
  ticketSessions.push({
    id: nextId,
    snapshot,
  })
  activeTicketId.value = nextId
  applyTicketSnapshot(snapshot)
  nextTick(() => {
    headerBarRef.value?.focusCustomerSearch?.()
  })
}

function closeTicketTab(ticketId) {
  if (!ticketId) {
    return
  }

  const ticketIndex = ticketSessions.findIndex((ticket) => ticket.id === ticketId)
  if (ticketIndex < 0) {
    return
  }

  if (ticketSessions.length === 1) {
    const snapshot = createEmptyTicketSnapshot()
    ticketSessions[0].snapshot = snapshot
    activeTicketId.value = ticketSessions[0].id
    applyTicketSnapshot(snapshot)
    return
  }

  const isActive = activeTicketId.value === ticketId
  const fallbackTicketId = ticketSessions[ticketIndex + 1]?.id || ticketSessions[ticketIndex - 1]?.id || ''
  ticketSessions.splice(ticketIndex, 1)

  if (!isActive) {
    return
  }

  activeTicketId.value = fallbackTicketId
  const fallbackTicket = getTicketSessionById(fallbackTicketId)
  applyTicketSnapshot(fallbackTicket?.snapshot || createEmptyTicketSnapshot())
}

function resetCurrentInvoiceState() {
  applyTicketSnapshot(createEmptyTicketSnapshot())
}

function patchFinancial(partial) {
  Object.assign(financial, partial || {})
}

function applyPOSProfileSummary(summary = {}) {
  posProfileSummary.name = String(summary?.name || '').trim()
  posProfileSummary.title = String(summary?.title || '').trim()
  posProfileSummary.company = String(summary?.company || '').trim()
  posProfileSummary.warehouse = String(summary?.warehouse || '').trim()
  posProfileSummary.selling_price_list = String(summary?.selling_price_list || '').trim()
  posProfileSummary.currency = String(summary?.currency || 'IRR').trim() || 'IRR'
  posProfileSummary.has_open_shift = Boolean(summary?.has_open_shift)
  posProfileSummary.shift_name = String(summary?.shift_name || '').trim()
  posProfileSummary.shift_opened_at = String(summary?.shift_opened_at || '').trim()
  posProfileSummary.shift_status = String(summary?.shift_status || '').trim()
}

function normalizeTableSelector(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/میز/g, '')
    .replace(/table/g, '')
}

function buildDineInTableOptions(rows = []) {
  return rows
    .map((row) => {
      const tableNumber = String(row.table_number || '').trim()
      const name = String(row.name || '').trim()
      if (!tableNumber || !name) {
        return null
      }
      const pendingOrders = Number(row.pending_orders || 0)
      const pendingRequests = Number(row.pending_requests || 0)
      const hasAttention = pendingOrders > 0 || pendingRequests > 0 || Boolean(row.has_attention)
      const hasActiveSession = Boolean(String(row.active_session || '').trim())
      const normalizedStatus = hasActiveSession ? 'occupied' : 'empty'
      return {
        name,
        table_number: tableNumber,
        label: `میز ${tableNumber}`,
        status: normalizedStatus === 'occupied' && hasAttention ? 'waiting' : normalizedStatus,
        pending_orders: pendingOrders,
        pending_requests: pendingRequests,
        active_session: String(row.active_session || '').trim(),
        active_since: row.active_since || '',
        occupied_minutes: Number(row.occupied_minutes || 0),
        customer_name: String(row.customer_name || '').trim(),
        customer_mobile: String(row.customer_mobile || '').trim(),
        customer_type: String(row.customer_type || '').trim(),
        guest_count: Number(row.guest_count || 0),
      }
    })
    .filter(Boolean)
}

function resolveSelectedDineInTable() {
  const selectedPlace = String(form.place || '').trim()
  if (!selectedPlace) {
    return null
  }

  const normalizedSelected = normalizeTableSelector(selectedPlace)
  return (
    tableOptions.value.find((table) => {
      if (table.name === selectedPlace || table.table_number === selectedPlace || table.label === selectedPlace) {
        return true
      }
      const tableTokens = [
        normalizeTableSelector(table.name),
        normalizeTableSelector(table.table_number),
        normalizeTableSelector(table.label),
      ]
      return tableTokens.includes(normalizedSelected)
    }) || null
  )
}

async function refreshSelectedDineInTableOrders() {
  if (form.order_mode !== 'dine_in') {
    selectedTablePreview.value = null
    tablePreviewError.value = ''
    tablePreviewLoading.value = false
    return
  }

  const selectedTable = resolveSelectedDineInTable()
  if (!selectedTable?.name) {
    selectedTablePreview.value = null
    tablePreviewError.value = ''
    tablePreviewLoading.value = false
    moveTableTarget.value = ''
    mergeTableTarget.value = ''
    showSplitBill.value = false
    return
  }

  tablePreviewLoading.value = true
  tablePreviewError.value = ''
  try {
    selectedTablePreview.value = await getTableDetail(selectedTable.name)
  } catch (tableErr) {
    selectedTablePreview.value = null
    tablePreviewError.value = tableErr.message || 'دریافت سفارش‌های میز ناموفق بود.'
  } finally {
    tablePreviewLoading.value = false
  }
}

async function selectDineInTable(table) {
  if (!table) {
    return
  }
  form.order_mode = 'dine_in'
  form.place = table.label
  await refreshSelectedDineInTableOrders()
  hydrateFormFromSelectedTableCustomer()
}

function hydrateFormFromSelectedTableCustomer() {
  const customerName = selectedTableCustomer.value.name
  const customerMobile = selectedTableCustomer.value.mobile
  const customerType = selectedTableCustomer.value.customer_type
  const guestCount = Number(selectedTableCustomer.value.guest_count || 0)

  if (!customerName && !customerMobile) {
    return
  }

  if (customerName) {
    form.customer_name = customerName
  }
  if (customerMobile) {
    form.mobile = customerMobile
  }
  if (customerType) {
    form.customer_type = customerType
  }
  if (guestCount > 0) {
    form.guest_count = guestCount
  }
  form.customer_query = customerMobile ? `${form.customer_name} - ${customerMobile}` : form.customer_name
}

async function changeTableOrderItemQty(order, item, delta) {
  if (!order?.name || !item) {
    return
  }
  const normalizedStatus = String(order.status || '').toLowerCase()
  if (!['pending', 'confirmed'].includes(normalizedStatus)) {
    error.value = 'فقط سفارش‌های باز میز قابل ویرایش هستند.'
    return
  }

  const qtyDelta = Number(delta || 0)
  if (!qtyDelta) {
    return
  }

  try {
    await updateTableOrderItem({
      order_name: order.name,
      row_name: item.row_name,
      quantity_delta: qtyDelta,
    })
    successMessage.value = 'سفارش میز به روز شد.'
    await refreshSelectedDineInTableOrders()
  } catch (updateErr) {
    error.value = updateErr.message || 'ویرایش آیتم میز ناموفق بود.'
  }
}

async function assignCustomerToSelectedTable() {
  const selectedTable = resolveSelectedDineInTable()
  if (!selectedTable?.name) {
    error.value = 'ابتدا میز را انتخاب کنید.'
    return
  }

  try {
    await assignTableSessionCustomer({
      table_name: selectedTable.name,
      customer_name: form.customer_name || '',
      mobile: form.mobile || '',
      customer_type: form.customer_type || '',
      guest_count: form.guest_count || 1,
    })
    successMessage.value = `مشتری روی ${selectedTable.label} ثبت شد.`
    await loadPOSBoot()
    form.order_mode = 'dine_in'
    form.place = selectedTable.label
    await refreshSelectedDineInTableOrders()
  } catch (assignErr) {
    error.value = assignErr.message || 'ثبت مشتری روی میز ناموفق بود.'
  }
}

async function clearTableSession(table) {
  if (!table?.name) {
    return
  }
  const activeSession = String(table.active_session || '').trim()
  if (!activeSession) {
    successMessage.value = `${table.label} همین الان خالی است.`
    await loadPOSBoot()
    return
  }
  const confirmed = window.confirm(`مطمئن هستید که می‌خواهید ${table.label} را خالی کنید؟`)
  if (!confirmed) {
    return
  }
  try {
    await closeTableSession(activeSession)
    successMessage.value = `${table.label} خالی شد.`
    await loadPOSBoot()
    if (selectedDineInTable.value?.name === table.name) {
      await refreshSelectedDineInTableOrders()
    }
  } catch (closeErr) {
    error.value = closeErr.message || 'خالی کردن میز ناموفق بود.'
  }
}

async function clearSelectedTableSession() {
  if (!selectedDineInTable.value) {
    error.value = 'ابتدا میز را انتخاب کنید.'
    return
  }
  await clearTableSession(selectedDineInTable.value)
}

async function moveSelectedTableSession() {
  if (!selectedTablePreview.value?.session?.name) {
    error.value = 'ابتدا یک میز فعال انتخاب کنید.'
    return
  }
  if (!moveTableTarget.value) {
    error.value = 'میز مقصد را انتخاب کنید.'
    return
  }

  try {
    await moveTableSession({
      session_name: selectedTablePreview.value.session.name,
      target_table: moveTableTarget.value,
    })
    const movedTarget = tableOptions.value.find((table) => table.name === moveTableTarget.value)
    successMessage.value = `سفارش‌های میز با موفقیت به ${movedTarget?.label || moveTableTarget.value} منتقل شد.`
    moveTableTarget.value = ''
    await loadPOSBoot()
    if (movedTarget) {
      form.order_mode = 'dine_in'
      form.place = movedTarget.label
      await refreshSelectedDineInTableOrders()
    }
  } catch (moveErr) {
    error.value = moveErr.message || 'انتقال میز ناموفق بود.'
  }
}

async function mergeSelectedTableSession() {
  if (!selectedTablePreview.value?.session?.name) {
    error.value = 'ابتدا یک میز فعال انتخاب کنید.'
    return
  }
  if (!mergeTableTarget.value) {
    error.value = 'میز مقصد برای ترکیب را انتخاب کنید.'
    return
  }

  try {
    await mergeTableSessions({
      source_session: selectedTablePreview.value.session.name,
      target_table: mergeTableTarget.value,
    })
    const targetTable = tableOptions.value.find((t) => t.name === mergeTableTarget.value)
    successMessage.value = `میز با موفقیت با ${targetTable?.label || mergeTableTarget.value} ترکیب شد.`
    mergeTableTarget.value = ''
    await loadPOSBoot()
    if (targetTable) {
      form.order_mode = 'dine_in'
      form.place = targetTable.label
      await refreshSelectedDineInTableOrders()
    }
  } catch (mergeErr) {
    error.value = mergeErr.message || 'ترکیب میز ناموفق بود.'
  }
}

function printConfirmedTableOrders() {
  if (!selectedDineInTable.value) {
    error.value = 'ابتدا یک میز انتخاب کنید.'
    return
  }
  if (!confirmedDineInOrders.value.length) {
    error.value = 'سفارش تاییدشده برای چاپ وجود ندارد.'
    return
  }

  const receiptContext = buildConfirmedTableReceiptContext()

  const content = `
    <!doctype html>
    <html lang="fa" dir="rtl">
      <head>
        <meta charset="utf-8" />
        <title>چاپ سفارش تایید شده میز</title>
        <style>${receiptStylesCss()}</style>
      </head>
      <body>
        ${buildReceiptMarkup(receiptContext)}
      </body>
    </html>
  `

  const printWindow = window.open('', '_blank', 'width=520,height=760')
  if (!printWindow) {
    error.value = 'پنجره چاپ باز نشد. لطفا popup blocker را غیرفعال کنید.'
    return
  }
  printWindow.document.open()
  printWindow.document.write(content)
  printWindow.document.close()
  printWindow.focus()
  window.setTimeout(() => {
    printWindow.print()
    printWindow.close()
  }, 180)
}

function setOrderMode(mode) {
  form.order_mode = mode
  form.place = placeOptions.value[0] || ''
}

function setCustomerQuery(value) {
  form.customer_query = value
  const digits = String(value || '').replace(/\D/g, '')
  if (digits.length >= 10) {
    form.mobile = digits.startsWith('0') ? digits : `0${digits.slice(-10)}`
  }
}

function normalizeCustomerMobile(value) {
  const digits = String(value || '').replace(/\D/g, '')
  if (digits.length < 10) {
    return ''
  }
  return digits.startsWith('0') ? digits : `0${digits.slice(-10)}`
}

function toComparableDate(value) {
  const date = new Date(value || '')
  const time = Number(date.getTime())
  return Number.isFinite(time) ? time : 0
}

function buildCustomerOptions(orders = []) {
  const grouped = new Map()

  for (const order of orders) {
    const status = String(order?.status || '').trim().toLowerCase()
    if (status === 'cancelled') {
      continue
    }

    const customerName = String(order?.customer_name || '').trim()
    const mobile = normalizeCustomerMobile(order?.mobile)
    const key = mobile || customerName.toLowerCase()
    if (!key) {
      continue
    }

    const orderTime = toComparableDate(order?.created_at)
    const amount = Number(order?.grand_total || 0)
    const bucket = grouped.get(key) || {
      key,
      label: customerName || mobile || 'مشتری',
      mobile,
      orders_count: 0,
      total_sales: 0,
      last_order_at: 0,
    }

    bucket.orders_count += 1
    bucket.total_sales += Number.isFinite(amount) ? amount : 0
    if (orderTime >= bucket.last_order_at) {
      bucket.last_order_at = orderTime
      if (customerName) {
        bucket.label = customerName
      }
      if (mobile) {
        bucket.mobile = mobile
      }
    }
    grouped.set(key, bucket)
  }

  return [...grouped.values()].sort((left, right) => {
    if (right.orders_count !== left.orders_count) {
      return right.orders_count - left.orders_count
    }
    if (right.total_sales !== left.total_sales) {
      return right.total_sales - left.total_sales
    }
    return right.last_order_at - left.last_order_at
  })
}

function openInvoiceKey(row) {
  return `${String(row?.source || 'web')}::${String(row?.name || row?.order_code || '')}`
}

function isUnpaidOpenInvoice(row) {
  const status = String(row?.status || '').trim().toLowerCase()
  const paymentStatus = String(row?.payment_status || '').trim().toLowerCase()
  if (['delivered', 'cancelled'].includes(status)) {
    return false
  }
  return paymentStatus !== 'paid'
}

function buildOpenInvoices(rows = []) {
  return (rows || [])
    .filter((row) => String(row?.source || '').toLowerCase() === 'web')
    .filter((row) => isUnpaidOpenInvoice(row))
    .map((row) => ({
      ...row,
      invoice_key: openInvoiceKey(row),
    }))
}

function applyOpenInvoiceProfile(order = {}) {
  if (!order || typeof order !== 'object') {
    return
  }
  const customerName = String(order.customer_name || '').trim()
  const mobile = String(order.mobile || '').trim()
  const customerType = String(order.customer_type || '').trim()
  const channel = String(order.channel || '').trim().toLowerCase()

  if (customerName) {
    form.customer_name = customerName
  }
  if (mobile) {
    form.mobile = mobile
  }
  if (customerType) {
    form.customer_type = customerType
  }
  form.customer_query = mobile ? `${form.customer_name} - ${mobile}` : form.customer_name

  if (['takeaway', 'delivery', 'dine_in'].includes(channel)) {
    form.order_mode = channel
  }

  const invoicePaymentMethod = String(order.payment_method || '').trim().toLowerCase()
  if (invoicePaymentMethod === 'card' || invoicePaymentMethod === 'cash') {
    payment.method = invoicePaymentMethod
  }
  payment.reference_no = String(order.payment_reference || '').trim()
  payment.rrn = String(order.payment_rrn || '').trim()
}

function setOpenInvoices(orders = [], preserveSelection = true) {
  const nextOpen = buildOpenInvoices(orders)
  openInvoices.value = nextOpen

  if (preserveSelection && selectedOpenInvoiceKey.value) {
    const hasCurrent = nextOpen.some((row) => row.invoice_key === selectedOpenInvoiceKey.value)
    if (hasCurrent) {
      return
    }
  }
  selectedOpenInvoiceKey.value = nextOpen[0]?.invoice_key || ''
}

async function loadSelectedOpenInvoiceDetail(applyProfile = false) {
  if (!selectedOpenInvoice.value?.name) {
    selectedOpenInvoiceDetail.value = null
    return
  }

  try {
    const payload = await getManagementOrderDetail(selectedOpenInvoice.value.name, selectedOpenInvoice.value.source || 'web')
    selectedOpenInvoiceDetail.value = payload
    if (applyProfile && payload?.order) {
      applyOpenInvoiceProfile(payload.order)
    }
  } catch (detailErr) {
    openInvoiceError.value = detailErr.message || 'دریافت جزئیات فاکتور باز ناموفق بود.'
    selectedOpenInvoiceDetail.value = null
  }
}

async function selectOpenInvoice(row) {
  if (!row?.invoice_key) {
    return
  }
  selectedOpenInvoiceKey.value = row.invoice_key
  await loadSelectedOpenInvoiceDetail(true)
}

function applySelectedOpenInvoiceProfile() {
  if (!selectedOpenInvoiceDetail.value?.order) {
    error.value = 'ابتدا یک فاکتور باز را انتخاب کنید.'
    return
  }
  applyOpenInvoiceProfile(selectedOpenInvoiceDetail.value.order)
  successMessage.value = `فاکتور ${selectedOpenInvoiceDetail.value.order.order_code} انتخاب شد.`
}

async function loadOpenInvoices(preserveSelection = true) {
  openInvoicesLoading.value = true
  openInvoiceError.value = ''
  try {
    const orderPayload = await listManagementOrders({ source: 'web' })
    const allOrders = orderPayload?.orders || []
    customerOptions.value = buildCustomerOptions(allOrders)
    setOpenInvoices(allOrders, preserveSelection)
    if (selectedOpenInvoiceKey.value) {
      await loadSelectedOpenInvoiceDetail(false)
    } else {
      selectedOpenInvoiceDetail.value = null
    }
  } catch (invoiceErr) {
    openInvoiceError.value = invoiceErr.message || 'بارگذاری فاکتورهای باز ناموفق بود.'
    openInvoices.value = []
    selectedOpenInvoiceKey.value = ''
    selectedOpenInvoiceDetail.value = null
  } finally {
    openInvoicesLoading.value = false
  }
}

async function settleSelectedOpenInvoice() {
  if (!selectedOpenInvoice.value?.name) {
    error.value = 'ابتدا یک فاکتور باز را انتخاب کنید.'
    return
  }
  settlingOpenInvoice.value = true
  error.value = ''
  try {
    await markManagementOrderPaid({
      order_name: selectedOpenInvoice.value.name,
      reference_no: payment.reference_no || '',
      rrn: payment.rrn || '',
      provider_payload: {
        source: 'management-pos-open-invoice',
      },
    })
    successMessage.value = `پرداخت فاکتور ${selectedOpenInvoice.value.order_code} ثبت شد.`
    await loadOpenInvoices(true)
  } catch (payErr) {
    error.value = payErr.message || 'ثبت پرداخت فاکتور باز ناموفق بود.'
  } finally {
    settlingOpenInvoice.value = false
  }
}

function selectCustomerFromHistory(customer) {
  if (!customer) {
    return
  }

  form.customer_name = String(customer.label || '').trim() || form.customer_name
  if (customer.mobile) {
    form.mobile = String(customer.mobile).trim()
  }
  form.customer_query = customer.mobile ? `${form.customer_name} - ${form.mobile}` : form.customer_name
}

function createCustomerFromQuery(payload) {
  const rawQuery = String(payload?.raw_query || form.customer_query || '').trim()
  if (!rawQuery) {
    return
  }

  const queryDigits = rawQuery.replace(/\D/g, '')
  let normalizedMobile = queryDigits.length >= 10 ? normalizeCustomerMobile(queryDigits) : ''
  let resolvedName = rawQuery.includes('-') ? String(rawQuery.split('-')[0] || '').trim() : rawQuery
  if (queryDigits && resolvedName.replace(/\D/g, '') === queryDigits) {
    resolvedName = ''
  }
  if (!resolvedName) {
    resolvedName = normalizedMobile ? `مشتری ${normalizedMobile.slice(-4)}` : 'POS Customer'
  }

  if (payload?.is_new) {
    const nameInput = window.prompt('نام مشتری جدید را وارد کنید:', resolvedName || '')
    if (nameInput === null) {
      return
    }
    const cleanedName = String(nameInput || '').trim()
    resolvedName = cleanedName || 'POS Customer'

    const mobileInput = window.prompt('شماره تماس مشتری جدید را وارد کنید (اختیاری):', normalizedMobile || '')
    if (mobileInput === null) {
      return
    }
    const normalizedInputMobile = normalizeCustomerMobile(mobileInput)
    if (String(mobileInput || '').trim() && !normalizedInputMobile) {
      error.value = 'شماره تماس باید حداقل 10 رقم باشد.'
      return
    }
    normalizedMobile = normalizedInputMobile
  }

  form.customer_name = resolvedName
  form.mobile = normalizedMobile || ''
  form.customer_query = normalizedMobile ? `${resolvedName} - ${normalizedMobile}` : resolvedName

  const optionKey = normalizedMobile || resolvedName.toLowerCase()
  const exists = customerOptions.value.some((row) => row.key === optionKey)
  if (!exists) {
    customerOptions.value.unshift({
      key: optionKey,
      label: resolvedName,
      mobile: normalizedMobile,
      orders_count: 0,
      total_sales: 0,
      last_order_at: Date.now(),
    })
  }
  successMessage.value = 'مشتری جدید انتخاب شد. بعد از ثبت سفارش در تاریخچه هم ذخیره می‌شود.'
  error.value = ''
}

function addQuickCustomer() {
  const name = window.prompt('نام مشتری را وارد کنید:', form.customer_name || '')
  if (name === null) {
    return
  }
  const mobile = window.prompt('شماره موبایل را وارد کنید:', form.mobile || '')
  if (mobile === null) {
    return
  }
  form.customer_name = String(name || '').trim() || 'POS Customer'
  form.mobile = String(mobile || '').trim() || form.mobile
  form.customer_query = `${form.customer_name} - ${form.mobile}`
}

function closePOS() {
  window.location.href = '/management'
}

function normalizeCartCustomization(customization, ingredients = []) {
  const clean = sanitizeCustomization(customization || {}, ingredients || [])
  const ingredientAdjustments = [...(clean.ingredient_adjustments || [])]
    .map((row) => ({
      ingredient_key: String(row.ingredient_key || '').trim(),
      multiplier: Number(row.multiplier || 0),
    }))
    .filter((row) => row.ingredient_key)
    .sort((a, b) => a.ingredient_key.localeCompare(b.ingredient_key))

  const selectedModifiers = [...(clean.selected_modifiers || [])]
    .map((row) => ({
      group: String(row.group || row.group_name || '').trim(),
      option: String(row.option || row.option_name || '').trim(),
      qty: Number(row.qty || 1),
    }))
    .filter((row) => row.group && row.option)
    .sort((a, b) => `${a.group}:${a.option}`.localeCompare(`${b.group}:${b.option}`))

  const selectedAlternatives = [...(clean.selected_alternatives || [])]
    .map((row) => ({
      ingredient_key: String(row.ingredient_key || '').trim(),
      alternative_item: String(row.alternative_item || '').trim(),
    }))
    .filter((row) => row.ingredient_key && row.alternative_item)
    .sort((a, b) => a.ingredient_key.localeCompare(b.ingredient_key))

  return {
    ingredient_adjustments: ingredientAdjustments,
    selected_modifiers: selectedModifiers,
    selected_alternatives: selectedAlternatives,
  }
}

function cartLineSignature(itemSlug, customizationPayload) {
  return `${itemSlug || ''}|${JSON.stringify(customizationPayload || {})}`
}

function getItemSlug(item = {}) {
  return String(item.slug || item.restaurant_slug || item.name || '').trim()
}

function canEditCustomizationLine(line) {
  const customization = line?.customization || {}
  return Boolean(
    line?.has_customization ||
      Number((line?.customization_ingredients || []).length || 0) > 0 ||
      Number((customization.ingredient_adjustments || []).length || 0) > 0 ||
      Number((customization.selected_modifiers || []).length || 0) > 0 ||
      Number((customization.selected_alternatives || []).length || 0) > 0,
  )
}

function resolveProductBySlug(itemSlug, fallback = {}) {
  const found = products.value.find((row) => getItemSlug(row) === itemSlug)
  if (found) {
    return found
  }
  return {
    slug: fallback.slug || itemSlug,
    restaurant_slug: fallback.slug || itemSlug,
    name: fallback.item_code || fallback.name || itemSlug,
    title: fallback.title || fallback.item_name || fallback.name || 'آیتم سفارشی',
    item_name: fallback.title || fallback.item_name || fallback.name || 'آیتم سفارشی',
    image: fallback.image || fallbackImage,
    base_price: Number(fallback.price || 0),
  }
}

function setCartQty(line, qty) {
  const safeQty = Math.max(Number(qty || 0), 0)
  if (safeQty === 0) {
    const idx = cart.findIndex((row) => row.line_id === line.line_id)
    if (idx >= 0) {
      cart.splice(idx, 1)
    }
    if (selectedCartLineId.value === line.line_id) {
      selectedCartLineId.value = cart[0]?.line_id || ''
    }
    return
  }
  line.qty = Number(safeQty.toFixed(3))
}

function addToCart(item, qty = 1, customizationPayload = null, hasCustomization = false, unitPrice = null, options = {}) {
  const itemSlug = getItemSlug(item)
  if (!itemSlug) {
    return
  }

  const normalizedCustomization = customizationPayload || {
    ingredient_adjustments: [],
    selected_modifiers: [],
    selected_alternatives: [],
  }
  const signature = cartLineSignature(itemSlug, normalizedCustomization)
  const existing = cart.find((row) => row.signature === signature)
  if (existing) {
    existing.qty = Number((existing.qty + Number(qty || 0)).toFixed(3))
    if ((!existing.customization_ingredients || !existing.customization_ingredients.length) && options.customizationIngredients) {
      existing.customization_ingredients = options.customizationIngredients
    }
    selectedCartLineId.value = existing.line_id
    return
  }

  const lineId = `line-${Math.random().toString(36).slice(2, 11)}`
  cart.push({
    line_id: lineId,
    signature,
    slug: itemSlug,
    title: item.title || item.item_name || item.name,
    image: item.image || fallbackImage,
    qty: Number(Number(qty || 1).toFixed(3)),
    price: Number(unitPrice ?? item.base_price ?? item.standard_rate ?? 0),
    item_code: item.name,
    note: '',
    has_customization: Boolean(hasCustomization),
    customization: normalizedCustomization,
    customization_ingredients: options.customizationIngredients || [],
  })
  selectedCartLineId.value = lineId
}

function incrementProduct(item) {
  const itemSlug = getItemSlug(item)
  const baseLine = cart.find((line) => line.slug === itemSlug && !line.has_customization)
  if (baseLine) {
    setCartQty(baseLine, Number(baseLine.qty || 0) + 1)
    return
  }
  addToCart(item, 1)
}

function decrementProduct(item) {
  const itemSlug = getItemSlug(item)
  const baseLine = cart.find((line) => line.slug === itemSlug && !line.has_customization)
  if (!baseLine) {
    return
  }
  setCartQty(baseLine, Number(baseLine.qty || 0) - 1)
}

function editLineNote(line) {
  const next = window.prompt('یادداشت آیتم:', line.note || '')
  if (next === null) {
    return
  }
  line.note = String(next || '').trim()
}

function clearCart() {
  if (!cart.length) {
    return
  }
  const confirmed = window.confirm('سبد خرید خالی شود؟')
  if (!confirmed) {
    return
  }
  cart.splice(0, cart.length)
  selectedCartLineId.value = ''
}

function closeCustomizationSheet() {
  customizationSheet.open = false
  customizationSheet.loading = false
  customizationSheet.error = ''
  customizationSheet.item = null
  customizationSheet.ingredients = []
  customizationSheet.modifierGroups = []
  customizationSheet.customization = {
    ingredient_adjustments: [],
    selected_modifiers: [],
    selected_alternatives: [],
  }
  customizationSheet.qty = 1
  customizationSheet.editing_line_id = ''
}

function setSheetCustomization(next) {
  customizationSheet.customization = sanitizeCustomization(
    {
      ...customizationSheet.customization,
      ...next,
    },
    customizationSheet.ingredients || [],
  )
}

function setSheetModifiers(next) {
  customizationSheet.customization = sanitizeCustomization(
    {
      ...customizationSheet.customization,
      selected_modifiers: next,
    },
    customizationSheet.ingredients || [],
  )
}

async function openCustomizationSheet(item, options = {}) {
  const editingLine = options?.editingLine || null
  const itemSlug = getItemSlug(item) || getItemSlug(editingLine || {})
  if (!itemSlug) {
    return
  }

  const sourceItem = resolveProductBySlug(itemSlug, item || editingLine || {})
  customizationSheet.open = true
  customizationSheet.loading = true
  customizationSheet.error = ''
  customizationSheet.item = sourceItem
  customizationSheet.qty = 1
  customizationSheet.editing_line_id = editingLine?.line_id || ''
  try {
    const payload = detailCache.get(itemSlug) || (await getItemDetail(itemSlug))
    detailCache.set(itemSlug, payload)

    const detailItem = payload.item || sourceItem
    const ingredients = payload.ingredients || []
    const modifierGroups = payload.modifier_groups || []
    customizationSheet.item = {
      ...sourceItem,
      ...detailItem,
    }
    customizationSheet.ingredients = ingredients
    customizationSheet.modifierGroups = modifierGroups
    if (editingLine) {
      customizationSheet.customization = sanitizeCustomization(
        editingLine.customization || createDefaultCustomization(ingredients, modifierGroups),
        ingredients,
      )
      customizationSheet.qty = Math.max(Number(editingLine.qty || 1), 1)
    } else {
      customizationSheet.customization = createDefaultCustomization(ingredients, modifierGroups)
      customizationSheet.qty = 1
    }
  } catch (sheetErr) {
    customizationSheet.error = sheetErr.message || 'دریافت تنظیمات BOM ناموفق بود.'
  } finally {
    customizationSheet.loading = false
  }
}

function openLineCustomizationEditor(line) {
  if (!line) {
    return
  }
  const baseItem = resolveProductBySlug(line.slug, line)
  openCustomizationSheet(baseItem, { editingLine: line })
}

function confirmCustomizationAdd() {
  if (!customizationSheet.item) {
    return
  }
  const normalized = normalizeCartCustomization(customizationSheet.customization, customizationSheet.ingredients)
  const customizationIngredients = (customizationSheet.ingredients || []).map((ingredient) => ({
    key: String(ingredient.key || ingredient.name || '').trim(),
    name: String(ingredient.name || '').trim(),
    customer_label: String(ingredient.customer_label || '').trim(),
    is_included_by_default: Number(ingredient.is_included_by_default || 0),
  }))
  const nextQty = Number(Number(customizationSheet.qty || 1).toFixed(3))
  const nextPrice = Number(sheetPreview.value.unitPrice || customizationSheet.item.base_price || 0)

  if (customizationSheet.editing_line_id) {
    const editingLine = cart.find((line) => line.line_id === customizationSheet.editing_line_id)
    if (editingLine) {
      const nextSlug = getItemSlug(customizationSheet.item) || editingLine.slug
      const nextSignature = cartLineSignature(nextSlug, normalized)
      const duplicateLine = cart.find((line) => line.signature === nextSignature && line.line_id !== editingLine.line_id)

      if (duplicateLine) {
        duplicateLine.qty = Number((Number(duplicateLine.qty || 0) + nextQty).toFixed(3))
        duplicateLine.has_customization = true
        duplicateLine.customization = normalized
        duplicateLine.customization_ingredients = customizationIngredients
        if (!duplicateLine.note && editingLine.note) {
          duplicateLine.note = editingLine.note
        }
        setCartQty(editingLine, 0)
        selectedCartLineId.value = duplicateLine.line_id
      } else {
        editingLine.signature = nextSignature
        editingLine.slug = nextSlug
        editingLine.title = customizationSheet.item.title || customizationSheet.item.item_name || editingLine.title
        editingLine.image = customizationSheet.item.image || editingLine.image || fallbackImage
        editingLine.qty = nextQty
        editingLine.price = nextPrice
        editingLine.item_code = customizationSheet.item.name || editingLine.item_code
        editingLine.has_customization = true
        editingLine.customization = normalized
        editingLine.customization_ingredients = customizationIngredients
        selectedCartLineId.value = editingLine.line_id
      }

      closeCustomizationSheet()
      return
    }
  }

  addToCart(customizationSheet.item, nextQty, normalized, true, nextPrice, {
    customizationIngredients,
  })
  closeCustomizationSheet()
}

function normalizeNumericCode(value) {
  const digits = String(value || '').replace(/\D/g, '')
  return digits.replace(/^0+/, '') || '0'
}

function parseScaleBarcode(rawValue) {
  const digitsOnly = String(rawValue || '').replace(/\D/g, '')
  const prefix = String(scaleConfig.prefix || '20')
  const prefixLen = prefix.length
  const itemDigits = Number(scaleConfig.item_code_digits || 5)
  const weightDigits = Number(scaleConfig.weight_digits || 5)
  const checksumDigits = Number(scaleConfig.checksum_digits || 1)
  const totalLen = prefixLen + itemDigits + weightDigits + checksumDigits

  if (!digitsOnly || digitsOnly.length !== totalLen) {
    throw new Error('طول بارکد وزنی معتبر نیست.')
  }
  if (!digitsOnly.startsWith(prefix)) {
    throw new Error('پیشوند بارکد ترازو معتبر نیست.')
  }

  const itemCode = digitsOnly.slice(prefixLen, prefixLen + itemDigits)
  const weightRaw = digitsOnly.slice(prefixLen + itemDigits, prefixLen + itemDigits + weightDigits)
  const checksum = checksumDigits ? digitsOnly.slice(-checksumDigits) : ''

  if (digitsOnly.length === 13 && checksumDigits === 1) {
    const body = digitsOnly.slice(0, 12).split('').map(Number)
    const checksumValue = Number(checksum)
    const odd = body.filter((_, idx) => idx % 2 === 0).reduce((sum, n) => sum + n, 0)
    const even = body.filter((_, idx) => idx % 2 === 1).reduce((sum, n) => sum + n, 0)
    const expected = (10 - ((odd + even * 3) % 10)) % 10
    if (checksumValue !== expected) {
      throw new Error('checksum بارکد معتبر نیست.')
    }
  }

  const divisor = Number(scaleConfig.weight_divisor || 1000)
  const qty = Number(weightRaw) / divisor
  if (!Number.isFinite(qty) || qty <= 0) {
    throw new Error('وزن استخراج شده از بارکد معتبر نیست.')
  }

  return {
    itemCode,
    qty: Number(qty.toFixed(3)),
    raw: digitsOnly,
  }
}

function resolveScaleProduct(itemCode) {
  const normalizedTarget = normalizeNumericCode(itemCode)
  return products.value.find((item) => {
    const keys = [item.name, item.slug]
      .map((value) => normalizeNumericCode(value))
      .filter((value) => value !== '0')
    return keys.some((key) => key === normalizedTarget || key.endsWith(normalizedTarget))
  })
}

async function reportHardwareEvent(eventType, severity, message, payload = {}) {
  try {
    await reportManagementPOSHardwareEvent({
      event_type: eventType,
      severity,
      message,
      payload,
      source: 'management-pos-ui',
    })
  } catch (eventErr) {
    console.error(eventErr)
  }
}

async function handleScaleBarcodeScan() {
  const raw = scannerInput.value.trim()
  scannerFeedback.value = ''
  if (!raw) {
    return
  }
  if (!scaleConfig.enabled) {
    error.value = 'پردازش بارکد وزنی در تنظیمات غیرفعال است.'
    return
  }

  try {
    const parsed = parseScaleBarcode(raw)
    const item = resolveScaleProduct(parsed.itemCode)
    if (!item) {
      throw new Error(`کالایی با کد ترازو ${parsed.itemCode} پیدا نشد.`)
    }
    addToCart(item, parsed.qty)
    scannerFeedback.value = `بارکد وزنی اعمال شد: ${item.title || item.item_name} × ${parsed.qty}`
    error.value = ''
  } catch (scanErr) {
    error.value = scanErr.message || 'خطا در تحلیل بارکد وزنی.'
    await reportHardwareEvent('scale', 'warn', scanErr.message || 'Invalid weighted barcode', {
      reason: 'invalid_barcode',
      barcode: raw,
    })
  } finally {
    scannerInput.value = ''
  }
}

function buildOrderNote() {
  const noteParts = [form.note]
  if (form.place) {
    noteParts.push(`جایگاه: ${form.place}`)
  }
  noteParts.push(`مهمان: ${form.guest_count}`)
  if (financial.printProduction) {
    noteParts.push('[PRINT_PRODUCTION]')
  }
  if (financial.couponCode) {
    noteParts.push(`کد تخفیف: ${financial.couponCode}`)
  }
  if (financial.creditCardCode) {
    noteParts.push(`کارت اعتباری: ${financial.creditCardCode}`)
  }
  return noteParts.filter(Boolean).join(' | ')
}

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function formatCompactNumber(value, decimals = 3) {
  const parsed = Number(value || 0)
  if (!Number.isFinite(parsed)) {
    return '0'
  }
  return parsed.toFixed(decimals).replace(/\.?0+$/, '')
}

function formatInvoiceDateTime(value) {
  const raw = String(value || '').trim()
  if (!raw) {
    return '-'
  }
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(raw))
  } catch (dateErr) {
    return raw
  }
}

function toFaDigits(value) {
  return Number(value || 0).toLocaleString('fa-IR')
}

function formatOccupiedMinutes(value) {
  const minutes = Number(value || 0)
  if (!Number.isFinite(minutes) || minutes <= 0) {
    return '۰ دقیقه'
  }
  if (minutes < 60) {
    return `${toFaDigits(minutes)} دقیقه`
  }
  const hours = Math.floor(minutes / 60)
  const remain = minutes % 60
  if (!remain) {
    return `${toFaDigits(hours)} ساعت`
  }
  return `${toFaDigits(hours)} ساعت و ${toFaDigits(remain)} دقیقه`
}

function ingredientBaseMultiplierForPrint(ingredient = {}) {
  return Number(ingredient?.is_included_by_default || 0) === 1 ? 1 : 0
}

function buildCustomizationPrintLines(line) {
  const customization = line?.customization || {}
  const ingredientMap = new Map(
    (line?.customization_ingredients || [])
      .map((row) => ({
        key: String(row?.key || '').trim(),
        name: String(row?.name || '').trim(),
        customer_label: String(row?.customer_label || '').trim(),
        is_included_by_default: Number(row?.is_included_by_default || 0),
      }))
      .filter((row) => row.key)
      .map((row) => [row.key, row]),
  )
  const lines = []

  for (const row of customization.ingredient_adjustments || []) {
    const ingredientKey = String(row?.ingredient_key || '').trim()
    if (!ingredientKey) {
      continue
    }
    const selected = Number(row?.multiplier || 0)
    if (!Number.isFinite(selected)) {
      continue
    }
    const ingredient = ingredientMap.get(ingredientKey)
    const label = ingredient?.customer_label || ingredient?.name || ingredientKey
    if (ingredient) {
      const base = ingredientBaseMultiplierForPrint(ingredient)
      if (Math.abs(selected - base) < 0.001) {
        continue
      }
      if (base <= 0 && selected > 0) {
        lines.push(`+ افزودن ${label} x${formatCompactNumber(selected, 2)}`)
        continue
      }
      if (base > 0 && selected <= 0) {
        lines.push(`- حذف ${label}`)
        continue
      }
      if (selected > base) {
        lines.push(`+ افزایش ${label} (${formatCompactNumber(base, 2)} → ${formatCompactNumber(selected, 2)})`)
      } else {
        lines.push(`- کاهش ${label} (${formatCompactNumber(base, 2)} → ${formatCompactNumber(selected, 2)})`)
      }
      continue
    }

    if (selected > 0) {
      lines.push(`* ${label}: x${formatCompactNumber(selected, 2)}`)
    }
  }

  for (const row of customization.selected_modifiers || []) {
    const group = String(row?.group || row?.group_name || '').trim()
    const option = String(row?.option || row?.option_name || '').trim()
    if (!group || !option) {
      continue
    }
    const qty = Math.max(Number(row?.qty || 1), 1)
    lines.push(`+ ${group} / ${option}${qty > 1 ? ` x${formatCompactNumber(qty, 2)}` : ''}`)
  }

  for (const row of customization.selected_alternatives || []) {
    const ingredientKey = String(row?.ingredient_key || '').trim()
    const alternative = String(row?.alternative_item || '').trim()
    if (!ingredientKey || !alternative) {
      continue
    }
    const ingredient = ingredientMap.get(ingredientKey)
    const label = ingredient?.customer_label || ingredient?.name || ingredientKey
    lines.push(`↺ جایگزین ${label} با ${alternative}`)
  }

  return lines
}

function hydrateReceiptSettings() {
  if (typeof window === 'undefined') {
    return
  }
  try {
    const raw = window.localStorage.getItem(RECEIPT_SETTINGS_STORAGE_KEY)
    if (!raw) {
      return
    }
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') {
      return
    }
    receiptSettings.store_name = String(parsed.store_name || receiptSettings.store_name || '').trim() || 'وی درخت'
    receiptSettings.store_phone = String(parsed.store_phone || '').trim()
  } catch (storageErr) {
    console.error(storageErr)
  }
}

function persistReceiptSettings() {
  if (typeof window === 'undefined') {
    return
  }
  try {
    window.localStorage.setItem(
      RECEIPT_SETTINGS_STORAGE_KEY,
      JSON.stringify({
        store_name: receiptSettings.store_name,
        store_phone: receiptSettings.store_phone,
      }),
    )
  } catch (storageErr) {
    console.error(storageErr)
  }
}

function updateReceiptSetting(key, value) {
  const nextValue = String(value || '').trim()
  if (key === 'store_name') {
    receiptSettings.store_name = nextValue || 'وی درخت'
  } else if (key === 'store_phone') {
    receiptSettings.store_phone = nextValue
  } else {
    return
  }
  persistReceiptSettings()
}

function isNonZeroAmount(value) {
  return Math.abs(Number(value || 0)) > 0.0001
}

const receiptInvoiceNumber = computed(() => {
  const manualValue = String(receiptSettings.manual_invoice_no || '').trim()
  if (manualValue) {
    return manualValue
  }
  const now = new Date()
  const datePart = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`
  const ticketPart = String(activeTicketId.value || 'ticket-1').replace(/^ticket-/, '')
  return `POS-${datePart}-${ticketPart}`
})

function buildReceiptPrintableItems() {
  return buildReceiptPrintableItemsFromLines(cart)
}

function buildReceiptPrintableItemsFromLines(lines = []) {
  return (lines || [])
    .map((line, index) => {
      const qty = Number(line.qty || 0)
      const price = Number(line.price || 0)
      const total = qty * price
      const customizationLines = buildCustomizationPrintLines(line)
      const customizationHtml = customizationLines.length
        ? `
          <ul class="item-custom">
            ${customizationLines.map((entry) => `<li>${escapeHtml(entry)}</li>`).join('')}
          </ul>
        `
        : ''
      const lineNoteText = String(line.note || '').trim()
      const lineNoteHtml = lineNoteText ? `<div class="item-note">یادداشت: ${escapeHtml(lineNoteText)}</div>` : ''

      return `
        <section class="item-row">
          <div class="item-head">
            <span class="item-index">${index + 1}.</span>
            <span class="item-title">${escapeHtml(line.title || '')}</span>
            <span class="item-total">${escapeHtml(formatMoney(total, currency.value))}</span>
          </div>
          <div class="item-meta">
            <span>تعداد: ${escapeHtml(formatCompactNumber(qty))}</span>
            <span>قیمت واحد: ${escapeHtml(formatMoney(price, currency.value))}</span>
          </div>
          ${customizationHtml}
          ${lineNoteHtml}
        </section>
      `
    })
    .join('')
}

function receiptStylesCss() {
  return `
    @font-face { font-family: Peyda; src: url('/fonts/Pevda-Reqular.ttf') format('truetype'); font-weight: 400; font-style: normal; }
    @font-face { font-family: Peyda; src: url('/fonts/Peyda-Medium.ttf') format('truetype'); font-weight: 500; font-style: normal; }
    @font-face { font-family: Peyda; src: url('/fonts/Peyda-SemiBold.ttf') format('truetype'); font-weight: 600; font-style: normal; }
    @font-face { font-family: Peyda; src: url('/fonts/Peyda-Bold.ttf') format('truetype'); font-weight: 700; font-style: normal; }
    @page { size: 80mm auto; margin: 4mm; }
    html, body { width: 100%; margin: 0; padding: 0; }
    body { font-family: Peyda, sans-serif; color: #102c24; background: #fff; }
    .receipt { width: 72mm; margin: 0 auto; font-size: 11px; line-height: 1.35; }
    .center { text-align: center; }
    .brand-name { font-size: 13px; font-weight: 700; margin-bottom: 2px; }
    .title { font-size: 14px; font-weight: 700; margin-bottom: 2px; }
    .muted { color: #355e52; font-size: 10px; }
    .sep { border-top: 1px dashed #97b6ac; margin: 6px 0; }
    .meta-row { display: flex; justify-content: space-between; gap: 6px; margin: 2px 0; }
    .meta-block { margin-top: 4px; border: 1px dashed #d3e2dc; border-radius: 7px; padding: 4px 5px; }
    .meta-block strong { display: block; font-size: 10px; color: #355e52; margin-bottom: 2px; }
    .meta-block p { margin: 0; white-space: pre-wrap; font-size: 10px; }
    .item-row { padding: 4px 0; border-bottom: 1px dashed #d3e2dc; }
    .item-head { display: grid; grid-template-columns: auto 1fr auto; gap: 4px; align-items: start; }
    .item-index { font-weight: 600; }
    .item-title { font-weight: 600; }
    .item-total { font-weight: 700; }
    .item-meta { display: flex; justify-content: space-between; gap: 6px; margin-top: 2px; font-size: 10px; color: #355e52; }
    .item-custom { margin: 3px 0 0; padding-right: 12px; font-size: 10px; color: #20483d; }
    .item-custom li { margin: 1px 0; }
    .item-note { margin-top: 3px; font-size: 10px; color: #20483d; }
    .totals { margin-top: 6px; display: grid; gap: 3px; }
    .total-row { display: flex; justify-content: space-between; gap: 6px; }
    .payable { border-top: 1px dashed #97b6ac; margin-top: 2px; padding-top: 4px; font-size: 12px; font-weight: 700; }
    .note { margin-top: 6px; font-size: 10px; color: #20483d; white-space: pre-wrap; }
  `
}

function buildReceiptTotalsRowsHtml(totalValues = totals.value) {
  const rows = [
    {
      label: 'جمع کالاها',
      value: totalValues.itemsTotal || 0,
      always: true,
      negative: false,
      className: '',
    },
    {
      label: 'تخفیف',
      value: totalValues.discountAmount || 0,
      always: false,
      negative: true,
      className: '',
    },
    {
      label: 'کیف پول',
      value: totalValues.walletApplied || 0,
      always: false,
      negative: true,
      className: '',
    },
    {
      label: 'مالیات',
      value: totalValues.taxAmount || 0,
      always: false,
      negative: false,
      className: '',
    },
    {
      label: 'انعام',
      value: totalValues.tipAmount || 0,
      always: false,
      negative: false,
      className: '',
    },
    {
      label: 'حق سرویس',
      value: totalValues.serviceAmount || 0,
      always: false,
      negative: false,
      className: '',
    },
    {
      label: 'قابل پرداخت',
      value: totalValues.payableAmount || 0,
      always: true,
      negative: false,
      className: 'payable',
    },
  ]

  return rows
    .filter((row) => row.always || isNonZeroAmount(row.value))
    .map((row) => {
      const sign = row.negative ? '- ' : ''
      return `
        <div class="total-row ${row.className}">
          <span>${escapeHtml(row.label)}</span>
          <span>${escapeHtml(`${sign}${formatMoney(row.value || 0, currency.value)}`)}</span>
        </div>
      `
    })
    .join('')
}

function buildReceiptMarkup({
  printableItems,
  totalsRows,
  paymentLabel,
  customerName,
  mobile,
  orderMode,
  place,
  note,
  invoiceNo = receiptInvoiceNumber.value,
  heading = 'فیش فروش POS',
}) {
  const printDate = new Date().toLocaleString('fa-IR')
  const storeName = String(receiptSettings.store_name || '').trim() || 'وی درخت'
  const storePhone = String(receiptSettings.store_phone || '').trim()
  const customerDescription = String(note || '').trim() || '-'
  const placeLabel = String(place || '').trim() || '-'
  const mobileLabel = String(mobile || '').trim() || '-'

  return `
    <div class="receipt">
      <div class="center brand-name">${escapeHtml(storeName)}</div>
      <div class="center title">${escapeHtml(heading)}</div>
      <div class="center muted">POS</div>
      <div class="sep"></div>

      <div class="meta-row"><span>تاریخ</span><span>${escapeHtml(printDate)}</span></div>
      <div class="meta-row"><span>شماره فاکتور</span><span>${escapeHtml(invoiceNo)}</span></div>
      <div class="meta-row"><span>مشتری</span><span>${escapeHtml(customerName || 'POS Customer')}</span></div>
      <div class="meta-row"><span>موبایل مشتری</span><span>${escapeHtml(mobileLabel)}</span></div>
      <div class="meta-row"><span>نوع سفارش</span><span>${escapeHtml(orderMode)}</span></div>
      <div class="meta-row"><span>جایگاه</span><span>${escapeHtml(placeLabel)}</span></div>
      <div class="meta-row"><span>روش پرداخت</span><span>${escapeHtml(paymentLabel)}</span></div>
      <div class="meta-row"><span>شماره تماس فروشگاه</span><span>${escapeHtml(storePhone || '-')}</span></div>
      <div class="meta-block">
        <strong>توضیحات مشتری</strong>
        <p>${escapeHtml(customerDescription)}</p>
      </div>

      <div class="sep"></div>
      ${printableItems}

      <div class="totals">
        ${totalsRows}
      </div>
    </div>
  `
}

function buildCurrentTicketReceiptMarkup() {
  return buildReceiptMarkup({
    printableItems: buildReceiptPrintableItems(),
    totalsRows: buildReceiptTotalsRowsHtml(),
    paymentLabel: payment.method === 'card' ? 'کارتخوان' : 'نقدی',
    customerName: form.customer_name || 'POS Customer',
    mobile: form.mobile || '',
    orderMode: form.order_mode,
    place: form.place,
    note: form.note,
    invoiceNo: receiptInvoiceNumber.value,
    heading: 'فیش فروش POS',
  })
}

function buildConfirmedTableReceiptContext() {
  const flatLines = []
  const noteParts = []
  for (const order of confirmedDineInOrders.value) {
    const orderCode = String(order.order_code || order.name || '').trim()
    if (order.note) {
      noteParts.push(`${orderCode || 'سفارش'}: ${String(order.note).trim()}`)
    }
    for (const item of order.items || []) {
      flatLines.push({
        qty: Number(item.quantity || 0),
        price: Number(item.price_at_time || 0),
        title: item.menu_item_title || item.menu_item || '-',
        note: orderCode ? `کد سفارش: ${orderCode}` : '',
        customization: {
          ingredient_adjustments: [],
          selected_modifiers: [],
          selected_alternatives: [],
        },
        customization_ingredients: [],
      })
    }
  }

  const confirmedTotal = Number(selectedTablePreview.value?.totals?.session_confirmed_total || 0)
  const itemsTotal = flatLines.reduce((sum, line) => sum + Number(line.qty || 0) * Number(line.price || 0), 0)
  const payable = confirmedTotal > 0 ? confirmedTotal : itemsTotal
  const sessionName = String(selectedTablePreview.value?.session?.name || '').trim()
  const invoiceNo = sessionName || `TABLE-${Date.now()}`

  return {
    printableItems: buildReceiptPrintableItemsFromLines(flatLines),
    totalsRows: buildReceiptTotalsRowsHtml({
      itemsTotal: payable,
      discountAmount: 0,
      walletApplied: 0,
      taxAmount: 0,
      tipAmount: 0,
      serviceAmount: 0,
      payableAmount: payable,
    }),
    paymentLabel: 'تسویه میز',
    customerName: selectedDineInTable.value?.label || 'میز سالن',
    mobile: '-',
    orderMode: 'dine_in',
    place: selectedDineInTable.value?.label || '-',
    note: noteParts.join('\n'),
    invoiceNo,
    heading: 'فیش سفارش میز',
  }
}

const receiptPreviewHtml = computed(() => {
  if (!cart.length) {
    return '<p class="muted">برای مشاهده پیش نمایش چاپ، آیتم به سبد اضافه کنید.</p>'
  }
  return `<style>${receiptStylesCss()}</style>${buildCurrentTicketReceiptMarkup()}`
})

function openPrintEditor() {
  if (form.order_mode === 'dine_in') {
    printConfirmedTableOrders()
    return
  }
  if (!cart.length) {
    error.value = 'برای چاپ، باید حداقل یک آیتم در فاکتور باشد.'
    return
  }
  printEditorOpen.value = true
}

function closePrintEditor() {
  printEditorOpen.value = false
}

function printCurrentTicket() {
  if (!cart.length) {
    error.value = 'برای چاپ، باید حداقل یک آیتم در فاکتور باشد.'
    return
  }
  const content = `
    <!doctype html>
    <html lang="fa" dir="rtl">
      <head>
        <meta charset="utf-8" />
        <title>چاپ فاکتور POS</title>
        <style>${receiptStylesCss()}</style>
      </head>
      <body>
        ${buildCurrentTicketReceiptMarkup()}
      </body>
    </html>
  `

  const printWindow = window.open('', '_blank', 'width=480,height=760')
  if (!printWindow) {
    error.value = 'پنجره چاپ باز نشد. لطفا popup blocker را غیرفعال کنید.'
    return
  }
  printWindow.document.open()
  printWindow.document.write(content)
  printWindow.document.close()
  printWindow.focus()
  window.setTimeout(() => {
    printWindow.print()
    printWindow.close()
  }, 180)
}

function resolveCustomerFromQuery() {
  const query = String(form.customer_query || '').trim()
  if (!query) {
    return
  }
  const namePart = query.includes('-') ? String(query.split('-')[0] || '').trim() : ''
  if (namePart) {
    form.customer_name = namePart
  }
  const digits = query.replace(/\D/g, '')
  if (digits.length >= 10) {
    form.mobile = digits.startsWith('0') ? digits : `0${digits.slice(-10)}`
  }
  if (query.length >= 2 && !digits) {
    form.customer_name = query
  }
}

async function submitPOSOrder(payNow = true) {
  if (!cart.length) {
    error.value = 'حداقل یک محصول به سبد اضافه کنید.'
    return
  }

  if (form.order_mode === 'dine_in') {
    const selectedTable = resolveSelectedDineInTable()
    if (!selectedTable) {
      error.value = 'برای افزودن به میز، ابتدا میز را انتخاب کنید.'
      return
    }
    if (payNow) {
      error.value = 'تسویه میز از روی سفارش‌های میز انجام می‌شود. از دکمه افزودن به میز استفاده کنید.'
      return
    }

    submitting.value = true
    error.value = ''
    successMessage.value = ''
    try {
      await createManagementTableOrderFromPOS({
        table_name: selectedTable.name,
        note: buildOrderNote(),
        items: cart.map((line) => ({
          item_code: line.item_code || '',
          title: line.title || '',
          qty: line.qty,
          unit_price: line.price,
          note: line.note || '',
        })),
      })
      successMessage.value = `آیتم‌ها به میز ${selectedTable.table_number} اضافه شد.`
      await refreshSelectedDineInTableOrders()
      resetCurrentInvoiceState()
      form.order_mode = 'dine_in'
      form.place = selectedTable.label
      saveActiveTicketSnapshot()
    } catch (submitErr) {
      error.value = submitErr.message || 'افزودن سفارش به میز ناموفق بود.'
    } finally {
      submitting.value = false
    }
    return
  }

  resolveCustomerFromQuery()

  if (payNow && payment.method === 'card' && !paymentBoot.supports_card) {
    error.value = 'اتصال کارتخوان غیرفعال است.'
    return
  }
  if (payNow && payment.method === 'card' && paymentBoot.provider === 'local_node' && !hardwareStatus.connected) {
    const hasManualRef = Boolean(payment.reference_no || payment.rrn)
    if (!hasManualRef) {
      error.value = 'نود محلی قطع است. برای ادامه مرجع یا RRN دستی ثبت کنید.'
      return
    }
  }

  const paymentPayload = payNow
    ? {
        method: payment.method,
        provider: paymentBoot.provider,
        terminal_id: paymentBoot.terminal_id || '',
        reference_no: payment.reference_no || '',
        rrn: payment.rrn || '',
      }
    : {
        method: 'card',
        provider: 'manual',
        terminal_id: paymentBoot.terminal_id || '',
        reference_no: '',
        rrn: '',
      }

  const payload = {
    customer_name: form.customer_name || 'POS Customer',
    mobile: form.mobile || '09120000000',
    order_type: form.order_mode,
    note: buildOrderNote(),
    customer_type: form.customer_type,
    guest_count: form.guest_count,
    place: form.place,
    totals: {
      ...totals.value,
      currency: currency.value,
    },
    financial_modifiers: {
      discount_type: financial.discountType,
      discount_value: financial.discountValue,
      service_type: financial.serviceType,
      service_value: financial.serviceValue,
      tax_amount: financial.taxExempt ? 0 : financial.taxAmount,
      tip_amount: financial.tipAmount,
      use_wallet: financial.useWallet,
      wallet_applied: totals.value.walletApplied,
      coupon_code: financial.couponCode,
      gift_card_code: financial.creditCardCode,
      tax_exempt: financial.taxExempt,
    },
    items: cart.map((line) => ({
      item_slug: line.slug,
      qty: line.qty,
      note: line.note || '',
      customization: line.customization || {
        ingredient_adjustments: [],
        selected_modifiers: [],
        selected_alternatives: [],
      },
    })),
    payment: paymentPayload,
  }

  submitting.value = true
  error.value = ''
  successMessage.value = ''

  try {
    const result = await createManagementPOSOrder(payload)
    const paymentState = result.payment?.status
    if (paymentState === 'paid') {
      successMessage.value = `سفارش ${result.order_code} ثبت و پرداخت شد.`
    } else if (paymentState === 'pending') {
      successMessage.value = `سفارش ${result.order_code} ثبت شد و در انتظار پرداخت است.`
    } else if (paymentState === 'failed') {
      successMessage.value = `سفارش ${result.order_code} ثبت شد اما پرداخت ناموفق بود.`
    } else {
      successMessage.value = `سفارش ${result.order_code} ثبت شد.`
    }

    if (financial.createNextInvoice) {
      resetCurrentInvoiceState()
      saveActiveTicketSnapshot()
    } else {
      saveActiveTicketSnapshot()
      window.location.href = '/management/orders'
    }

    await refreshHardwareStatus()
  } catch (submitErr) {
    error.value = submitErr.message || 'ثبت سفارش POS ناموفق بود.'
  } finally {
    submitting.value = false
  }
}

function verifyCreditCard() {
  const digits = String(financial.creditCardCode || '').replace(/\D/g, '')
  if (digits.length !== 16) {
    error.value = 'شماره کارت اعتباری باید 16 رقم باشد.'
    return
  }
  error.value = ''
  successMessage.value = 'کارت اعتباری بررسی شد و معتبر است.'
}

function verifyCoupon() {
  const code = String(financial.couponCode || '').trim()
  if (code.length < 3) {
    error.value = 'کد تخفیف معتبر نیست.'
    return
  }
  error.value = ''
  successMessage.value = `کد ${code} اعمال شد.`
}

function updateNetworkState() {
  const wasOffline = isOffline.value
  isOffline.value = !navigator.onLine
  if (wasOffline && !isOffline.value) {
    syncReminder.value = 'اینترنت وصل شد. لطفا اگر سفارشی آفلاین مانده، دکمه Sync را بزنید.'
    if (reminderTimer.value) {
      clearTimeout(reminderTimer.value)
    }
    reminderTimer.value = setTimeout(() => {
      syncReminder.value = ''
    }, 7000)
  }
}

async function refreshHardwareStatus() {
  hardwareLoading.value = true
  try {
    const payload = await getManagementPOSHardwareStatus()
    hardwareStatus.connected = Boolean(payload.connected)
    hardwareStatus.message = payload.message || 'وضعیت سخت افزار دریافت نشد.'
    hardwareStatus.latency_ms = Number(payload.latency_ms || 0)
  } catch (statusErr) {
    hardwareStatus.connected = false
    hardwareStatus.message = statusErr.message || 'بررسی وضعیت سخت افزار ناموفق بود.'
  } finally {
    hardwareLoading.value = false
  }
}

async function loadPOSBoot() {
  loading.value = true
  error.value = ''
  try {
    const payload = await getManagementPOSBoot()
    products.value = payload.items || []
    categories.value = payload.categories || []
    currency.value = payload.currency || 'IRR'
    applyPOSProfileSummary(payload.pos_profile || {})

    const bootPayment = payload.payment || {}
    paymentBoot.enabled = Boolean(bootPayment.enabled)
    paymentBoot.supports_card = Boolean(bootPayment.supports_card)
    paymentBoot.provider = bootPayment.provider || 'manual'
    paymentBoot.provider_label =
      paymentBoot.provider === 'local_node'
        ? 'نود محلی'
        : paymentBoot.provider === 'webhook'
          ? 'وب هوک'
          : 'حالت دستی'
    paymentBoot.terminal_id = bootPayment.terminal_id || ''

    payment.method = bootPayment.default_method || 'cash'
    bootDefaultPaymentMethod = payment.method
    if (payment.method === 'card' && !paymentBoot.supports_card) {
      payment.method = 'cash'
      bootDefaultPaymentMethod = 'cash'
    }

    bootWalletBalance = Number(payload.wallet_balance || bootPayment.wallet_balance || 0)
    financial.walletBalance = bootWalletBalance

    const bootScale = bootPayment.scale || {}
    scaleConfig.enabled = bootScale.enabled === undefined ? true : Boolean(bootScale.enabled)
    scaleConfig.prefix = String(bootScale.prefix || '20')
    scaleConfig.item_code_digits = Number(bootScale.item_code_digits || 5)
    scaleConfig.weight_digits = Number(bootScale.weight_digits || 5)
    scaleConfig.checksum_digits = Number(bootScale.checksum_digits || 1)
    scaleConfig.weight_divisor = Number(bootScale.weight_divisor || 1000)

    openInvoiceError.value = ''
    try {
      const orderPayload = await listManagementOrders({ source: 'web' })
      const allOrders = orderPayload?.orders || []
      customerOptions.value = buildCustomerOptions(allOrders)
      setOpenInvoices(allOrders, true)
      if (selectedOpenInvoiceKey.value) {
        await loadSelectedOpenInvoiceDetail(false)
      } else {
        selectedOpenInvoiceDetail.value = null
      }
    } catch (customerErr) {
      customerOptions.value = []
      openInvoices.value = []
      selectedOpenInvoiceKey.value = ''
      selectedOpenInvoiceDetail.value = null
    }

    try {
      const tablePayload = await getTableOverview()
      tableOptions.value = buildDineInTableOptions(tablePayload?.tables || [])
      if (form.order_mode === 'dine_in') {
        const selected = resolveSelectedDineInTable()
        if (!selected) {
          form.place = placeOptions.value[0] || ''
        }
      }
    } catch (tableErr) {
      tableOptions.value = []
      if (form.order_mode === 'dine_in' && !String(form.place || '').trim()) {
        form.place = placeOptions.value[0] || ''
      }
    }

    await refreshHardwareStatus()
  } catch (bootErr) {
    error.value = bootErr.message || 'بارگذاری POS ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function isTextEntryTarget(target) {
  const element = target && target instanceof HTMLElement ? target : null
  if (!element) {
    return false
  }
  if (element.isContentEditable) {
    return true
  }
  const tagName = element.tagName
  return tagName === 'INPUT' || tagName === 'TEXTAREA' || tagName === 'SELECT'
}

function handleGlobalProductSearchTyping(event) {
  if (event.altKey) {
    return false
  }
  if (isTextEntryTarget(event.target)) {
    return false
  }

  const key = event.key
  if (key === 'Backspace') {
    if (!search.value) {
      return false
    }
    event.preventDefault()
    if (event.metaKey || event.ctrlKey) {
      search.value = ''
    } else {
      search.value = search.value.slice(0, -1)
    }
    return true
  }
  if (key === 'Delete') {
    if (!search.value) {
      return false
    }
    event.preventDefault()
    search.value = ''
    return true
  }
  if (key === 'Escape') {
    if (!search.value) {
      return false
    }
    event.preventDefault()
    search.value = ''
    return true
  }
  if (event.metaKey || event.ctrlKey) {
    return false
  }
  if (key.length === 1) {
    event.preventDefault()
    search.value = `${search.value}${key}`
    return true
  }
  return false
}

function onWindowKeydown(event) {
  const key = event.key

  if (customizationSheet.open) {
    if (key === 'Escape') {
      event.preventDefault()
      closeCustomizationSheet()
      return
    }
    if (key === 'F2') {
      event.preventDefault()
      confirmCustomizationAdd()
      return
    }
    if (key === 'Insert') {
      event.preventDefault()
      const nextQty = window.prompt('تعداد BOM را وارد کنید:', String(customizationSheet.qty))
      const parsed = Number(nextQty)
      if (Number.isFinite(parsed) && parsed > 0) {
        customizationSheet.qty = Math.round(parsed)
      }
      return
    }
  }

  if (printEditorOpen.value) {
    if (key === 'Escape') {
      event.preventDefault()
      closePrintEditor()
      return
    }
    if (key === 'F9') {
      event.preventDefault()
      printCurrentTicket()
      return
    }
    return
  }

  if (handleGlobalProductSearchTyping(event)) {
    return
  }

  if (key === 'F2') {
    event.preventDefault()
    submitPOSOrder(true)
    return
  }

  if (key === 'F4') {
    event.preventDefault()
    headerBarRef.value?.focusCustomerSearch?.()
    return
  }

  if (key === 'F8') {
    event.preventDefault()
    cartPanelRef.value?.focusDiscountInput?.()
    return
  }

  if (key === 'Insert') {
    event.preventDefault()
    const line = cart.find((row) => row.line_id === selectedCartLineId.value) || cart[0]
    if (!line) {
      return
    }
    const nextQty = window.prompt('تعداد جدید را وارد کنید:', String(line.qty))
    if (nextQty === null) {
      return
    }
    const parsedQty = Number(nextQty)
    if (!Number.isFinite(parsedQty) || parsedQty <= 0) {
      error.value = 'تعداد وارد شده معتبر نیست.'
      return
    }
    setCartQty(line, parsedQty)
  }
}

watch(
  [() => form.order_mode, () => form.place],
  () => {
    refreshSelectedDineInTableOrders()
  },
  { immediate: true },
)

watch(
  () => selectedDineInTable.value?.name || '',
  () => {
    moveTableTarget.value = ''
    mergeTableTarget.value = ''
    showSplitBill.value = false
  },
)

watch(
  () => selectedTablePreview.value?.session?.name || '',
  () => {
    hydrateFormFromSelectedTableCustomer()
  },
)

onMounted(async () => {
  window.addEventListener('keydown', onWindowKeydown)
  window.addEventListener('online', updateNetworkState)
  window.addEventListener('offline', updateNetworkState)
  hydrateReceiptSettings()
  await loadPOSBoot()
  saveActiveTicketSnapshot()
  await nextTick()
  window.scrollTo({ top: 0, behavior: 'auto' })
  headerBarRef.value?.focusCustomerSearch?.()
})

onBeforeUnmount(() => {
  saveActiveTicketSnapshot()
  window.removeEventListener('keydown', onWindowKeydown)
  window.removeEventListener('online', updateNetworkState)
  window.removeEventListener('offline', updateNetworkState)
  if (reminderTimer.value) {
    clearTimeout(reminderTimer.value)
  }
})
</script>

<style scoped>
.pos-theme {
  --pos-primary: var(--pos-primary-color, #015a72);
  --pos-accent: var(--pos-accent-color, #ff9836);
  --pos-success: var(--pos-success-color, #0b7d4a);
  --pos-danger: var(--pos-danger-color, #ab3535);
  --pos-warning: var(--pos-warning-color, #f59e0b);
  --pos-white: var(--pos-surface-color, #ffffff);
  --pos-text: var(--pos-primary-color, #015a72);
  --pos-border: rgb(var(--pos-primary-rgb, 1 90 114) / 0.22);
  --pos-soft: rgb(var(--pos-primary-rgb, 1 90 114) / 0.06);
  --pos-accent-soft: rgb(var(--pos-accent-rgb, 255 152 54) / 0.12);
}

.pos-theme :deep(.hero-card) {
  border: 1px solid var(--pos-border);
  background: var(--pos-white);
  box-shadow: none;
}

.pos-theme :deep(.hero-card h2) {
  color: var(--pos-primary);
}

.pos-theme :deep(.hero-card p) {
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.78);
}

.open-invoices-panel {
  border: 1px solid var(--pos-border);
  border-radius: 16px;
  background: var(--pos-white);
  padding: 0.62rem;
  display: grid;
  gap: 0.45rem;
}

.open-invoices-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
}

.open-invoices-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.84rem;
  color: var(--pos-primary);
}

.open-inv-head-right {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.open-invoice-strip {
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
  padding-bottom: 0.2rem;
}

.open-invoice-card {
  min-width: 170px;
  border: 1px solid var(--pos-border);
  border-radius: 12px;
  background: var(--pos-white);
  padding: 0.42rem 0.5rem;
  display: grid;
  gap: 0.18rem;
  cursor: pointer;
}

.open-invoice-card strong {
  font-size: 0.82rem;
}

.open-invoice-card small {
  font-size: 0.72rem;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.82);
}

.open-invoice-card.active {
  border-color: var(--pos-primary);
  box-shadow: inset 0 0 0 1px var(--pos-primary);
}

.open-invoice-detail {
  border: 1px dashed var(--pos-border);
  border-radius: 12px;
  padding: 0.5rem;
  display: grid;
  gap: 0.38rem;
}

.open-invoice-detail > header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
}

.open-invoice-detail > header small {
  display: block;
  margin-top: 0.18rem;
  font-size: 0.72rem;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.78);
}

.open-invoice-actions {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.open-invoice-detail ul {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.28rem;
}

.open-invoice-detail li {
  border: 1px solid var(--pos-border);
  border-radius: 10px;
  padding: 0.35rem 0.45rem;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 0.45rem;
  font-size: 0.74rem;
}

.pos-status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  border: 1px solid var(--pos-border);
  border-radius: 12px;
  background: var(--pos-white);
  padding: 0.5rem 0.75rem;
}

.pos-status-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  font-size: 0.82rem;
  color: var(--pos-text);
}

.pos-status-right {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-shrink: 0;
}

.shift-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}

.shift-dot.shift-open {
  background: var(--pos-success);
  box-shadow: 0 0 0 3px rgb(var(--pos-success-rgb, 11 125 74) / 0.22);
}

.shift-dot.shift-closed {
  background: rgb(var(--pos-primary-rgb, 1 90 114) / 0.35);
}

.pos-status-name {
  font-size: 0.84rem;
  color: var(--pos-primary);
}

.pos-status-sep {
  color: var(--pos-border);
}

.pos-status-shift {
  font-size: 0.78rem;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.72);
}

.pos-status-method {
  font-size: 0.76rem;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.65);
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  background: var(--pos-soft);
}

.pos-info-toggle {
  border: 1px solid var(--pos-border);
  background: transparent;
  color: var(--pos-text);
  border-radius: 8px;
  padding: 0.22rem 0.5rem;
  font-size: 0.73rem;
  cursor: pointer;
  white-space: nowrap;
}

.pos-settings-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid var(--pos-border);
  background: var(--pos-soft);
  color: var(--pos-text);
  font-size: 0.85rem;
  text-decoration: none;
}

.pos-info-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1.2rem;
  border: 1px dashed var(--pos-border);
  border-radius: 12px;
  background: var(--pos-soft);
  padding: 0.55rem 0.8rem;
}

.pos-info-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
}

.pos-info-label {
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.62);
  font-size: 0.73rem;
}

.pos-info-item strong {
  color: var(--pos-primary);
  font-size: 0.8rem;
}

.table-session-preview {
  border: 1px solid var(--pos-border);
  border-radius: 16px;
  background: var(--pos-white);
  padding: 0.6rem;
  display: grid;
  gap: 0.5rem;
}

.table-session-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
}

.table-head-title {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.84rem;
  color: var(--pos-primary);
}

.table-head-right {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 0.35rem;
  border-radius: 999px;
  background: var(--pos-primary);
  color: #fff;
  font-size: 0.7rem;
  font-weight: 600;
}

.count-badge.empty {
  background: rgb(var(--pos-primary-rgb, 1 90 114) / 0.18);
  color: var(--pos-text);
}

.occupied-badge {
  font-size: 0.73rem;
  color: var(--pos-danger);
  background: rgb(var(--pos-danger-rgb, 171 53 53) / 0.1);
  border-radius: 999px;
  padding: 0.12rem 0.45rem;
}

.icon-refresh-btn {
  border: 1px solid var(--pos-border);
  background: transparent;
  color: var(--pos-text);
  border-radius: 8px;
  width: 28px;
  height: 28px;
  font-size: 1rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.collapse-arrow {
  font-size: 0.7rem;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.55);
  width: 18px;
  text-align: center;
}

.table-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.table-cell {
  width: 90px;
  height: 80px;
  border: 2px solid var(--pos-border);
  border-radius: 14px;
  background: var(--pos-white);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.18rem;
  cursor: pointer;
  transition: all 0.15s ease;
  padding: 0.35rem 0.25rem;
  text-align: center;
}

.table-cell-name {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--pos-primary);
  line-height: 1.1;
}

.table-cell-time {
  font-size: 0.65rem;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.65);
}

.table-cell-orders {
  font-size: 0.65rem;
  background: var(--pos-accent-soft);
  color: var(--pos-accent, #ff9836);
  border-radius: 999px;
  padding: 0.08rem 0.32rem;
}

.table-cell-empty {
  font-size: 0.65rem;
  color: var(--pos-success);
}

.table-cell.status-empty {
  background: rgb(var(--pos-success-rgb, 11 125 74) / 0.07);
  border-color: rgb(var(--pos-success-rgb, 11 125 74) / 0.3);
}

.table-cell.status-occupied {
  background: rgb(var(--pos-danger-rgb, 171 53 53) / 0.08);
  border-color: rgb(var(--pos-danger-rgb, 171 53 53) / 0.28);
}

.table-cell.status-waiting {
  background: rgb(var(--pos-warning-rgb, 245 158 11) / 0.1);
  border-color: rgb(var(--pos-warning-rgb, 245 158 11) / 0.4);
}

.table-cell.active {
  border-color: var(--pos-primary);
  box-shadow: 0 0 0 2px rgb(var(--pos-primary-rgb, 1 90 114) / 0.18);
  transform: translateY(-2px);
}

.table-detail-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.55rem;
  border: 1px dashed var(--pos-border);
  border-radius: 12px;
  padding: 0.5rem 0.65rem;
  background: var(--pos-soft);
}

.table-detail-info {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.88);
}

.table-detail-info strong {
  color: var(--pos-primary);
  font-size: 0.86rem;
}

.table-detail-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.38rem;
}

.table-detail-actions .danger {
  border-color: rgb(var(--pos-danger-rgb, 171 53 53) / 0.3);
  color: var(--pos-danger);
}

.table-move-panel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.5rem;
  align-items: end;
  padding: 0.48rem;
  border: 1px dashed var(--pos-border);
  border-radius: 12px;
}

.table-move-panel label {
  display: grid;
  gap: 0.2rem;
  font-size: 0.75rem;
}

.table-move-panel .primary-btn {
  min-width: 150px;
}

.ticket-tabs {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  overflow-x: auto;
  padding-bottom: 0.2rem;
}

.ticket-tab-group {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--pos-border);
  background: var(--pos-white);
  border-radius: 999px;
  overflow: hidden;
}

.ticket-tab {
  border: 0;
  background: transparent;
  color: var(--pos-text);
  padding: 0.36rem 0.65rem;
  font-size: 0.76rem;
  cursor: pointer;
  white-space: nowrap;
}

.ticket-tab-close {
  border: 0;
  border-inline-start: 1px solid var(--pos-border);
  background: transparent;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.78);
  width: 26px;
  min-height: 28px;
  font-size: 0.95rem;
  line-height: 1;
  cursor: pointer;
}

.ticket-tab-group.active {
  background: var(--pos-primary);
  border-color: var(--pos-primary);
}

.ticket-tab-group.active .ticket-tab,
.ticket-tab-group.active .ticket-tab-close {
  color: var(--pos-white);
}

.ticket-tab-group.active .ticket-tab-close {
  border-inline-start-color: rgb(255 255 255 / 0.35);
}

.ticket-tab.new {
  background: var(--pos-accent);
  border-color: var(--pos-accent);
  color: var(--pos-white);
}

.pos-shell {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr) 420px;
  gap: 0.65rem;
}

.categories-col,
.products-col,
.cart-col {
  min-height: 0;
}

.offline-banner,
.sync-banner,
.error,
.success {
  margin: 0;
  border-radius: 12px;
  padding: 0.5rem 0.62rem;
  font-size: 0.8rem;
  background: var(--pos-white);
  border: 1px solid var(--pos-border);
  color: var(--pos-text);
}

.offline-banner {
  background: var(--pos-accent-soft);
  border-color: rgb(var(--pos-accent-rgb, 255 152 54) / 0.3);
}

.sync-banner {
  background: var(--pos-soft);
}

.error {
  background: rgb(var(--pos-danger-rgb, 171 53 53) / 0.12);
  border-color: rgb(var(--pos-danger-rgb, 171 53 53) / 0.35);
  color: var(--pos-danger);
}

.success {
  background: rgb(var(--pos-success-rgb, 11 125 74) / 0.1);
  border-color: rgb(var(--pos-success-rgb, 11 125 74) / 0.34);
  color: var(--pos-success);
}

.print-editor-backdrop {
  position: fixed;
  inset: 0;
  z-index: 60;
  background: rgb(0 0 0 / 0.45);
  display: grid;
  place-items: center;
  padding: 1rem;
}

.print-editor-sheet {
  width: min(1100px, 100%);
  max-height: calc(100vh - 2rem);
  background: #fff;
  border-radius: 18px;
  border: 1px solid var(--pos-border);
  display: grid;
  grid-template-rows: auto 1fr;
  overflow: hidden;
}

.print-editor-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.8rem;
  padding: 0.8rem 0.9rem;
  border-bottom: 1px solid var(--pos-border);
}

.print-editor-head h3 {
  margin: 0;
  font-size: 0.95rem;
  color: var(--pos-primary);
}

.print-editor-head p {
  margin: 0.2rem 0 0;
  font-size: 0.76rem;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.76);
}

.print-editor-actions {
  display: inline-flex;
  gap: 0.45rem;
}

.print-meta-editor {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.55rem;
  padding: 0.7rem 0.9rem 0;
}

.print-meta-editor label {
  display: grid;
  gap: 0.2rem;
  font-size: 0.72rem;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.86);
}

.print-editor-grid {
  display: grid;
  grid-template-columns: minmax(260px, 320px) minmax(0, 1fr);
  gap: 0.7rem;
  padding: 0.8rem;
  min-height: 0;
}

.print-editor-cart {
  border: 1px solid var(--pos-border);
  border-radius: 14px;
  background: var(--pos-soft);
  padding: 0.6rem;
  display: grid;
  gap: 0.5rem;
  min-height: 0;
}

.print-editor-cart h4 {
  margin: 0;
  font-size: 0.82rem;
  color: var(--pos-primary);
}

.print-editor-list {
  display: grid;
  gap: 0.4rem;
  overflow: auto;
  padding-inline-end: 0.2rem;
}

.print-editor-row {
  border: 1px solid var(--pos-border);
  border-radius: 12px;
  padding: 0.5rem;
  background: #fff;
  display: grid;
  gap: 0.4rem;
}

.print-editor-row-main {
  display: grid;
  gap: 0.16rem;
}

.print-editor-row-main strong {
  font-size: 0.8rem;
}

.print-editor-row-main small {
  font-size: 0.73rem;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.78);
}

.print-editor-row-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.print-editor-row-actions button {
  border: 1px solid var(--pos-border);
  border-radius: 8px;
  background: #fff;
  color: var(--pos-primary);
  min-width: 28px;
  height: 28px;
  padding: 0 0.45rem;
  font-size: 0.78rem;
  cursor: pointer;
}

.print-editor-row-actions span {
  min-width: 30px;
  text-align: center;
  font-size: 0.76rem;
}

.print-editor-row-actions .ghost-btn {
  min-width: auto;
}

.print-editor-row-actions .danger-btn {
  color: var(--pos-danger);
  border-color: rgb(var(--pos-danger-rgb, 171 53 53) / 0.25);
}

.print-editor-preview {
  border: 1px solid var(--pos-border);
  border-radius: 14px;
  padding: 0.7rem;
  overflow: auto;
  background: #f7faf9;
}

.receipt-preview-host {
  min-height: 100%;
}

@media (max-width: 1260px) {
  .pos-shell {
    grid-template-columns: 190px minmax(0, 1fr) 360px;
  }

  .print-editor-grid {
    grid-template-columns: minmax(220px, 280px) minmax(0, 1fr);
  }
}

@media (max-width: 1040px) {
  .pos-shell {
    grid-template-columns: 1fr;
  }

  .print-editor-grid {
    grid-template-columns: 1fr;
  }

  .print-meta-editor {
    grid-template-columns: 1fr;
    padding: 0.6rem 0.8rem 0;
  }
}

@media (max-width: 720px) {
  .open-invoices-head,
  .open-invoice-detail > header {
    flex-direction: column;
    align-items: stretch;
  }

  .open-invoice-card {
    min-width: 146px;
  }

  .open-invoice-detail li {
    grid-template-columns: 1fr;
    gap: 0.25rem;
  }

  .table-box {
    min-width: 136px;
  }

  .table-move-panel {
    grid-template-columns: 1fr;
  }

  .pos-device-hero {
    grid-template-columns: 1fr;
  }

  .pos-profile-actions {
    justify-self: start;
  }
}
</style>
