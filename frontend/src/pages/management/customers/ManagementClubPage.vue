<template>
  <ManagementPageScaffold title="باشگاه مشتریان" subtitle="اعضا و کد اشتراک، پیامک، کیف پول، معرف‌ها و کمپین‌های وفاداری">
    <template #actions>
      <button type="button" class="secondary-btn" @click="loadBoot" :disabled="bootLoading">
        {{ bootLoading ? 'در حال بروزرسانی...' : 'بروزرسانی' }}
      </button>
    </template>

    <div v-if="boot" class="totals-grid boot-kpis">
      <div class="total-box"><small>کل مشتریان</small><strong>{{ formatQty(boot.kpis.customers_total) }}</strong></div>
      <div class="total-box"><small>دارای کد اشتراک</small><strong>{{ formatQty(boot.kpis.members_with_code) }}</strong></div>
      <div class="total-box"><small>کیف‌های پول</small><strong>{{ formatQty(boot.kpis.wallets_count) }}</strong></div>
      <div class="total-box"><small>موجودی کل کیف‌ها</small><strong>{{ formatMoneyValue(boot.kpis.wallet_balance_total) }}</strong></div>
      <div class="total-box"><small>پیامک ۳۰ روز</small><strong>{{ formatQty(boot.kpis.sms_sent_30d) }}<small v-if="boot.kpis.sms_failed_30d" class="warn-text"> ({{ formatQty(boot.kpis.sms_failed_30d) }} ناموفق)</small></strong></div>
      <div class="total-box"><small>کمپین فعال</small><strong>{{ formatQty(boot.kpis.active_campaigns) }}</strong></div>
      <div class="total-box"><small>میانگین نظرسنجی ۳۰ روز</small><strong :class="boot.kpis.survey_avg_30d && boot.kpis.survey_avg_30d <= 3 ? 'warn-text' : 'ok-text'">{{ boot.kpis.survey_avg_30d ? boot.kpis.survey_avg_30d + ' / ۵' : '—' }}</strong></div>
    </div>

    <nav class="tabs-bar">
      <button v-for="tab in tabs" :key="tab.key" type="button" :class="['tab-btn', { active: activeTab === tab.key }]" @click="setActiveTab(tab.key)">
        {{ tab.label }}
      </button>
    </nav>

    <!-- ======================= مشتریان ======================= -->
    <section v-if="activeTab === 'customers'" class="tab-body">
      <ManagementSurfaceCard title="مشتریان باشگاه" subtitle="کد اشتراک، سطح (VIP/عمده‌فروش/عادی/جدید) و سگمنت رفتاری هر مشتری">
        <div class="toolbar">
          <input class="input" v-model.trim="customerFilters.search" placeholder="جستجوی نام یا موبایل..." @keyup.enter="loadCustomers" />
          <select class="input" v-model="customerFilters.tier" @change="loadCustomers">
            <option value="">همه سطوح</option>
            <option v-for="t in tiers" :key="t" :value="t">{{ t }}</option>
          </select>
          <select class="input" v-model="customerFilters.segment" @change="loadCustomers">
            <option value="">همه سگمنت‌ها</option>
            <option v-for="s in segments" :key="s" :value="s">{{ s }}</option>
          </select>
          <select class="input" v-model="customerFilters.kind" @change="loadCustomers">
            <option value="">همه انواع</option>
            <option v-for="k in customerKinds" :key="k" :value="k">{{ k }}</option>
          </select>
          <button type="button" class="secondary-btn" @click="loadCustomers" :disabled="customersLoading">{{ customersLoading ? '...' : 'جستجو' }}</button>
        </div>
        <div class="btn-row">
          <button type="button" class="primary-btn" @click="openCustomerForm()">مشتری جدید</button>
          <button type="button" class="secondary-btn" @click="exportCustomersExcel" :disabled="excelBusy">{{ excelBusy && excelMode === 'export' ? '...' : 'خروجی اکسل' }}</button>
          <button type="button" class="secondary-btn" @click="triggerCustomerExcelImport" :disabled="excelBusy">{{ excelBusy && excelMode === 'import' ? '...' : 'ورود از اکسل' }}</button>
          <button type="button" class="tertiary-btn" @click="assignCodes" :disabled="codesBusy">{{ codesBusy ? '...' : 'تخصیص کد اشتراک به همه' }}</button>
          <button type="button" class="tertiary-btn" @click="computeSegments" :disabled="segmentsBusy">{{ segmentsBusy ? '...' : 'محاسبه خودکار سگمنت‌ها' }}</button>
          <input ref="customerExcelInput" type="file" accept=".xlsx,.xls,.csv" class="visually-hidden" @change="handleCustomerExcelFile" />
        </div>
        <p class="muted" v-if="customersLoading">در حال دریافت مشتریان...</p>
        <p class="error" v-if="customersError">{{ customersError }}</p>
        <p class="success-msg" v-if="customersMessage">{{ customersMessage }}</p>
        <ManagementListView
          v-if="!customersLoading"
          :columns="clubCustomerColumns"
          :rows="customers"
          row-key="name"
          :row-clickable="false"
        >
          <template #cell-customer_name="{ row }">
            <strong>{{ row.customer_name || 'بدون نام' }}</strong>
            <small class="muted d-block">{{ row.mobile || '—' }}<template v-if="row.organization"> · سازمان: {{ row.organization }}</template></small>
          </template>
          <template #cell-kind="{ row }"><span class="pill" :class="{ ok: row.kind === 'سازمانی' }">{{ row.kind || 'حقیقی' }}</span></template>
          <template #cell-membership_code="{ value }"><span class="pill">{{ value || '—' }}</span></template>
          <template #cell-tier="{ row }"><span class="pill" :class="{ ok: row.tier === 'VIP' }">{{ row.tier || '—' }}</span><small v-if="row.loyalty_tier" class="muted d-block">{{ row.loyalty_tier }}</small></template>
          <template #cell-segment="{ value }">{{ value || '—' }}</template>
          <template #cell-points_balance="{ value }"><span :class="{ 'ok-text': Number(value || 0) > 0 }">{{ formatQty(value) }}</span></template>
          <template #cell-orders="{ value }">{{ formatQty(value) }}</template>
          <template #cell-total_spent="{ value }">{{ formatMoneyValue(value) }}</template>
          <template #cell-wallet_balance="{ value }">{{ formatMoneyValue(value) }}</template>
          <template #cell-referral_code="{ row }"><small class="muted">{{ row.referral_code || '—' }}</small><small v-if="row.referred_by" class="muted d-block">معرف: {{ row.referred_by }}</small></template>
          <template #cell-actions="{ row }"><button type="button" class="tertiary-btn" @click="openCustomerForm(row)">ویرایش</button></template>
          <template #empty>مشتری‌ای یافت نشد.</template>
        </ManagementListView>
        <p v-else class="muted">در حال دریافت مشتریان...</p>
      </ManagementSurfaceCard>

      <div v-if="customerForm" class="popup-backdrop" @click.self="customerForm = null">
        <div class="popup">
          <h3>{{ customerForm.name ? 'ویرایش مشتری' : 'مشتری جدید' }}</h3>
          <div class="form-grid">
            <label>نام مشتری <span class="req">*</span><input class="input" v-model.trim="customerForm.customer_name" /></label>
            <label>موبایل<input class="input" v-model.trim="customerForm.mobile" inputmode="tel" /></label>
            <label>تاریخ تولد<input class="input" type="date" v-model="customerForm.birth_date" /></label>
            <label>سطح
              <select class="input" v-model="customerForm.tier">
                <option v-for="t in tiers" :key="t" :value="t">{{ t }}</option>
              </select>
            </label>
            <label>سگمنت
              <select class="input" v-model="customerForm.segment">
                <option value="">—</option>
                <option v-for="s in segments" :key="s" :value="s">{{ s }}</option>
              </select>
            </label>
            <label>نوع مشتری
              <select class="input" v-model="customerForm.kind">
                <option v-for="k in customerKinds" :key="k" :value="k">{{ k }}</option>
              </select>
            </label>
            <label>سازمان مادر (اختیاری)<input class="input" v-model.trim="customerForm.organization" placeholder="Customer-0001" /></label>
          </div>
          <p class="muted hint-line">کد اشتراک و کد معرف به‌صورت خودکار پس از ذخیره تخصیص می‌یابند.</p>
          <p class="error" v-if="customerFormError">{{ customerFormError }}</p>
          <div class="btn-row">
            <button type="button" class="primary-btn" @click="saveCustomer" :disabled="customerSaving">{{ customerSaving ? '...' : 'ذخیره' }}</button>
            <button type="button" class="tertiary-btn" @click="customerForm = null">انصراف</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ======================= سازمان‌ها ======================= -->
    <section v-if="activeTab === 'org'" class="tab-body">
      <div class="totals-grid boot-kpis" v-if="orgBoot && orgBoot.kpis">
        <div class="total-box"><small>مشتریان سازمانی</small><strong>{{ formatQty(orgBoot.kpis.organizations) }}</strong></div>
        <div class="total-box"><small>قراردادهای فعال</small><strong>{{ formatQty(orgBoot.kpis.active_contracts) }}</strong></div>
        <div class="total-box"><small>معین‌های فعال</small><strong>{{ formatQty(orgBoot.kpis.members) }}</strong></div>
        <div class="total-box"><small>مصرف سازمانی این ماه</small><strong>{{ formatMoneyValue(orgBoot.kpis.month_usage) }}</strong></div>
      </div>
      <p class="error" v-if="orgError">{{ orgError }}</p>
      <p class="success-msg" v-if="orgMessage">{{ orgMessage }}</p>

      <ManagementSurfaceCard title="قراردادهای سازمانی" subtitle="نوع مشتری «سازمانی» + سقف سفارش روزانه/ماهانه، روزها و ساعات مجاز، محدودیت آدرس و زمان صدور فاکتور">
        <div class="toolbar">
          <button type="button" class="primary-btn" @click="openContractForm()">قرارداد جدید</button>
          <span class="muted">پورتال حسابدار: <code class="link-code">{{ orgPublicUrl }}</code></span>
        </div>
        <p class="muted" v-if="orgLoading">در حال دریافت قراردادها...</p>
        <ManagementListView
          v-else
          :columns="orgContractColumns"
          :rows="orgContracts"
          row-key="name"
          :row-clickable="true"
          @row-click="openContractForm"
        >
          <template #cell-organization_label="{ row }"><strong>{{ row.organization_label }}</strong></template>
          <template #cell-contract_no="{ row }"><small class="muted">{{ row.contract_no || row.name }}</small></template>
          <template #cell-daily_order_cap="{ row }">{{ row.daily_order_cap ? formatMoneyValue(row.daily_order_cap) : '—' }}</template>
          <template #cell-monthly_order_cap="{ row }">{{ row.monthly_order_cap ? formatMoneyValue(row.monthly_order_cap) : '—' }}</template>
          <template #cell-allowed_schedule="{ row }"><small class="muted">{{ (row.allowed_days && row.allowed_days.length ? row.allowed_days.join('، ') : 'همه روزها') }}{{ row.allowed_to_hour ? ` · ${row.allowed_from_hour} تا ${row.allowed_to_hour}` : '' }}</small></template>
          <template #cell-invoice_mode="{ value }">{{ value || '—' }}</template>
          <template #cell-status="{ row }"><span class="pill" :class="{ ok: row.status === 'فعال', warn: row.status !== 'فعال' }">{{ row.status }}</span></template>
          <template #cell-actions="{ row }">
            <div class="row-actions">
              <button type="button" class="secondary-btn" @click="selectOrg(row.organization)">اعتبار و سفارش‌ها</button>
              <button type="button" class="tertiary-btn" @click="openContractForm(row)">ویرایش</button>
              <button type="button" class="tertiary-btn danger" @click="removeContract(row)">حذف</button>
            </div>
          </template>
          <template #empty>قراردادی ثبت نشده است؛ ابتدا مشتری را با نوع «سازمانی» بسازید و سپس قرارداد جدید بزنید.</template>
        </ManagementListView>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="معین‌های سازمانی" subtitle="زیرمجموعه‌های هر سازمان با نام کاربری و رمز عبور اختصاصی و سقف سفارش جداگانه">
        <div class="toolbar"><button type="button" class="primary-btn" @click="openMemberForm(null)">معین جدید</button></div>
        <ManagementListView
          :columns="orgMemberColumns"
          :rows="orgMembers"
          row-key="name"
          :row-clickable="true"
          @row-click="openMemberForm"
        >
          <template #cell-member="{ row }"><strong>{{ row.full_name }}</strong><small class="muted d-block">{{ row.mobile || '—' }}<template v-if="row.role_title"> · {{ row.role_title }}</template></small></template>
          <template #cell-organization_label="{ value }">{{ value || '—' }}</template>
          <template #cell-username="{ value }"><span class="pill">{{ value || '—' }}</span></template>
          <template #cell-daily_cap="{ row }">{{ row.daily_cap ? formatMoneyValue(row.daily_cap) : 'ارث از قرارداد' }}</template>
          <template #cell-monthly_cap="{ row }">{{ row.monthly_cap ? formatMoneyValue(row.monthly_cap) : 'ارث از قرارداد' }}</template>
          <template #cell-is_active="{ row }"><span class="pill" :class="{ ok: row.is_active, warn: !row.is_active }">{{ row.is_active ? 'فعال' : 'غیرفعال' }}</span></template>
          <template #cell-actions="{ row }">
            <div class="row-actions">
              <button type="button" class="tertiary-btn" @click="openMemberForm(row)">ویرایش</button>
              <button type="button" class="tertiary-btn danger" @click="removeMember(row)">حذف</button>
            </div>
          </template>
          <template #empty>معینی تعریف نشده است؛ برای هر زیرمجموعه سازمان یک معین با نام کاربری/رمز بسازید.</template>
        </ManagementListView>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard v-if="selectedOrg && orgCredit" :title="`رصد لحظه‌ای اعتبار «${orgCredit.organization_label}»`" subtitle="مصرف روزانه/ماهانه نسبت به سقف قرارداد، وضعیت معین‌ها و سفارش‌های فاکتورنشده">
        <div class="totals-grid">
          <div class="total-box"><small>مصرف امروز</small><strong :class="{ 'warn-text': orgCredit.contract && orgCredit.contract.daily_order_cap && orgCredit.usage.day_usage >= orgCredit.contract.daily_order_cap }">{{ formatMoneyValue(orgCredit.usage.day_usage) }}<small v-if="orgCredit.contract && orgCredit.contract.daily_order_cap" class="muted"> / {{ formatMoneyValue(orgCredit.contract.daily_order_cap) }}</small></strong></div>
          <div class="total-box"><small>مصرف این ماه</small><strong :class="{ 'warn-text': orgCredit.contract && orgCredit.contract.monthly_order_cap && orgCredit.usage.month_usage >= orgCredit.contract.monthly_order_cap }">{{ formatMoneyValue(orgCredit.usage.month_usage) }}<small v-if="orgCredit.contract && orgCredit.contract.monthly_order_cap" class="muted"> / {{ formatMoneyValue(orgCredit.contract.monthly_order_cap) }}</small></strong></div>
          <div class="total-box"><small>فاکتورنشده ({{ formatQty(orgCredit.usage.uninvoiced?.count || 0) }} سفارش)</small><strong>{{ formatMoneyValue(orgCredit.usage.uninvoiced?.total || 0) }}</strong></div>
          <div class="total-box"><small>زمان صدور فاکتور</small><strong>{{ orgCredit.contract ? orgCredit.contract.invoice_mode : '—' }}</strong></div>
        </div>

        <ManagementListView
          v-if="orgCredit.members && orgCredit.members.length"
          :columns="orgCreditMemberColumns"
          :rows="orgCredit.members"
          row-key="name"
        >
          <template #cell-member="{ row }"><strong>{{ row.full_name }}</strong><small class="muted d-block">{{ row.username || '—' }}</small></template>
          <template #cell-day_usage="{ row }">{{ formatMoneyValue(row.day_usage) }}</template>
          <template #cell-month_usage="{ row }">{{ formatMoneyValue(row.month_usage) }}</template>
          <template #cell-uninvoiced="{ row }">{{ formatMoneyValue(row.uninvoiced?.total || 0) }} ({{ formatQty(row.uninvoiced?.count || 0) }})</template>
        </ManagementListView>

        <div class="toolbar" style="margin-top:0.8rem">
          <label class="date-label">از تاریخ<input class="input" type="date" v-model="orgOrderFilters.date_from" /></label>
          <label class="date-label">تا تاریخ<input class="input" type="date" v-model="orgOrderFilters.date_to" /></label>
          <select class="input" v-model="orgOrderFilters.invoiced" @change="loadOrgOrders">
            <option value="">همه</option>
            <option value="no">فاکتورنشده</option>
            <option value="yes">فاکتورشده</option>
          </select>
          <button type="button" class="secondary-btn" @click="loadOrgOrders" :disabled="orgOrdersLoading">{{ orgOrdersLoading ? '...' : 'جستجو' }}</button>
          <button type="button" class="secondary-btn" @click="exportOrgExcel" :disabled="orgInvoiceBusy">خروجی اکسل</button>
          <button type="button" class="primary-btn" @click="issueConsolidatedInvoice" :disabled="orgInvoiceBusy || !selectedOrgOrderNames.length">{{ orgInvoiceBusy ? '...' : `صدور فاکتور تجمیعی (${formatQty(selectedOrgOrderNames.length)})` }}</button>
        </div>
        <p class="muted" v-if="orgOrdersLoading">در حال دریافت سفارش‌ها...</p>
        <ManagementListView
          v-else
          :columns="orgOrderColumns"
          :rows="orgOrders"
          row-key="name"
        >
          <template #cell-select="{ row }"><input type="checkbox" :disabled="!!row.org_invoice" v-model="selectedOrgOrders[row.name]" /></template>
          <template #cell-name="{ row }"><strong>{{ row.name }}</strong></template>
          <template #cell-date="{ value }">{{ value || '—' }}</template>
          <template #cell-org_member="{ value }">{{ value || '—' }}</template>
          <template #cell-grand_total="{ row }">{{ formatMoneyValue(row.grand_total) }}</template>
          <template #cell-status="{ row }"><span class="pill">{{ row.status || '—' }}</span></template>
          <template #cell-org_invoice="{ value }"><small class="muted">{{ value || '—' }}</small></template>
          <template #empty>سفارشی مطابق فیلتر یافت نشد.</template>
        </ManagementListView>
      </ManagementSurfaceCard>

      <!-- فرم قرارداد -->
      <div v-if="contractForm" class="popup-backdrop" @click.self="contractForm = null">
        <div class="popup wide">
          <h3>{{ contractForm.name ? 'ویرایش قرارداد' : 'قرارداد سازمانی جدید' }}</h3>
          <div class="form-grid">
            <label>مشتری سازمانی (نام Customer) <span class="req">*</span><input class="input" v-model.trim="contractForm.organization" :disabled="!!contractForm.name" placeholder="Customer-0001 یا نام سازمان" /></label>
            <label>شماره قرارداد<input class="input" v-model.trim="contractForm.contract_no" /></label>
            <label>تاریخ شروع<input class="input" type="date" v-model="contractForm.start_date" /></label>
            <label>تاریخ پایان<input class="input" type="date" v-model="contractForm.end_date" /></label>
            <label>وضعیت
              <select class="input" v-model="contractForm.status"><option v-for="s in orgBoot.contract_statuses" :key="s" :value="s">{{ s }}</option></select>
            </label>
            <label>زمان صدور فاکتور
              <select class="input" v-model="contractForm.invoice_mode"><option v-for="m in orgBoot.invoice_modes" :key="m" :value="m">{{ m }}</option></select>
            </label>
            <label>سقف سفارش روزانه (ریال، ۰=نامحدود)<input class="input" type="number" min="0" v-model.number="contractForm.daily_order_cap" /></label>
            <label>سقف سفارش ماهانه (ریال، ۰=نامحدود)<input class="input" type="number" min="0" v-model.number="contractForm.monthly_order_cap" /></label>
            <label>از ساعت مجاز (۰=بدون محدودیت)<input class="input" type="number" min="0" max="23" v-model.number="contractForm.allowed_from_hour" /></label>
            <label>تا ساعت مجاز<input class="input" type="number" min="0" max="24" v-model.number="contractForm.allowed_to_hour" /></label>
            <label class="full-row check-row">
              <span>روزهای مجاز سفارش (بدون انتخاب = همه روزها):</span>
              <span class="days-row">
                <label v-for="d in orgBoot.weekdays" :key="d" class="day-chip" :class="{ sel: contractForm.allowed_days.includes(d) }" @click="toggleContractDay(d)">{{ d }}</label>
              </span>
            </label>
            <label class="check-row full-row"><input type="checkbox" v-model="contractForm.restrict_addresses" :true-value="1" :false-value="0" /> سفارش فقط به آدرس‌های مجاز (پایین)</label>
            <label class="full-row" v-if="contractForm.restrict_addresses">
              آدرس‌های مجاز (شناسه Address ثبت‌شده برای سازمان)
              <div class="address-adder">
                <input class="input" v-model.trim="contractForm.new_address" placeholder="ADDR-0001" @keyup.enter.prevent="addContractAddress" />
                <button type="button" class="secondary-btn" @click="addContractAddress">افزودن</button>
              </div>
              <span class="pill" v-for="(a, i) in contractForm.allowed_addresses" :key="a" @click="contractForm.allowed_addresses.splice(i, 1)">{{ a }} ✕</span>
            </label>
            <label class="full-row">کد دسترسی پورتال حسابدار (خالی = بدون تغییر)<input class="input" v-model.trim="contractForm.portal_access_code" :placeholder="contractForm.portal_access_code_set ? '••••••' : ''" /></label>
            <ManagementNoteField
              v-model="contractForm.note"
              class="full-row"
              label="یادداشت"
              rows="2"
              placeholder="یادداشت داخلی قرارداد..."
            />
          </div>
          <p class="error" v-if="contractFormError">{{ contractFormError }}</p>
          <div class="btn-row">
            <button type="button" class="primary-btn" @click="saveContract" :disabled="contractFormSaving">{{ contractFormSaving ? '...' : 'ذخیره قرارداد' }}</button>
            <button type="button" class="tertiary-btn" @click="contractForm = null">انصراف</button>
          </div>
        </div>
      </div>

      <!-- فرم معین -->
      <div v-if="memberForm" class="popup-backdrop" @click.self="memberForm = null">
        <div class="popup">
          <h3>{{ memberForm.name ? 'ویرایش معین' : 'معین جدید' }}</h3>
          <div class="form-grid">
            <label>سازمان <span class="req">*</span>
              <select class="input" v-model="memberForm.organization" :disabled="!!memberForm.name">
                <option v-for="c in orgContracts" :key="c.organization" :value="c.organization">{{ c.organization_label }}</option>
              </select>
            </label>
            <label>نام و نام خانوادگی <span class="req">*</span><input class="input" v-model.trim="memberForm.full_name" /></label>
            <label>موبایل<input class="input" v-model.trim="memberForm.mobile" inputmode="tel" /></label>
            <label>نام کاربری<input class="input" v-model.trim="memberForm.username" placeholder="در صورت خالی‌بودن: موبایل" /></label>
            <label>رمز عبور<input class="input" v-model.trim="memberForm.access_code" :placeholder="memberForm.name ? '•••••• (بدون تغییر)' : ''" /></label>
            <label>سمت / عنوان<input class="input" v-model.trim="memberForm.role_title" placeholder="مثلاً سرپرست رفاه" /></label>
            <label>سقف روزانه معین (۰=ارث از قرارداد)<input class="input" type="number" min="0" v-model.number="memberForm.daily_cap" /></label>
            <label>سقف ماهانه معین (۰=ارث از قرارداد)<input class="input" type="number" min="0" v-model.number="memberForm.monthly_cap" /></label>
            <label>مشتری باشگاه متصل (اختیاری)<input class="input" v-model.trim="memberForm.member_customer" placeholder="Customer-0001" /></label>
            <label class="check-row"><input type="checkbox" v-model="memberForm.is_active" :true-value="1" :false-value="0" /> فعال</label>
          </div>
          <p class="error" v-if="memberFormError">{{ memberFormError }}</p>
          <div class="btn-row">
            <button type="button" class="primary-btn" @click="saveMember" :disabled="memberFormSaving">{{ memberFormSaving ? '...' : 'ذخیره معین' }}</button>
            <button type="button" class="tertiary-btn" @click="memberForm = null">انصراف</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ======================= صدای مشتری ======================= -->
    <section v-if="activeTab === 'voice'" class="tab-body">
      <ManagementSurfaceCard title="صدای مشتری" subtitle="ثبت و رسیدگی به شکایات، انتقادها، پیشنهادها، درخواست‌ها و تقدیرها — همراه آمار به تفکیک نوع">
        <div class="totals-grid">
          <div class="total-box" v-for="(count, type) in voiceSummary.by_type" :key="type"><small>{{ type }}</small><strong>{{ formatQty(count) }}</strong></div>
          <div class="total-box" v-if="voiceSummary.by_status && voiceSummary.by_status['جدید']"><small>در انتظار رسیدگی</small><strong class="warn-text">{{ formatQty(voiceSummary.by_status['جدید']) }}</strong></div>
        </div>
        <p class="muted hint-line">لینک ثبت عمومی برای مشتریان: <code class="link-code">{{ voicePublicUrl }}</code> — ثبت با موبایل؛ در صورت داشتن کد سفارش، صحت آن بررسی می‌شود.</p>
        <div class="toolbar">
          <select class="input" v-model="voiceFilters.type" @change="loadVoices">
            <option value="">همه انواع</option>
            <option v-for="t in voiceCustomerKinds" :key="t" :value="t">{{ t }}</option>
          </select>
          <select class="input" v-model="voiceFilters.status" @change="loadVoices">
            <option value="">همه وضعیت‌ها</option>
            <option v-for="s in voiceStatusesList" :key="s" :value="s">{{ s }}</option>
          </select>
          <label class="date-label">از تاریخ<input class="input" type="date" v-model="voiceFilters.date_from" /></label>
          <label class="date-label">تا تاریخ<input class="input" type="date" v-model="voiceFilters.date_to" /></label>
          <input class="input" v-model.trim="voiceFilters.search" placeholder="جستجو (نام/موبایل/موضوع/کد سفارش)..." @keyup.enter="loadVoices" />
          <button type="button" class="secondary-btn" @click="loadVoices" :disabled="voicesLoading">{{ voicesLoading ? '...' : 'جستجو' }}</button>
          <button type="button" class="primary-btn" @click="openVoiceForm()">ثبت مراجعه/پیام</button>
        </div>
        <p class="muted" v-if="voicesLoading">در حال دریافت...</p>
        <p class="error" v-if="voicesError">{{ voicesError }}</p>
        <p class="success-msg" v-if="voicesMessage">{{ voicesMessage }}</p>
        <ManagementListView
          v-if="!voicesLoading"
          :columns="voiceColumns"
          :rows="voices"
          row-key="name"
          :row-clickable="true"
          @row-click="openVoiceReply"
        >
          <template #cell-type="{ row }"><span class="pill" :class="{ warn: row.type === 'شکایت' }">{{ row.type }}</span></template>
          <template #cell-subject="{ row }"><strong>{{ row.subject }}</strong><br><small class="muted">{{ row.creation }}</small><small v-if="row.order_code" class="muted"> · {{ row.order_code }}</small></template>
          <template #cell-customer="{ row }">{{ row.customer_name || 'مهمان' }}<br><small class="muted">{{ row.mobile }}</small></template>
          <template #cell-message="{ value }"><span class="sms-cell">{{ value }}</span></template>
          <template #cell-status="{ row }"><span class="pill" :class="{ ok: row.status === 'پاسخ داده‌شده' || row.status === 'بسته', warn: row.status === 'جدید' }">{{ row.status }}</span></template>
          <template #cell-response="{ value }"><span class="sms-cell"><small>{{ value || '—' }}</small></span></template>
          <template #cell-actions="{ row }">
            <span class="row-actions">
              <button type="button" class="tertiary-btn" @click="openVoiceReply(row)">پاسخ/وضعیت</button>
              <button type="button" class="tertiary-btn danger" @click="removeVoice(row)">حذف</button>
            </span>
          </template>
          <template #empty>پیامی ثبت نشده است.</template>
        </ManagementListView>
      </ManagementSurfaceCard>

      <div v-if="voiceForm" class="popup-backdrop" @click.self="voiceForm = null">
        <div class="popup">
          <h3>ثبت مراجعه / پیام مشتری</h3>
          <div class="form-grid">
            <label>نوع
              <select class="input" v-model="voiceForm.type"><option v-for="t in voiceCustomerKinds" :key="t" :value="t">{{ t }}</option></select>
            </label>
            <label>نام مشتری<input class="input" v-model.trim="voiceForm.customer_name" /></label>
            <label>موبایل<input class="input" v-model.trim="voiceForm.mobile" inputmode="tel" /></label>
            <label class="full-row">موضوع <span class="req">*</span><input class="input" v-model.trim="voiceForm.subject" /></label>
            <label class="full-row">متن پیام<textarea class="input" rows="3" v-model="voiceForm.message"></textarea></label>
          </div>
          <p class="error" v-if="voiceFormError">{{ voiceFormError }}</p>
          <div class="btn-row">
            <button type="button" class="primary-btn" @click="saveVoice" :disabled="voiceFormSaving">{{ voiceFormSaving ? '...' : 'ثبت' }}</button>
            <button type="button" class="tertiary-btn" @click="voiceForm = null">انصراف</button>
          </div>
        </div>
      </div>

      <div v-if="voiceReply" class="popup-backdrop" @click.self="voiceReply = null">
        <div class="popup">
          <h3>پاسخ و وضعیت پیام</h3>
          <div class="form-grid">
            <label>وضعیت
              <select class="input" v-model="voiceReply.status"><option v-for="s in voiceStatusesList" :key="s" :value="s">{{ s }}</option></select>
            </label>
            <label class="full-row">پاسخ مجموعه<textarea class="input" rows="3" v-model="voiceReply.response"></textarea></label>
          </div>
          <div class="btn-row">
            <button type="button" class="primary-btn" @click="saveVoiceReply" :disabled="voiceReplySaving">{{ voiceReplySaving ? '...' : 'ثبت پاسخ' }}</button>
            <button type="button" class="tertiary-btn" @click="voiceReply = null">انصراف</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ======================= پیامک ======================= -->
    <section v-if="activeTab === 'sms'" class="tab-body">
      <ManagementSurfaceCard title="قالب‌های پیامک خودکار" subtitle="تبریک تولد، خوش‌آمدگویی و یادآوری خرید — متغیرها: {name} {membership_code} {message}">
        <p class="muted" v-if="!smsTemplates.sms_enabled">⚠️ ارسال پیامک غیرفعال است؛ پیامک‌ها فقط در سوابق ثبت می‌شوند تا وقتی درگاه پیامک (تنظیمات SMS فراپه) و گزینه فعال‌سازی را روشن کنید.</p>
        <div class="form-grid" v-if="smsTemplates.templates">
          <label class="full-row">خوش‌آمدگویی<textarea class="input" rows="2" v-model="smsTemplates.templates.welcome"></textarea></label>
          <label class="full-row">تبریک تولد<textarea class="input" rows="2" v-model="smsTemplates.templates.birthday"></textarea></label>
          <label class="full-row">یادآوری خرید (مشتری غیرفعال)<textarea class="input" rows="2" v-model="smsTemplates.templates.inactive"></textarea></label>
          <label class="full-row">قالب پیش‌فرض ارسال انبوه<textarea class="input" rows="2" v-model="smsTemplates.templates.bulk_default"></textarea></label>
        </div>
        <div class="btn-row">
          <label class="check-row"><input type="checkbox" v-model="smsTemplates.sms_enabled" /> فعال‌سازی ارسال واقعی پیامک</label>
          <button type="button" class="primary-btn" @click="saveSmsTemplates" :disabled="smsTemplatesSaving">{{ smsTemplatesSaving ? '...' : 'ذخیره قالب‌ها' }}</button>
        </div>
        <p class="error" v-if="smsTemplatesError">{{ smsTemplatesError }}</p>
        <p class="success-msg" v-if="smsTemplatesMessage">{{ smsTemplatesMessage }}</p>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="ارسال پیامک" subtitle="ارسال اختصاصی یا انبوه بر اساس سگمنت، سطح یا لیست شماره‌ها">
        <div class="form-grid">
          <label>نوع
            <select class="input" v-model="smsForm.kind">
              <option v-for="k in smsKinds" :key="k" :value="k">{{ k }}</option>
            </select>
          </label>
          <label v-if="smsForm.kind !== 'دستی'">سگمنت هدف
            <select class="input" v-model="smsForm.segment"><option value="">همه</option><option v-for="s in segments" :key="s" :value="s">{{ s }}</option></select>
          </label>
          <label v-if="smsForm.kind !== 'دستی'">سطح هدف
            <select class="input" v-model="smsForm.tier"><option value="">همه</option><option v-for="t in tiers" :key="t" :value="t">{{ t }}</option></select>
          </label>
          <label>کمپین مرتبط
            <select class="input" v-model="smsForm.campaign"><option value="">—</option><option v-for="c in campaigns" :key="c.name" :value="c.name">{{ c.title }}</option></select>
          </label>
          <label class="full-row" v-if="smsForm.kind === 'دستی'">شماره موبایل‌ها (هر خط یک شماره یا جدا با کاما)
            <textarea class="input" rows="3" v-model="smsForm.mobilesText" placeholder="0912...&#10;0935..."></textarea>
          </label>
          <label class="full-row">متن پیامک <span class="req">*</span>
            <textarea class="input" rows="3" v-model="smsForm.message" placeholder="متن پیامک... ({name} با نام مشتری جایگزین می‌شود)"></textarea>
          </label>
        </div>
        <div class="btn-row">
          <button type="button" class="primary-btn" @click="sendSms" :disabled="smsSending">{{ smsSending ? 'در حال ارسال...' : 'ارسال پیامک' }}</button>
        </div>
        <p class="error" v-if="smsFormError">{{ smsFormError }}</p>
        <p class="success-msg" v-if="smsFormMessage">{{ smsFormMessage }}</p>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="آمار منشور ارتباط با مشتری" subtitle="آمارگیری به تفکیک پیامک‌های تبلیغاتی، اطلاع‌رسانی و یادآوری (۳۰ روز گذشته)">
        <p class="muted" v-if="smsKindStatsLoading">در حال محاسبه آمار...</p>
        <template v-else-if="smsKindStats && smsKindStats.classes">
          <div class="totals-grid">
            <div class="total-box" v-for="cls in smsKindStats.classes" :key="cls.class">
              <small>پیامک {{ cls.class }}</small>
              <strong>{{ formatQty(cls.total) }}</strong>
              <small class="muted">موفق: {{ formatQty(cls.sent) }} · نرخ موفقیت {{ cls.success_rate }}٪</small>
            </div>
            <div class="total-box"><small>مجموع کل</small><strong>{{ formatQty(smsKindStats.grand_total) }}</strong><small class="muted">ارسال‌شده: {{ formatQty(smsKindStats.grand_sent) }}</small></div>
          </div>
          <ManagementListView
            :columns="smsKindStatsColumns"
            :rows="smsKindStatsRows"
            row-key="row_key"
          >
            <template #cell-kind="{ value }">{{ value }}</template>
            <template #cell-class_label="{ value }"><span class="pill">{{ value }}</span></template>
            <template #cell-total="{ value }">{{ formatQty(value) }}</template>
            <template #cell-sent="{ value }"><span class="ok-text">{{ formatQty(value) }}</span></template>
            <template #cell-failed="{ value }"><span class="warn-text">{{ formatQty(value) }}</span></template>
            <template #cell-queued="{ value }">{{ formatQty(value) }}</template>
            <template #cell-success_rate="{ value }">{{ value }}٪</template>
            <template #empty>داده‌ای برای نمایش نیست.</template>
          </ManagementListView>
        </template>
        <p class="muted" v-else>داده‌ای برای نمایش نیست.</p>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="سوابق پیامک‌ها" subtitle="لیست پیامک‌های ارسال‌شده و ناموفق">
        <div class="toolbar">
          <select class="input" v-model="smsHistoryFilters.kind" @change="loadSmsHistory">
            <option value="">همه انواع</option>
            <option v-for="k in smsKinds" :key="k" :value="k">{{ k }}</option>
          </select>
          <select class="input" v-model="smsHistoryFilters.status" @change="loadSmsHistory">
            <option value="">همه وضعیت‌ها</option>
            <option value="ارسال‌شده">ارسال‌شده</option>
            <option value="ناموفق">ناموفق</option>
            <option value="بدون درگاه">بدون درگاه</option>
            <option value="در صف">در صف</option>
          </select>
          <input class="input" v-model.trim="smsHistoryFilters.search" placeholder="جستجوی موبایل یا متن..." @keyup.enter="loadSmsHistory" />
          <button type="button" class="secondary-btn" @click="loadSmsHistory" :disabled="smsHistoryLoading">{{ smsHistoryLoading ? '...' : 'جستجو' }}</button>
        </div>
        <div class="btn-row" v-if="smsHistory && smsHistory.summary">
          <span v-for="(count, status) in smsHistory.summary" :key="status" class="pill" :class="{ ok: status === 'ارسال‌شده', warn: status !== 'ارسال‌شده' }">{{ status }}: {{ formatQty(count) }}</span>
        </div>
        <p class="muted" v-if="smsHistoryLoading">در حال دریافت سوابق...</p>
        <ManagementListView
          v-else-if="smsHistory"
          :columns="smsHistoryColumns"
          :rows="smsHistory.messages || []"
          row-key="name"
        >
          <template #cell-mobile="{ value }">{{ value }}</template>
          <template #cell-kind="{ value }"><span class="pill">{{ value }}</span></template>
          <template #cell-message="{ row }"><span class="sms-cell">{{ row.message }}<small v-if="row.provider_note" class="muted d-block">{{ row.provider_note }}</small></span></template>
          <template #cell-status="{ row }"><span class="pill" :class="{ ok: row.status === 'ارسال‌شده', warn: row.status !== 'ارسال‌شده' }">{{ row.status }}</span></template>
          <template #cell-campaign="{ value }">{{ value || '—' }}</template>
          <template #cell-sent_at="{ row }"><small class="muted">{{ row.sent_at || row.creation }}</small></template>
          <template #empty>پیامکی یافت نشد.</template>
        </ManagementListView>
      </ManagementSurfaceCard>
    </section>

    <!-- ======================= کیف پول ======================= -->
    <section v-if="activeTab === 'wallet'" class="tab-body">
      <ManagementSurfaceCard title="کیف پول مشتریان" subtitle="شارژ، پرداخت، انتقال و کش‌بک — کارت اعتباری الکترونیکی مشتریان">
        <div class="toolbar">
          <input class="input" v-model.trim="walletSearch" placeholder="جستجوی مشتری..." @keyup.enter="loadWallets" />
          <button type="button" class="secondary-btn" @click="loadWallets" :disabled="walletsLoading">{{ walletsLoading ? '...' : 'جستجو' }}</button>
        </div>
        <p class="muted hint-line">پرداخت با کیف پول در صندوق از طریق روش پرداخت «{{ (boot && boot.settings.wallet_mode_of_payment) || 'تنظیم‌نشده' }}» انجام می‌شود؛ پیکربندی در تب تنظیمات.</p>
        <p class="muted" v-if="walletsLoading">در حال دریافت کیف‌ها...</p>
        <ManagementListView
          v-else
          :columns="walletColumns"
          :rows="wallets"
          row-key="wallet"
        >
          <template #cell-customer_label="{ row }"><strong>{{ row.customer_name }}</strong><small class="muted d-block">{{ row.customer }}</small></template>
          <template #cell-tier="{ value }">{{ value || '—' }}</template>
          <template #cell-balance="{ row }"><strong>{{ formatMoneyValue(row.balance) }}</strong></template>
          <template #cell-total_charged="{ value }">{{ formatMoneyValue(value) }}</template>
          <template #cell-total_spent="{ value }">{{ formatMoneyValue(value) }}</template>
          <template #cell-total_rewards="{ value }">{{ formatMoneyValue(value) }}</template>
          <template #cell-status="{ row }"><span class="pill" :class="{ ok: row.status === 'فعال', warn: row.status !== 'فعال' }">{{ row.status }}</span></template>
          <template #cell-actions="{ row }">
            <div class="row-actions">
              <button type="button" class="tertiary-btn" @click="openWalletDetail(row.customer)">جزئیات</button>
              <button type="button" class="tertiary-btn" @click="openWalletAction('charge', row)">شارژ</button>
              <button type="button" class="tertiary-btn" @click="openWalletAction('transfer', row)">انتقال</button>
              <button type="button" class="tertiary-btn" @click="openWalletAction('adjust', row)">تعدیل</button>
            </div>
          </template>
          <template #empty>کیف پولی یافت نشد؛ با اولین شارژ یا کش‌بک به‌صورت خودکار ساخته می‌شود.</template>
        </ManagementListView>
      </ManagementSurfaceCard>

      <div v-if="walletAction" class="popup-backdrop" @click.self="walletAction = null">
        <div class="popup">
          <h3>{{ walletActionTitles[walletAction.mode] }} — {{ walletAction.customer_name }}</h3>
          <div class="form-grid">
            <label v-if="walletAction.mode === 'transfer'">مشتری مقصد
              <select class="input" v-model="walletAction.to_customer">
                <option value="">انتخاب کنید...</option>
                <option v-for="w in wallets" :key="w.customer" :value="w.customer" :disabled="w.customer === walletAction.customer">{{ w.customer_name }}</option>
              </select>
            </label>
            <label>مبلغ <span class="req">*</span><input class="input" type="number" min="0" v-model.number="walletAction.amount" /></label>
            <label v-if="walletAction.mode === 'adjust'">جهت
              <select class="input" v-model="walletAction.direction"><option value="واریز">واریز (افزایش)</option><option value="برداشت">برداشت (کاهش)</option></select>
            </label>
            <ManagementNoteField
              v-model="walletAction.note"
              class="full-row"
              label="شرح"
              :multiline="false"
              placeholder="شرح عملیات کیف پول..."
            />
          </div>
          <p class="error" v-if="walletActionError">{{ walletActionError }}</p>
          <div class="btn-row">
            <button type="button" class="primary-btn" @click="submitWalletAction" :disabled="walletActionSaving">{{ walletActionSaving ? '...' : 'ثبت' }}</button>
            <button type="button" class="tertiary-btn" @click="walletAction = null">انصراف</button>
          </div>
        </div>
      </div>

      <div v-if="walletDetail" class="popup-backdrop" @click.self="walletDetail = null">
        <div class="popup wide">
          <h3>کیف پول {{ walletDetail.wallet.customer_name }}</h3>
          <div class="totals-grid">
            <div class="total-box"><small>موجودی</small><strong>{{ formatMoneyValue(walletDetail.wallet.balance) }}</strong></div>
            <div class="total-box"><small>مجموع شارژ</small><strong>{{ formatMoneyValue(walletDetail.wallet.total_charged) }}</strong></div>
            <div class="total-box"><small>مصرف</small><strong>{{ formatMoneyValue(walletDetail.wallet.total_spent) }}</strong></div>
            <div class="total-box"><small>پاداش‌ها</small><strong>{{ formatMoneyValue(walletDetail.wallet.total_rewards) }}</strong></div>
          </div>
          <div v-if="walletDetail.points" class="points-strip">
            <div>
              <small class="muted">امتیاز وفاداری</small>
              <strong class="points-value">{{ formatQty(walletDetail.points.balance) }}</strong>
              <small class="muted" v-if="walletDetail.points.settings?.rial_value">هر امتیاز {{ formatMoneyValue(walletDetail.points.settings.rial_value) }}</small>
            </div>
            <button v-if="walletDetail.points.settings?.enabled" type="button" class="secondary-btn" @click="openRedeemForm(walletDetail.wallet.customer)">تبدیل امتیاز به اعتبار</button>
          </div>
          <p class="success-msg" v-if="walletDetailMessage">{{ walletDetailMessage }}</p>
          <ManagementListView
            v-if="walletDetail.point_entries && walletDetail.point_entries.length"
            :columns="pointEntryColumns"
            :rows="walletDetail.point_entries"
            row-key="name"
          >
            <template #cell-kind="{ value }"><span class="pill">{{ value }}</span></template>
            <template #cell-points="{ row }"><span :class="row.points > 0 ? 'ok-text' : 'warn-text'">{{ formatQty(row.points) }}</span></template>
            <template #cell-note="{ value }"><span class="sms-cell">{{ value }}</span></template>
            <template #cell-expiry_date="{ value }"><small class="muted">{{ value || '—' }}</small></template>
            <template #cell-creation="{ value }"><small class="muted">{{ value }}</small></template>
          </ManagementListView>
          <ManagementListView
            v-if="walletDetail.transactions && walletDetail.transactions.length"
            :columns="walletTransactionColumns"
            :rows="walletDetail.transactions"
            row-key="name"
          >
            <template #cell-kind="{ value }"><span class="pill">{{ value }}</span></template>
            <template #cell-direction="{ row }"><span :class="row.direction === 'واریز' ? 'ok-text' : 'warn-text'">{{ row.direction }}</span></template>
            <template #cell-amount="{ value }">{{ formatMoneyValue(value) }}</template>
            <template #cell-balance_after="{ value }">{{ formatMoneyValue(value) }}</template>
            <template #cell-reference_name="{ value }"><small class="muted">{{ value || '—' }}</small></template>
            <template #cell-note="{ value }"><span class="sms-cell">{{ value }}</span></template>
            <template #cell-entry_date="{ value }"><small class="muted">{{ value }}</small></template>
          </ManagementListView>
          <p class="muted" v-else>تراکنشی ثبت نشده است.</p>
          <div class="btn-row"><button type="button" class="tertiary-btn" @click="walletDetail = null">بستن</button></div>
        </div>
      </div>

      <div v-if="redeemForm" class="popup-backdrop" @click.self="redeemForm = null">
        <div class="popup">
          <h3>تبدیل امتیاز به اعتبار کیف پول</h3>
          <div class="form-grid">
            <label>تعداد امتیاز<input class="input" type="number" min="1" v-model.number="redeemForm.points" /></label>
          </div>
          <p class="muted hint-line">امتیازها با نرخ تعیین‌شده در «تنظیمات وفاداری» به ریال تبدیل و به کیف پول واریز می‌شوند.</p>
          <p class="error" v-if="redeemError">{{ redeemError }}</p>
          <div class="btn-row">
            <button type="button" class="primary-btn" @click="saveRedeem" :disabled="redeemSaving">{{ redeemSaving ? '...' : 'تبدیل' }}</button>
            <button type="button" class="tertiary-btn" @click="redeemForm = null">انصراف</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ======================= معرف‌ها ======================= -->
    <section v-if="activeTab === 'referral'" class="tab-body">
      <ManagementSurfaceCard title="کد معرف و سفیران برند" subtitle="هر مشتری یک کد معرف یکتا دارد؛ پاداش معرف و مهمان پس از اولین سفارش موفق به کیف پول واریز می‌شود">
        <div class="totals-grid" v-if="referral">
          <div class="total-box"><small>سفیران برند</small><strong>{{ formatQty(referral.ambassadors) }}</strong></div>
          <div class="total-box"><small>معرفی‌های موفق</small><strong>{{ formatQty(referral.referrals) }}</strong></div>
          <div class="total-box"><small>پاداش‌های پرداخت‌شده</small><strong>{{ formatMoneyValue(referral.rewards_paid) }}</strong></div>
        </div>
        <div class="form-grid" v-if="referral">
          <label>پاداش معرف (ریال)<input class="input" type="number" min="0" v-model.number="referral.settings.referrer_reward" /></label>
          <label>پاداش مهمان (ریال)<input class="input" type="number" min="0" v-model.number="referral.settings.referee_reward" /></label>
        </div>
        <div class="btn-row" v-if="referral">
          <button type="button" class="primary-btn" @click="saveReferralSettings" :disabled="referralSaving">{{ referralSaving ? '...' : 'ذخیره پاداش‌ها' }}</button>
        </div>
        <p class="success-msg" v-if="referralMessage">{{ referralMessage }}</p>
        <p class="error" v-if="referralError">{{ referralError }}</p>
        <h4 v-if="referral && referral.top && referral.top.length">برترین سفیران</h4>
        <ManagementListView
          v-if="referral && referral.top && referral.top.length"
          :columns="referralTopColumns"
          :rows="referral.top"
          row-key="referrer"
        >
          <template #cell-customer_name="{ value }">{{ value }}</template>
          <template #cell-count="{ value }">{{ formatQty(value) }}</template>
        </ManagementListView>
        <p class="muted hint-line">کد معرف هر مشتری در تب «مشتریان» قابل مشاهده است و هنگام ثبت سفارش میهمان قابل استفاده است؛ پردازش پاداش هر شب به‌صورت خودکار انجام می‌شود.</p>
      </ManagementSurfaceCard>
    </section>

    <!-- ======================= کمپین‌ها ======================= -->
    <section v-if="activeTab === 'campaigns'" class="tab-body">
      <ManagementSurfaceCard title="کمپین‌های بازاریابی" subtitle="کمپین نامحدود برای کانال‌های فروش مختلف با کد تخفیف، کش‌بک یا امتیاز">
        <div class="toolbar">
          <select class="input" v-model="campaignFilters.status" @change="loadCampaigns">
            <option value="">همه وضعیت‌ها</option>
            <option v-for="s in campaignStatuses" :key="s" :value="s">{{ s }}</option>
          </select>
          <button type="button" class="primary-btn" @click="openCampaignForm()">کمپین جدید</button>
        </div>
        <p class="muted" v-if="campaignsLoading">در حال دریافت کمپین‌ها...</p>
        <ManagementListView
          v-else
          :columns="campaignColumns"
          :rows="campaigns"
          row-key="name"
        >
          <template #cell-title="{ row }"><strong>{{ row.title }}</strong><small class="muted d-block">{{ row.name }}</small></template>
          <template #cell-coupon="{ value }">{{ value || '—' }}</template>
          <template #cell-channels="{ row }"><span v-for="ch in splitChannels(row.channels)" :key="ch" class="pill">{{ ch }}</span></template>
          <template #cell-validity="{ row }"><small class="muted">{{ row.valid_from || '...' }} ← {{ row.valid_to || '...' }}</small></template>
          <template #cell-bonus="{ row }">{{ row.bonus_type }}<span v-if="row.bonus_value"> ({{ row.bonus_type === 'کش‌بک' || row.bonus_type === 'تخفیف' ? formatQty(row.bonus_value) + '٪' : formatQty(row.bonus_value) }})</span></template>
          <template #cell-status="{ row }"><span class="pill" :class="{ ok: row.status === 'فعال', warn: row.status === 'متوقف' }">{{ row.status }}</span></template>
          <template #cell-actions="{ row }">
            <div class="row-actions">
              <button type="button" class="tertiary-btn" @click="openCampaignForm(row)">ویرایش</button>
              <button type="button" class="tertiary-btn" @click="showCampaignStats(row)">آمار</button>
              <button type="button" class="tertiary-btn" @click="toggleCampaignStatus(row)">{{ row.status === 'فعال' ? 'توقف' : 'فعال‌سازی' }}</button>
            </div>
          </template>
          <template #empty>کمپینی ثبت نشده است.</template>
        </ManagementListView>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="کدهای تخفیف (کوپن)" subtitle="کوپن‌ها برای اتصال به کمپین‌ها و فروش">
        <div class="btn-row"><button type="button" class="primary-btn" @click="openCouponForm()">کوپن جدید</button></div>
        <ManagementListView
          :columns="couponColumns"
          :rows="coupons"
          row-key="name"
        >
          <template #cell-coupon_code="{ row }"><strong>{{ row.coupon_code }}</strong></template>
          <template #cell-title="{ value }">{{ value || '—' }}</template>
          <template #cell-discount="{ row }">{{ row.discount_type === 'Percent' ? formatQty(row.discount_value) + '٪' : formatMoneyValue(row.discount_value) }}</template>
          <template #cell-min_order_amount="{ value }">{{ formatMoneyValue(value) }}</template>
          <template #cell-usage_limit="{ row }">{{ row.usage_limit ? formatQty(row.usage_limit) : 'نامحدود' }}</template>
          <template #cell-used_count="{ value }">{{ formatQty(value) }}</template>
          <template #cell-is_active="{ row }"><span class="pill" :class="{ ok: row.is_active, warn: !row.is_active }">{{ row.is_active ? 'فعال' : 'غیرفعال' }}</span></template>
          <template #cell-actions="{ row }"><button type="button" class="tertiary-btn" @click="openCouponForm(row)">ویرایش</button></template>
          <template #empty>کوپنی ثبت نشده است.</template>
        </ManagementListView>
      </ManagementSurfaceCard>

      <div v-if="campaignForm" class="popup-backdrop" @click.self="campaignForm = null">
        <div class="popup wide">
          <h3>{{ campaignForm.name ? 'ویرایش کمپین' : 'کمپین جدید' }}</h3>
          <div class="form-grid">
            <label>عنوان <span class="req">*</span><input class="input" v-model.trim="campaignForm.title" /></label>
            <label>کد تخفیف (کوپن)
              <select class="input" v-model="campaignForm.coupon">
                <option value="">— بدون کوپن —</option>
                <option v-for="cp in coupons" :key="cp.name" :value="cp.name">{{ cp.coupon_code }}</option>
              </select>
            </label>
            <label>کانال‌های فروش (جدا با کاما)<input class="input" v-model="campaignForm.channels" placeholder="حضوری, بیرون‌بر, ارسال با پیک, اینترنتی" /></label>
            <label>نوع پاداش
              <select class="input" v-model="campaignForm.bonus_type"><option v-for="b in campaignBonusTypes" :key="b" :value="b">{{ b }}</option></select>
            </label>
            <label>مقدار پاداش (٪ یا امتیاز)<input class="input" type="number" min="0" v-model.number="campaignForm.bonus_value" /></label>
            <label>از تاریخ<input class="input" type="date" v-model="campaignForm.valid_from" /></label>
            <label>تا تاریخ<input class="input" type="date" v-model="campaignForm.valid_to" /></label>
            <label>سگمنت هدف
              <select class="input" v-model="campaignForm.target_segment"><option value="">همه</option><option v-for="s in segments" :key="s" :value="s">{{ s }}</option></select>
            </label>
            <label>حداقل مبلغ سفارش<input class="input" type="number" min="0" v-model.number="campaignForm.min_order_amount" /></label>
            <label class="full-row">متن پیامک کمپین<textarea class="input" rows="2" v-model="campaignForm.sms_text"></textarea></label>
            <ManagementNoteField
              v-model="campaignForm.notes"
              class="full-row"
              label="یادداشت کمپین"
              rows="2"
              placeholder="یادداشت داخلی کمپین..."
            />
          </div>
          <p class="error" v-if="campaignFormError">{{ campaignFormError }}</p>
          <div class="btn-row">
            <button type="button" class="primary-btn" @click="saveCampaign" :disabled="campaignSaving">{{ campaignSaving ? '...' : 'ذخیره کمپین' }}</button>
            <button type="button" class="tertiary-btn" @click="campaignForm = null">انصراف</button>
          </div>
        </div>
      </div>

      <div v-if="campaignStats" class="popup-backdrop" @click.self="campaignStats = null">
        <div class="popup">
          <h3>آمار کمپین «{{ campaignStats.campaign }}»</h3>
          <div class="totals-grid">
            <div class="total-box"><small>مشارکت (مصرف کوپن)</small><strong>{{ formatQty(campaignStats.participants) }}</strong></div>
            <div class="total-box"><small>سفارش‌های کانال در بازه</small><strong>{{ formatQty(campaignStats.channel_orders) }}</strong></div>
            <div class="total-box"><small>فروش کانال در بازه</small><strong>{{ formatMoneyValue(campaignStats.channel_revenue) }}</strong></div>
            <div class="total-box"><small>بودجه پاداش تخمینی</small><strong>{{ formatMoneyValue(campaignStats.bonus_budget) }}</strong></div>
          </div>
          <div class="btn-row"><button type="button" class="tertiary-btn" @click="campaignStats = null">بستن</button></div>
        </div>
      </div>

      <div v-if="couponForm" class="popup-backdrop" @click.self="couponForm = null">
        <div class="popup">
          <h3>{{ couponForm.name ? 'ویرایش کوپن' : 'کوپن جدید' }}</h3>
          <div class="form-grid">
            <label>کد تخفیف <span class="req">*</span><input class="input" v-model.trim="couponForm.coupon_code" :disabled="!!couponForm.name" /></label>
            <label>عنوان<input class="input" v-model.trim="couponForm.title" /></label>
            <label>نوع تخفیف
              <select class="input" v-model="couponForm.discount_type"><option value="Percent">درصدی</option><option value="Fixed">مبلغ ثابت</option></select>
            </label>
            <label>مقدار <span class="req">*</span><input class="input" type="number" min="0" v-model.number="couponForm.discount_value" /></label>
            <label>حداقل سفارش<input class="input" type="number" min="0" v-model.number="couponForm.min_order_amount" /></label>
            <label>سقف مبلغ تخفیف<input class="input" type="number" min="0" v-model.number="couponForm.max_discount_amount" /></label>
            <label>از تاریخ<input class="input" type="date" v-model="couponForm.valid_from" /></label>
            <label>تا تاریخ<input class="input" type="date" v-model="couponForm.valid_to" /></label>
            <label>سقف تعداد استفاده<input class="input" type="number" min="0" v-model.number="couponForm.usage_limit" /></label>
            <label class="check-row full-row"><input type="checkbox" v-model="couponForm.is_active" /> فعال</label>
          </div>
          <p class="error" v-if="couponFormError">{{ couponFormError }}</p>
          <div class="btn-row">
            <button type="button" class="primary-btn" @click="saveCoupon" :disabled="couponSaving">{{ couponSaving ? '...' : 'ذخیره کوپن' }}</button>
            <button type="button" class="tertiary-btn" @click="couponForm = null">انصراف</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ======================= تنظیمات وفاداری ======================= -->
    <section v-if="activeTab === 'settings'" class="tab-body">
      <ManagementSurfaceCard title="تنظیمات وفاداری" subtitle="کش‌بک، روش پرداخت کیف پول و آستانه هشدار نارضایتی">
        <div class="form-grid" v-if="settingsForm">
          <label class="check-row full-row"><input type="checkbox" v-model="settingsForm.restaurant_club_enabled" /> باشگاه مشتریان فعال است</label>
          <label>درصد کش‌بک هر سفارش<input class="input" type="number" min="0" max="100" step="0.5" v-model.number="settingsForm.restaurant_cashback_percent" /></label>
          <label>حداقل سفارش برای کش‌بک (ریال)<input class="input" type="number" min="0" v-model.number="settingsForm.restaurant_cashback_min_order" /></label>
          <label>روش پرداخت کیف پول در صندوق
            <select class="input" v-model="settingsForm.restaurant_wallet_mode_of_payment">
              <option value="">— انتخاب کنید —</option>
              <option v-for="m in modeOfPayments" :key="m" :value="m">{{ m }}</option>
            </select>
          </label>
          <label>آستانه هشدار نارضایتی (امتیاز ≤)
            <select class="input" v-model.number="settingsForm.restaurant_survey_alert_threshold">
              <option :value="1">۱</option><option :value="2">۲</option><option :value="3">۳</option><option :value="4">۴</option>
            </select>
          </label>
        </div>
        <p class="muted hint-line">برای پرداخت با کیف پول در صندوق، ابتدا یک «روش پرداخت» (Mode of Payment) با نام دلخواه مثل «کیف پول» در تنظیمات ERPNext بسازید و اینجا انتخابش کنید. کش‌بک پس از تسویه هر سفارش به‌صورت خودکار به کیف مشتری واریز می‌شود.</p>
        <div class="btn-row">
          <button type="button" class="primary-btn" @click="saveSettings" :disabled="settingsSaving">{{ settingsSaving ? '...' : 'ذخیره تنظیمات' }}</button>
        </div>
        <p class="error" v-if="settingsError">{{ settingsError }}</p>
        <p class="success-msg" v-if="settingsMessage">{{ settingsMessage }}</p>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="سیستم امتیازدهی" subtitle="کسب امتیاز بر اساس مبلغ فاکتور، نحوه استفاده، انقضا و لایه‌های وفاداری (طلایی/نقره‌ای/برنزی)">
        <div class="form-grid" v-if="settingsForm">
          <label class="check-row full-row"><input type="checkbox" v-model="settingsForm.restaurant_points_enabled" /> امتیازدهی فعال است</label>
          <label>هر چند ریال خرید = ۱ امتیاز<input class="input" type="number" min="0" v-model.number="settingsForm.restaurant_points_rial_per_point" /></label>
          <label>ارزش هر امتیاز هنگام استفاده (ریال)<input class="input" type="number" min="0" v-model.number="settingsForm.restaurant_points_rial_value" /></label>
          <label>مدت اعتبار امتیاز (روز، ۰=بدون انقضا)<input class="input" type="number" min="0" v-model.number="settingsForm.restaurant_points_expiry_days" /></label>
          <label>حداقل امتیاز قابل استفاده<input class="input" type="number" min="0" v-model.number="settingsForm.restaurant_points_min_redeem" /></label>
          <label>آستانه لایه طلایی (مجموع امتیاز)<input class="input" type="number" min="0" v-model.number="settingsForm.restaurant_points_gold_threshold" /></label>
          <label>آستانه لایه نقره‌ای<input class="input" type="number" min="0" v-model.number="settingsForm.restaurant_points_silver_threshold" /></label>
          <label>آستانه لایه برنزی<input class="input" type="number" min="0" v-model.number="settingsForm.restaurant_points_bronze_threshold" /></label>
        </div>
        <p class="muted hint-line">امتیاز پس از تسویه یا تحویل هر سفارش به‌صورت خودکار محاسبه می‌شود؛ انقضای امتیازها هر شب به‌صورت خودکار پردازش می‌گردد و لایه‌ها از مجموع امتیاز کسب‌شده مشتری محاسبه می‌شوند.</p>
        <div class="btn-row">
          <button type="button" class="primary-btn" @click="saveSettings" :disabled="settingsSaving">{{ settingsSaving ? '...' : 'ذخیره تنظیمات' }}</button>
        </div>
      </ManagementSurfaceCard>
    </section>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import ManagementListView from '@/components/management/ManagementListView.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementNoteField from '@/components/management/ManagementNoteField.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import {
  getManagementClubBoot,
  updateManagementClubSettings,
  listManagementClubCustomers,
  saveManagementClubCustomer,
  assignManagementMembershipCodes,
  exportManagementCustomersExcel,
  importManagementCustomersExcel,
  computeManagementCustomerSegments,
  getManagementSmsTemplates,
  setManagementSmsTemplates,
  sendManagementSms,
  listManagementSmsMessages,
  getManagementSmsKindStats,
  listManagementWallets,
  getManagementWalletDetail,
  chargeManagementWallet,
  transferManagementWallet,
  adjustManagementWallet,
  getManagementReferralSummary,
  listManagementCampaigns,
  saveManagementCampaign,
  updateManagementCampaignStatus,
  getManagementCampaignStats,
  listManagementCoupons,
  saveManagementCoupon,
  listManagementCustomerVoices,
  saveManagementCustomerVoice,
  updateManagementCustomerVoiceStatus,
  deleteManagementCustomerVoice,
  listManagementPointEntries,
  redeemManagementPoints,
  getManagementOrgBoot,
  listManagementOrgContracts,
  saveManagementOrgContract,
  deleteManagementOrgContract,
  listManagementOrgMembers,
  saveManagementOrgMember,
  deleteManagementOrgMember,
  getManagementOrgCredit,
  listManagementOrgOrders,
  exportManagementOrgOrdersExcel,
  createManagementOrgInvoice,
  uploadFileToFrappe,
} from '@/utils/api'
import { formatMoney as formatMoneyUtil } from '@/utils/format'

