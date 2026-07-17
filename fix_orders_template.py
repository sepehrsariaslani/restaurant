import re

with open("frontend/src/pages/management/ManagementOrdersPage.vue", "r") as f:
    content = f.read()

template_block = content[content.find("<template>"):content.rfind("</template>") + len("</template>")]

new_template = """<template>
  <ManagementPageScaffold title="" subtitle="" :show-title="false">
    
    <div class="workspace-header">
      <div class="header-intro">
        <h1 class="page-title">مدیریت سفارش‌ها</h1>
        <p class="page-subtitle">پایش لحظه‌ای سفارش‌ها، وضعیت پرداخت و پیشرفت تولید</p>
      </div>

      <div class="header-actions">
        <div class="search-box">
          <Search :size="18" class="search-icon" />
          <input
            v-model.trim="search"
            class="search-input"
            placeholder="جستجو (کد سفارش، مشتری، موبایل...)"
            @keyup.enter="loadOrders"
          />
        </div>
        <button class="refresh-btn" type="button" :disabled="loading" @click="loadOrders" title="بروزرسانی اطلاعات">
          <RefreshCcw :size="18" :class="{ 'is-spinning': loading }" />
        </button>
      </div>
    </div>

    <!-- Composed KPI Strip -->
    <div class="kpi-strip">
      <div class="kpi-hero">
        <div class="kpi-hero-val">{{ toFaDigits(orders.length) }}</div>
        <div class="kpi-hero-label">کل سفارش‌ها</div>
      </div>
      <div class="kpi-tiles">
        <div class="kpi-tile">
          <span class="kpi-dot new"></span>
          <div class="kpi-info">
            <span class="kpi-val">{{ toFaDigits(getTabCount('new')) }}</span>
            <span class="kpi-label">جدید</span>
          </div>
        </div>
        <div class="kpi-tile">
          <span class="kpi-dot preparing"></span>
          <div class="kpi-info">
            <span class="kpi-val">{{ toFaDigits(getTabCount('preparing')) }}</span>
            <span class="kpi-label">در حال تولید</span>
          </div>
        </div>
        <div class="kpi-tile">
          <span class="kpi-dot ready"></span>
          <div class="kpi-info">
            <span class="kpi-val">{{ toFaDigits(getTabCount('ready')) }}</span>
            <span class="kpi-label">آماده تحویل</span>
          </div>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-tile">
          <div class="kpi-info">
            <span class="kpi-val">{{ toFaDigits(getTabCount('unpaid')) }}</span>
            <span class="kpi-label">پرداخت نشده</span>
          </div>
        </div>
      </div>
    </div>

    <div class="workspace-tabs-container">
      <div class="workspace-tabs" role="tablist">
        <button
          v-for="tab in mobileTabs"
          :key="tab.value"
          class="workspace-tab"
          :class="{ active: activeTab === tab.value }"
          type="button"
          role="tab"
          :aria-selected="activeTab === tab.value"
          @click="activeTab = tab.value"
        >
          <span>{{ tab.label }}</span>
          <span class="tab-badge" v-if="getTabCount(tab.value) > 0">{{ toFaDigits(getTabCount(tab.value)) }}</span>
        </button>
      </div>
    </div>

    <p class="muted-loading" v-if="loading && !orders.length">در حال همگام‌سازی سفارش‌ها...</p>
    <div class="workspace-alerts" v-if="error">
      <p class="error-alert"><AlertCircle :size="16" /> {{ error }}</p>
    </div>

    <template v-if="!loading || orders.length">
      <section class="workspace-floor">
        <div class="floor-grid-area">
          <div class="floor-filters">
            <span class="floor-filter-label">فیلتر منبع:</span>
            <button class="floor-chip" :class="{ active: !filters.source }" @click="filters.source = ''; loadOrders()">همه</button>
            <button class="floor-chip" :class="{ active: filters.source === 'web' }" @click="filters.source = 'web'; loadOrders()">آنلاین</button>
            <button class="floor-chip" :class="{ active: filters.source === 'table' }" @click="filters.source = 'table'; loadOrders()">سالن</button>
          </div>

          <div v-if="displayOrders.length" class="order-list">
            <article 
              v-for="row in displayOrders" 
              :key="row.name" 
              class="order-row"
              :class="{ 'is-selected': isOrderDetailView && selectedOrder?.order?.name === row.name }"
              @click="openOrderDetail(row)"
            >
              <div class="order-row-main">
                <div class="order-identity">
                  <strong>{{ row.order_code || row.name }}</strong>
                  <span class="customer-name">{{ row.customer_name || 'مشتری ناشناس' }}</span>
                </div>
                <div class="order-metrics">
                  <span class="order-total" dir="ltr">{{ formatMoney(row.grand_total, currency) }}</span>
                  <div class="order-badges">
                    <span class="status-badge" :class="`status-${(row.status || '').toLowerCase()}`">{{ formatStatus(row.status) }}</span>
                    <span v-if="row.payment_status" class="payment-badge" :class="`pay-${(row.payment_status || '').toLowerCase()}`">
                      {{ row.payment_status }}
                    </span>
                  </div>
                </div>
              </div>
              <div class="order-row-meta">
                <span class="meta-item"><Clock3 :size="14" /> {{ formatDateTime(row.created_at) }}</span>
                <span class="meta-item" v-if="row.channel"><Store :size="14" /> {{ row.channel }}</span>
              </div>
            </article>
          </div>
          <div v-else class="empty-state">
            <div class="empty-icon-wrapper"><ClipboardList :size="32" /></div>
            <strong>سفارشی یافت نشد</strong>
            <p>در این نما با فیلترهای فعلی موردی وجود ندارد.</p>
            <button v-if="filters.source || search || activeTab !== 'all'" class="secondary-btn mt-2" @click="activeTab = 'all'; search = ''; filters.source = ''; loadOrders()">پاک کردن فیلترها</button>
          </div>
        </div>

        <aside class="floor-detail-area">
          <div class="inspection-panel">
            <div v-if="!isOrderDetailView || !selectedOrder" class="inspection-empty">
              <div class="empty-illustration"><ClipboardList :size="32" /></div>
              <strong>یک سفارش را انتخاب کنید</strong>
              <p>برای مشاهده جزئیات، اقلام فاکتور و عملیات پرداخت، سفارشی را از لیست باز کنید.</p>
            </div>
            
            <template v-else>
              <header class="inspection-head">
                <div class="head-info">
                  <span class="head-kicker">جزئیات سفارش ({{ selectedOrder.order.channel || 'نامشخص' }})</span>
                  <h2>{{ selectedOrder.order.order_code || selectedOrder.order.name }}</h2>
                  <span class="head-location">{{ selectedOrder.order.customer_name || 'مشتری ناشناس' }}</span>
                </div>
                <div class="head-badges">
                  <span class="status-badge" :class="`status-${(selectedOrder.order.status || '').toLowerCase()}`">{{ formatStatus(selectedOrder.order.status) }}</span>
                </div>
              </header>

              <div class="inspection-body">
                <div class="kpi-grid">
                  <div class="kpi-box highlight">
                    <span class="kpi-box-label">مبلغ کل</span>
                    <strong class="kpi-box-value" dir="ltr">{{ formatMoney(selectedOrder.order.grand_total, currency) }}</strong>
                  </div>
                  <div class="kpi-box">
                    <span class="kpi-box-label">وضعیت پرداخت</span>
                    <strong class="kpi-box-value" :class="{'text-danger': selectedOrder.order.payment_status !== 'Paid', 'text-success': selectedOrder.order.payment_status === 'Paid'}">
                      {{ selectedOrder.order.payment_status || 'Unpaid' }}
                    </strong>
                  </div>
                </div>

                <section class="inspection-section mt-4">
                  <h3 class="section-title">اقلام سفارش</h3>
                  <div class="items-list">
                    <div class="item-row" v-for="(item, idx) in selectedOrder.order.items" :key="idx">
                      <div class="item-qty">{{ toFaDigits(item.qty) }}×</div>
                      <div class="item-name">{{ item.title || item.item_name }}</div>
                      <div class="item-price" dir="ltr">{{ formatMoney(item.line_total, currency) }}</div>
                    </div>
                  </div>
                </section>
                
                <section class="inspection-section mt-4" v-if="selectedOrder.order.source === 'web' && selectedOrder.order.payment_status !== 'Paid'">
                  <h3 class="section-title">ثبت پرداخت دستی</h3>
                  <div class="form-grid">
                    <div class="form-group full-width">
                      <label>شماره پیگیری (اختیاری)</label>
                      <input class="input" v-model="manualPayment.reference_no" placeholder="Reference No" dir="ltr" />
                    </div>
                    <div class="form-group full-width">
                      <label>RRN (اختیاری)</label>
                      <input class="input" v-model="manualPayment.rrn" placeholder="RRN" dir="ltr" />
                    </div>
                  </div>
                </section>
              </div>

              <footer class="inspection-footer">
                <button 
                  v-if="selectedOrder.order.source === 'web'"
                  class="primary-btn flex-1" 
                  type="button" 
                  :disabled="isPayDisabled(selectedOrder.order)" 
                  @click="markOrderPaid(selectedOrder.order)"
                >
                  <CreditCard :size="16" />
                  <span>{{ updatingOrderAction ? 'در حال ثبت...' : 'ثبت پرداخت' }}</span>
                </button>
                
                <button 
                  v-if="selectedOrder.order.source === 'web'"
                  class="secondary-btn flex-1" 
                  type="button" 
                  :disabled="isCompleteDisabled(selectedOrder.order)" 
                  @click="completeOrder(selectedOrder.order)"
                >
                  <CheckCheck :size="16" />
                  <span>تکمیل سفارش</span>
                </button>
                
                <button class="ghost-btn flex-1" type="button" @click="closeOrderDetail">
                  <X :size="16" />
                  <span>بستن</span>
                </button>
              </footer>
            </template>
          </div>
        </aside>
      </section>
    </template>
  </ManagementPageScaffold>
</template>"""

content = content.replace(template_block, new_template)

with open("frontend/src/pages/management/ManagementOrdersPage.vue", "w") as f:
    f.write(content)

print("Updated ManagementOrdersPage template cleanly")
