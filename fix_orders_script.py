import re

with open("frontend/src/pages/management/ManagementOrdersPage.vue", "r") as f:
    content = f.read()

new_script = """<script setup>
import { computed, reactive, ref } from 'vue'
import { Search, RefreshCcw, AlertCircle, CheckCircle2, ClipboardList, Clock3, Store, CreditCard, CheckCheck, X } from 'lucide-vue-next'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import { completeManagementOrder, getManagementOrderDetail, listManagementOrders, markManagementOrderPaid } from '@/utils/api'
import { formatMoney, formatStatus, parseQuery } from '@/utils/format'

const query = parseQuery()
const detailOrderName = ref(String(query.order_name || query.order || '').trim())
const detailOrderSource = ref(String(query.source || '').trim())

const loading = ref(false)
const error = ref('')
const successMessage = ref('')
const orders = ref([])
const selectedOrder = ref(null)
const currency = ref('IRR')
const updatingOrderAction = ref(false)
const activeTab = ref('all')
const search = ref('')

const manualPayment = reactive({
  reference_no: '',
  rrn: '',
})

const filters = reactive({
  source: '',
  status: '',
})

const mobileTabs = [
  { value: 'all', label: 'همه' },
  { value: 'new', label: 'جدید' },
  { value: 'preparing', label: 'در حال آماده سازی' },
  { value: 'ready', label: 'آماده تحویل' },
  { value: 'unpaid', label: 'پرداخت نشده' },
]

const isOrderDetailView = computed(() => Boolean(detailOrderName.value))

const displayOrders = computed(() => {
  let list = orders.value
  
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(o => 
      String(o.order_code || o.name).toLowerCase().includes(q) ||
      String(o.customer_name || '').toLowerCase().includes(q) ||
      String(o.mobile || '').toLowerCase().includes(q) ||
      String(o.grand_total || '').includes(q)
    )
  }

  if (activeTab.value === 'all') return list
  
  if (activeTab.value === 'unpaid') {
    return list.filter(row => {
      const ps = String(row.payment_status || '').toLowerCase()
      const s = String(row.status || '').toLowerCase()
      return ps !== 'paid' && !['cancelled', 'delivered'].includes(s)
    })
  }
  
  return list.filter(row => String(row.status || '').toLowerCase() === activeTab.value)
})

function getTabCount(tab) {
  if (tab === 'all') return orders.value.length
  
  if (tab === 'unpaid') {
    return orders.value.filter(row => {
      const ps = String(row.payment_status || '').toLowerCase()
      const s = String(row.status || '').toLowerCase()
      return ps !== 'paid' && !['cancelled', 'delivered'].includes(s)
    }).length
  }
  
  return orders.value.filter(row => String(row.status || '').toLowerCase() === tab).length
}

function formatDateTime(value) {
  if (!value) return '-'
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value))
  } catch (error) {
    return value
  }
}

function toFaDigits(value) {
  return Number(value || 0).toLocaleString('fa-IR')
}

function isWebOrder(order) {
  return String(order?.source || '').toLowerCase() === 'web'
}

function isPayDisabled(order) {
  const paid = String(order?.payment_status || '').toLowerCase() === 'paid'
  return updatingOrderAction.value || !isWebOrder(order) || paid
}

function isCompleteDisabled(order) {
  const delivered = String(order?.status || '').toLowerCase() === 'delivered'
  return updatingOrderAction.value || !isWebOrder(order) || delivered
}

async function loadOrders() {
  loading.value = true
  error.value = ''
  try {
    const payload = await listManagementOrders({
      source: filters.source,
      status: filters.status,
    })
    orders.value = payload.orders || []
  } catch (errObj) {
    error.value = errObj.message || 'بارگذاری سفارش‌ها ناموفق بود.'
  } finally {
    loading.value = false
  }
}

async function loadOrderDetail(orderName, source = '') {
  const normalizedOrderName = String(orderName || '').trim()
  if (!normalizedOrderName) return
  
  error.value = ''
  loading.value = true
  try {
    const payload = await getManagementOrderDetail(normalizedOrderName, String(source || '').trim())
    selectedOrder.value = payload
    detailOrderName.value = String(payload?.order?.name || normalizedOrderName).trim()
    detailOrderSource.value = String(payload?.order?.source || source || '').trim()
    currency.value = String(payload?.order?.currency || currency.value || 'IRR').trim() || 'IRR'
    manualPayment.reference_no = payload?.order?.payment_reference || ''
    manualPayment.rrn = payload?.order?.payment_rrn || ''
  } catch (errObj) {
    error.value = errObj.message || 'دریافت جزئیات سفارش ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function openOrderDetail(row) {
  const orderName = String(row?.name || row?.order_code || '').trim()
  if (!orderName) return
  detailOrderName.value = orderName
  detailOrderSource.value = String(row?.source || '').trim()
  loadOrderDetail(orderName, detailOrderSource.value)
  
  // Update URL silently
  const url = new URL(window.location)
  url.searchParams.set('order_name', orderName)
  if (detailOrderSource.value) url.searchParams.set('source', detailOrderSource.value)
  window.history.replaceState({}, '', url)
}

function closeOrderDetail() {
  selectedOrder.value = null
  detailOrderName.value = ''
  detailOrderSource.value = ''
  
  const url = new URL(window.location)
  url.searchParams.delete('order_name')
  url.searchParams.delete('source')
  window.history.replaceState({}, '', url)
}

async function markOrderPaid(order) {
  if (!order?.name) return
  updatingOrderAction.value = true
  error.value = ''
  successMessage.value = ''
  try {
    await markManagementOrderPaid({
      order_name: order.name,
      reference_no: manualPayment.reference_no,
      rrn: manualPayment.rrn,
      provider_payload: { source: 'management-orders-page' },
    })
    successMessage.value = 'پرداخت با موفقیت ثبت شد.'
    await loadOrderDetail(order.name, order.source || detailOrderSource.value)
    loadOrders()
  } catch (errObj) {
    error.value = errObj.message || 'ثبت پرداخت سفارش ناموفق بود.'
  } finally {
    updatingOrderAction.value = false
  }
}

async function completeOrder(order) {
  if (!order?.name) return
  updatingOrderAction.value = true
  error.value = ''
  successMessage.value = ''
  try {
    await completeManagementOrder({
      order_name: order.name,
      reference_no: manualPayment.reference_no,
      rrn: manualPayment.rrn,
      provider_payload: { source: 'management-orders-page' },
    })
    successMessage.value = 'سفارش با موفقیت تکمیل شد.'
    await loadOrderDetail(order.name, order.source || detailOrderSource.value)
    loadOrders()
  } catch (errObj) {
    error.value = errObj.message || 'تکمیل سفارش ناموفق بود.'
  } finally {
    updatingOrderAction.value = false
  }
}

if (isOrderDetailView.value) {
  loadOrderDetail(detailOrderName.value, detailOrderSource.value)
  loadOrders() // Also load list in background
} else {
  loadOrders()
}
</script>"""

content = re.sub(r'<script setup>.*?</script>', new_script, content, flags=re.DOTALL)

with open("frontend/src/pages/management/ManagementOrdersPage.vue", "w") as f:
    f.write(content)

print("Updated ManagementOrdersPage script")
