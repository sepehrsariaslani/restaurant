<template>
  <section class="pos-theme pos-fullpage">
    <p class="offline-banner" v-if="isOffline">اینترنت قطع است.</p>
    <p class="error pos-inline-error" v-if="error">{{ error }}</p>
    <p class="success pos-inline-success" v-if="successMessage">{{ successMessage }}</p>

    <div class="ticket-tabs-bar">
      <div class="ticket-tabs">
        <div
          v-for="(ticket, tIdx) in ticketSessions"
          :key="ticket.id"
          class="ticket-tab-group"
          :class="{ active: ticket.id === activeTicketId }"
        >
          <button type="button" class="ticket-tab" @click="switchToTicket(ticket.id)">{{ ticketLabel(ticket, tIdx) }}</button>
          <button type="button" class="ticket-tab-close" @click.stop="closeTicketTab(ticket.id)">×</button>
        </div>
        <button type="button" class="ticket-tab new" @click="createNewTicketTab">+ فاکتور جدید</button>
      </div>
      <div class="ticket-rail-actions">
        <button type="button" class="ops-trigger" @click="openOperationsOverlay()">
          <ShoppingCart :size="16" />
          <span>عملیات POS</span>
        </button>
        <button type="button" class="kbd-help-btn" title="میانبرهای کیبورد (?)" @click="showKeyboardMap = true">
          <Keyboard :size="16" />
          <span>میانبرها</span>
        </button>
      </div>
    </div>

    <section class="pos-shell" dir="rtl">
      <div class="pos-main-grid">
        <PosProductPanel
          class="products-col"
          :categories="categories"
          :selected-category="selectedCategory"
          @update:selected-category="selectedCategory = $event"
          :products="filteredProducts"
          :loading="بارگذاری"
          :error="بارگذاری ? '' : productError"
          :search-term="search"
          :scanner-input="scannerInput"
          :scanner-feedback="scannerFeedback"
          :product-view="productView"
          :quantity-map="productQtyMap"
          :fallback-image="fallbackImage"
          :currency="currency"
          :customer-query="form.customer_query"
          :customer-options="customerOptions"
          @update:customer-query="setCustomerQuery"
          @select-customer="selectCustomerFromHistory"
          @create-customer="createCustomerFromQuery"
          @add-customer="addQuickCustomer"
          @update:search-term="search = $event"
          @update:product-view="productView = $event"
          @update:scanner-input="scannerInput = $event"
          @scan-scale="handleScaleBarcodeScan"
          @increment-product="incrementProduct"
          @decrement-product="decrementProduct"
          @open-bom="openCustomizationSheet"
        />

        <aside v-if="isDesktopViewport" class="cart-desktop-col">
          <PosCartPanel
            ref="cartPanelRef"
            :cart-lines="cart"
            :selected-line-id="selectedCartLineId"
            :currency="currency"
            :order-mode="form.order_mode"
            :place="form.place"
            :place-options="placeOptions"
            :table-orders="selectedDineInOrders"
            :table-preview-loading="tablePreviewبارگذاری"
            :selected-table-label="selectedDineInTable?.label || ''"
            :can-print-table-orders="confirmedDineInOrders.length > 0"
            :note="form.note"
            :payment-method="payment.method"
            :payment-reference="payment.reference_no"
            :payment-rrn="payment.rrn"
            :payment-boot="paymentBoot"
            :payment-options="posPaymentOptions"
            :financial="financial"
            :totals="totals"
            :submitting="submitting"
            :undo-line="lastRemovedLine"
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
            @undo-last-line="undoLastRemoval"
            @edit-line-note="editLineNote"
            @edit-line-customization="openLineCustomizationEditor"
            @clear-cart="clearCart"
            @verify-credit="verifyCreditCard"
            @verify-coupon="verifyCoupon"
            @update-table-order-item="changeTableOrderItemQty($event.order, $event.item, $event.delta)"
            @print-confirmed-table="printConfirmedTableOrders"
            @submit-order="submitPOSOrder(false)"
            @submit-and-settle="submitPOSOrder(true, $event, true)"
            @submit-and-pay="submitPOSOrder(true, $event)"
            @print-ticket="openPrintEditor"
          />
        </aside>
      </div>

      <button v-if="!isDesktopViewport" type="button" class="cart-fab" :class="{ 'has-items': cart.length }" title="سبد خرید" @click="cartDrawerOpen = true">
        <ShoppingCart :size="18" />
        <span v-if="cart.length" class="cart-fab-badge">{{ toFaDigits(cart.length) }}</span>
      </button>

      <div v-if="showKeyboardMap" class="kbd-map-backdrop" @click.self="showKeyboardMap = false">
        <section class="kbd-map-modal" dir="rtl">
          <header class="kbd-map-head">
            <h3><Keyboard :size="18" /> میانبرهای کیبورد</h3>
            <button type="button" class="kbd-map-close" @click="showKeyboardMap = false">×</button>
          </header>
          <table class="kbd-map-table">
            <tbody>
              <tr><td><kbd>F1</kbd></td><td>باز کردن پاپ‌آپ پرداخت نقدی</td></tr>
              <tr><td><kbd>F2</kbd></td><td>باز کردن پاپ‌آپ پرداخت (کارتخوان)</td></tr>
              <tr><td><kbd>F8</kbd></td><td>رفتن به فیلد تخفیف</td></tr>
              <tr><td><kbd>F9</kbd></td><td>چاپ فاکتور</td></tr>
              <tr><td><kbd>Delete</kbd></td><td>حذف آخرین آیتم سبد خرید</td></tr>
              <tr><td><kbd>/</kbd></td><td>رفتن سریع به جستجوی محصول</td></tr>
              <tr><td><kbd>Insert</kbd></td><td>ویرایش تعداد آیتم انتخابی</td></tr>
              <tr><td><kbd>Escape</kbd></td><td>بستن سرچ / بستن پنجره‌ها</td></tr>
              <tr><td><kbd>?</kbd></td><td>نمایش / پنهان کردن همین صفحه</td></tr>
            </tbody>
          </table>
          <p class="kbd-map-note">میانبرها فقط زمانی که در فیلد تایپ نیستید فعال هستند.</p>
        </section>
      </div>

    </section>

    <Transition name="ops-overlay">
      <div v-if="operationsOverlayOpen" class="ops-overlay-backdrop" @click.self="closeOperationsOverlay">
        <aside class="ops-overlay-sheet" dir="rtl">
          <header class="ops-overlay-head">
            <div>
              <p class="ops-overlay-kicker">عملیات صندوق</p>
              <h3>{{ leftPanelTabLabel }}</h3>
            </div>
            <button type="button" class="ops-overlay-close" @click="closeOperationsOverlay">×</button>
          </header>

          <div class="left-col">
            <div class="left-col-tabs">
              <button
                type="button"
                class="left-tab-btn"
                :class="{ active: leftPanelTab === 'tables' }"
                @click="setLeftPanelTab('tables')"
              >
                میزها
                <span class="count-badge" v-if="tableOptions.length">{{ toFaDigits(tableOptions.length) }}</span>
                <span class="occupied-badge" v-if="occupiedTableCount">{{ occupiedTableCount }} اشغال</span>
              </button>
              <button
                type="button"
                class="left-tab-btn"
                :class="{ active: leftPanelTab === 'invoices' }"
                @click="setLeftPanelTab('invoices')"
              >
                فاکتورهای باز
                <span class="count-badge" v-if="openInvoices.length">{{ toFaDigits(openInvoices.length) }}</span>
              </button>
              <button
                type="button"
                class="left-tab-btn"
                :class="{ active: leftPanelTab === 'history' }"
                @click="setLeftPanelTab('history')"
              >
                تراکنش‌های امروز
                <span class="count-badge" v-if="todayTransactions.length">{{ toFaDigits(todayTransactions.length) }}</span>
              </button>
              <button
                type="button"
                class="left-tab-btn"
                :class="{ active: leftPanelTab === 'recent' }"
                @click="setLeftPanelTab('recent')"
              >
                سفارش‌های اخیر
                <span class="count-badge" v-if="recentOrders.length">{{ toFaDigits(recentOrders.length) }}</span>
              </button>
            </div>

            <section v-if="leftPanelTab === 'tables'" class="table-session-preview">
              <div class="tab-panel-toolbar">
                <button type="button" class="icon-refresh-btn" @click="loadPOSBoot" title="بروزرسانی">↻</button>
                <span class="tables-stats">
                  <span class="ts-item"><span class="ts-dot free"></span>{{ freeTablesCount }} آزاد</span>
                  <span class="ts-item"><span class="ts-dot occ"></span>{{ occupiedTableCount }} اشغال</span>
                </span>
              </div>

              <div class="waiter-select-box" v-if="waiterOptions.length || waiterبارگذاری">
                <label class="waiter-select-label">گارسون سفارش:</label>
                <select class="input waiter-select" :value="form.waiter" @change="onWaiterChange">
                  <option value="">— بدون گارسون —</option>
                  <option v-for="w in waiterOptions" :key="w.name" :value="w.name">{{ w.label }}</option>
                </select>
              </div>
              
              <div class="table-modern-grid">
                <div
                  v-for="table in tableOptions"
                  :key="table.name"
                  class="table-modern-card"
                  :class="[`tm-${String(table.status || 'empty').toLowerCase()}`, { active: selectedDineInTable?.name === table.name }]"
                  @click="selectDineInTable(table)"
                >
                  <div class="tm-top">
                    <span class="tm-name">{{ table.label }}</span>
                    <span class="tm-status-badge" :class="`tms-${String(table.status || 'empty').toLowerCase()}`">
                      {{ table.status === 'empty' ? 'آزاد' : table.status === 'occupied' ? 'اشغال' : table.status }}
                    </span>
                  </div>
                  <div class="tm-body" v-if="table.status !== 'empty'">
                    <span class="tm-meta" v-if="table.occupied_minutes">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                      {{ formatOccupiedMinutes(table.occupied_minutes) }}
                    </span>
                    <span class="tm-meta" v-if="table.pending_orders">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
                      {{ toFaDigits(table.pending_orders) }} سفارش
                    </span>
                  </div>
                </div>
              </div>
              
              <p class="muted" v-if="tablePreviewبارگذاری">در حال دریافت...</p>
              <p class="error" v-else-if="tablePreviewError">{{ tablePreviewError }}</p>
              
              <template v-else-if="selectedDineInTable">
                <div class="table-detail-modern" v-if="selectedTablePreview?.session?.name">
                  <div class="tdm-head">
                    <div class="tdm-brand">
                      <strong>{{ selectedDineInTable.label }}</strong>
                      <span class="tdm-total">{{ formatMoney(selectedTablePreview.totals?.session_grand_total || 0, currency) }}</span>
                    </div>
                    <div class="tdm-meta">
                      <span v-if="selectedTableCustomer.name"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg> {{ selectedTableCustomer.name }}</span>
                      <span v-if="selectedTableCustomer.guest_count"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg> {{ toFaDigits(selectedTableCustomer.guest_count) }} نفر</span>
                    </div>
                  </div>
                  
                  <div class="tdm-actions">
                    <button class="tdm-btn" @click="assignCustomerToSelectedTable">ثبت مشتری</button>
                    <button class="tdm-btn tdm-danger" :disabled="!selectedTablePreview?.session?.name" @click="clearSelectedTableSession">خالی کردن میز</button>
                  </div>
                  
                  <div class="tdm-adv-actions">
                    <div class="tdm-row">
                      <SearchableDropdown v-model="moveTableTarget" :options="movableTableDropdownOptions" placeholder="انتقال به..." search-placeholder="جستجو..." include-empty-option empty-label="انتقال به..." />
                      <button class="tdm-btn tdm-primary" :disabled="!moveTableTarget" @click="moveSelectedTableSession">انتقال</button>
                    </div>
                    <div class="tdm-row" v-if="mergeableTableDropdownOptions.length">
                      <SearchableDropdown v-model="mergeTableTarget" :options="mergeableTableDropdownOptions" placeholder="ترکیب با..." search-placeholder="جستجو..." include-empty-option empty-label="ترکیب با..." />
                      <button class="tdm-btn tdm-primary" :disabled="!mergeTableTarget" @click="mergeSelectedTableSession">ترکیب</button>
                    </div>
                    <button v-if="confirmedDineInOrders.length" class="tdm-btn tdm-split" @click="showSplitBill = true">مشاهده و تسویه</button>
                  </div>
                  
                  <div class="tdm-orders-list" v-if="confirmedDineInOrders.length">
                    <strong class="tdm-section-title">سفارش‌های ثبت شده این میز</strong>
                    <div v-for="order in confirmedDineInOrders" :key="order.name" class="tdm-order-card" @click="openOrderDetailModal(order)">
                      <div class="tdm-order-header">
                        <span>{{ order.order_code || order.name }}</span>
                        <strong>{{ formatMoney(order.grand_total, currency) }}</strong>
                      </div>
                      <div class="tdm-order-items-preview">
                        <div v-for="item in order.items" :key="item.row_name" class="tdm-order-item-row">
                          <span class="tdm-item-title">{{ toFaDigits(item.quantity || 1) }}x {{ item.menu_item_title }}</span>
                          <span class="tdm-item-price muted">{{ formatMoney(item.line_total, currency) }}</span>
                        </div>
                      </div>
                      <div class="tdm-order-meta">
                        <span class="order-status-badge" :class="`status-${order.status}`">{{ formatStatus(order.status) }}</span>
                        <span v-if="order.payment_method" class="history-method-badge">{{ order.payment_method }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
              <p class="muted" v-else-if="!tablePreviewبارگذاری && !tablePreviewError">یک میز را انتخاب کنید.</p>
            </section>

            <section v-if="leftPanelTab === 'history'" class="history-panel">
              <div class="tab-panel-toolbar">
                <button type="button" class="icon-refresh-btn" @click="loadTodayTransactions(true)" title="بروزرسانی">↻</button>
              </div>
              <p class="muted" v-if="todayTransactionsبارگذاری">در حال دریافت...</p>
              <p class="error" v-else-if="todayTransactionsError">{{ todayTransactionsError }}</p>
              <p class="muted" v-else-if="!todayTransactions.length">هنوز تراکنشی امروز ثبت نشده.</p>
              <div v-else class="history-list">
                <article v-for="tx in todayTransactions" :key="tx.name" class="history-card history-card-interactive" @click="openOrderDetailModal(tx)">
                  <div class="history-card-head">
                    <strong>{{ tx.order_code || tx.name }}</strong>
                    <span class="history-time">{{ formatInvoiceDateTime(tx.created_at) }}</span>
                  </div>
                  <div class="history-card-body">
                    <span>{{ tx.customer_name || 'مشتری POS' }}</span>
                    <span class="history-amount">{{ formatMoney(tx.grand_total || 0, currency) }}</span>
                  </div>
                  <span class="history-method-badge" v-if="tx.payment_method">
                    {{ paymentMethodDisplayLabel(tx.payment_method) }}
                  </span>
                </article>
              </div>
            </section>

            <section v-if="leftPanelTab === 'invoices'" class="open-invoices-panel">
              <div class="tab-panel-toolbar">
                <button type="button" class="icon-refresh-btn" @click="loadOpenInvoices" title="بروزرسانی">↻</button>
              </div>
              <p class="muted" v-if="openInvoicesبارگذاری">در حال دریافت...</p>
              <p class="error" v-else-if="openInvoiceError">{{ openInvoiceError }}</p>
              <p class="muted" v-else-if="!openInvoices.length">فاکتور بازی وجود ندارد.</p>
              <div v-else class="open-invoice-accordion">
                <article
                  v-for="invoice in openInvoices"
                  :key="invoice.invoice_key"
                  class="accordion-card"
                  :class="{ expanded: expandedInvoiceKey === invoice.invoice_key }"
                >
                  <div class="accordion-header" @click="toggleInvoiceAccordion(invoice)">
                    <strong>{{ invoice.name }}</strong>
                    <button type="button" class="print-icon-btn" @click.stop="printOrderReceipt(invoice)" title="پرینت"><Printer :size="14" /></button>
                    <small class="accordion-customer">{{ invoice.customer_name || 'مشتری POS' }}</small>
                    <small class="accordion-amount">{{ formatMoney(invoice.grand_total || 0, currency) }}</small>
                    <small class="accordion-time">{{ formatInvoiceDateTime(invoice.created_at) }}</small>
                    <span class="accordion-chevron">{{ expandedInvoiceKey === invoice.invoice_key ? '▲' : '▼' }}</span>
                  </div>
                  <div class="accordion-body" v-if="expandedInvoiceKey === invoice.invoice_key && invoice.detail">
                    <div class="accordion-items">
                      <div v-for="(item, idx) in (invoice.detail?.order?.items || invoice.detail?.items || [])" :key="idx" class="accordion-item">
                        <span class="accordion-item-title">{{ item.title }}</span>
                        <span class="accordion-item-qty">× {{ formatCompactNumber(item.qty, 2) }}</span>
                        <span class="accordion-item-total">{{ formatMoney(item.line_total || 0, currency) }}</span>
                      </div>
                    </div>
                    <div class="accordion-footer">
                      <button type="button" class="tbl-btn" @click.stop="selectAndLoadInvoice(invoice)"><Download :size="13" /> انتخاب و بارگذاری</button>
                      <button type="button" class="tbl-btn" @click.stop="settleSelectedInvoice(invoice)"><CreditCard :size="13" /> تسویه</button>
                      <template v-if="!invoice.delivery_exists">
                        <button type="button" class="tbl-btn success settle-btn" @click.stop="settleAndDeliverFromInvoice(invoice)"><CheckCheck :size="13" /> تسویه و تحویل</button>
                        <button type="button" class="tbl-btn deliver-acc-btn" @click.stop="deliverFromInvoice(invoice)"><Truck :size="13" /> تحویل</button>
                      </template>
                      <button type="button" class="tbl-btn danger" style="margin-right: auto;" @click.stop="openPurgeModalFromList(invoice)"><Trash2 :size="13" /> حذف کامل</button>
                    </div>
                  </div>
                  <div class="accordion-بارگذاری" v-if="expandedInvoiceKey === invoice.invoice_key && !invoice.detail && !invoice.loadError">
                    <small>در حال دریافت...</small>
                  </div>
                  <small class="error" v-if="expandedInvoiceKey === invoice.invoice_key && invoice.loadError">{{ invoice.loadError }}</small>
                </article>
              </div>
            </section>

            <section v-if="leftPanelTab === 'recent'" class="recent-orders-panel">
              <div class="tab-panel-toolbar">
                <button type="button" class="icon-refresh-btn" @click="loadRecentOrders(true)" title="بروزرسانی">↻</button>
              </div>
              <div class="recent-orders-filter">
                <input
                  class="input dark-input recent-search-input"
                  v-model="recentOrdersSearch"
                  placeholder="جستجو... (کد سفارش، نام مشتری)"
                  type="search"
                />
                <input
                  class="input dark-input recent-date-input"
                  type="date"
                  v-model="recentOrdersDateFrom"
                  @change="loadRecentOrders(true)"
                />
              </div>
              <p class="muted" v-if="recentOrdersبارگذاری">در حال دریافت...</p>
              <p class="error" v-else-if="recentOrdersError">{{ recentOrdersError }}</p>
              <p class="muted" v-else-if="!filteredRecentOrders.length">سفارشی یافت نشد.</p>
              <div v-else class="history-list">
                <article
                  v-for="order in filteredRecentOrders"
                  :key="order.name"
                  class="history-card history-card-interactive"
                  @click="openOrderDetailModal(order)"
                >
                  <div class="history-card-head">
                    <strong>{{ order.name }}</strong>
                    <span class="history-time">{{ formatInvoiceDateTime(order.created_at) }}</span>
                    <button
                      type="button"
                      class="print-icon-btn"
                      @click.stop="printOrderReceipt(order)"
                      title="پرینت فاکتور"
                    ><Printer :size="14" /></button>
                  </div>
                  <div class="history-card-body">
                    <span>{{ order.customer_name || 'مشتری POS' }}</span>
                    <span class="history-amount">{{ formatMoney(order.grand_total || 0, currency) }}</span>
                  </div>
                  <div class="history-card-footer">
                    <span class="history-method-badge" v-if="order.payment_method">
                      {{ paymentMethodDisplayLabel(order.payment_method) }}
                    </span>
                    <span class="order-status-badge" :class="`status-${order.status}`">
                      {{ formatStatus(order.status) }}
                    </span>
                    <button
                      v-if="canSettleOrder(order)"
                      type="button"
                      class="settle-order-btn"
                      @click.stop="quickSettleOrder(order)"
                      title="تسویه"
                    >
                      تسویه
                    </button>
                    <button
                      v-if="canDeliverOrder(order)"
                      type="button"
                      class="deliver-order-btn"
                      @click.stop="deliverOrder(order)"
                      title="تولید و تحویل"
                    >
                      <Truck :size="13" /> تحویل
                    </button>
                    <button
                      v-if="order.status !== 'cancelled'"
                      type="button"
                      class="tbl-btn danger"
                      style="margin-right: auto;"
                      @click.stop="openPurgeModalFromList(order)"
                      title="لغو و حذف کامل"
                    >
                      <Trash2 :size="13" /> حذف
                    </button>
                  </div>
                </article>
              </div>
            </section>
          </div>
        </aside>
      </div>
    </Transition>

    <!-- Cart Drawer -->
    <Teleport to="body">
    <Transition name="cart-drawer">
      <div v-if="cartDrawerOpen && !isDesktopViewport" class="cart-drawer-backdrop" @click.self="cartDrawerOpen = false">
        <aside class="cart-drawer" dir="rtl">
          <PosCartPanel
            ref="cartPanelRef"
            :cart-lines="cart"
            :selected-line-id="selectedCartLineId"
            :currency="currency"
            :order-mode="form.order_mode"
            :place="form.place"
            :place-options="placeOptions"
            :table-orders="selectedDineInOrders"
            :table-preview-loading="tablePreviewبارگذاری"
            :selected-table-label="selectedDineInTable?.label || ''"
            :can-print-table-orders="confirmedDineInOrders.length > 0"
            :note="form.note"
            :payment-method="payment.method"
            :payment-reference="payment.reference_no"
            :payment-rrn="payment.rrn"
            :payment-boot="paymentBoot"
            :payment-options="posPaymentOptions"
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
            :undo-line="lastRemovedLine"
            @remove-line="setCartQty($event, 0)"
            @undo-last-line="undoLastRemoval"
            @edit-line-note="editLineNote"
            @edit-line-customization="openLineCustomizationEditor"
            @clear-cart="clearCart"
            @verify-credit="verifyCreditCard"
            @verify-coupon="verifyCoupon"
            @update-table-order-item="changeTableOrderItemQty($event.order, $event.item, $event.delta)"
            @print-confirmed-table="printConfirmedTableOrders"
            @submit-order="submitPOSOrder(false)"
            @submit-and-settle="submitPOSOrder(true, $event, true)"
            @submit-and-pay="submitPOSOrder(true, $event)"
            @print-ticket="openPrintEditor"
          />
        </aside>
      </div>
    </Transition>
    </Teleport>

    <PosBomSheet
      :open="customizationSheet.open"
      :بارگذاری="customizationSheet.بارگذاری"
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
            <button type="button" class="secondary-btn" @click="closePrintEditor"><X :size="14" /> بستن</button>
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

    <!-- Order Detail / Edit Modal -->
    <div v-if="orderDetailModal.open" class="od-modal-overlay" @click.self="closeOrderDetailModal">
      <div class="od-modal">
        <div class="od-header">
          <div class="od-header-info">
            <span class="od-badge" :class="`od-badge-${orderDetailModal.order?.status || ''}`">
              {{ formatStatus(orderDetailModal.order?.status || '') }}
            </span>
            <h3>{{ orderDetailModal.order?.order_code || 'جزئیات سفارش' }}</h3>
            <span class="od-time" v-if="orderDetailModal.order?.created_at">
              {{ formatInvoiceDateTime(orderDetailModal.order.created_at) }}
            </span>
          </div>
          <button class="od-close" @click="closeOrderDetailModal">✕</button>
        </div>

        <p class="od-بارگذاری" v-if="orderDetailModal.بارگذاری">در حال دریافت...</p>
        <p class="od-error" v-else-if="orderDetailModal.loadError">{{ orderDetailModal.loadError }}</p>

        <template v-else-if="orderDetailModal.order">
          
          <!-- Customer & Payment Summary -->
          <div class="od-summary">
            <div class="od-summary-row">
              <div class="od-summary-item">
                <span class="od-label">مشتری</span>
                <span class="od-value">{{ orderDetailModal.order.customer_name || 'مشتری POS' }}</span>
              </div>
              <div class="od-summary-item">
                <span class="od-label">روش پرداخت</span>
                <span class="od-value" v-if="orderDetailModal.order.payment_method">{{ paymentMethodDisplayLabel(orderDetailModal.order.payment_method) }}</span>
                <span class="od-value muted" v-else>ثبت نشده</span>
              </div>
              <div class="od-summary-item">
                <span class="od-label">مبلغ کل</span>
                <span class="od-value od-price">{{ formatMoney(orderDetailModal.order.grand_total || 0, currency) }}</span>
              </div>
            </div>
          </div>

          <!-- Items -->
          <div class="od-items">
            <div class="od-items-head">
              <span>آیتم‌ها</span>
              <span class="od-items-count">{{ (orderDetailModal.order.items || []).length }} عنوان</span>
            </div>
            <div v-for="(item, idx) in orderDetailModal.order.items || []" :key="idx" class="od-item">
              <div class="od-item-info">
                <span class="od-item-name">{{ item.title }}</span>
                <span class="od-item-qty">×{{ formatCompactNumber(item.qty, 2) }}</span>
              </div>
              <span class="od-item-price">{{ formatMoney(item.line_total || 0, currency) }}</span>
            </div>
          </div>

          <!-- Notes -->
          <div class="od-note" v-if="orderDetailModal.order.note">
            <span class="od-label">یادداشت</span>
            <p>{{ orderDetailModal.order.note }}</p>
          </div>

          <!-- Actions -->
          <div class="od-actions">
            
            <!-- تسویه Section (for unpaid orders) -->
            <div class="od-settle" v-if="orderDetailModal.canSettle">
              <select class="od-select" v-model="orderDetailModal.settleMethod">
                <option value="">انتخاب روش پرداخت</option>
                <option v-for="opt in editablePaymentMethodOptions" :key="`settle-${opt.method}`" :value="opt.method">{{ opt.label }}</option>
              </select>
              <input
                v-if="normalizePaymentMethodKind(orderDetailModal.settleMethod) !== 'credit'"
                class="od-input"
                v-model="orderDetailModal.settleReference"
                placeholder="شماره پیگیری / مرجع"
              />
              <p class="od-credit-note" v-else>
                پرداخت اعتباری فاکتور فروش را باز و بدهکار نگه می‌دارد.
              </p>
              <p class="od-err" v-if="orderDetailModal.settleError">{{ orderDetailModal.settleError }}</p>
              <button class="od-btn od-btn-primary" :disabled="orderDetailModal.settling" @click="confirmSettleOrder">
                {{ orderDetailModal.settling ? '...' : '✓ تسویه سفارش' }}
              </button>
            </div>

            <!-- Edit Section (collapsible) -->
            <div class="od-edit-toggle" @click="editExpanded = !editExpanded">
              <span><Save :size="14" /> ویرایش اطلاعات</span>
              <span class="od-chevron" :class="{ open: editExpanded }">▼</span>
            </div>
            <div class="od-edit" v-if="editExpanded">
              <input class="od-input" v-model="orderDetailModal.editForm.customer_name" placeholder="نام مشتری" />
              <select class="od-select" v-model="orderDetailModal.editForm.payment_method">
                <option value="">انتخاب روش پرداخت</option>
                <option v-for="opt in editablePaymentMethodOptions" :key="opt.method" :value="opt.method">{{ opt.label }}</option>
              </select>
              <textarea class="od-textarea" v-model="orderDetailModal.editForm.note" rows="2" placeholder="یادداشت..."></textarea>
              <p class="od-err" v-if="orderDetailModal.saveError">{{ orderDetailModal.saveError }}</p>
              <button class="od-btn" :disabled="orderDetailModal.saving" @click="saveOrderDetailEdit">
                <Save :size="14" v-if="!orderDetailModal.saving" /> {{ orderDetailModal.saving ? '...' : 'ذخیره' }}
              </button>
            </div>

            <!-- Bottom Actions -->
            <div class="od-bottom">
              <button class="od-btn od-btn-danger" style="margin-left: auto;" @click="openPurgeModal">
                <Trash2 :size="14" /> لغو و حذف کامل
              </button>
              <button class="od-btn od-btn-danger" @click="openReturnInvoiceModal" v-if="['paid','delivered','completed'].includes(String(orderDetailModal.order.status || '').toLowerCase())">
                فاکتور برگشتی
              </button>
              <button class="od-btn" @click="closeOrderDetailModal"><X :size="14" /> بستن</button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Shared Prompt Modal -->
    <div v-if="promptModal.open" class="pos-modal-backdrop" @click.self="cancelPrompt">
      <section class="pos-modal" dir="rtl">
        <header class="pos-modal-head">
          <h3>{{ promptModal.title }}</h3>
          <button type="button" class="pos-modal-close" @click="cancelPrompt">×</button>
        </header>
        <div class="return-modal-body">
          <input class="input dark-input full-width" type="text" v-model="promptModal.value" @keyup.enter="confirmPrompt" autofocus />
        </div>
        <div class="pos-modal-actions">
          <button type="button" class="tbl-btn" @click="cancelPrompt">انصراف</button>
          <button type="button" class="tbl-btn primary" @click="confirmPrompt">تایید</button>
        </div>
      </section>
    </div>

    <!-- Purge Order Confirmation Modal -->
    <div v-if="purgeModal.open" class="pos-modal-backdrop" @click.self="closePurgeModal">
      <section class="pos-modal" dir="rtl">
        <header class="pos-modal-head">
          <h3>لغو و حذف کامل سفارش</h3>
          <button type="button" class="pos-modal-close" @click="closePurgeModal">×</button>
        </header>
        <div class="return-modal-body">
          <p>شما در حال لغو و حذف کامل سفارش <strong>{{ purgeModal.orderCode }}</strong> هستید.</p>
          <p class="muted" style="color: var(--mg-danger); font-weight: bold; margin-top: 10px;">
            توجه: این عملیات تمامی رکوردهای مرتبط شامل اسناد فروش، حواله‌های تحویل، اسناد تولید، ورود و خروج انبار و گزارش‌های پرداخت این سفارش را در صورت امکان حذف و یا باطل خواهد کرد. این عملیات قابل بازگشت نیست.
          </p>
          <p class="error" v-if="purgeModal.error">{{ purgeModal.error }}</p>
          <p class="success" v-if="purgeModal.success" style="color: var(--mg-success); font-size: 0.85rem; margin-top: 10px;">{{ purgeModal.success }}</p>
        </div>
        <div class="pos-modal-actions">
          <button type="button" class="tbl-btn" @click="closePurgeModal" :disabled="purgeModal.loading">انصراف</button>
          <button type="button" class="tbl-btn danger" :disabled="purgeModal.loading || !!purgeModal.success" @click="executePurgeOrder">
            <Trash2 :size="14" v-if="!purgeModal.loading" /> {{ purgeModal.loading ? 'در حال حذف...' : 'تایید و حذف کامل' }}
          </button>
        </div>
      </section>
    </div>

    <!-- Return Invoice Confirmation Modal -->
    <div v-if="returnInvoiceModal.open" class="pos-modal-backdrop" @click.self="closeReturnInvoiceModal">
      <section class="pos-modal" dir="rtl">
        <header class="pos-modal-head">
          <h3>ساخت فاکتور برگشتی</h3>
          <button type="button" class="pos-modal-close" @click="closeReturnInvoiceModal">×</button>
        </header>
        <div class="return-modal-body">
          <p>فاکتور برگشتی برای سفارش <strong>{{ orderDetailModal.order?.order_code }}</strong> ساخته خواهد شد.</p>
          <p class="muted" v-if="orderDetailModal.order">مبلغ کل: {{ formatMoney(orderDetailModal.order.grand_total || 0, currency) }}</p>
          <label>
            دلیل برگشت
            <textarea class="input dark-input" v-model="returnInvoiceModal.reason" rows="2" placeholder="مثال: اشتباه در سفارش، درخواست مشتری..."></textarea>
          </label>
          <p class="error" v-if="returnInvoiceModal.error">{{ returnInvoiceModal.error }}</p>
        </div>
        <div class="pos-modal-actions">
          <button type="button" class="tbl-btn" @click="closeReturnInvoiceModal"><X :size="14" /> انصراف</button>
          <button type="button" class="tbl-btn danger" :disabled="returnInvoiceModal.بارگذاری" @click="confirmCreateReturnInvoice">
            <RefreshCw :size="14" v-if="!returnInvoiceModal.بارگذاری" /> {{ returnInvoiceModal.بارگذاری ? 'در حال ساخت...' : 'تایید و ساخت فاکتور برگشتی' }}
          </button>
        </div>
      </section>
    </div>

    <div v-if="kitchenReadyQueue.length" class="kitchen-ready-toasts">
      <div v-for="o in kitchenReadyQueue" :key="o.name" class="kitchen-ready-toast">
        <span>🍽️ سفارش <strong>{{ o.name }}</strong><template v-if="o.customer_name"> — {{ o.customer_name }}</template> آماده تحویل است</span>
        <button type="button" class="toast-close" @click="dismissKitchenNotice(o.name)"><X :size="14" /></button>
      </div>
    </div>

  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { Keyboard, ShoppingCart, Printer, Truck, CheckCheck, CreditCard, Download, X, Save, ArrowLeft, Plus, RefreshCw, Trash2 } from 'lucide-vue-next'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
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
  listManagementCustomers,
  markManagementOrderPaid,
  createPOSOrder,
  producePOSOrder,
  settlePOSOrder,
  deliverPOSOrder,
  deliverInvoiceOnly,
  voidManagementPOSOrder,
  purgeManagementPOSOrder,
  produceAndDeliverPOSOrder,
  createAndPayPOSOrder,
  createAndSettlePOSOrder,
  mergeTableSessions,
  moveTableSession,
  getManagementPOSBoot,
  getManagementPOSHardwareStatus,
  getManagementPosKitchenNotifications,
  getManagementProductByBarcode,
  reportManagementPOSHardwareEvent,
  listManagementUsers,
  updateTableOrderItem,
  updateManagementOrder,
  createManagementReturnOrder,
} from '@/utils/api'
import { formatMoney, formatStatus, toPersianNumber } from '@/utils/format'
import { createDefaultCustomization, estimateLine, sanitizeCustomization } from '@/utils/itemConfig'
import { calculatePosTotals } from '@/utils/posPricingEngine'