const tabs = [
  { key: 'customers', label: 'مشتریان' },
  { key: 'org', label: 'سازمان‌ها' },
  { key: 'voice', label: 'صدای مشتری' },
  { key: 'sms', label: 'پیامک' },
  { key: 'wallet', label: 'کیف پول و امتیاز' },
  { key: 'referral', label: 'معرف‌ها' },
  { key: 'campaigns', label: 'کمپین‌ها' },
  { key: 'settings', label: 'تنظیمات وفاداری' },
]
const activeTab = ref('customers')
const loadedTabs = reactive({})

const boot = ref(null)
const bootLoading = ref(false)
const tiers = computed(() => boot.value?.tiers || ['VIP', 'عمده‌فروش', 'عادی', 'جدید'])
const segments = computed(() => boot.value?.segments || [])
const customerKinds = computed(() => boot.value?.settings?.customer_kinds || ['حقیقی', 'حقوقی', 'سازمانی'])
const smsKinds = computed(() => boot.value?.sms_kinds || ['دستی', 'انبوه'])
const campaignStatuses = computed(() => boot.value?.campaign_statuses || ['پیش‌نویس', 'فعال', 'متوقف', 'پایان‌یافته'])
const campaignBonusTypes = computed(() => boot.value?.campaign_bonus_types || ['تخفیف', 'کش‌بک', 'امتیاز'])
const modeOfPayments = computed(() => boot.value?.mode_of_payments || [])

