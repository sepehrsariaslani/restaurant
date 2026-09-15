<template>
  <ManagementPageScaffold title="اسناد خرید و انبار" subtitle="فاکتور خرید، رسید خرید و انتقال‌های ثبت‌شده در ERPNext">
    <template #actions>
      <a class="secondary-btn" href="/management/inventory/purchases">خرید مواد</a>
      <a class="secondary-btn" href="/management/inventory/movements">گردش انبار</a>
    </template>

    <ManagementSurfaceCard title="دفتر اسناد عملیاتی" subtitle="برای مشاهده جزئیات، یک ردیف را انتخاب کنید.">
      <div class="document-tabs" role="tablist" aria-label="نوع سند">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          type="button"
          class="document-tab"
          :class="{ active: activeKey === tab.key }"
          :aria-selected="activeKey === tab.key"
          @click="selectTab(tab.key)"
        >
          {{ tab.label }}
        </button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="loading" class="muted" role="status">در حال دریافت {{ activeTab.label }}...</p>
      <ManagementSmartDataTable
        v-else
        :key="activeKey"
        :columns="activeTab.columns"
        :rows="rows"
        row-key="name"
        :row-clickable="true"
        search-placeholder="جستجوی شماره، تأمین‌کننده یا انبار..."
        @row-click="openDetail"
      >
        <template #cell-name="{ row }"><strong dir="ltr">{{ row.name }}</strong></template>
        <template #cell-posting_date="{ value }">{{ formatDate(value) }}</template>
        <template #cell-supplier="{ value }">{{ value || '—' }}</template>
        <template #cell-supplier_name="{ value }">{{ value || '—' }}</template>
        <template #cell-stock_entry_type="{ value }">{{ value || '—' }}</template>
        <template #cell-warehouse="{ value }">{{ value || '—' }}</template>
        <template #cell-total="{ value }">{{ formatMoney(value) }}</template>
        <template #empty>سندی برای نمایش پیدا نشد.</template>
      </ManagementSmartDataTable>
    </ManagementSurfaceCard>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSmartDataTable from '@/components/management/ManagementSmartDataTable.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { callMethodByPath } from '@/utils/api'
import { formatMoney } from '@/utils/format'
import { formatPersianDate } from '@/utils/persianDate'

const tabs = [
  {
    key: 'purchase-invoices',
    label: 'فاکتور خرید',
    doctype: 'Purchase Invoice',
    fields: ['name', 'posting_date', 'supplier', 'supplier_name', 'grand_total', 'status', 'docstatus'],
    columns: [
      { key: 'name', label: 'شماره فاکتور' },
      { key: 'posting_date', label: 'تاریخ' },
      { key: 'supplier_name', label: 'تأمین‌کننده' },
      { key: 'grand_total', label: 'مبلغ کل' },
      { key: 'status', label: 'وضعیت' },
    ],
  },
  {
    key: 'purchase-receipts',
    label: 'رسید خرید',
    doctype: 'Purchase Receipt',
    fields: ['name', 'posting_date', 'supplier', 'supplier_name', 'grand_total', 'status', 'docstatus'],
    columns: [
      { key: 'name', label: 'شماره رسید' },
      { key: 'posting_date', label: 'تاریخ' },
      { key: 'supplier_name', label: 'تأمین‌کننده' },
      { key: 'grand_total', label: 'مبلغ کل' },
      { key: 'status', label: 'وضعیت' },
    ],
  },
  {
    key: 'stock-transfers',
    label: 'انتقال انبار',
    doctype: 'Stock Entry',
    fields: ['name', 'posting_date', 'stock_entry_type', 'purpose', 'from_warehouse', 'to_warehouse', 'docstatus'],
    filters: { stock_entry_type: 'Material Transfer' },
    columns: [
      { key: 'name', label: 'شماره سند' },
      { key: 'posting_date', label: 'تاریخ' },
      { key: 'stock_entry_type', label: 'نوع سند' },
      { key: 'from_warehouse', label: 'مبدأ' },
      { key: 'to_warehouse', label: 'مقصد' },
      { key: 'docstatus', label: 'وضعیت' },
    ],
  },
]

const activeKey = ref(tabs[0].key)
const rows = ref([])
const loading = ref(false)
const error = ref('')
const activeTab = computed(() => tabs.find((tab) => tab.key === activeKey.value) || tabs[0])

function formatDate(value) {
  return value ? formatPersianDate(value) : '—'
}

function selectTab(key) {
  activeKey.value = key
  load()
}

function openDetail(row) {
  const name = String(row?.name || '').trim()
  if (!name) return
  window.location.href = `/management/inventory/documents/detail?doctype=${encodeURIComponent(activeTab.value.doctype)}&name=${encodeURIComponent(name)}`
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const result = await callMethodByPath('frappe.client.get_list', {
      doctype: activeTab.value.doctype,
      fields: activeTab.value.fields,
      filters: activeTab.value.filters || { docstatus: ['<', 2] },
      order_by: 'posting_date desc, creation desc',
      limit_page_length: 200,
    })
    rows.value = Array.isArray(result) ? result : []
  } catch (err) {
    rows.value = []
    error.value = err?.message || `دریافت ${activeTab.value.label} ناموفق بود.`
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.document-tabs {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
  margin-bottom: 0.85rem;
  border-bottom: 1px solid var(--mg-border-light);
}

.document-tab {
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--mg-text-muted);
  padding: 0.65rem 0.75rem;
  cursor: pointer;
  font: inherit;
  font-weight: 800;
}

.document-tab.active {
  color: var(--mg-primary);
  border-bottom-color: var(--mg-primary);
}

.error { color: var(--mg-danger); }
</style>