let bootWalletBalance = 0
let bootDefaultPaymentMethod = 'cash'
let bootPosConfig = null
const RECEIPT_SETTINGS_STORAGE_KEY = 'restaurant-pos-receipt-settings-v1'

function defaultFormState() {
  const cfg = bootPosConfig || {}
  const defaultMode = cfg.default_order_mode || 'dine_in'
  const defaultCustomers = cfg.default_customers || {}
  const modeCustomer = defaultCustomers[defaultMode] || {}
  return {
    customer_query: '',
    customer_name: modeCustomer.name || 'مشتری POS',
    mobile: modeCustomer.mobile || '',
    customer_type: 'normal',
    guest_count: 1,
    order_mode: defaultMode,
    place: '',
    note: '',
    waiter: '',
    waiter_name: '',
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
    taxType: 'fixed',
    taxValue: 0,
    tipAmount: 0,
    serviceType: 'fixed',
    serviceValue: 0,
    printProduction: true,
    createNextInvoice: true,
  }
}

const بارگذاری = ref(false)
const submitting = ref(false)
const hardwareبارگذاری = ref(false)
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
const waiterOptions = ref([])
const waiterبارگذاری = ref(false)
const posInfoExpanded = ref(false)
const openInvoicesExpanded = ref(false)
const tableExpanded = ref(false)
const leftPanelTab = ref('recent')
const lastRemovedLine = ref(null)
const showKeyboardMap = ref(false)
const operationsOverlayOpen = ref(false)
const cartDrawerOpen = ref(false)
const isDesktopViewport = ref(typeof window === 'undefined' ? true : window.innerWidth >= 1180)
const todayTransactions = ref([])
const todayTransactionsبارگذاری = ref(false)
const todayTransactionsError = ref('')
const recentOrders = ref([])
const recentOrdersبارگذاری = ref(false)
const recentOrdersError = ref('')
const recentOrdersSearch = ref('')
const recentOrdersDateFrom = ref(new Date().toISOString().split('T')[0])

const editExpanded = ref(false)
const orderDetailModal = reactive({
  open: false,
  بارگذاری: false,
  saving: false,
  loadخطا: '',
  saveخطا: '',
  order: null,
  canتسویه: false,
  تسویهMethod: '',
  تسویهReference: '',
  تسویهخطا: '',
  settling: false,
  editForm: {
    payment_method: '',
    note: '',
    customer_name: '',
  },
})

const promptModal = reactive({
  open: false,
  title: '',
  value: '',
  resolve: null,
  reject: null,
})

function showPrompt(title, defaultValue = '') {
  return new Promise((resolve, reject) => {
    promptModal.title = title
    promptModal.value = defaultValue
    promptModal.resolve = resolve
    promptModal.reject = reject
    promptModal.open = true
  })
}

function confirmPrompt() {
  if (promptModal.resolve) {
    promptModal.resolve(promptModal.value)
  }
  promptModal.open = false
}

function cancelPrompt() {
  if (promptModal.resolve) {
    promptModal.resolve(null)
  }
  promptModal.open = false
}

const purgeModal = reactive({
  open: false,
  loading: false,
  error: '',
  success: '',
  orderCode: '',
  orderName: '',
})

const returnInvoiceModal = reactive({
  open: false,
  بارگذاری: false,
  خطا: '',
  reason: '',
})

const popularSlugsMap = ref({})
const posProfileSummary = reactive({
  name: '',
  title: '',
  company: '',
  warehouse: '',
  selling_price_list: '',
  currency: 'IRR',
  payments: [],
  has_open_shift: false,
  shift_name: '',
  shift_opened_at: '',
  shift_status: '',
})
const selectedTablePreview = ref(null)
const tablePreviewبارگذاری = ref(false)
const tablePreviewError = ref('')
const moveTableTarget = ref('')
const mergeTableTarget = ref('')
const showSplitBill = ref(false)
const openInvoices = ref([])
const openInvoicesبارگذاری = ref(false)
const openInvoiceError = ref('')
const selectedOpenInvoiceKey = ref('')
const selectedOpenInvoiceDetail = ref(null)
const settlingOpenInvoice = ref(false)
const deliveredInvoices = reactive(new Set())
const expandedInvoiceKey = ref('')
const editingOriginalOrder = reactive({
  name: '',
  order_code: '',
  isEditing: false,
  draftSignature: '',
})
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
  methods: [],
})

const packagingSettings = reactive({
  enabled: false,
  flat_fee: 0,
  per_item: true,
  apply_modes: [],
  label: 'هزینه بسته‌بندی',
})

const printFontSettings = reactive({
  font_family: 'Peyda',
  font_size: 11,
  receipt_font_scale: 'متوسط',
})

const payment = reactive(defaultPaymentState())

const form = reactive(defaultFormState())

const financial = reactive(defaultFinancialState())