function formatMoneyValue(value) {
  return formatMoneyUtil(Number(value || 0))
}
function formatQty(value) {
  return Number(value || 0).toLocaleString('fa-IR')
}
function splitChannels(channels) {
  return String(channels || '').split(',').map((c) => c.trim()).filter(Boolean)
}

// --------------------------------------------------------------------------
// Boot
// --------------------------------------------------------------------------
async function loadBoot() {
  bootLoading.value = true
  try {
    boot.value = await getManagementClubBoot()
    if (!settingsForm.value) {
      settingsForm.value = {
        restaurant_club_enabled: !!boot.value.settings.club_enabled,
        restaurant_cashback_percent: boot.value.settings.cashback_percent,
        restaurant_cashback_min_order: boot.value.settings.cashback_min_order,
        restaurant_wallet_mode_of_payment: boot.value.settings.wallet_mode_of_payment,
        restaurant_survey_alert_threshold: boot.value.settings.survey_alert_threshold,
        restaurant_points_enabled: !!boot.value.settings.points_enabled,
        restaurant_points_rial_per_point: boot.value.settings.points_rial_per_point,
        restaurant_points_rial_value: boot.value.settings.points_rial_value,
        restaurant_points_expiry_days: boot.value.settings.points_expiry_days,
        restaurant_points_min_redeem: boot.value.settings.points_min_redeem,
        restaurant_points_gold_threshold: boot.value.settings.points_gold_threshold,
        restaurant_points_silver_threshold: boot.value.settings.points_silver_threshold,
        restaurant_points_bronze_threshold: boot.value.settings.points_bronze_threshold,
      }
    }
  } catch (err) {
    boot.value = boot.value || null
  } finally {
    bootLoading.value = false
  }
}

function setActiveTab(key) {
  activeTab.value = key
  if (loadedTabs[key]) return
  loadedTabs[key] = true
  if (key === 'customers') loadCustomers()
  if (key === 'sms') { loadSmsTemplates(); loadSmsHistory(); loadSmsKindStats(); if (!campaigns.value.length) loadCampaigns() }
  if (key === 'wallet') loadWallets()
  if (key === 'referral') loadReferral()
  if (key === 'campaigns') { loadCampaigns(); loadCoupons() }
  if (key === 'voice') loadVoices()
  if (key === 'org') { loadOrgBoot(); loadOrgContracts(); loadOrgMembers() }
}

// --------------------------------------------------------------------------
// Customers
// --------------------------------------------------------------------------
const customers = ref([])
const customersLoading = ref(false)
const customersError = ref('')
const customersMessage = ref('')
const customerFilters = reactive({ search: '', tier: '', segment: '', kind: '', organization: '' })
const customerForm = ref(null)
const customerFormError = ref('')
const customerSaving = ref(false)
const excelBusy = ref(false)
const excelMode = ref('')
const codesBusy = ref(false)
const segmentsBusy = ref(false)
const customerExcelInput = ref(null)
const clubCustomerColumns = [
  { key: 'customer_name', label: 'مشتری' },
  { key: 'kind', label: 'نوع' },
  { key: 'membership_code', label: 'کد اشتراک' },
  { key: 'tier', label: 'سطح' },
  { key: 'segment', label: 'سگمنت' },
  { key: 'points_balance', label: 'امتیاز' },
  { key: 'orders', label: 'سفارش‌ها' },
  { key: 'total_spent', label: 'مجموع خرید' },
  { key: 'wallet_balance', label: 'کیف پول' },
  { key: 'referral_code', label: 'کد معرف' },
  { key: 'actions', label: 'عملیات' },
]