const customizationSheet = reactive({
  open: false,
  بارگذاری: false,
  خطا: '',
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
  ''

const leftPanelTabLabel = computed(() => {
  switch (leftPanelTab.value) {
    case 'tables':
      return 'میزها'
    case 'invoices':
      return 'فاکتورهای باز'
    case 'history':
      return 'تراکنش‌های امروز'
    case 'recent':
    default:
      return 'سفارش‌های اخیر'
  }
})

const placeOptions = computed(() => {
  const cfg = bootPosConfig || {}
  if (form.order_mode === 'dine_in') {
    if (tableOptions.value.length) {
      return tableOptions.value.map((row) => row.label)
    }
    return ['میز 1', 'میز 2', 'میز 3', 'میز 4', 'میز VIP']
  }
  if (form.order_mode === 'delivery') {
    const couriers = Array.isArray(cfg.delivery_couriers) ? cfg.delivery_couriers : []
    if (couriers.length) {
      return couriers.map((row) => row.label).filter(Boolean)
    }
    const places = cfg.delivery_places
    return Array.isArray(places) && places.length ? places : ['پیک 1', 'پیک 2', 'پیک 3', 'ارسال اکسپرس']
  }
  const places = cfg.takeaway_places
  return Array.isArray(places) && places.length ? places : ['بیرون بر حضوری', 'تحویل کنار سالن']
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
  const filtered = products.value.filter((row) => {
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
  return filtered
})

const filteredRecentOrders = computed(() => {
  const activeOrders = recentOrders.value.filter(o => String(o.status || '').toLowerCase() !== 'cancelled')
  const q = recentOrdersSearch.value.trim().toLowerCase()
  if (!q) return activeOrders
  return activeOrders.filter((o) =>
    String(o.order_code || o.name || '').toLowerCase().includes(q) ||
    String(o.customer_name || '').toLowerCase().includes(q)
  )
})

function canDeliverOrder(order) {
  if (!order) return false
  if (order.delivery_exists) return false
  const status = String(order.status || '').toLowerCase()
  // اگه تحویل شده یا کنسل شده => قطعاً دکمه نمایش نده
  if (['delivered', 'completed', 'cancelled'].includes(status)) return false
  // اگه وضعیت paid با روش پرداخت واقعی (نقد/کارت) => تسویه کامل شده => دکمه نمایش نده
  if (status === 'paid' && order.payment_method && order.payment_method !== 'credit') return false
  // اعتباری همیشه دکمه تحویل داشته باشه چون هنوز تحویل داده نشده
  return true
}

async function deliverOrder(order) {
  if (!order?.name) {
    error.value = 'سفارشی انتخاب نشده.'
    return
  }
  const confirmed = window.confirm(`سفارش ${order.name} تولید و تحویل داده شود؟`)
  if (!confirmed) return
  error.value = ''
  successMessage.value = ''
  try {
    const result = await deliverPOSOrder(order.name)
    const dnInfo = result.delivery_note ? ` | رسید: ${result.delivery_note}` : ''
    const woInfo = result.submitted_work_orders?.length ? ` (${result.submitted_work_orders.length} دستور کار)` : ''
    order.status = 'delivered'
    order.delivery_exists = true
    order.payment_method = order.payment_method || ''
    successMessage.value = `سفارش ${order.name} برای تحویل ثبت شد.${dnInfo}${woInfo}`
    
    // If order was fully paid, remove from open invoices. Else keep it there.
    if (order.status === 'paid' || order.payment_method) {
        openInvoices.value = openInvoices.value.filter(o => o.name !== order.name)
    }
  } catch (err) {
    error.value = err.message || 'تولید و تحویل ناموفق بود.'
  }
}

async function printOrderReceipt(order) {
  if (!order?.name) return
  try {
    const detail = await getManagementOrderDetail(order.name)
    const orderData = detail?.order || detail
    const items = orderData?.items || []
    const customer = order.customer_name || 'مشتری POS'
    const orderCode = order.name
    const total = order.grand_total || 0
    
    // Build receipt using the same format as POS
    const printableItems = buildReceiptPrintableItemsFromLines(items.map(item => ({
      title: item.title || item.item_name || '',
      qty: item.qty || 1,
      price: item.unit_price || item.price || 0,
      note: item.note || '',
      customization_ingredients: [],
      customization: {}
    })))
    
    const totalsRows = buildReceiptTotalsRowsHtml({
      itemsTotal: Number(total || 0),
      discountAmount: 0,
      walletApplied: 0,
      taxAmount: 0,
      tipAmount: 0,
      serviceAmount: 0,
      payableAmount: Number(total || 0),
    })
    
    const paymentLabel = order.payment_method 
      ? (paymentMethodDisplayLabel(order.payment_method) || order.payment_method)
      : '-'
    
    const html = '<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"/>' +
      '<style>' + receiptStylesCss() + '</style></head><body>' +
      buildReceiptMarkup({
        printableItems,
        totalsRows,
        paymentLabel,
        customerName: customer,
        mobile: order.mobile || '',
        orderMode: order.channel || 'takeaway',
        place: order.place || '-',
        note: order.note || '',
        invoiceNo: orderCode,
        heading: 'فیش فروش POS',
      }) +
      '</body></html>'

    const w = window.open('', '_blank', 'width=380,height=700')
    if (!w) return
    w.document.write(html)
    w.document.close()
    w.focus()
    setTimeout(() => { w.print() }, 300)
  } catch(err) {
    error.value = 'خطا در پرینت: ' + (err.message || '')
  }
}

function canSettleOrder(order) {
  if (!order) return false
  const status = String(order.status || '').toLowerCase()
  if (['completed', 'cancelled'].includes(status)) return false
  return !isOrderFullySettled(order)
}

function isManagementPOSTransaction(order = {}) {
  const status = String(order.status || '').toLowerCase()
  const paymentStatus = String(order.payment_status || '').toLowerCase()
  return (
    ['paid', 'delivered', 'completed'].includes(status) ||
    paymentStatus === 'paid' ||
    Boolean(order.has_sales_invoice)
  )
}

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

const freeTablesCount = computed(() => tableOptions.value.filter(t => String(t.status || '').toLowerCase() === 'empty').length)
const occupiedTableCount = computed(() =>
  tableOptions.value.filter((t) => t.status === 'occupied' || t.status === 'waiting').length,
)

function normalizePaymentMethodKind(value) {
  const normalized = String(value || '').trim().toLowerCase()
  if (normalized === 'credit') return 'credit'
  if (normalized === 'card') return 'card'
  return 'cash'
}

function inferPaymentMethodKind(row = {}) {
  const type = String(row?.type || '').trim().toLowerCase()
  const mode = String(row?.mode_of_payment || row?.payment_method || '').trim().toLowerCase()
  const combined = `${type} ${mode}`
  if (/(credit|receivable|invoice|debt|اعتبار|نسیه|بدهکار)/i.test(combined)) {
    return 'credit'
  }
  if (/(card|pos|terminal|bank|kart|کارت|پوز|پاس|بانک|ترمینال)/i.test(combined)) {
    return 'card'
  }
  return 'cash'
}

const posPaymentOptions = computed(() => {
  const dedup = new Map()
  const profilePayments = Array.isArray(posProfileSummary.payments) ? posProfileSummary.payments : []

  for (const row of profilePayments) {
    const modeOfPayment = String(row?.mode_of_payment || row?.payment_method || '').trim()
    if (!modeOfPayment) {
      continue
    }
    const method = inferPaymentMethodKind(row)
    const key = `${method}:${modeOfPayment}`
    if (!dedup.has(key)) {
      dedup.set(key, {
        key,
        method,
        label: modeOfPayment,
        mode_of_payment: modeOfPayment,
        default: Boolean(row?.default),
      })
    }
  }

  if (!dedup.size) {
    dedup.set('cash:نقدی', {
      key: 'cash:نقدی',
      method: 'cash',
      label: 'نقدی',
      mode_of_payment: 'نقدی',
      default: true,
    })
    dedup.set('card:کارتخوان', {
      key: 'card:کارتخوان',
      method: 'card',
      label: 'کارتخوان',
      mode_of_payment: 'کارتخوان',
      default: paymentBoot.supports_card,
    })
  }

  if (!dedup.has('credit:اعتباری')) {
    dedup.set('credit:اعتباری', {
      key: 'credit:اعتباری',
      method: 'credit',
      label: 'اعتباری',
      mode_of_payment: 'اعتباری',
      default: false,
    })
  }

  return [...dedup.values()]
})

const editablePaymentMethodOptions = computed(() => {
  const byMethod = new Map()
  for (const option of posPaymentOptions.value) {
    const method = normalizePaymentMethodKind(option.method)
    if (!byMethod.has(method)) {
      byMethod.set(method, {
        method,
        label: option.label || option.mode_of_payment || method,
      })
    }
  }
  return [...byMethod.values()]
})

function paymentMethodDisplayLabel(value) {
  const method = normalizePaymentMethodKind(value)
  const matched = editablePaymentMethodOptions.value.find((option) => option.method === method)
  if (matched) {
    return matched.label
  }
  if (method === 'credit') return 'اعتباری'
  if (method === 'card') return 'کارتخوان'
  if (method === 'cash') return 'نقدی'
  return String(value || '').trim() || '-'
}

const packagingAmount = computed(() => {
  if (!packagingSettings.enabled) {
    return 0
  }
  const mode = String(form.order_mode || '').trim()
  if (!packagingSettings.apply_modes.includes(mode)) {
    return 0
  }
  let fee = Number(packagingSettings.flat_fee || 0)
  if (packagingSettings.per_item) {
    for (const line of cart) {
      const perItemPrice = Number(line?.packaging_price || 0)
      if (perItemPrice > 0) {
        fee += perItemPrice * Number(line?.qty || 0)
      }
    }
  }
  return Math.max(fee, 0)
})

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
    taxType: financial.taxExempt ? 'fixed' : financial.taxType,
    taxValue: financial.taxExempt ? 0 : financial.taxValue,
    tipAmount: financial.tipAmount,
    packagingAmount: packagingAmount.value,
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
  if (!filteredProducts.value.length && !بارگذاری.value) {
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
    editingOriginalOrder: {
      name: '',
      order_code: '',
      isEditing: false,
      draftSignature: '',
    },
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
    editingOriginalOrder: { ...editingOriginalOrder },
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
  Object.assign(editingOriginalOrder, {
    name: '',
    order_code: '',
    isEditing: false,
    draftSignature: '',
  }, next.editingOriginalOrder || {})
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
    return activeName && activeName !== 'مشتری POS' ? activeName : `فاکتور ${toPersianNumber(index + 1)}`
  }
  const ticketName = String(ticket.snapshot?.form?.customer_name || '').trim()
  return ticketName && ticketName !== 'مشتری POS' ? ticketName : `فاکتور ${toPersianNumber(index + 1)}`
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
  editingOriginalOrder.isEditing = false
  editingOriginalOrder.name = ''
  editingOriginalOrder.order_code = ''
  editingOriginalOrder.draftSignature = ''
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
  posProfileSummary.payments = Array.isArray(summary?.payments)
    ? summary.payments
        .map((row) => ({
          mode_of_payment: String(row?.mode_of_payment || '').trim(),
          type: String(row?.type || '').trim(),
          account: String(row?.account || '').trim(),
          default: Boolean(row?.default),
        }))
        .filter((row) => row.mode_of_payment)
    : []
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
    tablePreviewبارگذاری.value = false
    return
  }

  const selectedTable = resolveSelectedDineInTable()
  if (!selectedTable?.name) {
    selectedTablePreview.value = null
    tablePreviewError.value = ''
    tablePreviewبارگذاری.value = false
    moveTableTarget.value = ''
    mergeTableTarget.value = ''
    showSplitBill.value = false
    return
  }

  tablePreviewبارگذاری.value = true
  tablePreviewError.value = ''
  try {
    selectedTablePreview.value = await getTableDetail(selectedTable.name)
  } catch (tableErr) {
    selectedTablePreview.value = null
    tablePreviewError.value = tableErr.message || 'دریافت سفارش‌های میز ناموفق بود.'
  } finally {
    tablePreviewبارگذاری.value = false
  }
}

async function loadWaitersOnce() {
  if (waiterOptions.value.length || waiterبارگذاری.value) return
  waiterبارگذاری.value = true
  try {
    const payload = await listManagementUsers({ search: '' })
    const rows = Array.isArray(payload?.users) ? payload.users : []
    waiterOptions.value = rows
      .filter((row) => row && row.enabled !== 0)
      .map((row) => ({
        name: row.name,
        label: row.full_name || row.name,
        roles: Array.isArray(row.roles) ? row.roles : [],
      }))
  } catch (errObj) {
    waiterOptions.value = []
  } finally {
    waiterبارگذاری.value = false
  }
}

function onWaiterChange(event) {
  const userName = String(event?.target?.value || '').trim()
  const found = waiterOptions.value.find((row) => row.name === userName)
  form.waiter = userName
  form.waiter_name = found ? found.label : ''
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
  const cfg = bootPosConfig || {}
  if (mode === 'takeaway') {
    form.place = cfg.default_takeaway_place || (placeOptions.value[0] || '')
  } else if (mode === 'delivery') {
    form.place = cfg.default_delivery_courier || cfg.default_delivery_place || (placeOptions.value[0] || '')
  } else {
    form.place = placeOptions.value[0] || ''
  }
  const defaultCustomers = cfg.default_customers || {}
  const modeCustomer = defaultCustomers[mode] || {}
  if (modeCustomer.name) {
    form.customer_name = modeCustomer.name
  }
  if (modeCustomer.mobile) {
    form.mobile = modeCustomer.mobile
  }
}

function setLeftPanelTab(tab) {
  leftPanelTab.value = tab
  if (tab === 'history') {
    loadTodayTransactions()
  }
  if (tab === 'recent') {
    loadRecentOrders()
  }
}

function openOperationsOverlay(tab = leftPanelTab.value) {
  setLeftPanelTab(tab)
  operationsOverlayOpen.value = true
}

function closeOperationsOverlay() {
  operationsOverlayOpen.value = false
}

function syncViewportMode() {
  if (typeof window === 'undefined') {
    isDesktopViewport.value = true
    return
  }
  isDesktopViewport.value = window.innerWidth >= 1180
  if (isDesktopViewport.value) {
    cartDrawerOpen.value = false
  }
}

let customerSearchTimeout = null
function setCustomerQuery(value) {
  form.customer_query = value
  const digits = String(value || '').replace(/\D/g, '')
  if (digits.length >= 10) {
    form.mobile = digits.startsWith('0') ? digits : `0${digits.slice(-10)}`
  }
  
  if (customerSearchTimeout) clearTimeout(customerSearchTimeout)
  customerSearchTimeout = setTimeout(() => {
    if (value && value.length > 1) {
      loadCustomers(value)
    }
  }, 400)
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

async function loadCustomers(search = '') {
  try {
    const payload = await listManagementCustomers({ search })
    const customers = payload?.customers || []
    const mapped = customers.map(c => {
      const mobile = c.mobile || ''
      const name = c.customer_name || 'مشتری'
      return {
        key: mobile || name.toLowerCase(),
        label: name,
        mobile: mobile,
        orders_count: c.orders_count || 0,
        total_sales: c.total_spent || 0,
        last_order_at: c.last_order_at,
      }
    })
    
    if (search) {
      // Merge results preserving existing
      const existing = [...customerOptions.value]
      const existingKeys = new Set(existing.map(r => r.key))
      for (const row of mapped) {
        if (!existingKeys.has(row.key)) {
          existing.unshift(row)
          existingKeys.add(row.key)
        }
      }
      customerOptions.value = existing
    } else {
      customerOptions.value = mapped
    }
  } catch (err) {
    console.error('Failed to load customers:', err)
  }
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
  
  if (status === 'cancelled') {
    return false
  }

  return !isOrderFullySettled(row)
}

function isOrderFullySettled(row) {
  const hasSalesInvoice = Boolean(row?.has_sales_invoice || (Array.isArray(row?.sales_invoices) && row.sales_invoices.length))
  const outstanding = Number(row?.outstanding_amount)
  if (hasSalesInvoice && Number.isFinite(outstanding)) {
    return outstanding <= 0.1
  }

  const paymentStatus = String(row?.payment_status || '').trim().toLowerCase()
  return hasSalesInvoice && paymentStatus === 'paid'
}

function buildOpenInvoices(rows = []) {
  return (rows || [])
    .filter((row) => String(row?.source || '').toLowerCase() === 'web')
    .filter((row) => isUnpaidOpenInvoice(row))
    .map((row) => ({
      ...row,
      invoice_key: openInvoiceKey(row),
      // بررسی اینکه آیا این فاکتور از قبل تحویل داده شده (با چک کردن existing DN توی response)
      delivery_exists: deliveredInvoices.has(row.name) || row.delivery_exists || row.dn_exists || false,
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
  if (invoicePaymentMethod === 'card' || invoicePaymentMethod === 'cash' || invoicePaymentMethod === 'credit') {
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
  openInvoicesبارگذاری.value = true
  openInvoiceError.value = ''
  try {
    const orderPayload = await listManagementOrders({ source: 'web' })
    const allOrders = orderPayload?.orders || []
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
    openInvoicesبارگذاری.value = false
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
    loadOpenInvoices(true)
  } catch (payErr) {
    error.value = payErr.message || 'ثبت پرداخت فاکتور باز ناموفق بود.'
  } finally {
    settlingOpenInvoice.value = false
  }
}

async function toggleInvoiceAccordion(invoice) {
  if (expandedInvoiceKey.value === invoice.invoice_key) {
    expandedInvoiceKey.value = ''
    return
  }
  expandedInvoiceKey.value = invoice.invoice_key
  if (!invoice.detail && !invoice.بارگذاری) {
    invoice.بارگذاری = true
    invoice.loadError = ''
    try {
      const detail = await getManagementOrderDetail(invoice.name, invoice.source || 'web')
      invoice.detail = detail
    } catch (err) {
      invoice.loadError = err.message || 'خطا در دریافت جزئیات'
    } finally {
      invoice.بارگذاری = false
    }
  }
}

async function selectAndLoadInvoice(invoice) {
  if (!invoice?.name) {
    error.value = 'ابتدا یک فاکتور را انتخاب کنید.'
    return
  }
  closeOperationsOverlay()
  try {
    const detail = invoice.detail || await getManagementOrderDetail(invoice.name, invoice.source || 'web')
    const order = detail?.order || detail
    
    const originalOrderName = order.name || invoice.name || ''
    const originalOrderCode = order.order_code || order.name || invoice.order_code || invoice.name || ''

    applyOpenInvoiceProfile(order)
    
    clearCartState()
    
    // Reset financial state
    Object.assign(financial, defaultFinancialState())
    
    // Build a lookup map from loaded products (keyed by item code / name)
    const productByItemCode = {}
    for (const p of products.value) {
      const code = String(p.name || '').trim().toLowerCase()
      if (code) productByItemCode[code] = p
      const slug = String(p.slug || p.restaurant_slug || '').trim().toLowerCase()
      if (slug) productByItemCode[slug] = p
    }
    
    // Load items into cart with correct slug and pricing
    const items = order?.items || []
    for (const item of items) {
      const qty = Number(item.qty || 1)
      if (qty <= 0) continue
      
      const itemCode = String(item.item_code || item.name || item.title || '').trim()
      const matchedProduct = productByItemCode[itemCode.toLowerCase()]
      
      let customization = null
      let hasCustomization = false
      if (item.customization_json) {
        try {
          customization = typeof item.customization_json === 'string' 
            ? JSON.parse(item.customization_json) 
            : item.customization_json
          if (customization && Object.keys(customization).length > 0) {
            hasCustomization = true
          }
        } catch (e) {
          console.warn("Could not parse customization json for line", item)
        }
      }
      
      if (matchedProduct) {
        // Use the real product with correct slug from loaded products
        const unitPrice = Number(item.unit_price || item.price || matchedProduct.base_price || matchedProduct.standard_rate || 0)
        addToCart({
          slug: matchedProduct.slug || matchedProduct.restaurant_slug,
          name: matchedProduct.name,
          title: matchedProduct.title || matchedProduct.item_name || item.title,
          item_name: matchedProduct.item_name || matchedProduct.title || item.title,
          base_price: unitPrice,
          standard_rate: unitPrice,
          price: unitPrice,
          image: matchedProduct.image || item.image || '',
        }, qty, customization, hasCustomization, unitPrice, {
          variant_of: matchedProduct.variant_of || ''
        })
      } else {
        // Fallback: use item_code as-is and just set price
        const unitPrice = Number(item.unit_price || item.price || 0)
        addToCart({
          slug: itemCode,
          name: itemCode,
          title: item.title || item.item_name || itemCode || 'آیتم',
          item_name: item.title || item.item_name || itemCode || 'آیتم',
          base_price: unitPrice,
          standard_rate: unitPrice,
          price: unitPrice,
          image: item.image || '',
        }, qty, customization, hasCustomization, unitPrice, {})
      }
    }
    
    // Restore note
    if (order.note) {
      // Strip automatically generated audit notes
      let cleanNote = order.note.split(' | روش پرداخت:')[0]
      cleanNote = cleanNote.split(' | ادامه فاکتور')[0]
      form.note = cleanNote.trim()
    }

    // Apply financial modifiers from order if available
    const fm = order.financial_modifiers || order.totals || {}
    if (fm.discount_value > 0 || order.discount_amount > 0) {
      financial.discountValue = Number(fm.discount_value || order.discount_amount || 0)
      financial.discountType = fm.discount_type === 'percent' ? 'percent' : 'fixed'
    }
    
    // Check if it's partially paid
    const outstanding = Number(order.outstanding_amount)
    if (Number.isFinite(outstanding) && outstanding >= 0 && outstanding < Number(order.grand_total)) {
      financial.walletApplied = Number(order.grand_total) - outstanding
      financial.useWallet = true
    }
    if (fm.service_value > 0 || order.service_amount > 0) {
      financial.serviceValue = Number(fm.service_value || order.service_amount || 0)
      financial.serviceType = fm.service_type === 'percent' ? 'percent' : 'fixed'
    }
    if (fm.tip_amount > 0 || order.tip_amount > 0) {
      financial.tipAmount = Number(fm.tip_amount || order.tip_amount || 0)
    }
    if (fm.coupon_code || order.coupon_code) {
      financial.couponCode = String(fm.coupon_code || order.coupon_code || '').trim()
    }
    
    // Set payment info
    if (order.payment_method) {
      payment.method = order.payment_method
    }
    if (order.payment_reference || order.reference_no) {
      payment.reference_no = String(order.payment_reference || order.reference_no || '').trim()
    }
    if (order.payment_rrn || order.rrn) {
      payment.rrn = String(order.payment_rrn || order.rrn || '').trim()
    }

    editingOriginalOrder.name = originalOrderName
    editingOriginalOrder.order_code = originalOrderCode
    editingOriginalOrder.isEditing = Boolean(originalOrderName)
    editingOriginalOrder.draftSignature = currentOrderDraftSignature()
    saveActiveTicketSnapshot()
    
    successMessage.value = `فاکتور ${order.order_code || invoice.order_code} با اطلاعات کامل بارگذاری شد.`
    expandedInvoiceKey.value = ''
  } catch (err) {
    error.value = err.message || 'بارگذاری فاکتور ناموفق بود.'
  }
}

async function settleSelectedInvoice(invoice) {
  if (!invoice?.name) return
  settlingOpenInvoice.value = true
  error.value = ''
  successMessage.value = ''
  try {
    const result = await markManagementOrderPaid({
      order_name: invoice.name,
      reference_no: payment.reference_no || '',
      rrn: payment.rrn || '',
      provider_payload: {
        source: 'management-pos-open-invoice-list',
      },
    })
    const siInfo = result.sales_invoice ? ` | فاکتور: ${result.sales_invoice}` : ''
    successMessage.value = `فاکتور ${invoice.order_code || invoice.name} تسویه شد.${siInfo}`
    openInvoices.value = openInvoices.value.filter(o => o.name !== invoice.name)
    await loadOpenInvoices(true)
    await loadTodayTransactions(true)
  } catch (payErr) {
    error.value = payErr.message || 'تسویه فاکتور باز ناموفق بود.'
  } finally {
    settlingOpenInvoice.value = false
  }
}

async function settleAndDeliverFromInvoice(invoice) {
  if (!invoice?.name) return
  settlingOpenInvoice.value = true
  error.value = ''
  successMessage.value = ''
  try {
    const payResult = await markManagementOrderPaid({
      order_name: invoice.name,
      reference_no: payment.reference_no || '',
      rrn: payment.rrn || '',
      provider_payload: {
        source: 'management-pos-open-invoice-list-settle-deliver',
      },
    })
    const deliverResult = invoice.delivery_exists ? {} : await deliverInvoiceOnly(invoice.name)
    const siInfo = payResult.sales_invoice ? ` | فاکتور: ${payResult.sales_invoice}` : ''
    const dnInfo = deliverResult.delivery_note ? ` | رسید: ${deliverResult.delivery_note}` : ''
    successMessage.value = `فاکتور ${invoice.order_code || invoice.name} تسویه و تحویل شد.${siInfo}${dnInfo}`
    openInvoices.value = openInvoices.value.filter(o => o.name !== invoice.name)
    await loadOpenInvoices(true)
    await loadTodayTransactions(true)
  } catch (err) {
    error.value = err.message || 'تسویه و تحویل فاکتور باز ناموفق بود.'
  } finally {
    settlingOpenInvoice.value = false
  }
}

async function deliverFromInvoice(invoice) {
  if (!invoice?.name) return
  const confirmed = window.confirm(`فاکتور ${invoice.name} تحویل داده شود؟ (پرداخت نشده باقی می‌ماند)`)
  if (!confirmed) return
  error.value = ''
  successMessage.value = ''
  try {
    const result = await deliverInvoiceOnly(invoice.name)
    const dnInfo = result.delivery_note ? ` | رسید: ${result.delivery_note}` : ''
    invoice.delivery_exists = true
    deliveredInvoices.add(invoice.name)
    successMessage.value = `فاکتور ${invoice.order_code} تحویل شد (بدون پرداخت).${dnInfo}`
    
    // Optimistically update local state instead of full refetch
    const recentIdx = recentOrders.value.findIndex(o => o.name === invoice.name)
    if (recentIdx !== -1) {
      recentOrders.value[recentIdx].delivery_exists = true
    }
  } catch (err) {
    error.value = err.message || 'تحویل ناموفق بود.'
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

async function createCustomerFromQuery(payload) {
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
    resolvedName = normalizedMobile ? `مشتری ${normalizedMobile.slice(-4)}` : 'مشتری POS'
  }

  if (payload?.is_new) {
    const nameInput = await showPrompt('نام مشتری جدید را وارد کنید:', resolvedName || '')
    if (nameInput === null) {
      return
    }
    const cleanedName = String(nameInput || '').trim()
    resolvedName = cleanedName || 'مشتری POS'

    const mobileInput = await showPrompt('شماره تماس مشتری جدید را وارد کنید (اختیاری):', normalizedMobile || '')
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

async function addQuickCustomer() {
  const name = await showPrompt('نام مشتری را وارد کنید:', form.customer_name || '')
  if (name === null) {
    return
  }
  const mobile = await showPrompt('شماره موبایل را وارد کنید:', form.mobile || '')
  if (mobile === null) {
    return
  }
  form.customer_name = String(name || '').trim() || 'مشتری POS'
  form.mobile = String(mobile || '').trim()
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

function currentOrderDraftSignature() {
  const lines = cart
    .map((line) => ({
      slug: String(line.slug || '').trim(),
      item_code: String(line.item_code || '').trim(),
      title: String(line.title || '').trim(),
      qty: Number(line.qty || 0),
      price: Number(line.price || 0),
      note: String(line.note || '').trim(),
      variant_of: String(line.variant_of || '').trim(),
      customization: normalizeCartCustomization(line.customization || {}, line.customization_ingredients || []),
    }))
    .sort((a, b) => `${a.slug}:${a.item_code}:${a.note}`.localeCompare(`${b.slug}:${b.item_code}:${b.note}`))

  return JSON.stringify({
    form: {
      customer_name: String(form.customer_name || '').trim(),
      mobile: String(form.mobile || '').trim(),
      order_mode: String(form.order_mode || '').trim(),
      customer_type: String(form.customer_type || '').trim(),
      guest_count: Number(form.guest_count || 0),
      place: String(form.place || '').trim(),
      waiter: String(form.waiter || '').trim(),
      waiter_name: String(form.waiter_name || '').trim(),
      note: String(form.note || '').trim(),
    },
    financial: {
      discountType: financial.discountType,
      discountValue: Number(financial.discountValue || 0),
      serviceType: financial.serviceType,
      serviceValue: Number(financial.serviceValue || 0),
      taxType: financial.taxExempt ? 'fixed' : financial.taxType,
      taxValue: financial.taxExempt ? 0 : Number(financial.taxValue || 0),
      tipAmount: Number(financial.tipAmount || 0),
      couponCode: String(financial.couponCode || '').trim(),
      creditCardCode: String(financial.creditCardCode || '').trim(),
      taxExempt: Boolean(financial.taxExempt),
    },
    lines,
  })
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
      lastRemovedLine.value = { ...cart[idx] }
      cart.splice(idx, 1)
    }
    if (selectedCartLineId.value === line.line_id) {
      selectedCartLineId.value = cart[0]?.line_id || ''
    }
    return
  }
  line.qty = Number(safeQty.toFixed(3))
}

function undoLastRemoval() {
  if (!lastRemovedLine.value) return
  cart.push({ ...lastRemovedLine.value })
  selectedCartLineId.value = lastRemovedLine.value.line_id
  lastRemovedLine.value = null
}

function addToCart(item, qty = 1, customizationPayload = null, hasCustomization = false, unitPrice = null, options = {}) {
  if (Number(item?.out_of_stock || 0) === 1) {
    error.value = `«${item?.title || item?.item_name || item?.name || ''}» ناموجود است و قابل فروش نیست.`
    return
  }
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
    recordPopularItem(itemSlug, qty)
    return
  }

  recordPopularItem(itemSlug, qty)
  popularSlugsMap.value = buildPopularSlugsMapFromLocalStorage()
  const lineId = `line-${Math.random().toString(36).slice(2, 11)}`
  cart.push({
    line_id: lineId,
    signature,
    slug: itemSlug,
    title: item.title || item.item_name || item.name,
    image: item.image || fallbackImage,
    qty: Number(Number(qty || 1).toFixed(3)),
    price: Number(unitPrice ?? item.base_price ?? item.standard_rate ?? item.price ?? 0),
    item_code: item.name,
    packaging_price: Number(item.packaging_price || 0),
    note: '',
    has_customization: Boolean(hasCustomization),
    customization: normalizedCustomization,
    customization_ingredients: options.customizationIngredients || [],
    variant_of: options.variant_of || item.variant_of || '',
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

async function editLineNote(line) {
  const next = await showPrompt('یادداشت آیتم:', line.note || '')
  if (next === null) {
    return
  }
  line.note = String(next || '').trim()
}

function clearCartState({ preserveEditing = false } = {}) {
  if (!preserveEditing) {
    editingOriginalOrder.isEditing = false
    editingOriginalOrder.name = ''
    editingOriginalOrder.order_code = ''
    editingOriginalOrder.draftSignature = ''
  }
  cart.splice(0, cart.length)
  selectedCartLineId.value = ''
  lastRemovedLine.value = null
}

function clearCart() {
  if (!cart.length) {
    return
  }
  const confirmed = window.confirm('سبد خرید خالی شود؟')
  if (!confirmed) {
    return
  }
  clearCartState()
}

const POPULAR_ITEMS_KEY = 'pos-popular-items-v2'

function buildPopularSlugsMapFromLocalStorage() {
  try {
    const raw = localStorage.getItem(POPULAR_ITEMS_KEY)
    if (!raw) return {}
    const stored = JSON.parse(raw)
    const cutoff = Date.now() - 30 * 24 * 60 * 60 * 1000
    const result = {}
    for (const [slug, entries] of Object.entries(stored)) {
      const total = (entries || []).filter(e => e.ts >= cutoff).reduce((s, e) => s + e.qty, 0)
      if (total > 0) result[slug] = total
    }
    return result
  } catch {
    return {}
  }
}

function recordPopularItem(slug, qty) {
  if (!slug) return
  try {
    const raw = localStorage.getItem(POPULAR_ITEMS_KEY)
    const stored = raw ? JSON.parse(raw) : {}
    if (!stored[slug]) stored[slug] = []
    stored[slug].push({ ts: Date.now(), qty: Number(qty || 1) })
    const cutoff = Date.now() - 30 * 24 * 60 * 60 * 1000
    for (const key of Object.keys(stored)) {
      stored[key] = (stored[key] || []).filter(e => e.ts >= cutoff)
      if (!stored[key].length) delete stored[key]
    }
    localStorage.setItem(POPULAR_ITEMS_KEY, JSON.stringify(stored))
  } catch {
    // ignore
  }
}

async function loadTodayTransactions(force = false) {
  if (todayTransactionsبارگذاری.value) return
  if (!force && todayTransactions.value.length > 0) return
  todayTransactionsبارگذاری.value = true
  todayTransactionsError.value = ''
  try {
    const today = new Date().toISOString().split('T')[0]
    const payload = await listManagementOrders({ date_from: today, date_to: today, source: 'web' })
    todayTransactions.value = (payload?.orders || []).filter(isManagementPOSTransaction)
  } catch (err) {
    todayTransactionsError.value = err.message || 'خطا در بارگذاری تراکنش‌های امروز'
  } finally {
    todayTransactionsبارگذاری.value = false
  }
}

async function loadRecentOrders(force = false) {
  if (recentOrdersبارگذاری.value) return
  if (!force && recentOrders.value.length > 0) return
  recentOrdersبارگذاری.value = true
  recentOrdersError.value = ''
  try {
    const dateFrom = recentOrdersDateFrom.value || new Date().toISOString().split('T')[0]
    const payload = await listManagementOrders({ date_from: dateFrom, date_to: dateFrom })
    recentOrders.value = payload?.orders || []
  } catch (err) {
    recentOrdersError.value = err.message || 'خطا در بارگذاری سفارش‌های اخیر'
  } finally {
    recentOrdersبارگذاری.value = false
  }
}

async function openOrderDetailModal(tx) {
  if (!tx) return
  orderDetailModal.open = true
  orderDetailModal.بارگذاری = true
  orderDetailModal.loadError = ''
  orderDetailModal.saveError = ''
  orderDetailModal.order = null
  orderDetailModal.canSettle = false
  orderDetailModal.settleMethod = ''
  orderDetailModal.settleReference = ''
  orderDetailModal.settleError = ''
  orderDetailModal.settling = false
  orderDetailModal.editForm.payment_method = ''
  orderDetailModal.editForm.note = ''
  orderDetailModal.editForm.customer_name = ''

  try {
    const orderName = String(tx.name || tx.order_code || '').trim()
    if (!orderName) throw new Error('شناسه سفارش معتبر نیست.')
    const payload = await getManagementOrderDetail(orderName)
    orderDetailModal.order = payload?.order || null
    if (orderDetailModal.order) {
      orderDetailModal.canSettle = canSettleOrder(orderDetailModal.order)
      orderDetailModal.settleMethod = orderDetailModal.order.payment_method || ''
      orderDetailModal.editForm.payment_method = orderDetailModal.order.payment_method || ''
      orderDetailModal.editForm.note = orderDetailModal.order.note || ''
      orderDetailModal.editForm.customer_name = orderDetailModal.order.customer_name || ''
    }
  } catch (err) {
    orderDetailModal.loadError = err.message || 'خطا در بارگذاری جزئیات سفارش'
  } finally {
    orderDetailModal.بارگذاری = false
  }
}

function closeOrderDetailModal() {
  orderDetailModal.open = false
  orderDetailModal.بارگذاری = false
  orderDetailModal.saving = false
  orderDetailModal.loadError = ''
  orderDetailModal.saveError = ''
  orderDetailModal.order = null
  orderDetailModal.canSettle = false
  orderDetailModal.settleMethod = ''
  orderDetailModal.settleReference = ''
  orderDetailModal.settleError = ''
  orderDetailModal.settling = false
}

async function saveOrderDetailEdit() {
  if (!orderDetailModal.order?.name) return
  orderDetailModal.saving = true
  orderDetailModal.saveError = ''
  try {
    await updateManagementOrder({
      order_name: orderDetailModal.order.name,
      payment_method: orderDetailModal.editForm.payment_method || undefined,
      note: orderDetailModal.editForm.note,
      customer_name: orderDetailModal.editForm.customer_name || undefined,
    })
    successMessage.value = 'سفارش با موفقیت ویرایش شد.'
    orderDetailModal.order.payment_method = orderDetailModal.editForm.payment_method
    orderDetailModal.order.note = orderDetailModal.editForm.note
    orderDetailModal.order.customer_name = orderDetailModal.editForm.customer_name
    closeOrderDetailModal()
    if (leftPanelTab.value === 'history') {
      loadTodayTransactions(true)
    } else if (leftPanelTab.value === 'recent') {
      loadRecentOrders(true)
    }
  } catch (err) {
    orderDetailModal.saveError = err.message || 'ویرایش سفارش ناموفق بود.'
  } finally {
    orderDetailModal.saving = false
  }
}

async function quickSettleOrder(order) {
  if (!order?.name) return
  await openOrderDetailModal(order)
}

async function confirmSettleOrder() {
  if (!orderDetailModal.order?.name) return
  const selectedMethod = normalizePaymentMethodKind(orderDetailModal.settleMethod || payment.method || 'cash')
  const selectedOption = posPaymentOptions.value.find((option) => normalizePaymentMethodKind(option.method) === selectedMethod)
  orderDetailModal.settling = true
  orderDetailModal.settleError = ''
  try {
    const result = await settlePOSOrder(orderDetailModal.order.name, {
      method: selectedMethod,
      mode_of_payment: selectedOption?.mode_of_payment || selectedOption?.label || '',
      provider: 'manual',
      reference_no: selectedMethod === 'credit' ? '' : (orderDetailModal.settleReference || payment.reference_no || ''),
      rrn: selectedMethod === 'credit' ? '' : (payment.rrn || ''),
      provider_payload: {
        source: 'management-pos-order-detail',
      },
    })
    const siInfo = result.sales_invoice ? ` | فاکتور: ${result.sales_invoice}` : ''
    successMessage.value = selectedMethod === 'credit'
      ? `فاکتور ${orderDetailModal.order.order_code || orderDetailModal.order.name} اعتباری ثبت شد و بدهکار ماند.${siInfo}`
      : `فاکتور ${orderDetailModal.order.order_code || orderDetailModal.order.name} تسویه شد.${siInfo}`
    closeOrderDetailModal()
    await loadOpenInvoices(true)
    await loadTodayTransactions(true)
    await loadRecentOrders(true)
  } catch (err) {
    orderDetailModal.settleError = err.message || 'تسویه سفارش ناموفق بود.'
  } finally {
    orderDetailModal.settling = false
  }
}

function openReturnInvoiceModal() {
  if (!orderDetailModal.order?.name) return
  returnInvoiceModal.open = true
  returnInvoiceModal.بارگذاری = false
  returnInvoiceModal.error = ''
  returnInvoiceModal.reason = ''
}

function openPurgeModalFromList(order) {
  if (!order?.name) return
  purgeModal.open = true
  purgeModal.loading = false
  purgeModal.error = ''
  purgeModal.success = ''
  purgeModal.orderCode = order.order_code || order.name
  purgeModal.orderName = order.name
}

function openPurgeModal() {
  if (!orderDetailModal.order?.name) return
  purgeModal.open = true
  purgeModal.loading = false
  purgeModal.error = ''
  purgeModal.success = ''
  purgeModal.orderCode = orderDetailModal.order.order_code || orderDetailModal.order.name
  purgeModal.orderName = orderDetailModal.order.name
}

function closePurgeModal() {
  if (purgeModal.loading) return
  purgeModal.open = false
  purgeModal.loading = false
  purgeModal.error = ''
  purgeModal.success = ''
  purgeModal.orderCode = ''
  purgeModal.orderName = ''
}

async function executePurgeOrder() {
  if (!purgeModal.orderName) return
  purgeModal.loading = true
  purgeModal.error = ''
  purgeModal.success = ''
  try {
    const result = await purgeManagementPOSOrder(purgeModal.orderName)
    
    // Safety check objects
    const summary = result.summary?.cleaned_records || {}
    const errors = result.summary?.errors || []

    // Update local state instead of full refetch
    const orderName = purgeModal.orderName
    
    // Update Open Invoices
    if (openInvoices.value.some(o => o.name === orderName)) {
      openInvoices.value = openInvoices.value.filter(o => o.name !== orderName)
    }
    
    // Update Recent Orders
    if (recentOrders.value.some(o => o.name === orderName)) {
      recentOrders.value = recentOrders.value.filter(o => o.name !== orderName)
    }
    
    // Update Today Transactions
    if (todayTransactions.value.some(o => o.name === orderName)) {
      todayTransactions.value = todayTransactions.value.filter(o => o.name !== orderName)
    }

    if (selectedOpenInvoiceKey.value && selectedOpenInvoiceKey.value.includes(orderName)) {
      selectedOpenInvoiceKey.value = ''
      selectedOpenInvoiceDetail.value = null
    }

    if (expandedInvoiceKey.value && expandedInvoiceKey.value.includes(orderName)) {
      expandedInvoiceKey.value = ''
    }

    if (result.status === 'partial_success' || errors.length > 0) {
      purgeModal.error = 'بخشی از فرآیند ناموفق بود:\n' + errors.join('\n')
      purgeModal.loading = false
      return // Wait for user to dismiss
    }

    const deletedTypes = Object.keys(summary).filter(k => summary[k].length > 0).join(', ')
    purgeModal.success = 'سفارش با موفقیت لغو و از عملیات صندوق پاکسازی شد.\n' + (deletedTypes ? 'جزئیات: ' + deletedTypes : '')
    
    setTimeout(() => {
      purgeModal.loading = false // Reset before closing
      closePurgeModal()
      closeOrderDetailModal()
    }, 2000)
    
  } catch (err) {
    purgeModal.error = err.message || 'حذف کامل سفارش ناموفق بود.'
    purgeModal.loading = false
  }
}

function closeReturnInvoiceModal() {
  returnInvoiceModal.open = false
  returnInvoiceModal.بارگذاری = false
  returnInvoiceModal.error = ''
  returnInvoiceModal.reason = ''
}

async function confirmCreateReturnInvoice() {
  if (!orderDetailModal.order?.name) return
  returnInvoiceModal.بارگذاری = true
  returnInvoiceModal.error = ''
  try {
    const result = await createManagementReturnOrder({
      order_name: orderDetailModal.order.name,
      reason: returnInvoiceModal.reason || 'درخواست مشتری',
    })
    successMessage.value = `فاکتور برگشتی ${result.return_order_code} برای سفارش ${result.original_order_code} ساخته شد.`
    closeReturnInvoiceModal()
    closeOrderDetailModal()
    if (leftPanelTab.value === 'history') {
      loadTodayTransactions(true)
    } else if (leftPanelTab.value === 'recent') {
      loadRecentOrders(true)
    }
  } catch (err) {
    returnInvoiceModal.error = err.message || 'ساخت فاکتور برگشتی ناموفق بود.'
  } finally {
    returnInvoiceModal.بارگذاری = false
  }
}

function closeCustomizationSheet() {
  customizationSheet.open = false
  customizationSheet.بارگذاری = false
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
  
  // Quick pre-check: If this is an exact variant that has NO customization and NO BOM, just add it directly.
  // We can't know for sure until we fetch, but we open the sheet and auto-close if true.
  
  customizationSheet.open = true
  customizationSheet.بارگذاری = true
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
    customizationSheet.variantsMapping = payload.variants_mapping || []
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
    
    // Auto-confirm variant-only items that don't need user input if it's a new add
    // Wait, if it's a template, we DO need user input.
    // If it's ALREADY a variant, and has NO ingredients and NO non-variant modifier groups, just add it.
    const isVariantOnly = ingredients.length === 0 && 
                          modifierGroups.every(g => g.group_name.startsWith('variant::'));
    if (!editingLine && isVariantOnly && !detailItem.variant_of && !detailItem.has_variants) {
      // It's a resolved variant item with no customization.
      // We shouldn't hit this often because PosProductPanel bypasses it if has_bom=0 & customizable=0
    }
    
  } catch (sheetErr) {
    customizationSheet.error = sheetErr.message || 'دریافت تنظیمات BOM ناموفق بود.'
  } finally {
    customizationSheet.بارگذاری = false
  }
}

function openLineCustomizationEditor(line) {
  if (!line) {
    return
  }
  
  let baseItem = resolveProductBySlug(line.slug, line)
  
  // If we are editing a variant-only item, we want to open the parent template so the user can switch variants.
  // Otherwise, the backend will treat the current variant's attributes as fixed and hide the selector.
  let targetItem = baseItem
  const parentName = line.variant_of || baseItem.variant_of || (baseItem.item && baseItem.item.variant_of)
  if (parentName) {
    const parentItem = products.value.find(p => p.name === parentName || getItemSlug(p) === parentName)
    if (parentItem) {
      targetItem = parentItem
    } else {
      targetItem = { name: parentName, item_code: parentName, slug: parentName }
    }
  }
  
  // If we swapped to parent, we need to map the current variant back into a customization payload so it preselects.
  const isVariant = !!parentName
  let sheetLine = line
  if (isVariant && (!line.customization || !line.customization.selected_modifiers || line.customization.selected_modifiers.length === 0)) {
    const attrs = baseItem.variant_attributes || (baseItem.item && baseItem.item.variant_attributes) || []
    if (attrs.length > 0) {
      sheetLine = { ...line, customization: { selected_modifiers: attrs.map(a => ({ group: `variant::${a.attribute}`, option: a.value })) } }
    }
  }
  
  openCustomizationSheet(targetItem, { editingLine: sheetLine })
}

function confirmCustomizationAdd() {
  if (!customizationSheet.item) {
    return
  }
  const normalized = normalizeCartCustomization(customizationSheet.customization, customizationSheet.ingredients)
  
  // Detect if this is a variant-only selection
  const hasVariantSelectors = customizationSheet.modifierGroups.some(g => g.group_name.startsWith('variant::'));

  if (hasVariantSelectors && (customizationSheet.variantsMapping || []).length > 0) {
    // Find the matching variant from variantsMapping
    const selectedAttributes = normalized.selected_modifiers || [];
    let matchedVariant = null;
    for (const variant of customizationSheet.variantsMapping) {
      let isMatch = true;
      const fixedAttributes = customizationSheet.item.variant_fixed_attributes || {};
      for (const attr of variant.attributes || []) {
        // If it's a fixed attribute, it won't be in selectedAttributes
        if (fixedAttributes[attr.attribute] === attr.value) {
          continue;
        }
        
        // Check if this attribute was presented to the user as a modifier group
        const isVariable = customizationSheet.modifierGroups.some(g => g.group_name === `variant::${attr.attribute}`);
        if (!isVariable) {
          continue; // It's likely a show_in_website=0 attribute, ignore it.
        }
        
        const sel = selectedAttributes.find(m => m.group === `variant::${attr.attribute}`);
        if (!sel || sel.option !== attr.value) {
          isMatch = false;
          break;
        }
      }
      if (isMatch) {
        matchedVariant = variant;
        break;
      }
    }
    
    if (matchedVariant) {
      const nextQty = Number(Number(customizationSheet.qty || 1).toFixed(3));
      const nextPrice = Number(matchedVariant.base_price || 0);
      const nextSlug = matchedVariant.slug || matchedVariant.name;
      
      if (customizationSheet.editing_line_id) {
        const editingLine = cart.find(line => line.line_id === customizationSheet.editing_line_id);
        if (editingLine) {
          const nextSignature = cartLineSignature(nextSlug, null);
          const duplicateLine = cart.find(line => line.signature === nextSignature && line.line_id !== editingLine.line_id);
          if (duplicateLine) {
            duplicateLine.qty = Number((Number(duplicateLine.qty || 0) + nextQty).toFixed(3));
            setCartQty(editingLine, 0);
            selectedCartLineId.value = duplicateLine.line_id;
          } else {
            editingLine.signature = nextSignature;
            editingLine.slug = nextSlug;
            editingLine.title = matchedVariant.item_name || matchedVariant.name;
            editingLine.item_code = matchedVariant.item_code || matchedVariant.name;
            editingLine.name = matchedVariant.name;
            editingLine.price = nextPrice;
            editingLine.qty = nextQty;
            // WE MUST KEEP the customization so it can be edited again!
            editingLine.has_customization = true;
            editingLine.customization = normalized;
            editingLine.customization_ingredients = customizationIngredients;
            
            // Store parent info so edit knows how to open
            editingLine.variant_of = customizationSheet.item.name;
            
            selectedCartLineId.value = editingLine.line_id;
          }
          closeCustomizationSheet();
          return;
        }
      }
      
      addToCart({
        ...matchedVariant,
        title: matchedVariant.item_name || matchedVariant.name,
        variant_of: customizationSheet.item.name
      }, nextQty, normalized, true, nextPrice, {
        customizationIngredients
      });
      closeCustomizationSheet();
      return;
    }
  }

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

async function lookupProductBarcode(raw) {
  try {
    const payload = await getManagementProductByBarcode(raw)
    if (payload?.status !== 'success' || !payload.item) {
      error.value = 'محصولی با این بارکد پیدا نشد.'
      return
    }
    const found = payload.item
    const match = products.value.find((item) => {
      const keys = [item.name, item.item_code, item.slug].map((value) => String(value || '').trim())
      return keys.includes(String(found.name || '').trim()) || keys.includes(String(found.item_code || '').trim())
    })
    if (!match) {
      error.value = `محصول «${found.item_name || found.name}» در لیست POS این شعبه موجود نیست.`
      return
    }
    if (Number(match.out_of_stock || 0) === 1) {
      error.value = `«${match.title || match.item_name || found.item_name}» فعلاً ناموجود است.`
      return
    }
    addToCart(match, 1)
    scannerFeedback.value = `بارکد اسکن شد: ${match.title || match.item_name || found.item_name}`
    error.value = ''
  } catch (lookupErr) {
    error.value = lookupErr?.message || 'خطا در استعلام بارکد محصول.'
  }
}

async function handleScaleBarcodeScan() {
  const raw = scannerInput.value.trim()
  scannerFeedback.value = ''
  if (!raw) {
    return
  }

  let scaleHandled = false
  if (scaleConfig.enabled) {
    try {
      const parsed = parseScaleBarcode(raw)
      const item = resolveScaleProduct(parsed.itemCode)
      if (item) {
        addToCart(item, parsed.qty)
        scannerFeedback.value = `بارکد وزنی اعمال شد: ${item.title || item.item_name} × ${formatCompactNumber(parsed.qty)}`
        error.value = ''
        scaleHandled = true
      }
    } catch (scanErr) {
      scaleHandled = false
    }
  }

  if (!scaleHandled) {
    await lookupProductBarcode(raw)
  }
  scannerInput.value = ''
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

function buildPaymentSplitAuditLine(splits = []) {
  const normalizedSplits = (splits || [])
    .map((row) => ({
      method: normalizePaymentMethodKind(row?.method),
      amount: Number(row?.amount || 0),
      label: String(row?.label || row?.mode_of_payment || '').trim(),
      mode_of_payment: String(row?.mode_of_payment || '').trim(),
    }))
    .filter((row) => row.amount > 0)

  if (!normalizedSplits.length) {
    return ''
  }

  return normalizedSplits
    .map((row) => `${row.label || row.mode_of_payment || row.method}: ${formatMoney(row.amount, currency.value)}`)
    .join(' | ')
}

function resolvePaymentSubmission(paymentMeta = {}) {
  const splits = (Array.isArray(paymentMeta?.splits) ? paymentMeta.splits : [])
    .map((row) => ({
      method: normalizePaymentMethodKind(row?.method),
      amount: Number(row?.amount || 0),
      label: String(row?.label || row?.mode_of_payment || '').trim(),
      mode_of_payment: String(row?.mode_of_payment || '').trim(),
      option_key: String(row?.optionKey || row?.option_key || '').trim(),
    }))
    .filter((row) => row.amount > 0)

  if (!splits.length) {
    return {
      splits: [],
      primary: {
        method: normalizePaymentMethodKind(payment.method),
        amount: Number(totals.value?.payableAmount || 0),
        label: '',
        mode_of_payment: '',
        option_key: '',
      },
      auditLine: '',
    }
  }

  const creditSplit = splits.find((row) => row.method === 'credit')
  const cardSplit = splits.find((row) => row.method === 'card')
  const cashSplit = splits.find((row) => row.method === 'cash')

  return {
    splits,
    primary: creditSplit || cardSplit || cashSplit || splits[0],
    auditLine: buildPaymentSplitAuditLine(splits),
  }
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
    return '۰'
  }
  const trimmed = parsed.toFixed(decimals).replace(/\.?0+$/, '')
  if (trimmed.includes('.')) {
    return trimmed.replace(/\d/g, (digit) => '۰۱۲۳۴۵۶۷۸۹'[Number(digit)])
  }
  return toPersianNumber(Number(trimmed || 0))
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
  return toPersianNumber(value)
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
  // Try to use the last created order code from ordersAPI or form
  const ticket = getTicketSessionById(activeTicketId.value)
  const snapshotCode = ticket?.snapshot?.lastOrderCode || ''
  if (snapshotCode) return snapshotCode
  // Fallback: use form data if available
  const formCode = editingOriginalOrder.name || ''
  if (formCode) return formCode
  // Last resort: temporary code
  const ticketPart = String(activeTicketId.value || 'ticket-1').replace(/^ticket-/, '')
  return ticketPart
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
            <span class="item-index">${toPersianNumber(index + 1)}.</span>
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

function receiptFontSizePx() {
  const base = Math.min(Math.max(Number(printFontSettings.font_size || 11), 8), 24)
  const scale = String(printFontSettings.receipt_font_scale || 'متوسط')
  if (scale === 'کوچک') return Math.max(base - 1, 8)
  if (scale === 'بزرگ') return Math.min(base + 2, 26)
  return base
}

function receiptStylesCss() {
  return `
    @font-face { font-family: Peyda; src: url('/fonts/Pevda-Reqular.ttf') format('truetype'); font-weight: 400; font-style: normal; }
    @font-face { font-family: Peyda; src: url('/fonts/Peyda-Medium.ttf') format('truetype'); font-weight: 500; font-style: normal; }
    @font-face { font-family: Peyda; src: url('/fonts/Peyda-SemiBold.ttf') format('truetype'); font-weight: 600; font-style: normal; }
    @font-face { font-family: Peyda; src: url('/fonts/Peyda-Bold.ttf') format('truetype'); font-weight: 700; font-style: normal; }
    @page { size: 80mm auto; margin: 4mm; }
    html, body { width: 100%; margin: 0; padding: 0; }
    body { font-family: ${printFontSettings.font_family || 'Peyda'}, Peyda, sans-serif; color: var(--mg-text-main); background: var(--mg-bg-surface); }
    .receipt { width: 72mm; margin: 0 auto; font-size: ${receiptFontSizePx()}px; line-height: 1.35; }
    .center { text-align: center; }
    .brand-name { font-size: 13px; font-weight: 700; margin-bottom: 2px; }
    .title { font-size: 14px; font-weight: 700; margin-bottom: 2px; }
    .muted { color: var(--mg-success); font-size: 10px; }
    .sep { border-top: 1px dashed var(--mg-success-bg); margin: 6px 0; }
    .meta-row { display: flex; justify-content: space-between; gap: 6px; margin: 2px 0; }
    .meta-block { margin-top: 4px; border: 1px dashed var(--mg-success-bg); border-radius: 7px; padding: 4px 5px; }
    .meta-block strong { display: block; font-size: 10px; color: var(--mg-success); margin-bottom: 2px; }
    .meta-block p { margin: 0; white-space: pre-wrap; font-size: 10px; }
    .item-row { padding: 4px 0; border-bottom: 1px dashed var(--mg-success-bg); }
    .item-head { display: grid; grid-template-columns: auto 1fr auto; gap: 4px; align-items: start; }
    .item-index { font-weight: 600; }
    .item-title { font-weight: 600; }
    .item-total { font-weight: 700; }
    .item-meta { display: flex; justify-content: space-between; gap: 6px; margin-top: 2px; font-size: 10px; color: var(--mg-success); }
    .item-custom { margin: 3px 0 0; padding-right: 12px; font-size: 10px; color: var(--mg-success); }
    .item-custom li { margin: 1px 0; }
    .item-note { margin-top: 3px; font-size: 10px; color: var(--mg-success); }
    .totals { margin-top: 6px; display: grid; gap: 3px; }
    .total-row { display: flex; justify-content: space-between; gap: 6px; }
    .payable { border-top: 1px dashed var(--mg-success-bg); margin-top: 2px; padding-top: 4px; font-size: 12px; font-weight: 700; }
    .note { margin-top: 6px; font-size: 10px; color: var(--mg-success); white-space: pre-wrap; }
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
      label: packagingSettings.label || 'بسته‌بندی',
      value: totalValues.packagingAmount || 0,
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
      <div class="meta-row"><span>مشتری</span><span>${escapeHtml(customerName || 'مشتری POS')}</span></div>
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
    paymentLabel: paymentMethodDisplayLabel(payment.method),
    customerName: form.customer_name || 'مشتری POS',
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
    const orderCode = String(order.name || '').trim()
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
  if (normalizePaymentMethodKind(payment.method) === 'credit') {
    error.value = 'برای پرداخت اعتباری، فیش پرداخت POS چاپ نمی‌شود چون مبلغ هنوز دریافت نشده است.'
    return
  }
  printEditorOpen.value = true
}

function closePrintEditor() {
  printEditorOpen.value = false
}

function autoPrintReceipt() {
  if (normalizePaymentMethodKind(payment.method) === 'credit') {
    return
  }
  // چاپ خودکار رسید بعد از تسویه
  if (!cart.length) {
    // Try building from last receipt info
    printCurrentTicket()
    return
  }
  printCurrentTicket()
}

function printCurrentTicket() {
  if (!cart.length) {
    error.value = 'برای چاپ، باید حداقل یک آیتم در فاکتور باشد.'
    return
  }
  if (normalizePaymentMethodKind(payment.method) === 'credit') {
    error.value = 'برای پرداخت اعتباری، فیش پرداخت POS چاپ نمی‌شود چون مبلغ هنوز دریافت نشده است.'
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

async function submitPOSOrder(payNow = true, paymentMeta = {}, withProduction = false) {
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
  let paymentSelection = resolvePaymentSubmission(paymentMeta)
  let paymentNoteLine = paymentSelection.auditLine

  const paymentPayload = payNow
    ? {
        method: paymentSelection.primary?.method || normalizePaymentMethodKind(payment.method),
        mode_of_payment: paymentSelection.primary?.mode_of_payment || '',
        provider: paymentSelection.primary?.method === 'card' ? paymentBoot.provider : 'manual',
        terminal_id: paymentBoot.terminal_id || '',
        reference_no: payment.reference_no || '',
        rrn: payment.rrn || '',
        splits: paymentSelection.splits,
      }
    : {
        method: 'credit',
        mode_of_payment: 'اعتباری',
        provider: 'manual',
        terminal_id: paymentBoot.terminal_id || '',
        reference_no: '',
        rrn: '',
        splits: [],
      }

  if (!payNow && editingOriginalOrder.isEditing && editingOriginalOrder.name) {
    const currentSignature = currentOrderDraftSignature()
    if (editingOriginalOrder.draftSignature && currentSignature === editingOriginalOrder.draftSignature) {
      successMessage.value = `فاکتور ${editingOriginalOrder.order_code || editingOriginalOrder.name} بدون تغییر باز ماند.`
      error.value = ''
      await loadOpenInvoices(true)
      saveActiveTicketSnapshot()
      return
    }
  }

  // Pay original invoice directly when editing
  if (payNow && editingOriginalOrder.isEditing && editingOriginalOrder.name) {
    submitting.value = true
    error.value = ''
    successMessage.value = ''
    try {
      const code = editingOriginalOrder.name
      const payResult = await settlePOSOrder(code, paymentPayload)
      let siInfo = payResult.sales_invoice ? ` | فاکتور: ${payResult.sales_invoice}` : ''
      
      let dnInfo = ''
      if (withProduction) {
        const deliverResult = await deliverInvoiceOnly(code)
        dnInfo = deliverResult.delivery_note ? ` | رسید: ${deliverResult.delivery_note}` : ''
        successMessage.value = `فاکتور ${code} تسویه و تحویل شد.${siInfo}${dnInfo}`
      } else {
        successMessage.value = `فاکتور ${code} با موفقیت تسویه شد.${siInfo}`
      }
      
      editingOriginalOrder.isEditing = false
      editingOriginalOrder.name = ''
      
      if (financial.createNextInvoice) {
        resetCurrentInvoiceState()
        saveActiveTicketSnapshot()
      } else {
        saveActiveTicketSnapshot()
      }
      
      // Optimistically update
      // If it's credit or partial, it should stay in openInvoices with updated outstanding.
      // But we don't have the exact outstanding amount returned from the backend currently.
      // Easiest is to filter out ONLY if it's fully paid (cash/card etc) and not partial.
      const isCredit = paymentPayload.method === 'credit'
      const isPartial = paymentPayload.splits && paymentPayload.splits.some(s => s.amount > 0) && 
                        paymentPayload.splits.reduce((sum, s) => sum + s.amount, 0) < Number(totals.value.payableAmount)
                        
      if (!isCredit && !isPartial) {
        openInvoices.value = openInvoices.value.filter(o => o.name !== code)
      }
      
      const recentIdx = recentOrders.value.findIndex(o => o.name === code)
      if (recentIdx !== -1) {
        recentOrders.value[recentIdx].status = withProduction ? 'delivered' : 'paid'
        recentOrders.value[recentIdx].payment_method = paymentPayload.method
      }
      await loadTodayTransactions(true)
      await loadRecentOrders(true)
      window.setTimeout(() => {
        refreshHardwareStatus()
      }, 0)
    } catch (err) {
      error.value = err.message || 'تسویه فاکتور ناموفق بود.'
    } finally {
      submitting.value = false
    }
    return
  }



  const payload = {
    customer_name: form.customer_name || 'مشتری POS',
    mobile: form.mobile || '',
    order_type: form.order_mode,
    note: [
      buildOrderNote(),
      editingOriginalOrder.isEditing ? `ادامه فاکتور ${editingOriginalOrder.name}` : '',
      paymentNoteLine ? `روش پرداخت: ${paymentNoteLine}` : '',
    ].filter(Boolean).join(' | '),
    customer_type: form.customer_type,
    guest_count: form.guest_count,
    place: form.place,
    waiter: form.waiter || '',
    waiter_name: form.waiter_name || '',
    totals: {
      ...totals.value,
      currency: currency.value,
    },
    financial_modifiers: {
      discount_type: financial.discountType,
      discount_value: financial.discountValue,
      service_type: financial.serviceType,
      service_value: financial.serviceValue,
      tax_type: financial.taxExempt ? 'fixed' : financial.taxType,
      tax_value: financial.taxExempt ? 0 : financial.taxValue,
      tax_amount: totals.value.taxAmount || 0,
      tip_amount: financial.tipAmount,
      use_wallet: financial.useWallet,
      wallet_applied: totals.value.walletApplied,
      coupon_code: financial.couponCode,
      gift_card_code: financial.creditCardCode,
      tax_exempt: financial.taxExempt,
    },
    items: cart.map((line) => {
      let finalCustomization = line.customization || {
        ingredient_adjustments: [],
        selected_modifiers: [],
        selected_alternatives: [],
      };
      // If this line is a variant, we MUST strip the variant:: modifiers from the payload
      // because the backend resolves to the variant doc, which doesn't have the variant:: groups,
      // and it will throw an 'Invalid modifier group' error.
      if (line.variant_of && finalCustomization.selected_modifiers && finalCustomization.selected_modifiers.length > 0) {
        const cleanedModifiers = finalCustomization.selected_modifiers.filter(m => !m.group.startsWith('variant::'));
        finalCustomization = {
          ...finalCustomization,
          selected_modifiers: cleanedModifiers,
        };
      }
      
      return {
        item_slug: line.slug,
        qty: line.qty,
        note: line.note || '',
        customization: finalCustomization,
      };
    }),
    payment: paymentPayload,
  }

  submitting.value = true
  error.value = ''
  successMessage.value = ''

  try {
    let result
    if (payNow) {
      if (editingOriginalOrder.isEditing && editingOriginalOrder.name) {
        // از فاکتور باز اومدیم: فقط SI + Payment رو SO موجود
        result = await settlePOSOrder(editingOriginalOrder.name, {
          method: normalizePaymentMethodKind(payment.method),
          reference_no: payment.reference_no || '',
        })
        editingOriginalOrder.isEditing = false
        editingOriginalOrder.name = ''
        editingOriginalOrder.name = ''
      } else if (withProduction) {
        // "ثبت و تسویه فاکتور": SO + تولید + SI + Payment + DN
        result = await createAndSettlePOSOrder(payload)
      } else {
        // "تسویه فاکتور": فقط SO + SI + Payment (بدون تولید، بدون تحویل) - یکجا
        result = await createAndPayPOSOrder(payload)
      }
    } else {
      if (editingOriginalOrder.isEditing && editingOriginalOrder.name) {
        // ویرایش فاکتور موجود: کنسل کردن فاکتور قبلی + ساخت فاکتور جدید
        const previousOrderName = editingOriginalOrder.name
        await voidManagementPOSOrder(previousOrderName, 'جایگزینی فاکتور باز در POS')
        payload.note = (payload.note || '') + ` | جایگزین فاکتور ${previousOrderName}`
      }
      // فقط ثبت سفارش (بدون تولید، بدون پرداخت)
      result = await createPOSOrder(payload)
    }
    let orderCode = result.order_id || ''
    if (payNow) {
      if (withProduction) {
        // ثبت و تسویه یکجا (همه چی)
        const siInfo = result.sales_invoice ? ` | فاکتور: ${result.sales_invoice}` : ''
        const dnInfo = result.delivery_note ? ` | رسید: ${result.delivery_note}` : ''
        successMessage.value = `سفارش ${orderCode} تسویه و برای تولید/تحویل ثبت شد.${siInfo}${dnInfo}`
      } else if (editingOriginalOrder.isEditing) {
        // تسویه از فاکتور باز
        successMessage.value = `فاکتور ${orderCode} تسویه شد.`
      } else {
        // تسویه فاکتور (SO + SI + Payment)
        const siInfo = result.sales_invoice ? ` | فاکتور: ${result.sales_invoice}` : ''
        successMessage.value = `سفارش ${orderCode} ثبت و تسویه شد.${siInfo}`
      }
    } else {
      successMessage.value = `سفارش ${orderCode} ثبت شد (آماده تولید).`
    }

    if (editingOriginalOrder.isEditing) {
      const oldName = editingOriginalOrder.name
      successMessage.value = oldName
        ? `فاکتور جدید با یادداشت ادامه فاکتور ${oldName} ساخته شد.`
        : 'فاکتور جدید ساخته شد.'
      editingOriginalOrder.isEditing = false
      editingOriginalOrder.name = ''
      
      // Remove old order from local open invoices
      openInvoices.value = openInvoices.value.filter(o => o.name !== oldName)
    }

    // Save order code to ticket snapshot for receipt numbering
    if (orderCode) {
      const ticket = getTicketSessionById(activeTicketId.value)
      if (ticket) {
        if (!ticket.snapshot) ticket.snapshot = {}
        ticket.snapshot.lastOrderCode = orderCode
      }
    }

    // Auto-print receipt after successful settlement
    if (payNow && result?.sales_invoice) {
      autoPrintReceipt()
    }

    if (payNow) {
      await loadTodayTransactions(true)
      await loadRecentOrders(true)
    }

    if (financial.createNextInvoice) {
      resetCurrentInvoiceState()
      saveActiveTicketSnapshot()
    } else {
      saveActiveTicketSnapshot()
      window.location.href = '/management/orders'
    }

    // Refresh only open invoices to keep the badge up to date.
    // Recent orders and today transactions will fetch when their tabs are opened.
    loadOpenInvoices()
    window.setTimeout(() => {
      refreshHardwareStatus()
    }, 0)
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
  hardwareبارگذاری.value = true
  try {
    const payload = await getManagementPOSHardwareStatus()
    hardwareStatus.connected = Boolean(payload.connected)
    hardwareStatus.message = payload.message || 'وضعیت سخت افزار دریافت نشد.'
    hardwareStatus.latency_ms = Number(payload.latency_ms || 0)
  } catch (statusErr) {
    hardwareStatus.connected = false
    hardwareStatus.message = statusErr.message || 'بررسی وضعیت سخت افزار ناموفق بود.'
  } finally {
    hardwareبارگذاری.value = false
  }
}

async function loadPOSBoot() {
  بارگذاری.value = true
  error.value = ''
  popularSlugsMap.value = buildPopularSlugsMapFromLocalStorage()
  try {
    const payload = await getManagementPOSBoot()
    products.value = payload.items || []
    categories.value = payload.categories || []
    currency.value = payload.currency || 'IRR'
    applyPOSProfileSummary(payload.pos_profile || {})

    const bootPackaging = payload.packaging || {}
    packagingSettings.enabled = Boolean(bootPackaging.enabled)
    packagingSettings.flat_fee = Number(bootPackaging.flat_fee || 0)
    packagingSettings.per_item = bootPackaging.per_item !== false
    packagingSettings.apply_modes = Array.isArray(bootPackaging.apply_modes) ? bootPackaging.apply_modes : []
    packagingSettings.label = bootPackaging.label || 'هزینه بسته‌بندی'

    const bootPrintFont = payload.print_font || {}
    printFontSettings.font_family = bootPrintFont.font_family || 'Peyda'
    printFontSettings.font_size = Number(bootPrintFont.font_size || 11)
    printFontSettings.receipt_font_scale = bootPrintFont.receipt_font_scale || 'متوسط'

    bootPosConfig = payload.pos_config || null
    if (bootPosConfig) {
      const cfg = bootPosConfig
      const defaultOrderMode = cfg.default_order_mode || 'dine_in'
      const defaultCustomers = cfg.default_customers || {}
      const modeCustomer = defaultCustomers[defaultOrderMode] || {}

      form.order_mode = defaultOrderMode
      form.customer_name = modeCustomer.name || 'مشتری POS'
      form.mobile = modeCustomer.mobile || ''
      if (defaultOrderMode === 'delivery') {
        form.place = cfg.default_delivery_courier || cfg.default_delivery_place || ''
      } else if (defaultOrderMode === 'takeaway') {
        form.place = cfg.default_takeaway_place || ''
      }
    }

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
    paymentBoot.methods = [...posPaymentOptions.value]

    payment.method = bootPayment.default_method || 'cash'
    bootDefaultPaymentMethod = payment.method
    if (!posPaymentOptions.value.some((row) => row.method === payment.method)) {
      payment.method = posPaymentOptions.value[0]?.method || 'cash'
      bootDefaultPaymentMethod = payment.method
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
      setOpenInvoices(allOrders, true)
      loadCustomers()
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
    بارگذاری.value = false
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

async function onWindowKeydown(event) {
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
      const nextQty = await showPrompt('تعداد BOM را وارد کنید:', String(customizationSheet.qty))
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

  if (operationsOverlayOpen.value && key === 'Escape') {
    event.preventDefault()
    closeOperationsOverlay()
    return
  }

  if (showKeyboardMap.value && key === 'Escape') {
    event.preventDefault()
    showKeyboardMap.value = false
    return
  }

  if (cartDrawerOpen.value && key === 'Escape') {
    event.preventDefault()
    cartDrawerOpen.value = false
    return
  }

  if (handleGlobalProductSearchTyping(event)) {
    return
  }

  if (key === '?') {
    event.preventDefault()
    showKeyboardMap.value = !showKeyboardMap.value
    return
  }

  if (key === '/') {
    event.preventDefault()
    document.querySelector('.product-search-input')?.focus()
    return
  }

  if (key === 'Delete' && !search.value) {
    if (cart.length > 0) {
      event.preventDefault()
      const lastLine = cart[cart.length - 1]
      setCartQty(lastLine, 0)
    }
    return
  }

  if (key === 'F1') {
    event.preventDefault()
    if (cart.length > 0 && form.order_mode !== 'dine_in') {
      cartPanelRef.value?.openPaymentPopup('cash')
    }
    return
  }

  if (key === 'F2') {
    event.preventDefault()
    if (cart.length > 0 && form.order_mode !== 'dine_in') {
      cartPanelRef.value?.openPaymentPopup('card')
    } else {
      submitPOSOrder(true)
    }
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
    const nextQty = await showPrompt('تعداد جدید را وارد کنید:', String(line.qty))
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

// ---------------------------------------------------------------------------
// Kitchen → POS notifications: toast when an order becomes ready
// ---------------------------------------------------------------------------
const kitchenReadyQueue = ref([])
const seenKitchenReady = new Set()
let kitchenPollTimer = null
let kitchenPollInFlight = false
let kitchenPollPrimed = false

async function pollKitchenReady() {
  if (kitchenPollInFlight || typeof document === 'undefined' || document.hidden) return
  kitchenPollInFlight = true
  try {
    const payload = await getManagementPosKitchenNotifications({})
    const orders = Array.isArray(payload?.orders) ? payload.orders : []
    if (!kitchenPollPrimed) {
      kitchenPollPrimed = true
      orders.forEach((o) => seenKitchenReady.add(o.name))
      return
    }
    const fresh = orders.filter((o) => !seenKitchenReady.has(o.name))
    fresh.forEach((o) => seenKitchenReady.add(o.name))
    if (fresh.length) {
      kitchenReadyQueue.value = [...kitchenReadyQueue.value, ...fresh].slice(-5)
    }
  } catch (err) {
    // kitchen notifications are best-effort; stay silent on failure
  } finally {
    kitchenPollInFlight = false
  }
}

function dismissKitchenNotice(name) {
  kitchenReadyQueue.value = kitchenReadyQueue.value.filter((o) => o.name !== name)
}

onMounted(async () => {
  syncViewportMode()
  window.addEventListener('keydown', onWindowKeydown)
  window.addEventListener('resize', syncViewportMode)
  window.addEventListener('online', updateNetworkState)
  window.addEventListener('offline', updateNetworkState)
  hydrateReceiptSettings()
  await loadPOSBoot()
  loadWaitersOnce()
  saveActiveTicketSnapshot()
  await nextTick()
  window.scrollTo({ top: 0, behavior: 'auto' })
  headerBarRef.value?.focusCustomerSearch?.()
  pollKitchenReady()
  kitchenPollTimer = setInterval(pollKitchenReady, 45000)
})

onBeforeUnmount(() => {
  saveActiveTicketSnapshot()
  window.removeEventListener('keydown', onWindowKeydown)
  window.removeEventListener('resize', syncViewportMode)
  window.removeEventListener('online', updateNetworkState)
  window.removeEventListener('offline', updateNetworkState)
  if (reminderTimer.value) {
    clearTimeout(reminderTimer.value)
  }
  if (kitchenPollTimer) {
    clearInterval(kitchenPollTimer)
    kitchenPollTimer = null
  }
})
</script>

<style scoped>
.kitchen-ready-toasts {
  position: fixed;
  bottom: 18px;
  inset-inline-start: 18px;
  z-index: 90;
  display: grid;
  gap: 0.5rem;
  max-width: min(360px, 90vw);
}
.kitchen-ready-toast {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  background: #2f6f5c;
  color: #fff;
  border-radius: 14px;
  padding: 0.7rem 1rem;
  font-size: 0.85rem;
  box-shadow: 0 10px 30px rgba(20, 40, 33, 0.35);
  animation: kitchen-toast-in 0.25s ease-out;
}
.kitchen-ready-toast .toast-close {
  background: rgba(255, 255, 255, 0.18);
  border: 0;
  color: #fff;
  border-radius: 8px;
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  cursor: pointer;
  flex-shrink: 0;
}
@keyframes kitchen-toast-in {
  from { transform: translateY(12px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
.pos-theme :deep(.hero-card) {
  border: 1px solid var(--mg-border);
  background: var(--mg-bg-surface);
  box-shadow: none;
}

.pos-theme :deep(.hero-card h2) {
  color: var(--mg-primary);
}

.pos-theme :deep(.hero-card p) {
  color: var(--mg-text-muted);
}


.open-invoice-strip {
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
  padding-bottom: 0.2rem;
}

.open-invoice-card {
  min-width: 170px;
  border: 1px solid var(--mg-border);
  border-radius: 12px;
  background: var(--mg-bg-surface);
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
  color: var(--mg-text-muted);
}

.open-invoice-card.active {
  border-color: var(--mg-primary);
  box-shadow: inset 0 0 0 1px var(--mg-primary);
}

.open-invoice-detail {
  border: 1px dashed var(--mg-border);
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
  color: var(--mg-text-muted);
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
  border: 1px solid var(--mg-border);
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
  border: 1px solid var(--mg-border);
  border-radius: 12px;
  background: var(--mg-bg-surface);
  padding: 0.5rem 0.75rem;
}

.pos-status-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  font-size: 0.82rem;
  color: var(--mg-text-main);
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
  background: var(--mg-success);
  box-shadow: 0 0 0 3px rgb(var(--mg-success-rgb, 11 125 74) / 0.22);
}

.shift-dot.shift-closed {
  background: rgb(var(--mg-primary-rgb, 1 90 114) / 0.35);
}

.pos-status-name {
  font-size: 0.84rem;
  color: var(--mg-primary);
}

.pos-status-sep {
  color: var(--mg-border);
}

.pos-status-shift {
  font-size: 0.78rem;
  color: var(--mg-text-muted);
}

.pos-status-method {
  font-size: 0.76rem;
  color: var(--mg-text-muted);
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  background: var(--mg-bg-page);
}

.pos-info-toggle {
  border: 1px solid var(--mg-border);
  background: transparent;
  color: var(--mg-text-main);
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
  border: 1px solid var(--mg-border);
  background: var(--mg-bg-page);
  color: var(--mg-text-main);
  font-size: 0.85rem;
  text-decoration: none;
}

.pos-info-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1.2rem;
  border: 1px dashed var(--mg-border);
  border-radius: 12px;
  background: var(--mg-bg-page);
  padding: 0.55rem 0.8rem;
}

.pos-info-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
}

.pos-info-label {
  color: var(--mg-text-muted);
  font-size: 0.73rem;
}

.pos-info-item strong {
  color: var(--mg-primary);
  font-size: 0.8rem;
}


.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 0.35rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--mg-primary) 16%, var(--mg-bg-surface) 84%);
  color: var(--mg-primary);
  font-size: 0.7rem;
  font-weight: 700;
  border: 1px solid color-mix(in srgb, var(--mg-primary) 22%, transparent);
}

.count-badge.empty {
  background: var(--mg-bg-surface);
  color: var(--mg-text-main);
}

.occupied-badge {
  font-size: 0.73rem;
  color: var(--mg-danger);
  background: rgb(var(--mg-danger-rgb, 171 53 53) / 0.1);
  border-radius: 999px;
  padding: 0.12rem 0.45rem;
}

.icon-refresh-btn {
  border: 1px solid color-mix(in srgb, var(--mg-border-light) 92%, transparent);
  background: color-mix(in srgb, var(--mg-bg-page) 60%, var(--mg-bg-surface) 40%);
  color: var(--mg-text-main);
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
  color: var(--mg-text-muted);
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
  border: 2px solid var(--mg-border);
  border-radius: 14px;
  background: var(--mg-bg-surface);
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
  color: var(--mg-primary);
  line-height: 1.1;
}

.table-cell-time {
  font-size: 0.65rem;
  color: var(--mg-text-muted);
}

.table-cell-orders {
  font-size: 0.65rem;
  background: var(--mg-primary-soft);
  color: var(--mg-primary, var(--mg-primary));
  border-radius: 999px;
  padding: 0.08rem 0.32rem;
}

.table-cell-empty {
  font-size: 0.65rem;
  color: var(--mg-success);
}

.table-cell.status-empty {
  background: rgb(var(--mg-success-rgb, 11 125 74) / 0.07);
  border-color: rgb(var(--mg-success-rgb, 11 125 74) / 0.3);
}

.table-cell.status-occupied {
  background: rgb(var(--mg-danger-rgb, 171 53 53) / 0.08);
  border-color: rgb(var(--mg-danger-rgb, 171 53 53) / 0.28);
}

.table-cell.status-waiting {
  background: var(--mg-bg-surface);
  border-color: var(--mg-text-muted);
}

.table-cell.active {
  border-color: var(--mg-primary);
  box-shadow: 0 0 0 2px var(--mg-primary);
  transform: translateY(-2px);
}

.table-detail-bar {
  display: grid;
  gap: 0.4rem;
  border: 1px dashed var(--mg-border);
  border-radius: 12px;
  padding: 0.5rem 0.55rem;
  background: var(--mg-bg-page);
}

.table-detail-info {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.35rem 0.55rem;
  font-size: 0.78rem;
  color: var(--mg-text-muted);
}

.table-detail-info strong {
  color: var(--mg-primary);
  font-size: 0.84rem;
  width: 100%;
}

.table-detail-actions {
  display: grid;
  gap: 0.3rem;
}

.table-detail-actions .danger {
  border-color: rgb(var(--mg-danger-rgb, 171 53 53) / 0.3);
  color: var(--mg-danger);
}

.table-move-panel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.5rem;
  align-items: end;
  padding: 0.48rem;
  border: 1px dashed var(--mg-border);
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
	gap: 0.5rem;
	overflow-x: auto;
	padding-bottom: 0.1rem;
	min-width: 0;
	flex: 1 1 auto;
}

.ticket-rail-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  flex: 0 0 auto;
  padding-bottom: 0.2rem;
}

.ticket-tab-group {
	display: inline-flex;
	align-items: center;
	border: 1px solid color-mix(in srgb, var(--mg-border-light) 95%, transparent);
	background: color-mix(in srgb, var(--mg-bg-surface) 72%, var(--mg-bg-page) 28%);
	border-radius: 999px;
	overflow: hidden;
  box-shadow: 0 8px 18px rgb(52 38 31 / 0.05);
}

.ticket-tab {
	border: 0;
	background: transparent;
	color: var(--mg-text-main);
	padding: 0.52rem 0.84rem;
	font-size: 0.8rem;
	font-weight: 700;
	cursor: pointer;
	white-space: nowrap;
}

.ticket-tab-close {
  border: 0;
  border-inline-start: 1px solid color-mix(in srgb, var(--mg-border-light) 95%, transparent);
  background: transparent;
  color: var(--mg-text-muted);
	width: 28px;
	min-height: 32px;
  font-size: 0.95rem;
  line-height: 1;
  cursor: pointer;
}

.ticket-tab-group.active {
  background: var(--mg-primary);
  border-color: var(--mg-primary);
}

.ticket-tab-group.active .ticket-tab,
.ticket-tab-group.active .ticket-tab-close {
  color: var(--mg-bg-surface);
}

.ticket-tab-group.active .ticket-tab-close {
  border-inline-start-color: rgb(255 255 255 / 0.35);
}

.ticket-tab.new {
  background: var(--mg-primary);
  border-color: var(--mg-primary);
  color: var(--mg-bg-surface);
  box-shadow: 0 14px 30px color-mix(in srgb, var(--mg-primary) 18%, transparent);
}

.pos-fullpage {
	display: grid;
	gap: 0.7rem;
	padding: 0.9rem;
	background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--mg-success) 5%, transparent), transparent 22%),
    radial-gradient(circle at top left, color-mix(in srgb, var(--mg-primary) 6%, transparent), transparent 26%),
    var(--mg-bg-page);
	width: 100%;
	height: calc(100vh - 4.5rem);
	box-sizing: border-box;
	overflow: hidden;
}

.pos-inline-error {
  margin: 0 0 0.35rem;
  color: var(--mg-primary);
  font-size: 0.8rem;
}

.pos-inline-success {
  margin: 0 0 0.35rem;
  color: var(--mg-primary);
  font-size: 0.8rem;
}

.pos-shell {
	display: flex;
	flex-direction: column;
	gap: 0.7rem;
	min-height: 520px;
	overflow: hidden;
}

.pos-main-grid {
	display: grid;
	grid-template-columns: minmax(0, 1fr);
	gap: 0.9rem;
	min-height: 0;
	flex: 1;
	overflow: hidden;
}

.cart-desktop-col {
  min-height: 0;
  display: flex;
  overflow: hidden;
}

.cart-desktop-col :deep(.cart-panel) {
  height: 100%;
  width: 100%;
}

.ops-trigger,
.kbd-help-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.48rem;
  min-height: 38px;
  border-radius: 12px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.16s ease;
  box-shadow: none;
  white-space: nowrap;
}

.ops-trigger {
  border: 1px solid var(--mg-primary);
  background: var(--mg-primary);
  color: var(--mg-bg-surface);
  padding: 0.55rem 0.9rem;
  min-width: 112px;
  box-shadow: 0 14px 28px color-mix(in srgb, var(--mg-primary) 18%, transparent);
}

.ops-trigger span {
  font-size: 0.78rem;
  font-weight: 700;
}

.ops-trigger:hover {
  filter: brightness(0.98);
  transform: translateY(-1px);
}

.left-col {
  display: grid;
  grid-template-rows: auto 1fr;
  align-content: start;
  gap: 0.55rem;
  overflow: hidden;
  min-height: 0;
  padding: 0 0.85rem 0.85rem;
}

.left-col-tabs {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid color-mix(in srgb, var(--mg-border-light) 96%, transparent);
  border-bottom: 0;
  background: color-mix(in srgb, var(--mg-bg-page) 88%, var(--mg-bg-surface) 12%);
  border-radius: 18px 18px 0 0;
  overflow: hidden;
  flex-shrink: 0;
  padding: 0.28rem;
  gap: 0.28rem;
}

.left-tab-btn {
  border: 1px solid transparent;
  background: transparent;
  color: var(--mg-text-main);
  padding: 0.55rem 0.4rem;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.79rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  transition: all 0.15s;
  border-radius: 14px 14px 0 0;
}

.left-tab-btn.active {
  color: var(--mg-bg-surface);
  border-color: var(--mg-primary);
  background: var(--mg-primary);
  box-shadow: 0 12px 24px color-mix(in srgb, var(--mg-primary) 16%, transparent);
}

.left-tab-btn.active .count-badge {
  background: rgb(255 255 255 / 0.18);
  border-color: rgb(255 255 255 / 0.22);
  color: var(--mg-bg-surface);
}

.left-tab-btn.active .occupied-badge {
  background: rgb(255 255 255 / 0.18);
  color: var(--mg-bg-surface);
}

.left-tab-btn:hover:not(.active) {
  background: color-mix(in srgb, var(--mg-bg-surface) 60%, var(--mg-bg-page) 40%);
  border-color: color-mix(in srgb, var(--mg-border-light) 95%, transparent);
}

.tab-panel-toolbar {
  display: flex;
  justify-content: flex-end;
  padding: 0.35rem 0.45rem 0;
}

.table-session-preview,
.open-invoices-panel,
.history-panel {
  border: 1px solid color-mix(in srgb, var(--mg-border-light) 96%, transparent);
  border-radius: 0 0 18px 18px;
  padding: 0 0.55rem 0.55rem;
  background: color-mix(in srgb, var(--mg-bg-surface) 96%, var(--mg-bg-surface) 4%);
  display: grid;
  gap: 0.45rem;
  align-content: start;
  overflow-y: auto;
  min-height: 0;
  box-shadow: 0 18px 34px rgb(52 38 31 / 0.06);
}

.waiter-select-box {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.4rem 0.45rem 0.1rem;
}

.waiter-select-label {
  font-size: 0.78rem;
  color: var(--mg-text-muted);
  font-weight: 700;
  white-space: nowrap;
}

.waiter-select {
  flex: 1;
  min-width: 0;
  padding: 0.32rem 0.5rem;
  border-radius: 10px;
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-surface);
  color: var(--mg-text-main);
  font-size: 0.8rem;
}

.recent-orders-panel {
  border: 1px solid color-mix(in srgb, var(--mg-border-light) 96%, transparent);
  border-radius: 0 0 18px 18px;
  padding: 0 0.55rem 0.55rem;
  background: color-mix(in srgb, var(--mg-bg-surface) 96%, var(--mg-bg-surface) 4%);
  display: grid;
  gap: 0.45rem;
  align-content: start;
  overflow-y: auto;
  min-height: 0;
  box-shadow: 0 18px 34px rgb(52 38 31 / 0.06);
}

.history-list {
  display: grid;
  gap: 0.4rem;
}

.history-card {
  border: 1px solid color-mix(in srgb, var(--mg-border-light) 96%, transparent);
  border-radius: 10px;
  padding: 0.45rem 0.55rem;
  display: grid;
  gap: 0.2rem;
  font-size: 0.78rem;
  background: linear-gradient(180deg, var(--mg-bg-surface) 0%, color-mix(in srgb, var(--mg-bg-surface) 92%, var(--mg-bg-surface) 8%) 100%);
}

.history-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-card-head strong {
  font-size: 0.8rem;
  color: var(--mg-primary);
}

.history-time {
  font-size: 0.7rem;
  color: var(--mg-text-muted);
}

.history-card-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-amount {
  font-weight: 600;
  color: var(--mg-success, var(--mg-success));
}

.history-method-badge {
  font-size: 0.7rem;
  background: var(--mg-bg-page);
  border-radius: 6px;
  padding: 0.1rem 0.4rem;
  display: inline-block;
  width: fit-content;
}

.kbd-help-btn {
  border: 1px solid color-mix(in srgb, var(--mg-border-light) 88%, transparent);
  background: color-mix(in srgb, var(--mg-bg-surface) 72%, var(--mg-bg-page) 28%);
  color: var(--mg-text-main);
  padding: 0.55rem 0.9rem;
  min-width: 112px;
}

.kbd-help-btn:hover {
  color: var(--mg-primary);
  background: var(--mg-bg-surface);
}

.kbd-help-btn span {
  font-size: 0.74rem;
  font-weight: 600;
}

.ops-overlay-backdrop {
  position: fixed;
  inset: 0;
  z-index: 260;
  direction: ltr;
  background: rgb(35 26 20 / 0.48);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: stretch;
  justify-content: flex-start;
  padding: 0;
}

.ops-overlay-sheet {
  width: min(780px, 64vw);
  max-width: calc(100vw - 5rem);
  height: 100vh;
  border-radius: 0 26px 26px 0;
  background: linear-gradient(180deg, color-mix(in srgb, var(--mg-bg-surface) 28%, var(--mg-bg-surface) 72%) 0%, var(--mg-bg-surface) 100%);
  border-inline-end: 1px solid color-mix(in srgb, var(--mg-border-light) 96%, transparent);
  box-shadow: 0 32px 70px rgb(22 16 12 / 0.34);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.ops-overlay-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 0.85rem 0.95rem;
  border-bottom: 1px solid color-mix(in srgb, var(--mg-border-light) 96%, transparent);
  background: color-mix(in srgb, var(--mg-bg-page) 78%, var(--mg-bg-surface) 22%);
}

.ops-overlay-kicker {
  margin: 0 0 0.12rem;
  font-size: 0.69rem;
  font-weight: 700;
  color: var(--mg-primary);
}

.ops-overlay-head h3 {
  margin: 0;
  font-size: 0.98rem;
  color: var(--mg-text-main);
}

.ops-overlay-close {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 10px;
  background: color-mix(in srgb, var(--mg-bg-surface) 70%, var(--mg-bg-page) 30%);
  color: var(--mg-text-muted);
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.ops-overlay-close:hover {
  background: var(--mg-bg-surface);
  color: var(--mg-primary);
}

.ops-overlay-enter-active,
.ops-overlay-leave-active {
  transition: opacity 0.22s ease;
}

.ops-overlay-enter-active .ops-overlay-sheet,
.ops-overlay-leave-active .ops-overlay-sheet {
  transition: transform 0.22s ease, opacity 0.22s ease;
}

.ops-overlay-enter-from,
.ops-overlay-leave-to {
  opacity: 0;
}

.ops-overlay-enter-from .ops-overlay-sheet,
.ops-overlay-leave-to .ops-overlay-sheet {
  transform: translateX(-40px);
  opacity: 0;
}

/* ─── Cart FAB ─── */
.cart-fab {
  position: fixed;
  bottom: 1.2rem;
  left: 10.4rem;
  z-index: 200;
  background: var(--mg-primary);
  color: var(--mg-bg-surface);
  border: none;
  border-radius: 50%;
  width: 2.8rem;
  height: 2.8rem;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px color-mix(in srgb, var(--mg-primary) 35%, transparent);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.cart-fab:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px color-mix(in srgb, var(--mg-primary) 45%, transparent);
}

.cart-fab.has-items {
  animation: cart-pulse 0.3s ease;
}

.cart-fab-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  border-radius: 999px;
  background: var(--mg-danger);
  color: var(--mg-bg-surface);
  font-size: 0.62rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  box-shadow: 0 1px 4px rgb(0 0 0 / 0.2);
}

@keyframes cart-pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.12); }
  100% { transform: scale(1); }
}

/* ─── Cart Drawer ─── */
.cart-drawer-backdrop {
  position: fixed;
  inset: 0;
  z-index: 250;
  background: rgb(0 0 0 / 0.35);
  backdrop-filter: blur(3px);
}

.cart-drawer {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: min(420px, 90vw);
  z-index: 251;
  background: var(--mg-bg-surface, var(--mg-bg-surface));
  box-shadow: 4px 0 24px rgb(0 0 0 / 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.cart-drawer > * {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.cart-drawer-enter-active,
.cart-drawer-leave-active {
  transition: all 0.25s ease;
}

.cart-drawer-enter-active .cart-drawer,
.cart-drawer-leave-active .cart-drawer {
  transition: transform 0.25s ease;
}

.cart-drawer-enter-from,
.cart-drawer-leave-to {
  background: rgb(0 0 0 / 0);
  backdrop-filter: blur(0);
}

.cart-drawer-enter-from .cart-drawer {
  transform: translateX(-100%);
}

.cart-drawer-leave-to .cart-drawer {
  transform: translateX(-100%);
}

.kbd-map-backdrop {
  position: fixed;
  inset: 0;
  background: rgb(0 0 0 / 0.45);
  z-index: 9000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.kbd-map-modal {
  background: var(--mg-bg-surface);
  border-radius: 18px;
  padding: 1.4rem;
  min-width: 340px;
  max-width: 92vw;
  box-shadow: 0 8px 40px rgb(0 0 0 / 0.22);
  display: grid;
  gap: 1rem;
}

.kbd-map-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kbd-map-head h3 {
  margin: 0;
  font-size: 1rem;
  color: var(--mg-primary);
}

.kbd-map-close {
  background: transparent;
  border: none;
  font-size: 1.4rem;
  cursor: pointer;
  color: var(--mg-text-main);
  line-height: 1;
  padding: 0 0.3rem;
}

.kbd-map-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.kbd-map-table td {
  padding: 0.4rem 0.5rem;
  border-bottom: 1px solid var(--mg-border);
  color: var(--mg-text-main);
}

.kbd-map-table td:first-child {
  text-align: center;
  width: 30%;
}

.kbd-map-table tr:last-child td {
  border-bottom: none;
}

kbd {
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border);
  border-radius: 5px;
  padding: 0.1rem 0.45rem;
  font-family: monospace;
  font-size: 0.82rem;
  color: var(--mg-primary);
}

.kbd-map-note {
  font-size: 0.74rem;
  color: var(--mg-text-muted);
  margin: 0;
  text-align: center;
}

.products-col {
  min-height: 0;
  overflow: hidden;
}

.tbl-btn {
  border: 1px solid var(--mg-border);
  border-radius: 9px;
  background: var(--mg-bg-surface);
  color: var(--mg-primary);
  padding: 0.3rem 0.55rem;
  font-size: 0.76rem;
  cursor: pointer;
  font-family: inherit;
  white-space: nowrap;
}

.tbl-btn.primary {
  background: var(--mg-primary);
  color: var(--mg-bg-surface);
  border-color: var(--mg-primary);
}

.tbl-btn.danger {
  border-color: rgb(var(--mg-danger-rgb, 171 53 53) / 0.3);
  color: var(--mg-danger);
}

.tbl-btn.split {
  background: var(--mg-bg-surface);
  border-color: var(--mg-border-light);
  color: var(--mg-primary, var(--mg-primary));
  width: 100%;
}

.tbl-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.tbl-action-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.3rem;
  align-items: center;
  width: 100%;
}

.offline-banner,
.sync-banner,
.error,
.success {
  margin: 0;
  border-radius: 12px;
  padding: 0.5rem 0.62rem;
  font-size: 0.8rem;
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border);
  color: var(--mg-text-main);
}

.offline-banner {
  background: var(--mg-primary-soft);
  border-color: var(--mg-border-light);
}

.sync-banner {
  background: var(--mg-bg-page);
}

.error {
  background: rgb(var(--mg-danger-rgb, 171 53 53) / 0.12);
  border-color: rgb(var(--mg-danger-rgb, 171 53 53) / 0.35);
  color: var(--mg-danger);
}

.success {
  background: rgb(var(--mg-success-rgb, 11 125 74) / 0.1);
  border-color: rgb(var(--mg-success-rgb, 11 125 74) / 0.34);
  color: var(--mg-success);
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
  background: var(--mg-bg-surface);
  border-radius: 18px;
  border: 1px solid var(--mg-border);
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
  border-bottom: 1px solid var(--mg-border);
}

.print-editor-head h3 {
  margin: 0;
  font-size: 0.95rem;
  color: var(--mg-primary);
}

.print-editor-head p {
  margin: 0.2rem 0 0;
  font-size: 0.76rem;
  color: var(--mg-text-muted);
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
  color: var(--mg-text-muted);
}

.print-editor-grid {
  display: grid;
  grid-template-columns: minmax(260px, 320px) minmax(0, 1fr);
  gap: 0.7rem;
  padding: 0.8rem;
  min-height: 0;
}

.print-editor-cart {
  border: 1px solid var(--mg-border);
  border-radius: 14px;
  background: var(--mg-bg-page);
  padding: 0.6rem;
  display: grid;
  gap: 0.5rem;
  min-height: 0;
}

.print-editor-cart h4 {
  margin: 0;
  font-size: 0.82rem;
  color: var(--mg-primary);
}

.print-editor-list {
  display: grid;
  gap: 0.4rem;
  overflow: auto;
  padding-inline-end: 0.2rem;
}

.print-editor-row {
  border: 1px solid var(--mg-border);
  border-radius: 12px;
  padding: 0.5rem;
  background: var(--mg-bg-surface);
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
  color: var(--mg-text-muted);
}

.print-editor-row-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.print-editor-row-actions button {
  border: 1px solid var(--mg-border);
  border-radius: 8px;
  background: var(--mg-bg-surface);
  color: var(--mg-primary);
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
  color: var(--mg-danger);
  border-color: rgb(var(--mg-danger-rgb, 171 53 53) / 0.25);
}

.print-editor-preview {
  border: 1px solid var(--mg-border);
  border-radius: 14px;
  padding: 0.7rem;
  overflow: auto;
  background: var(--mg-bg-page);
}

.receipt-preview-host {
  min-height: 100%;
}

@media (min-width: 1180px) {
  .pos-main-grid {
    grid-template-columns: minmax(0, 1fr) 360px;
  }
}

@media (max-width: 1040px) {
  .pos-shell {
    height: auto;
    overflow: visible;
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
  .pos-fullpage {
    padding: 0.45rem;
    height: auto;
    overflow: visible;
    min-height: 100vh;
  }

  .pos-shell {
    height: auto;
    overflow: visible;
    gap: 0.4rem;
  }

  .products-col {
    overflow: visible;
    min-height: 300px;
  }

  .ops-overlay-backdrop {
    padding: 0.35rem;
  }

  .ops-overlay-sheet {
    width: 100%;
    height: calc(100vh - 0.7rem);
    border-radius: 16px;
  }

  .ops-trigger,
  .kbd-help-btn {
    min-width: 104px;
    padding: 0.5rem 0.7rem;
  }

  .cart-fab {
    left: 1rem;
    bottom: calc(5.5rem + env(safe-area-inset-bottom));
  }

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

  .ticket-tabs-bar {
    padding: 0.3rem 0.4rem 0;
  }

  .recent-orders-filter {
    grid-template-columns: 1fr;
  }
}

/* Ticket Tabs Bar */
.ticket-tabs-bar {
  background: linear-gradient(180deg, color-mix(in srgb, var(--mg-bg-surface) 62%, var(--mg-bg-surface) 38%) 0%, color-mix(in srgb, var(--mg-bg-surface) 96%, var(--mg-bg-surface) 4%) 100%);
  border: 1px solid color-mix(in srgb, var(--mg-border-light) 96%, transparent);
  border-radius: 24px;
  padding: 0.7rem 0.85rem;
  direction: rtl;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.85rem;
  min-width: 0;
  flex-wrap: wrap;
  box-shadow: 0 20px 38px rgb(52 38 31 / 0.08);
}

/* Recent orders panel */
.recent-orders-panel {
  padding: 0.5rem 0;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
  scrollbar-width: thin;
}

.recent-orders-filter {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.5rem;
  padding: 0.4rem 0.75rem 0.6rem;
}

.recent-search-input,
.recent-date-input {
  font-size: 0.78rem;
  padding: 0.3rem 0.55rem;
  border-radius: 8px;
  border: 1px solid var(--mg-border);
  background: var(--mg-bg-surface);
  color: var(--mg-text-main);
}

/* Interactive history card */
.history-card-interactive {
  cursor: pointer;
  transition: background 0.12s, box-shadow 0.12s;
}

.history-card-interactive:hover {
  background: var(--mg-bg-surface);
  box-shadow: 0 16px 30px rgb(52 38 31 / 0.1);
}

.history-card-footer {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.25rem;
  flex-wrap: wrap;
}

.order-status-badge {
  display: inline-block;
  padding: 0.12rem 0.45rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  background: var(--mg-border);
  color: var(--mg-text-main);
}

.order-status-badge.status-paid,
.order-status-badge.status-completed,
.order-status-badge.status-delivered {
  background: var(--mg-success-bg);
  color: var(--mg-success);
}

.order-status-badge.status-pending,
.order-status-badge.status-new {
  background: var(--mg-bg-soft);
  color: var(--mg-primary);
}

.order-status-badge.status-cancelled,
.order-status-badge.status-canceled {
  background: var(--mg-danger-bg);
  color: var(--mg-danger);
}

/* Modals */
.pos-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 3000;
  background: rgb(0 0 0 / 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.pos-modal {
  background: var(--mg-bg-surface, var(--mg-bg-surface));
  border-radius: 18px;
  width: 100%;
  max-width: 520px;
  max-height: 90vh;
  overflow-y: auto;
  padding: 0 0 1rem;
  box-shadow: 0 8px 40px 0 rgb(0 0 0 / 0.35);
  display: flex;
  flex-direction: column;
}

.pos-modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 1rem 1.2rem 0.75rem;
  border-bottom: 1px solid var(--mg-border);
  gap: 0.5rem;
}

.pos-modal-head h3 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
}

.pos-modal-head small {
  color: var(--mg-text-muted, var(--mg-text-muted));
  font-size: 0.8rem;
}

.pos-modal-close {
  background: transparent;
  border: 0;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: var(--mg-text-muted, var(--mg-text-muted));
  padding: 0 0.25rem;
  margin-top: -0.2rem;
}

.pos-modal-close:hover {
  color: var(--mg-text-main, var(--mg-text-main));
}

.pos-modal-بارگذاری {
  padding: 1.5rem 1.2rem;
  text-align: center;
}

.pos-modal-err {
  padding: 0.4rem 1.2rem;
  font-size: 0.85rem;
}

.pos-modal-actions {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.6rem;
  padding: 0.8rem 1.2rem 0;
  flex-wrap: wrap;
}

.order-detail-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.2rem 0;
  font-size: 0.84rem;
}

.order-detail-items {
  list-style: none;
  margin: 0.6rem 0 0;
  padding: 0 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  max-height: 200px;
  overflow-y: auto;
}

.order-detail-items li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.83rem;
  padding: 0.3rem 0.6rem;
  background: var(--mg-bg-surface));
  border-radius: 8px;
  gap: 0.5rem;
}

.order-detail-edit-form {
  padding: 0.75rem 1.2rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.order-detail-edit-form h4 {
  margin: 0 0 0.25rem;
  font-size: 0.9rem;
  color: var(--mg-text-muted, var(--mg-text-muted));
}

.order-detail-edit-form label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.82rem;
}

.order-detail-edit-form .input {
  font-size: 0.85rem;
  padding: 0.4rem 0.65rem;
  border-radius: 8px;
  border: 1px solid var(--mg-border);
}

.return-modal-body {
  padding: 0.9rem 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  font-size: 0.88rem;
}

.return-modal-body label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.return-modal-body .input {
  font-size: 0.85rem;
  padding: 0.4rem 0.65rem;
  border-radius: 8px;
  border: 1px solid var(--mg-border);
}

.tbl-btn.danger {
  background: var(--mg-danger);
  color: var(--mg-bg-surface);
  border-color: var(--mg-danger);
}

.tbl-btn.danger:hover {
  background: var(--mg-danger);
  border-color: var(--mg-danger);
}

.order-تسویه-section {
  margin-top: 16px;
  padding: 16px;
  background: var(--mg-success-bg);
  border: 1px solid var(--mg-success-bg);
  border-radius: 8px;
}
.order-تسویه-section h4 {
  margin: 0 0 12px;
  font-size: 15px;
  color: var(--mg-success);
}
.تسویه-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.تسویه-label {
  font-size: 13px;
  color: var(--mg-text-main);
  min-width: 100px;
}
.تسویه-select, .تسویه-input {
  flex: 1;
  max-width: 250px;
}
.تسویه-amount {
  font-size: 16px;
  font-weight: 700;
  color: var(--mg-success);
}
.تسویه-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}
.settle-btn:disabled {
  background: var(--mg-success-bg);
  cursor: not-allowed;
}
.tbl-btn.success {
  background: var(--mg-success);
  color: var(--mg-bg-surface);
  border: 1px solid var(--mg-success);
}
.tbl-btn.success:hover:not(:disabled) {
  background: var(--mg-success);
}
.deliver-acc-btn {
  background: var(--mg-primary);
  color: var(--mg-bg-surface);
  border: 1px solid var(--mg-primary);
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  white-space: nowrap;
  transition: all 0.15s;
}
.deliver-acc-btn:hover:not(:disabled) {
  background: var(--mg-primary);
}
.settle-order-btn {
  margin-right: auto;
  padding: 4px 10px;
  background: var(--mg-success-bg);
  color: var(--mg-success);
  border: 1px solid var(--mg-success-bg);
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}
.settle-order-btn:hover {
  background: var(--mg-success-bg);
}


.open-invoice-accordion {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
}
.accordion-card {
  border: 1px solid var(--mg-border-light);
  border-radius: 8px;
  overflow: hidden;
  background: var(--mg-bg-surface);
  transition: box-shadow 0.15s;
}
.accordion-card.expanded {
  border-color: var(--mg-primary);
  box-shadow: 0 10px 22px color-mix(in srgb, var(--mg-primary) 16%, transparent);
}
.accordion-header {
  display: flex;
  align-items: center;
  gap: 6px;
  gap: 6px;
  padding: 10px 12px;
  cursor: pointer;
  align-items: center;
  user-select: none;
}
.accordion-header strong {
  font-size: 13px;
  color: var(--mg-text-main);
}
.accordion-customer {
  font-size: 11px;
  color: var(--mg-text-muted);
}
.accordion-amount {
  font-size: 12px;
  font-weight: 700;
  color: var(--mg-text-main);
  direction: ltr;
  text-align: left;
}
.accordion-time {
  font-size: 10px;
  color: var(--mg-text-muted);
}
.accordion-chevron {
  font-size: 10px;
  color: var(--mg-text-muted);
  text-align: center;
}
.accordion-body {
  border-top: 1px solid var(--mg-border-light);
  padding: 8px 12px;
}
.accordion-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.accordion-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  font-size: 12px;
}
.accordion-item-title {
  flex: 1;
  color: var(--mg-text-main);
}
.accordion-item-qty {
  color: var(--mg-text-muted);
  min-width: 30px;
  text-align: center;
}
.accordion-item-total {
  font-weight: 600;
  color: var(--mg-text-main);
  direction: ltr;
}
.accordion-footer {
  display: flex;
  gap: 6px;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--mg-bg-page);
}
.accordion-بارگذاری {
  padding: 8px 12px;
  text-align: center;
  color: var(--mg-text-muted);
}


.deliver-order-btn {
  margin-right: auto;
  padding: 4px 10px;
  background: var(--mg-bg-soft);
  color: var(--mg-primary);
  border: 1px solid var(--mg-bg-soft);
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}
.deliver-order-btn:hover {
  background: var(--mg-bg-soft);
}


/* ─── Redesigned Order Detail Modal ─── */
.od-modal-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgb(25 20 14 / 0.42); display: flex;
  align-items: center; justify-content: center;
  padding: 1rem;
}
.od-modal {
  background: var(--mg-bg-surface, var(--mg-bg-surface)); color: var(--mg-text-main, var(--mg-text-main));
  border-radius: 16px; width: 100%; max-width: 480px;
  max-height: 90vh; overflow-y: auto;
  box-shadow: 0 22px 48px rgb(52 38 31 / 0.16);
  direction: rtl;
}
.od-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: 1rem 1.25rem 0.5rem; gap: 1rem;
}
.od-header-info { display: flex; flex-direction: column; gap: 0.25rem; }
.od-header-info h3 { margin: 0; font-size: 1rem; font-weight: 700; }
.od-badge {
  display: inline-flex; align-items: center;
  font-size: 0.65rem; font-weight: 700; padding: 0.1rem 0.5rem;
  border-radius: 20px; width: fit-content;
}
.od-badge-pending { background: var(--mg-bg-soft); color: var(--mg-primary); }
.od-badge-confirmed { background: var(--mg-bg-soft); color: var(--mg-primary); }
.od-badge-preparing { background: var(--mg-bg-soft); color: var(--mg-primary); }
.od-badge-ready { background: var(--mg-success-bg); color: var(--mg-success); }
.od-badge-paid { background: var(--mg-success-bg); color: var(--mg-success); }
.od-badge-delivered { background: var(--mg-success-bg); color: var(--mg-success); }
.od-badge-cancelled { background: var(--mg-danger-bg); color: var(--mg-danger); }
.od-time { font-size: 0.72rem; color: var(--mg-text-muted, var(--mg-text-muted)); }
.od-close { background: none; border: none; font-size: 1.1rem; cursor: pointer; color: var(--mg-text-muted, var(--mg-text-muted)); padding: 0.25rem; line-height: 1; }
.od-بارگذاری, .od-error { padding: 1.25rem; text-align: center; color: var(--mg-text-muted, var(--mg-text-muted)); }
.od-error { color: var(--mg-danger); }

.od-summary { margin: 0.5rem 1.25rem; }
.od-summary-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; }
.od-summary-item { display: flex; flex-direction: column; gap: 0.15rem; }
.od-label { font-size: 0.65rem; color: var(--mg-text-muted, var(--mg-text-muted)); }
.od-value { font-size: 0.82rem; font-weight: 600; color: var(--mg-text-main, var(--mg-text-main)); }
.od-value.muted { color: var(--mg-text-muted, var(--mg-text-muted)); }
.od-price { direction: ltr; text-align: left; }

.od-items { margin: 0.75rem 1.25rem; }
.od-items-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; font-size: 0.78rem; font-weight: 600; color: var(--mg-text-muted, var(--mg-text-muted)); }
.od-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.35rem 0; border-bottom: 1px solid color-mix(in srgb, var(--mg-border-light) 82%, transparent);
}
.od-item:last-child { border-bottom: none; }
.od-item-info { display: flex; align-items: center; gap: 0.4rem; }
.od-item-name { font-size: 0.82rem; }
.od-item-qty { font-size: 0.68rem; color: var(--mg-text-muted, var(--mg-text-muted)); }
.od-item-price { font-size: 0.78rem; font-weight: 600; direction: ltr; }

.od-note { margin: 0 1.25rem 0.75rem; padding: 0.5rem; background: color-mix(in srgb, var(--mg-bg-page) 72%, var(--mg-bg-surface) 28%); border-radius: 8px; }
.od-note p { margin: 0.2rem 0 0; font-size: 0.78rem; }

.od-actions { padding: 0.75rem 1.25rem 1rem; display: flex; flex-direction: column; gap: 0.5rem; }
.od-settle { background: var(--mg-success-bg); border: 1px solid var(--mg-success-bg); border-radius: 10px; padding: 0.75rem; }
.od-settle-row { display: flex; gap: 0.4rem; flex-wrap: wrap; }
.od-select, .od-input, .od-textarea {
  background: var(--mg-bg-surface, var(--mg-bg-surface)); border: 1px solid var(--mg-text-muted);
  border-radius: 6px; padding: 0.4rem 0.6rem; font-size: 0.78rem;
  font-family: inherit; color: var(--mg-text-main, var(--mg-text-main)); outline: none;
  flex: 1; min-width: 100px;
}
.od-input::placeholder, .od-textarea::placeholder { color: var(--mg-text-muted); }
.od-textarea { resize: vertical; }
.od-err { font-size: 0.72rem; color: var(--mg-danger); margin: 0.3rem 0; }
.od-btn {
  background: var(--mg-bg-page, var(--mg-bg-page)); border: 1px solid var(--mg-text-muted);
  color: var(--mg-text-main, var(--mg-text-main)); border-radius: 8px; padding: 0.5rem 1rem;
  font-size: 0.8rem; font-weight: 600; cursor: pointer; font-family: inherit;
  transition: all 0.15s;
}
.od-btn-primary { background: var(--mg-success); color: var(--mg-bg-surface); border-color: var(--mg-success); }
.od-btn-primary:hover { background: var(--mg-success); }
.od-btn-primary:disabled { background: var(--mg-success-bg); cursor: not-allowed; }
.od-btn-danger { background: var(--mg-danger-bg); color: var(--mg-danger); border-color: var(--mg-danger-bg); }
.od-btn-danger:hover { background: var(--mg-danger-bg); }
.od-edit-toggle {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.4rem 0.5rem; cursor: pointer; border-radius: 6px;
  font-size: 0.78rem; color: var(--mg-text-muted, var(--mg-text-muted));
}
.od-edit-toggle:hover { background: color-mix(in srgb, var(--mg-bg-page) 72%, var(--mg-bg-surface) 28%); }
.od-chevron { transition: transform 0.2s; font-size: 0.6rem; }
.od-chevron.open { transform: rotate(180deg); }
.od-edit { display: flex; flex-direction: column; gap: 0.4rem; padding: 0.5rem; background: color-mix(in srgb, var(--mg-bg-page) 64%, var(--mg-bg-surface) 36%); border-radius: 8px; }
.od-bottom { display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 0.25rem; }

@media (max-width: 500px) {
  .od-summary-row { grid-template-columns: 1fr 1fr; }
  .od-modal { max-width: 100%; margin: 0.5rem; border-radius: 12px; }
}


.print-icon-btn {
  background: none; border: none; cursor: pointer;
  font-size: 0.85rem; padding: 2px 6px; border-radius: 4px;
  opacity: 0.5; transition: all 0.15s; line-height: 1;
  margin-right: auto;
}
.print-icon-btn:hover { opacity: 1; background: color-mix(in srgb, var(--mg-bg-page) 72%, var(--mg-bg-surface) 28%); }


/* ─── Modern Table Cards ─── */
.tables-stats { display: flex; gap: 0.5rem; margin-right: auto; font-size: 0.75rem; color: var(--mg-text-muted, var(--mg-text-muted)); }
.ts-item { display: flex; align-items: center; gap: 0.3rem; }
.ts-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.ts-dot.free { background: var(--mg-success); }
.ts-dot.occ { background: var(--mg-primary); }

.table-modern-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 0.5rem; padding: 0.5rem; }
.table-modern-card {
  background: linear-gradient(180deg, var(--mg-bg-surface) 0%, color-mix(in srgb, var(--mg-bg-surface) 92%, var(--mg-bg-surface) 8%) 100%);
  border: 1px solid color-mix(in srgb, var(--mg-border-light) 96%, transparent);
  border-radius: 16px; padding: 0.6rem; cursor: pointer;
  transition: all 0.15s; display: flex; flex-direction: column; gap: 0.25rem;
  box-shadow: 0 12px 24px rgb(52 38 31 / 0.05);
}
.table-modern-card:hover { transform: translateY(-2px); box-shadow: 0 14px 28px rgb(52 38 31 / 0.1); }
.table-modern-card.active { border-color: var(--mg-primary); box-shadow: 0 0 0 2px color-mix(in srgb, var(--mg-primary) 18%, transparent), 0 16px 32px color-mix(in srgb, var(--mg-primary) 12%, transparent); }
.tm-empty { border-color: color-mix(in srgb, var(--mg-success) 26%, var(--mg-border-light) 74%); }
.tm-occupied { border-color: color-mix(in srgb, var(--mg-primary) 34%, var(--mg-border-light) 66%); background: color-mix(in srgb, var(--mg-primary) 8%, var(--mg-bg-surface) 92%); }
.tm-occupied .tm-name { color: var(--mg-primary); }
:global(.dark) .tm-occupied { background: color-mix(in srgb, var(--mg-bg-surface) 84%, var(--mg-primary) 16%); }
.tm-top { display: flex; align-items: center; justify-content: space-between; gap: 0.3rem; }
.tm-name { font-size: 0.85rem; font-weight: 700; color: var(--mg-text-main); }
.tm-status-badge { font-size: 0.6rem; padding: 0.1rem 0.4rem; border-radius: 10px; font-weight: 600; white-space: nowrap; }
.tms-empty { background: var(--mg-success-bg); color: var(--mg-success); }
.tms-occupied { background: var(--mg-bg-soft); color: var(--mg-primary); }
.tm-body { display: flex; flex-direction: column; gap: 0.15rem; }
.tm-meta { display: flex; align-items: center; gap: 0.25rem; font-size: 0.68rem; color: var(--mg-text-muted, var(--mg-text-muted)); direction: ltr; }

.table-detail-modern { padding: 0.65rem; display: flex; flex-direction: column; gap: 0.65rem; }
.tdm-head { display: flex; flex-direction: column; gap: 0.35rem; }
.tdm-brand { display: flex; align-items: center; justify-content: space-between; }
.tdm-brand strong { font-size: 1rem; color: var(--mg-text-main); }
.tdm-total { font-size: 1.1rem; font-weight: 800; color: var(--mg-primary); direction: ltr; }
.tdm-meta { display: flex; gap: 0.75rem; font-size: 0.75rem; color: var(--mg-text-muted, var(--mg-text-muted)); }
.tdm-meta span { display: flex; align-items: center; gap: 0.25rem; }
.tdm-actions { display: flex; gap: 0.4rem; }
.tdm-adv-actions { display: flex; flex-direction: column; gap: 0.4rem; }
.tdm-row { display: flex; gap: 0.4rem; }
.tdm-row :deep(.search-dropdown) { flex: 1; min-width: 0; }
.tdm-btn {
  flex: 1; padding: 0.4rem 0.65rem; border: 1px solid var(--mg-border);
  border-radius: 6px; background: var(--mg-bg-surface); color: var(--mg-text-main);
  font-size: 0.75rem; font-weight: 600; cursor: pointer; font-family: inherit;
  transition: all 0.15s; white-space: nowrap;
}
.tdm-btn:hover { background: var(--mg-bg-page); }
.tdm-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.tdm-primary { background: var(--mg-primary); color: var(--mg-bg-surface); border-color: var(--mg-primary); }
.tdm-danger { color: var(--mg-danger); border-color: var(--mg-danger-bg); background: var(--mg-danger-bg); }
.tdm-split { background: var(--mg-text-main); color: var(--mg-bg-surface); border-color: var(--mg-text-main); }

@media (max-width: 768px) {
  .table-modern-grid { grid-template-columns: repeat(auto-fill, minmax(90px, 1fr)); }
}


.tdm-orders-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.5rem;
  border-top: 1px dashed var(--mg-border-light);
  padding-top: 0.75rem;
}

.tdm-section-title {
  font-size: 0.75rem;
  color: var(--mg-text-muted);
}

.tdm-order-card {
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: 8px;
  padding: 0.6rem;
  cursor: pointer;
  transition: all 0.15s ease;
  display: grid;
  gap: 0.4rem;
}

.tdm-order-card:hover {
  background: var(--mg-bg-page);
  border-color: var(--mg-primary);
}

.tdm-order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--mg-text-main);
}

.tdm-order-meta {
  display: flex;
  gap: 0.4rem;
  align-items: center;
}

.tdm-order-items-preview {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  font-size: 0.75rem;
  border-top: 1px dashed var(--mg-border-light);
  padding-top: 0.4rem;
  margin-top: 0.1rem;
}

.tdm-order-item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tdm-item-title {
  color: var(--mg-text-main);
}

.tdm-item-price {
  font-size: 0.7rem;
}


/* Fix overlapping of mobile header and dfm components on the side drawer */
.cart-drawer-backdrop {
  z-index: 10002 !important;
}
.cart-drawer {
  z-index: 10003 !important;
}

</style>