async function loadCustomers() {
  customersLoading.value = true
  customersError.value = ''
  try {
    const payload = await listManagementClubCustomers({ ...customerFilters })
    customers.value = payload?.customers || []
  } catch (err) {
    customersError.value = err.message || 'دریافت مشتریان ناموفق بود.'
  } finally {
    customersLoading.value = false
  }
}

function openCustomerForm(c = null) {
  customerFormError.value = ''
  customerForm.value = c
    ? { name: c.name, customer_name: c.customer_name, mobile: c.mobile, birth_date: c.birth_date, tier: c.tier, segment: c.segment, kind: c.kind || 'حقیقی', organization: c.organization || '' }
    : { name: '', customer_name: '', mobile: '', birth_date: '', tier: 'جدید', segment: '', kind: 'حقیقی', organization: '' }
}

async function saveCustomer() {
  customerSaving.value = true
  customerFormError.value = ''
  try {
    const payload = await saveManagementClubCustomer(customerForm.value)
    customersMessage.value = `مشتری ذخیره شد. کد اشتراک: ${payload.membership_code || '—'}`
    customerForm.value = null
    loadedTabs.customers = true
    await loadCustomers()
    await loadBoot()
  } catch (err) {
    customerFormError.value = err.message || 'ذخیره مشتری ناموفق بود.'
  } finally {
    customerSaving.value = false
  }
}

async function assignCodes() {
  codesBusy.value = true
  customersError.value = ''
  customersMessage.value = ''
  try {
    const payload = await assignManagementMembershipCodes()
    customersMessage.value = `کد اشتراک برای ${formatQty(payload?.membership_assigned || 0)} مشتری و کد معرف برای ${formatQty(payload?.referral_assigned || 0)} مشتری تخصیص یافت.`
    await loadCustomers()
    await loadBoot()
  } catch (err) {
    customersError.value = err.message || 'تخصیص کدها ناموفق بود.'
  } finally {
    codesBusy.value = false
  }
}

async function computeSegments() {
  segmentsBusy.value = true
  customersError.value = ''
  customersMessage.value = ''
  try {
    const payload = await computeManagementCustomerSegments()
    customersMessage.value = payload?.message || `سگمنت‌بندی ${formatQty(payload?.updated || 0)} مشتری به‌روزرسانی شد.`
    await loadCustomers()
  } catch (err) {
    customersError.value = err.message || 'محاسبه سگمنت‌ها ناموفق بود.'
  } finally {
    segmentsBusy.value = false
  }
}

async function exportCustomersExcel() {
  excelBusy.value = true
  excelMode.value = 'export'
  customersError.value = ''
  try {
    const payload = await exportManagementCustomersExcel({ search: customerFilters.search })
    if (payload?.file_url) {
      const link = document.createElement('a')
      link.href = payload.file_url
      link.download = payload.file_name || 'restaurant-customers.xlsx'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      customersMessage.value = `خروجی اکسل ${formatQty(payload.rows || 0)} مشتری آماده شد.`
    }
  } catch (err) {
    customersError.value = err.message || 'دریافت خروجی اکسل ناموفق بود.'
  } finally {
    excelBusy.value = false
    excelMode.value = ''
  }
}

function triggerCustomerExcelImport() {
  if (excelBusy.value) return
  const input = customerExcelInput.value
  if (input) {
    input.value = ''
    input.click()
  }
}

async function handleCustomerExcelFile(event) {
  const file = event?.target?.files?.[0]
  if (!file) return
  excelBusy.value = true
  excelMode.value = 'import'
  customersError.value = ''
  customersMessage.value = ''
  try {
    const uploaded = await uploadFileToFrappe(file, { isPrivate: true })
    const fileUrl = uploaded?.file_url || uploaded?.message?.file_url || ''
    const payload = await importManagementCustomersExcel({ file_url: fileUrl, file_name: file.name })
    customersMessage.value = payload?.message || `ورود از اکسل: ${formatQty(payload?.created || 0)} جدید، ${formatQty(payload?.updated || 0)} به‌روزرسانی.`
    if (payload?.errors && payload.errors.length) {
      customersError.value = payload.errors.slice(0, 3).join(' | ')
    }
    await loadCustomers()
    await loadBoot()
  } catch (err) {
    customersError.value = err.message || 'ورود از اکسل ناموفق بود.'
  } finally {
    excelBusy.value = false
    excelMode.value = ''
  }
}

// --------------------------------------------------------------------------
// SMS
// --------------------------------------------------------------------------
const smsTemplates = ref({ templates: null, sms_enabled: false })
const smsTemplatesSaving = ref(false)
const smsTemplatesError = ref('')
const smsTemplatesMessage = ref('')
const smsForm = reactive({ kind: 'دستی', segment: '', tier: '', campaign: '', mobilesText: '', message: '' })
const smsSending = ref(false)
const smsFormError = ref('')
const smsFormMessage = ref('')
const smsHistory = ref(null)
const smsHistoryLoading = ref(false)
const smsHistoryFilters = reactive({ kind: '', status: '', search: '' })
const smsHistoryColumns = [
  { key: 'mobile', label: 'موبایل' },
  { key: 'kind', label: 'نوع' },
  { key: 'message', label: 'متن' },
  { key: 'status', label: 'وضعیت' },
  { key: 'campaign', label: 'کمپین' },
  { key: 'sent_at', label: 'زمان' },
]

async function loadSmsTemplates() {
  try {
    const payload = await getManagementSmsTemplates()
    smsTemplates.value = { templates: { ...(payload?.defaults || {}), ...(payload?.templates || {}) }, sms_enabled: !!payload?.sms_enabled }
  } catch (err) {
    smsTemplatesError.value = err.message || 'دریافت قالب‌ها ناموفق بود.'
  }
}

async function saveSmsTemplates() {
  smsTemplatesSaving.value = true
  smsTemplatesError.value = ''
  smsTemplatesMessage.value = ''
  try {
    await setManagementSmsTemplates({ templates: smsTemplates.value.templates, sms_enabled: smsTemplates.value.sms_enabled ? 1 : 0 })
    smsTemplatesMessage.value = 'قالب‌های پیامک ذخیره شد.'
  } catch (err) {
    smsTemplatesError.value = err.message || 'ذخیره قالب‌ها ناموفق بود.'
  } finally {
    smsTemplatesSaving.value = false
  }
}

async function sendSms() {
  smsSending.value = true
  smsFormError.value = ''
  smsFormMessage.value = ''
  try {
    const payload = await sendManagementSms({
      kind: smsForm.kind,
      segment: smsForm.segment,
      tier: smsForm.tier,
      campaign: smsForm.campaign,
      message: smsForm.message,
      mobiles: smsForm.mobilesText.split(/[\n,]+/).map((m) => m.trim()).filter(Boolean),
    })
    const parts = [`${formatQty(payload?.total || 0)} گیرنده`]
    if (payload?.sent) parts.push(`${formatQty(payload.sent)} ارسال‌شده`)
    if (payload?.failed) parts.push(`${formatQty(payload.failed)} ناموفق/بدون درگاه`)
    smsFormMessage.value = `پیامک ثبت شد — ${parts.join('، ')}.`
    smsForm.message = ''
    loadedTabs.sms = true
    await loadSmsHistory()
  } catch (err) {
    smsFormError.value = err.message || 'ارسال پیامک ناموفق بود.'
  } finally {
    smsSending.value = false
  }
}

async function loadSmsHistory() {
  smsHistoryLoading.value = true
  try {
    smsHistory.value = await listManagementSmsMessages({ ...smsHistoryFilters })
  } catch (err) {
    smsHistory.value = { messages: [], summary: {} }
  } finally {
    smsHistoryLoading.value = false
  }
}

// --------------------------------------------------------------------------
// Wallets
// --------------------------------------------------------------------------
const wallets = ref([])
const walletsLoading = ref(false)
const walletSearch = ref('')
const walletAction = ref(null)
const walletActionError = ref('')
const walletActionSaving = ref(false)
const walletDetail = ref(null)
const walletDetailMessage = ref('')
const walletActionTitles = { charge: 'شارژ کیف پول', transfer: 'انتقال اعتبار', adjust: 'تعدیل دستی' }
const walletColumns = [
  { key: 'customer_label', label: 'مشتری' },
  { key: 'tier', label: 'سطح' },
  { key: 'balance', label: 'موجودی' },
  { key: 'total_charged', label: 'مجموع شارژ' },
  { key: 'total_spent', label: 'مصرف' },
  { key: 'total_rewards', label: 'پاداش‌ها' },
  { key: 'status', label: 'وضعیت' },
  { key: 'actions', label: 'عملیات' },
]
const pointEntryColumns = [
  { key: 'kind', label: 'نوع' },
  { key: 'points', label: 'امتیاز' },
  { key: 'note', label: 'شرح' },
  { key: 'expiry_date', label: 'انقضا' },
  { key: 'creation', label: 'زمان' },
]
const walletTransactionColumns = [
  { key: 'kind', label: 'نوع' },
  { key: 'direction', label: 'جهت' },
  { key: 'amount', label: 'مبلغ' },
  { key: 'balance_after', label: 'مانده' },
  { key: 'reference_name', label: 'مرجع' },
  { key: 'note', label: 'شرح' },
  { key: 'entry_date', label: 'زمان' },
]

async function loadWallets() {
  walletsLoading.value = true
  try {
    const payload = await listManagementWallets({ search: walletSearch.value })
    wallets.value = payload?.wallets || []
  } catch (err) {
    wallets.value = []
  } finally {
    walletsLoading.value = false
  }
}

function openWalletAction(mode, walletRow) {
  walletActionError.value = ''
  walletAction.value = {
    mode,
    customer: walletRow.customer,
    customer_name: walletRow.customer_name,
    to_customer: '',
    amount: null,
    direction: 'واریز',
    note: '',
  }
}

async function submitWalletAction() {
  const form = walletAction.value
  if (!form || !form.amount || form.amount <= 0) {
    walletActionError.value = 'مبلغ معتبر وارد کنید.'
    return
  }
  walletActionSaving.value = true
  walletActionError.value = ''
  try {
    if (form.mode === 'charge') {
      await chargeManagementWallet({ customer: form.customer, amount: form.amount, note: form.note })
    } else if (form.mode === 'transfer') {
      if (!form.to_customer) throw new Error('مشتری مقصد را انتخاب کنید.')
      await transferManagementWallet({ from_customer: form.customer, to_customer: form.to_customer, amount: form.amount, note: form.note })
    } else {
      await adjustManagementWallet({ customer: form.customer, amount: form.direction === 'برداشت' ? -Math.abs(form.amount) : form.amount, note: form.note })
    }
    walletAction.value = null
    await loadWallets()
    await loadBoot()
  } catch (err) {
    walletActionError.value = err.message || 'ثبت تراکنش ناموفق بود.'
  } finally {
    walletActionSaving.value = false
  }
}

async function openWalletDetail(customer) {
  walletDetailMessage.value = ''
  try {
    walletDetail.value = await getManagementWalletDetail(customer)
  } catch (err) {
    walletDetail.value = null
  }
}

// --------------------------------------------------------------------------
// Referral
// --------------------------------------------------------------------------
const referral = ref(null)
const referralSaving = ref(false)
const referralError = ref('')
const referralMessage = ref('')
const referralTopColumns = [
  { key: 'customer_name', label: 'سفیر' },
  { key: 'count', label: 'تعداد معرفی' },
]

async function loadReferral() {
  try {
    referral.value = await getManagementReferralSummary()
  } catch (err) {
    referralError.value = err.message || 'دریافت خلاصه معرف‌ها ناموفق بود.'
  }
}

async function saveReferralSettings() {
  referralSaving.value = true
  referralError.value = ''
  referralMessage.value = ''
  try {
    await updateManagementClubSettings({
      restaurant_referral_referrer_reward: referral.value.settings.referrer_reward,
      restaurant_referral_referee_reward: referral.value.settings.referee_reward,
    })
    referralMessage.value = 'پاداش‌های معرف ذخیره شد.'
  } catch (err) {
    referralError.value = err.message || 'ذخیره ناموفق بود.'
  } finally {
    referralSaving.value = false
  }
}

// --------------------------------------------------------------------------
// Campaigns & coupons
// --------------------------------------------------------------------------
const campaigns = ref([])
const campaignsLoading = ref(false)
const campaignFilters = reactive({ status: '' })
const campaignForm = ref(null)
const campaignFormError = ref('')
const campaignSaving = ref(false)
const campaignStats = ref(null)
const coupons = ref([])
const couponForm = ref(null)
const couponFormError = ref('')
const couponSaving = ref(false)
const campaignColumns = [
  { key: 'title', label: 'عنوان' },
  { key: 'coupon', label: 'کوپن' },
  { key: 'channels', label: 'کانال‌ها' },
  { key: 'validity', label: 'بازه' },
  { key: 'bonus', label: 'پاداش' },
  { key: 'status', label: 'وضعیت' },
  { key: 'actions', label: 'عملیات' },
]
const couponColumns = [
  { key: 'coupon_code', label: 'کد' },
  { key: 'title', label: 'عنوان' },
  { key: 'discount', label: 'تخفیف' },
  { key: 'min_order_amount', label: 'حداقل سفارش' },
  { key: 'usage_limit', label: 'سقف استفاده' },
  { key: 'used_count', label: 'مصرف‌شده' },
  { key: 'is_active', label: 'وضعیت' },
  { key: 'actions', label: 'عملیات' },
]

async function loadCampaigns() {
  campaignsLoading.value = true
  try {
    const payload = await listManagementCampaigns({ status: campaignFilters.status })
    campaigns.value = payload?.campaigns || []
  } catch (err) {
    campaigns.value = []
  } finally {
    campaignsLoading.value = false
  }
}

async function loadCoupons() {
  try {
    const payload = await listManagementCoupons({ include_inactive: 1 })
    coupons.value = payload?.coupons || []
  } catch (err) {
    coupons.value = []
  }
}

function openCampaignForm(c = null) {
  campaignFormError.value = ''
  campaignForm.value = c
    ? { name: c.name, title: c.title, coupon: c.coupon || '', channels: c.channels || '', bonus_type: c.bonus_type || 'کش‌بک', bonus_value: c.bonus_value || 0, valid_from: c.valid_from || '', valid_to: c.valid_to || '', target_segment: c.target_segment || '', min_order_amount: c.min_order_amount || 0, sms_text: c.sms_text || '', notes: c.notes || '' }
    : { name: '', title: '', coupon: '', channels: '', bonus_type: 'کش‌بک', bonus_value: 0, valid_from: '', valid_to: '', target_segment: '', min_order_amount: 0, sms_text: '', notes: '' }
}

async function saveCampaign() {
  campaignSaving.value = true
  campaignFormError.value = ''
  try {
    await saveManagementCampaign(campaignForm.value)
    campaignForm.value = null
    await loadCampaigns()
    await loadBoot()
  } catch (err) {
    campaignFormError.value = err.message || 'ذخیره کمپین ناموفق بود.'
  } finally {
    campaignSaving.value = false
  }
}

async function toggleCampaignStatus(c) {
  try {
    await updateManagementCampaignStatus({ name: c.name, status: c.status === 'فعال' ? 'متوقف' : 'فعال' })
    await loadCampaigns()
  } catch (err) {}
}

async function showCampaignStats(c) {
  try {
    campaignStats.value = await getManagementCampaignStats(c.name)
  } catch (err) {
    campaignStats.value = null
  }
}

function openCouponForm(cp = null) {
  couponFormError.value = ''
  couponForm.value = cp
    ? { name: cp.name, coupon_code: cp.coupon_code, title: cp.title || '', discount_type: cp.discount_type || 'Percent', discount_value: cp.discount_value || 0, min_order_amount: cp.min_order_amount || 0, max_discount_amount: cp.max_discount_amount || 0, valid_from: cp.valid_from || '', valid_to: cp.valid_to || '', usage_limit: cp.usage_limit || 0, is_active: !!cp.is_active }
    : { name: '', coupon_code: '', title: '', discount_type: 'Percent', discount_value: 10, min_order_amount: 0, max_discount_amount: 0, valid_from: '', valid_to: '', usage_limit: 0, is_active: true }
}

async function saveCoupon() {
  couponSaving.value = true
  couponFormError.value = ''
  try {
    await saveManagementCoupon({ ...couponForm.value, is_active: couponForm.value.is_active ? 1 : 0 })
    couponForm.value = null
    await loadCoupons()
  } catch (err) {
    couponFormError.value = err.message || 'ذخیره کوپن ناموفق بود.'
  } finally {
    couponSaving.value = false
  }
}

// --------------------------------------------------------------------------
// Settings
// --------------------------------------------------------------------------
const settingsForm = ref(null)
const settingsSaving = ref(false)
const settingsError = ref('')
const settingsMessage = ref('')

async function saveSettings() {
  settingsSaving.value = true
  settingsError.value = ''
  settingsMessage.value = ''
  try {
    await updateManagementClubSettings({
      restaurant_club_enabled: settingsForm.value.restaurant_club_enabled ? 1 : 0,
      restaurant_cashback_percent: settingsForm.value.restaurant_cashback_percent,
      restaurant_cashback_min_order: settingsForm.value.restaurant_cashback_min_order,
      restaurant_wallet_mode_of_payment: settingsForm.value.restaurant_wallet_mode_of_payment,
      restaurant_survey_alert_threshold: settingsForm.value.restaurant_survey_alert_threshold,
      restaurant_points_enabled: settingsForm.value.restaurant_points_enabled ? 1 : 0,
      restaurant_points_rial_per_point: settingsForm.value.restaurant_points_rial_per_point,
      restaurant_points_rial_value: settingsForm.value.restaurant_points_rial_value,
      restaurant_points_expiry_days: settingsForm.value.restaurant_points_expiry_days,
      restaurant_points_min_redeem: settingsForm.value.restaurant_points_min_redeem,
      restaurant_points_gold_threshold: settingsForm.value.restaurant_points_gold_threshold,
      restaurant_points_silver_threshold: settingsForm.value.restaurant_points_silver_threshold,
      restaurant_points_bronze_threshold: settingsForm.value.restaurant_points_bronze_threshold,
    })
    settingsMessage.value = 'تنظیمات وفاداری ذخیره شد.'
  } catch (err) {
    settingsError.value = err.message || 'ذخیره تنظیمات ناموفق بود.'
  } finally {
    settingsSaving.value = false
  }
}

// --------------------------------------------------------------------------
// SMS class stats (منشور ارتباط با مشتری)
// --------------------------------------------------------------------------
const smsKindStats = ref(null)
const smsKindStatsLoading = ref(false)
const smsKindStatsColumns = [
  { key: 'kind', label: 'نوع پیامک' },
  { key: 'class_label', label: 'کلاس' },
  { key: 'total', label: 'کل' },
  { key: 'sent', label: 'ارسال‌شده' },
  { key: 'failed', label: 'ناموفق' },
  { key: 'queued', label: 'در صف' },
  { key: 'success_rate', label: 'نرخ موفقیت' },
]
const smsKindStatsRows = computed(() => (smsKindStats.value?.classes || []).flatMap((cls) => (
  (cls.kinds || []).map((kind) => ({
    ...kind,
    class_label: cls.class,
    row_key: `${cls.class}-${kind.kind}`,
  }))
)))

async function loadSmsKindStats() {
  smsKindStatsLoading.value = true
  try {
    smsKindStats.value = await getManagementSmsKindStats({})
  } catch (err) {
    smsKindStats.value = null
  } finally {
    smsKindStatsLoading.value = false
  }
}

// --------------------------------------------------------------------------
// Customer voice (صدای مشتری: شکایت/پیشنهاد)
// --------------------------------------------------------------------------
const voices = ref([])
const voicesLoading = ref(false)
const voicesError = ref('')
const voicesMessage = ref('')
const voiceSummary = ref({ by_type: {}, by_status: {} })
const voiceFilters = reactive({ type: '', status: '', search: '', date_from: '', date_to: '' })
const voiceForm = ref(null)
const voiceFormError = ref('')
const voiceFormSaving = ref(false)
const voiceReply = ref(null)
const voiceReplySaving = ref(false)
const voiceColumns = [
  { key: 'type', label: 'نوع' },
  { key: 'subject', label: 'موضوع' },
  { key: 'customer', label: 'مشتری' },
  { key: 'message', label: 'پیام' },
  { key: 'status', label: 'وضعیت' },
  { key: 'response', label: 'پاسخ' },
  { key: 'actions', label: 'عملیات' },
]
const voiceCustomerKinds = computed(() => boot.value?.settings?.voice_types || ['شکایت', 'انتقاد', 'پیشنهاد', 'درخواست', 'تقدیر'])
const voiceStatusesList = computed(() => boot.value?.settings?.voice_statuses || ['جدید', 'در حال رسیدگی', 'پاسخ داده‌شده', 'بسته'])

async function loadVoices() {
  voicesLoading.value = true
  voicesError.value = ''
  try {
    const payload = await listManagementCustomerVoices({ ...voiceFilters })
    voices.value = payload.voices || []
    voiceSummary.value = payload.summary || { by_type: {}, by_status: {} }
  } catch (err) {
    voicesError.value = err.message || 'دریافت صدای مشتری ناموفق بود.'
    voices.value = []
  } finally {
    voicesLoading.value = false
  }
}

function openVoiceForm(voice) {
  voiceFormError.value = ''
  voiceForm.value = voice
    ? { name: voice.name, type: voice.type, subject: voice.subject, message: voice.message, customer_name: voice.customer_name, mobile: voice.mobile }
    : { name: '', type: 'شکایت', subject: '', message: '', customer_name: '', mobile: '' }
}

async function saveVoice() {
  if (!voiceForm.value) return
  voiceFormSaving.value = true
  voiceFormError.value = ''
  try {
    await saveManagementCustomerVoice({ ...voiceForm.value })
    voicesMessage.value = 'پیام ثبت شد.'
    voiceForm.value = null
    await loadVoices()
  } catch (err) {
    voiceFormError.value = err.message || 'ثبت پیام ناموفق بود.'
  } finally {
    voiceFormSaving.value = false
  }
}

function openVoiceReply(voice) {
  voiceReply.value = { name: voice.name, status: voice.status, response: voice.response || '' }
}

async function saveVoiceReply() {
  if (!voiceReply.value) return
  voiceReplySaving.value = true
  try {
    await updateManagementCustomerVoiceStatus({ ...voiceReply.value })
    voiceReply.value = null
    await loadVoices()
  } catch (err) {
    voicesError.value = err.message || 'ثبت پاسخ ناموفق بود.'
  } finally {
    voiceReplySaving.value = false
  }
}

async function removeVoice(voice) {
  if (!window.confirm(`پیام «${voice.subject}» حذف شود؟`)) return
  try {
    await deleteManagementCustomerVoice(voice.name)
    await loadVoices()
  } catch (err) {
    voicesError.value = err.message || 'حذف ناموفق بود.'
  }
}

const voicePublicUrl = computed(() => `${window.location.origin}/voice`)

// --------------------------------------------------------------------------
// Loyalty points (امتیاز وفاداری)
// --------------------------------------------------------------------------
const redeemForm = ref(null)
const redeemSaving = ref(false)
const redeemError = ref('')

function openRedeemForm(customer) {
  redeemError.value = ''
  redeemForm.value = { customer, points: 0 }
}

async function saveRedeem() {
  if (!redeemForm.value) return
  redeemSaving.value = true
  redeemError.value = ''
  try {
    const payload = await redeemManagementPoints({ customer: redeemForm.value.customer, points: Number(redeemForm.value.points || 0) })
    walletDetailMessage.value = `${formatQty(payload.points_used)} امتیاز به ${formatMoneyValue(payload.amount_credited)} اعتبار تبدیل شد.`
    redeemForm.value = null
    if (walletDetail.value?.wallet?.customer) await openWalletDetail(walletDetail.value.wallet.customer)
  } catch (err) {
    redeemError.value = err.message || 'تبدیل امتیاز ناموفق بود.'
  } finally {
    redeemSaving.value = false
  }
}

// --------------------------------------------------------------------------
// Organizations (سازمان‌ها: قرارداد، معین، اعتبار، فاکتور تجمیعی)
// --------------------------------------------------------------------------
const orgContractColumns = [
  { key: 'organization_label', label: 'سازمان' },
  { key: 'contract_no', label: 'قرارداد' },
  { key: 'daily_order_cap', label: 'سقف روزانه' },
  { key: 'monthly_order_cap', label: 'سقف ماهانه' },
  { key: 'allowed_schedule', label: 'روزها/ساعات مجاز' },
  { key: 'invoice_mode', label: 'صدور فاکتور' },
  { key: 'status', label: 'وضعیت' },
  { key: 'actions', label: 'عملیات' },
]
const orgMemberColumns = [
  { key: 'member', label: 'معین' },
  { key: 'organization_label', label: 'سازمان' },
  { key: 'username', label: 'نام کاربری' },
  { key: 'daily_cap', label: 'سقف روزانه' },
  { key: 'monthly_cap', label: 'سقف ماهانه' },
  { key: 'is_active', label: 'وضعیت' },
  { key: 'actions', label: 'عملیات' },
]
const orgCreditMemberColumns = [
  { key: 'member', label: 'معین' },
  { key: 'day_usage', label: 'مصرف امروز' },
  { key: 'month_usage', label: 'مصرف ماه' },
  { key: 'uninvoiced', label: 'فاکتورنشده' },
]
const orgOrderColumns = [
  { key: 'select', label: '' },
  { key: 'name', label: 'کد سفارش' },
  { key: 'date', label: 'تاریخ' },
  { key: 'org_member', label: 'معین' },
  { key: 'grand_total', label: 'مبلغ' },
  { key: 'status', label: 'وضعیت' },
  { key: 'org_invoice', label: 'فاکتور' },
]
const orgBoot = ref({ kpis: {}, weekdays: [], invoice_modes: [], contract_statuses: [] })
const orgContracts = ref([])
const orgMembers = ref([])
const orgLoading = ref(false)
const orgError = ref('')
const orgMessage = ref('')
const contractForm = ref(null)
const contractFormError = ref('')
const contractFormSaving = ref(false)
const memberForm = ref(null)
const memberFormError = ref('')
const memberFormSaving = ref(false)
const selectedOrg = ref('')
const orgCredit = ref(null)
const orgOrders = ref([])
const orgOrdersLoading = ref(false)
const orgOrderFilters = reactive({ date_from: '', date_to: '', invoiced: '', member: '', search: '' })
const orgInvoiceBusy = ref(false)
const selectedOrgOrders = ref({})

async function loadOrgBoot() {
  try {
    orgBoot.value = await getManagementOrgBoot()
  } catch (err) {
    orgError.value = err.message || 'دریافت اطلاعات سازمان‌ها ناموفق بود.'
  }
}

async function loadOrgContracts() {
  orgLoading.value = true
  orgError.value = ''
  try {
    const payload = await listManagementOrgContracts({})
    orgContracts.value = payload.contracts || []
  } catch (err) {
    orgError.value = err.message || 'دریافت قراردادها ناموفق بود.'
  } finally {
    orgLoading.value = false
  }
}

async function loadOrgMembers(organization) {
  try {
    const payload = await listManagementOrgMembers({ organization: organization || '' })
    orgMembers.value = payload.members || []
  } catch (err) {
    orgError.value = err.message || 'دریافت معین‌ها ناموفق بود.'
  }
}

function openContractForm(contract) {
  contractFormError.value = ''
  contractForm.value = contract
    ? { ...contract, portal_access_code: '', allowed_days: [...(contract.allowed_days || [])], allowed_addresses: [...(contract.allowed_addresses || [])] }
    : {
        name: '', organization: '', contract_no: '', start_date: '', end_date: '', status: 'فعال',
        daily_order_cap: 0, monthly_order_cap: 0, allowed_days: [], allowed_from_hour: 0, allowed_to_hour: 0,
        restrict_addresses: 0, allowed_addresses: [], invoice_mode: 'ماهانه', portal_access_code: '', note: '', new_address: '',
      }
}

function toggleContractDay(day) {
  const days = contractForm.value.allowed_days
  const idx = days.indexOf(day)
  if (idx >= 0) days.splice(idx, 1)
  else days.push(day)
}

function addContractAddress() {
  const addr = (contractForm.value.new_address || '').trim()
  if (!addr) return
  if (!contractForm.value.allowed_addresses.includes(addr)) contractForm.value.allowed_addresses.push(addr)
  contractForm.value.new_address = ''
}

async function saveContract() {
  if (!contractForm.value) return
  contractFormSaving.value = true
  contractFormError.value = ''
  try {
    await saveManagementOrgContract({ ...contractForm.value })
    contractForm.value = null
    orgMessage.value = 'قرارداد ذخیره شد.'
    await loadOrgContracts()
    await loadOrgBoot()
  } catch (err) {
    contractFormError.value = err.message || 'ذخیره قرارداد ناموفق بود.'
  } finally {
    contractFormSaving.value = false
  }
}

async function removeContract(contract) {
  if (!window.confirm(`قرارداد «${contract.contract_no || contract.name}» حذف شود؟`)) return
  try {
    await deleteManagementOrgContract(contract.name)
    if (selectedOrg.value === contract.organization) { selectedOrg.value = ''; orgCredit.value = null; orgOrders.value = [] }
    await loadOrgContracts()
    await loadOrgBoot()
  } catch (err) {
    orgError.value = err.message || 'حذف قرارداد ناموفق بود.'
  }
}

function openMemberForm(member, organization) {
  memberFormError.value = ''
  memberForm.value = member
    ? { ...member, access_code: '' }
    : { name: '', organization: organization || selectedOrg.value || '', full_name: '', mobile: '', username: '', access_code: '', role_title: '', daily_cap: 0, monthly_cap: 0, is_active: 1, member_customer: '' }
}

async function saveMember() {
  if (!memberForm.value) return
  memberFormSaving.value = true
  memberFormError.value = ''
  try {
    await saveManagementOrgMember({ ...memberForm.value })
    memberForm.value = null
    orgMessage.value = 'معین ذخیره شد.'
    await loadOrgMembers()
    await loadOrgBoot()
    if (selectedOrg.value) await selectOrg(selectedOrg.value)
  } catch (err) {
    memberFormError.value = err.message || 'ذخیره معین ناموفق بود.'
  } finally {
    memberFormSaving.value = false
  }
}

async function removeMember(member) {
  if (!window.confirm(`معین «${member.full_name}» حذف شود؟`)) return
  try {
    await deleteManagementOrgMember(member.name)
    await loadOrgMembers()
  } catch (err) {
    orgError.value = err.message || 'حذف معین ناموفق بود.'
  }
}

async function selectOrg(organization) {
  selectedOrg.value = organization
  orgCredit.value = null
  orgOrders.value = []
  selectedOrgOrders.value = {}
  try {
    orgCredit.value = await getManagementOrgCredit(organization)
    await loadOrgOrders()
  } catch (err) {
    orgError.value = err.message || 'دریافت اعتبار سازمان ناموفق بود.'
  }
}

async function loadOrgOrders() {
  if (!selectedOrg.value) return
  orgOrdersLoading.value = true
  try {
    const payload = await listManagementOrgOrders({ organization: selectedOrg.value, ...orgOrderFilters })
    orgOrders.value = payload.orders || []
  } catch (err) {
    orgError.value = err.message || 'دریافت سفارش‌ها ناموفق بود.'
  } finally {
    orgOrdersLoading.value = false
  }
}

async function exportOrgExcel() {
  if (!selectedOrg.value) return
  orgInvoiceBusy.value = true
  try {
    const payload = await exportManagementOrgOrdersExcel({ organization: selectedOrg.value, ...orgOrderFilters })
    if (payload.file_url) window.open(payload.file_url, '_blank')
    orgMessage.value = `خروجی اکسل (${formatQty(payload.rows)} سفارش) آماده شد.`
  } catch (err) {
    orgError.value = err.message || 'خروجی اکسل ناموفق بود.'
  } finally {
    orgInvoiceBusy.value = false
  }
}

const selectedOrgOrderNames = computed(() => Object.keys(selectedOrgOrders.value).filter((k) => selectedOrgOrders.value[k]))

async function issueConsolidatedInvoice() {
  if (!selectedOrg.value || !selectedOrgOrderNames.value.length) return
  if (!window.confirm(`فاکتور تجمیعی برای ${formatQty(selectedOrgOrderNames.value.length)} سفارش صادر شود؟`)) return
  orgInvoiceBusy.value = true
  try {
    const payload = await createManagementOrgInvoice({ organization: selectedOrg.value, order_names: selectedOrgOrderNames.value })
    orgMessage.value = `فاکتور ${payload.sales_invoice} (${formatMoneyValue(payload.grand_total)}) صادر شد.`
    selectedOrgOrders.value = {}
    await loadOrgOrders()
    await selectOrg(selectedOrg.value)
  } catch (err) {
    orgError.value = err.message || 'صدور فاکتور تجمیعی ناموفق بود.'
  } finally {
    orgInvoiceBusy.value = false
  }
}

const orgPublicUrl = computed(() => `${window.location.origin}/org`)

// --------------------------------------------------------------------------
onMounted(async () => {
  await loadBoot()
  loadedTabs.customers = true
  await loadCustomers()
})
</script>

<style scoped>
.boot-kpis {
  margin-bottom: 0.9rem;
}
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.75rem;
}
.toolbar .input {
  width: auto;
  min-width: 150px;
  flex: 0 1 auto;
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
  align-items: center;
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
}
.data-table th {
  color: var(--text-muted, #6b7a72);
  font-weight: 600;
  white-space: nowrap;
}
.data-table tr.inactive td {
  opacity: 0.55;
}
.row-actions {
  white-space: nowrap;
}
.sms-cell {
  max-width: 260px;
}
.d-block {
  display: block;
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
  width: min(680px, 100%);
  max-height: 88vh;
  overflow-y: auto;
  display: grid;
  gap: 0.65rem;
}
.popup.wide {
  width: min(860px, 100%);
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
.success-msg {
  color: var(--accent-green, #2f6f5c);
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
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}
.points-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  background: rgba(47, 111, 92, 0.07);
  border: 1px solid rgba(47, 111, 92, 0.22);
  border-radius: 12px;
  padding: 0.7rem 0.9rem;
  margin: 0.7rem 0;
  flex-wrap: wrap;
}
.points-value {
  font-size: 1.2rem;
  color: #2f6f5c;
  margin: 0 0.35rem;
}
.day-chip {
  display: inline-block;
  padding: 0.3rem 0.75rem;
  border-radius: 999px;
  border: 1px solid rgba(90, 74, 58, 0.25);
  font-size: 0.8rem;
  cursor: pointer;
  user-select: none;
  background: #fff;
}
.day-chip.sel {
  background: #2f6f5c;
  border-color: #2f6f5c;
  color: #fff;
}
.days-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.35rem;
}
.address-adder {
  display: flex;
  gap: 0.5rem;
  margin: 0.4rem 0;
}
.date-label {
  display: inline-flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.8rem;
  color: #6b5f52;
}
.link-code {
  direction: ltr;
  display: inline-block;
  background: rgba(90, 74, 58, 0.08);
  border-radius: 6px;
  padding: 0.1rem 0.45rem;
  font-size: 0.8rem;
}
@media (max-width: 720px) {
  .toolbar .input {
    flex: 1 1 100%;
    min-width: 100%;
  }
}
</style>
