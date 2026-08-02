<template>
  <ManagementPageScaffold title="انبارداری هوشمند" subtitle="مواد اولیه، انبارها، موجودی، خرید، تولید، ضایعات و انبارگردانی">
    <template #actions>
      <button type="button" class="secondary-btn" @click="reloadActiveTab" :disabled="loadingAny">
        {{ loadingAny ? 'در حال بروزرسانی...' : 'بروزرسانی' }}
      </button>
    </template>

    <div v-if="boot" class="totals-grid boot-kpis">
      <div class="total-box"><small>مواد اولیه</small><strong>{{ formatQty(boot.kpis.materials_total) }}</strong></div>
      <div class="total-box"><small>انبارها</small><strong>{{ formatQty(boot.kpis.warehouses_total) }}</strong></div>
      <div class="total-box" :class="{ 'warn-border': boot.kpis.below_reorder > 0 }">
        <small>زیر نقطه سفارش</small><strong :class="boot.kpis.below_reorder > 0 ? 'warn-text' : 'ok-text'">{{ formatQty(boot.kpis.below_reorder) }}</strong>
      </div>
      <div class="total-box"><small>ارزش موجودی</small><strong>{{ formatMoneyValue(boot.kpis.stock_value_total) }}</strong></div>
      <div class="total-box"><small>ضایعات/خسارت ۳۰ روز</small><strong>{{ formatMoneyValue(boot.kpis.waste_damage_30d_value) }}</strong></div>
      <div class="total-box"><small>خریدهای باز</small><strong>{{ formatQty(boot.kpis.open_purchase_orders) }}</strong></div>
    </div>

    <nav class="tabs-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        type="button"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="setActiveTab(tab.key)"
      >
        {{ tab.label }}
        <span v-if="tab.key === 'reorder' && boot && boot.kpis.below_reorder > 0" class="badge">{{ formatQty(boot.kpis.below_reorder) }}</span>
      </button>
    </nav>

    <!-- ======================= موجودی و ارزش ======================= -->
    <section v-if="activeTab === 'overview'" class="tab-body">
      <p class="error" v-if="overviewError">{{ overviewError }}</p>
      <ManagementSurfaceCard title="کنترل موجودی انبارها" subtitle="موجودی مقداری و مبلغی اقلام، به تفکیک انبار">
        <div class="toolbar">
          <select class="input" v-model="overviewFilters.warehouse" @change="loadOverview">
            <option value="">همه انبارها</option>
            <option v-for="wh in leafWarehouses" :key="wh" :value="wh">{{ wh }}</option>
          </select>
          <input class="input" v-model.trim="overviewFilters.search" placeholder="جستجوی کد یا نام کالا..." @keyup.enter="loadOverview" />
          <label class="check-row"><input type="checkbox" v-model="overviewFilters.only_materials" @change="loadOverview" /> فقط مواد اولیه</label>
          <button type="button" class="secondary-btn" @click="loadOverview" :disabled="overviewLoading">{{ overviewLoading ? '...' : 'جستجو' }}</button>
        </div>
        <div class="totals-grid" v-if="overview">
          <div class="total-box"><small>تعداد اقلام</small><strong>{{ formatQty(overview.total_items) }}</strong></div>
          <div class="total-box"><small>مجموع مقدار</small><strong>{{ formatQty(overview.total_qty) }}</strong></div>
          <div class="total-box"><small>ارزش ریالی موجودی</small><strong>{{ formatMoneyValue(overview.total_value) }}</strong></div>
        </div>
        <p class="muted" v-if="overviewLoading">در حال دریافت موجودی...</p>
        <div v-else-if="overview && overview.items.length" class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>کالا</th><th v-if="!overviewFilters.warehouse">انبار</th><th>مقدار</th><th>نرخ</th><th>ارزش</th></tr>
            </thead>
            <tbody>
              <template v-for="row in overview.items" :key="row.item_code">
                <tr v-if="overviewFilters.warehouse">
                  <td><strong>{{ row.item_name }}</strong><br><small class="muted">{{ row.item_code }}</small></td>
                  <td>{{ formatQty(row.qty) }} {{ row.stock_uom }}</td>
                  <td>{{ formatMoneyValue(row.rate) }}</td>
                  <td>{{ formatMoneyValue(row.value) }}</td>
                </tr>
                <template v-else>
                  <tr>
                    <td><strong>{{ row.item_name }}</strong><br><small class="muted">{{ row.item_code }}</small></td>
                    <td>{{ warehouseKeys(row).length }} انبار</td>
                    <td>{{ formatQty(row.qty) }} {{ row.stock_uom }}</td>
                    <td>{{ formatMoneyValue(row.rate) }}</td>
                    <td>{{ formatMoneyValue(row.value) }}</td>
                  </tr>
                  <tr v-for="wh in warehouseKeys(row)" :key="row.item_code + wh" class="sub-row">
                    <td colspan="2" class="muted">↳ {{ wh }}</td>
                    <td>{{ formatQty(row.warehouses[wh].qty) }}</td>
                    <td>{{ formatMoneyValue(row.warehouses[wh].rate) }}</td>
                    <td>{{ formatMoneyValue(row.warehouses[wh].value) }}</td>
                  </tr>
                </template>
              </template>
            </tbody>
          </table>
        </div>
        <p class="muted" v-else>موردی یافت نشد.</p>
      </ManagementSurfaceCard>
    </section>

    <!-- ======================= مواد اولیه ======================= -->
    <section v-if="activeTab === 'materials'" class="tab-body">
      <p class="error" v-if="materialsError">{{ materialsError }}</p>
      <p class="success-msg" v-if="materialsMessage">{{ materialsMessage }}</p>
      <ManagementSurfaceCard title="مواد اولیه" subtitle="ثبت نامحدود مواد اولیه، نقطه سفارش و تأمین‌کننده پیش‌فرض">
        <div class="toolbar">
          <input class="input" v-model.trim="materialsSearch" placeholder="جستجو..." @keyup.enter="loadMaterials" />
          <label class="check-row"><input type="checkbox" v-model="materialsShowInactive" @change="loadMaterials" /> نمایش غیرفعال‌ها</label>
          <button type="button" class="secondary-btn" @click="loadMaterials" :disabled="materialsLoading">{{ materialsLoading ? '...' : 'جستجو' }}</button>
          <button type="button" class="secondary-btn" @click="exportMaterialsExcel" :disabled="materialExcelBusy">
            {{ materialExcelBusy && materialExcelMode === 'export' ? 'در حال آماده‌سازی...' : 'خروجی اکسل' }}
          </button>
          <button type="button" class="secondary-btn" @click="triggerMaterialExcelImport" :disabled="materialExcelBusy">
            {{ materialExcelBusy && materialExcelMode === 'import' ? 'در حال ورود...' : 'ورود از اکسل' }}
          </button>
          <input ref="materialExcelInput" type="file" class="visually-hidden" accept=".xlsx,.xls,.csv" @change="handleMaterialExcelFile" />
          <button type="button" class="primary-btn" @click="openMaterialForm()">+ ماده اولیه جدید</button>
        </div>
        <div v-if="materialExcelSummary" class="inline-form">
          <strong>نتیجه ورود از اکسل:</strong>
          <span>ساخته‌شده: {{ formatQty(materialExcelSummary.created) }} • به‌روزشده: {{ formatQty(materialExcelSummary.updated) }} • ردشده: {{ formatQty(materialExcelSummary.skipped) }}</span>
          <ul v-if="materialExcelSummary.errors && materialExcelSummary.errors.length" class="error-list">
            <li v-for="err in materialExcelSummary.errors.slice(0, 6)" :key="err.row">سطر {{ formatQty(err.row) }} ({{ err.item_code || '—' }}): {{ err.message }}</li>
          </ul>
          <button type="button" class="tertiary-btn" @click="materialExcelSummary = null">بستن</button>
        </div>
        <p class="muted" v-if="materialsLoading">در حال دریافت...</p>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>ماده اولیه</th><th>گروه</th><th>موجودی</th><th>ارزش</th><th>نقطه سفارش</th><th>تأمین‌کننده</th><th></th></tr>
            </thead>
            <tbody>
              <tr v-for="row in materials" :key="row.name" :class="{ inactive: row.disabled }">
                <td>
                  <strong>{{ row.item_name }}</strong> <span v-if="row.below_reorder" class="badge warn">کمبود</span><br>
                  <small class="muted">{{ row.name }}</small>
                </td>
                <td>{{ row.item_group }}</td>
                <td>{{ formatQty(row.qty) }} {{ row.stock_uom }}</td>
                <td>{{ formatMoneyValue(row.value) }}</td>
                <td>
                  <template v-if="row.reorder_levels.length">
                    <span v-for="rl in row.reorder_levels.slice(0, 2)" :key="row.name + rl.warehouse" class="pill">{{ rl.warehouse }}: {{ formatQty(rl.level) }}</span>
                  </template>
                  <span v-else class="muted">—</span>
                </td>
                <td>{{ row.default_supplier || '—' }}</td>
                <td><button type="button" class="tertiary-btn" @click="openMaterialForm(row)">ویرایش</button></td>
              </tr>
              <tr v-if="!materials.length"><td colspan="7" class="muted">ماده اولیه‌ای ثبت نشده است.</td></tr>
            </tbody>
          </table>
        </div>
        <div class="btn-row" v-if="materialsHasMore">
          <button type="button" class="secondary-btn" @click="loadMoreMaterials">بارگذاری بیشتر</button>
        </div>
      </ManagementSurfaceCard>

      <div v-if="materialForm" class="popup-backdrop" @click.self="materialForm = null">
        <div class="popup">
          <h3>{{ materialForm.name ? 'ویرایش ماده اولیه' : 'ماده اولیه جدید' }}</h3>
          <p class="error" v-if="materialFormError">{{ materialFormError }}</p>
          <div class="form-grid">
            <label>کد کالا
              <input class="input" v-model.trim="materialForm.item_code" :disabled="!!materialForm.name" placeholder="مثلاً RM-CHEESE" />
            </label>
            <label>نام ماده اولیه <span class="req">*</span>
              <input class="input" v-model.trim="materialForm.item_name" placeholder="مثلاً پنیر موزارلا" />
            </label>
            <label>گروه کالا
              <select class="input" v-model="materialForm.item_group">
                <option v-for="g in (boot ? boot.item_groups : [])" :key="g.name" :value="g.name">{{ g.name }}</option>
              </select>
            </label>
            <label>واحد اندازه‌گیری
              <input class="input" v-model.trim="materialForm.stock_uom" placeholder="Nos / Kg / Gram" />
            </label>
            <label>نرخ خرید (دفتری)
              <input class="input" type="number" min="0" v-model.number="materialForm.purchase_rate" />
            </label>
            <label>تأمین‌کننده پیش‌فرض
              <select class="input" v-model="materialForm.default_supplier">
                <option value="">بدون تأمین‌کننده</option>
                <option v-for="s in supplierOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
              </select>
            </label>
            <label class="check-row full-row"><input type="checkbox" v-model="materialForm.disabled" /> غیرفعال</label>
          </div>

          <template v-if="!materialForm.name">
            <h4>موجودی اولیه (اختیاری)</h4>
            <div class="form-grid">
              <label>انبار
                <select class="input" v-model="materialForm.opening.warehouse">
                  <option value="">—</option>
                  <option v-for="wh in leafWarehouses" :key="wh" :value="wh">{{ wh }}</option>
                </select>
              </label>
              <label>مقدار
                <input class="input" type="number" min="0" v-model.number="materialForm.opening.qty" />
              </label>
            </div>
          </template>

          <h4>نقطه سفارش به تفکیک انبار</h4>
          <div class="lines-editor">
            <div v-for="(rl, i) in materialForm.reorder_levels" :key="i" class="line-row">
              <select class="input" v-model="rl.warehouse">
                <option value="">انبار...</option>
                <option v-for="wh in leafWarehouses" :key="wh" :value="wh">{{ wh }}</option>
              </select>
              <input class="input" type="number" min="0" step="0.001" v-model.number="rl.level" placeholder="حداقل موجودی" />
              <input class="input" type="number" min="0" step="0.001" v-model.number="rl.request_qty" placeholder="مقدار پیشنهادی خرید" />
              <button type="button" class="tertiary-btn danger" @click="materialForm.reorder_levels.splice(i, 1)">حذف</button>
            </div>
            <button type="button" class="secondary-btn" @click="materialForm.reorder_levels.push({ warehouse: '', level: 0, request_qty: 0 })">+ افزودن نقطه سفارش</button>
          </div>

          <div class="btn-row">
            <button type="button" class="primary-btn" @click="saveMaterial" :disabled="materialSaving">{{ materialSaving ? 'در حال ذخیره...' : 'ذخیره' }}</button>
            <button type="button" class="secondary-btn" @click="materialForm = null">انصراف</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ======================= انبارها ======================= -->
    <section v-if="activeTab === 'warehouses'" class="tab-body">
      <p class="error" v-if="warehousesError">{{ warehousesError }}</p>
      <p class="success-msg" v-if="warehousesMessage">{{ warehousesMessage }}</p>
      <ManagementSurfaceCard title="انبارها" subtitle="تعریف نامحدود انبار (اصلی، آشپزخانه، نوشیدنی و...)">
        <div class="toolbar">
          <button type="button" class="primary-btn" @click="openWarehouseForm()">+ انبار جدید</button>
          <button type="button" class="secondary-btn" @click="loadWarehouses" :disabled="warehousesLoading">{{ warehousesLoading ? '...' : 'بروزرسانی' }}</button>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>انبار</th><th>والد</th><th>شرکت</th><th>موجودی (مقدار)</th><th>ارزش</th><th>وضعیت</th><th></th></tr>
            </thead>
            <tbody>
              <tr v-for="row in warehouses" :key="row.name" :class="{ inactive: row.disabled, group: row.is_group }">
                <td><strong>{{ row.warehouse_name }}</strong><br><small class="muted">{{ row.name }}</small></td>
                <td>{{ row.parent_warehouse || '—' }}</td>
                <td>{{ row.company }}</td>
                <td>{{ row.is_group ? '—' : formatQty(row.qty) }}</td>
                <td>{{ row.is_group ? '—' : formatMoneyValue(row.value) }}</td>
                <td>
                  <span v-if="row.is_group" class="pill">گروه</span>
                  <span v-if="row.disabled" class="pill warn">غیرفعال</span>
                  <span v-if="!row.is_group && !row.disabled" class="pill ok">فعال</span>
                </td>
                <td class="row-actions">
                  <button type="button" class="tertiary-btn" @click="openWarehouseForm(row)">ویرایش</button>
                  <button type="button" class="tertiary-btn danger" @click="removeWarehouse(row)">حذف</button>
                </td>
              </tr>
              <tr v-if="!warehouses.length"><td colspan="7" class="muted">انباری تعریف نشده است.</td></tr>
            </tbody>
          </table>
        </div>
      </ManagementSurfaceCard>

      <div v-if="warehouseForm" class="popup-backdrop" @click.self="warehouseForm = null">
        <div class="popup">
          <h3>{{ warehouseForm.name ? 'ویرایش انبار' : 'انبار جدید' }}</h3>
          <p class="error" v-if="warehouseFormError">{{ warehouseFormError }}</p>
          <div class="form-grid">
            <label>نام انبار <span class="req">*</span>
              <input class="input" v-model.trim="warehouseForm.warehouse_name" placeholder="مثلاً انبار آشپزخانه" />
            </label>
            <label>انبار والد (گروه)
              <select class="input" v-model="warehouseForm.parent_warehouse">
                <option value="">بدون والد</option>
                <option v-for="w in warehouses.filter((x) => x.is_group && x.name !== warehouseForm.name)" :key="w.name" :value="w.name">{{ w.warehouse_name }}</option>
              </select>
            </label>
            <label class="check-row"><input type="checkbox" v-model="warehouseForm.is_group" /> انبار گروهی است</label>
            <label class="check-row"><input type="checkbox" v-model="warehouseForm.disabled" /> غیرفعال</label>
          </div>
          <div class="btn-row">
            <button type="button" class="primary-btn" @click="saveWarehouse" :disabled="warehouseSaving">{{ warehouseSaving ? '...' : 'ذخیره' }}</button>
            <button type="button" class="secondary-btn" @click="warehouseForm = null">انصراف</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ======================= ورود و خروج ======================= -->
    <section v-if="activeTab === 'movements'" class="tab-body">
      <p class="error" v-if="movementsError">{{ movementsError }}</p>
      <p class="success-msg" v-if="movementsMessage">{{ movementsMessage }}</p>
      <ManagementSurfaceCard title="ثبت گردش جدید" subtitle="ورود، خروج، انتقال، ضایعات و خسارت با جزئیات کامل">
        <div class="form-grid">
          <label>نوع گردش
            <select class="input" v-model="movementForm.movement_type">
              <option value="receipt">ورود کالا (خرید/سایر)</option>
              <option value="issue">خروج کالا (مصرف/سایر)</option>
              <option value="transfer">انتقال بین انبارها</option>
              <option value="waste">ضایعات</option>
              <option value="damage">خسارت</option>
            </select>
          </label>
          <label v-if="movementForm.movement_type !== 'receipt'">انبار مبدأ
            <select class="input" v-model="movementForm.from_warehouse">
              <option value="">انتخاب...</option>
              <option v-for="wh in leafWarehouses" :key="wh" :value="wh">{{ wh }}</option>
            </select>
          </label>
          <label v-if="movementForm.movement_type === 'receipt' || movementForm.movement_type === 'transfer'">انبار مقصد
            <select class="input" v-model="movementForm.to_warehouse">
              <option value="">انتخاب...</option>
              <option v-for="wh in leafWarehouses" :key="wh" :value="wh">{{ wh }}</option>
            </select>
          </label>
          <label>تاریخ سند
            <input class="input" type="date" v-model="movementForm.posting_date" />
          </label>
          <label class="full-row">شرح گردش
            <input class="input" v-model.trim="movementForm.reason" placeholder="علت یا توضیح (اختیاری)" />
          </label>
        </div>
        <div class="lines-editor">
          <div v-for="(line, i) in movementForm.lines" :key="i" class="line-row">
            <SearchableDropdown v-model="line.item_code" :options="materialOptions" placeholder="کالا..." search-placeholder="جستجوی کالا..." />
            <input class="input" type="number" min="0.0001" step="0.001" v-model.number="line.qty" placeholder="مقدار" />
            <input class="input" type="number" min="0" v-model.number="line.rate" placeholder="نرخ (فقط ورود)" :disabled="movementForm.movement_type !== 'receipt'" />
            <button type="button" class="tertiary-btn danger" @click="movementForm.lines.splice(i, 1)" :disabled="movementForm.lines.length <= 1">حذف</button>
          </div>
        </div>
        <div class="btn-row">
          <button type="button" class="secondary-btn" @click="movementForm.lines.push({ item_code: '', qty: 1, rate: 0 })">+ افزودن قلم</button>
          <button type="button" class="primary-btn" @click="submitMovement" :disabled="movementSaving">{{ movementSaving ? 'در حال ثبت...' : 'ثبت گردش' }}</button>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="سوابق گردش‌ها" subtitle="تاریخچه ورود و خروج انبار">
        <div class="toolbar">
          <input class="input" type="date" v-model="movementFilters.date_from" />
          <input class="input" type="date" v-model="movementFilters.date_to" />
          <select class="input" v-model="movementFilters.warehouse">
            <option value="">همه انبارها</option>
            <option v-for="wh in leafWarehouses" :key="wh" :value="wh">{{ wh }}</option>
          </select>
          <select class="input" v-model="movementFilters.kind">
            <option value="">همه انواع</option>
            <option v-for="(label, key) in movementKinds" :key="key" :value="label">{{ label }}</option>
          </select>
          <button type="button" class="secondary-btn" @click="loadMovements" :disabled="movementsLoading">{{ movementsLoading ? '...' : 'جستجو' }}</button>
        </div>
        <p class="muted" v-if="movementsLoading">در حال دریافت...</p>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>تاریخ</th><th>کالا</th><th>انبار</th><th>تغییر مقدار</th><th>تغییر ارزش</th><th>نوع</th><th>سند</th></tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in movements" :key="i">
                <td>{{ row.posting_date }}<br><small class="muted">{{ row.posting_time }}</small></td>
                <td>{{ row.item_name }}<br><small class="muted">{{ row.item_code }}</small></td>
                <td>{{ row.warehouse }}</td>
                <td :class="row.qty_change >= 0 ? 'ok-text' : 'warn-text'">{{ row.qty_change >= 0 ? '+' : '' }}{{ formatQty(row.qty_change) }} {{ row.stock_uom }}</td>
                <td>{{ formatMoneyValue(row.value_change) }}</td>
                <td><span class="pill">{{ row.kind }}</span></td>
                <td>
                  {{ row.voucher }}
                  <br><small class="muted" v-if="row.note">{{ row.note }}</small>
                </td>
              </tr>
              <tr v-if="!movements.length"><td colspan="7" class="muted">گردشی ثبت نشده است.</td></tr>
            </tbody>
          </table>
        </div>
      </ManagementSurfaceCard>
    </section>

    <!-- ======================= نقطه سفارش ======================= -->
    <section v-if="activeTab === 'reorder'" class="tab-body">
      <p class="error" v-if="reorderError">{{ reorderError }}</p>
      <p class="success-msg" v-if="reorderMessage">{{ reorderMessage }}</p>
      <ManagementSurfaceCard title="هشدار نقطه سفارش" subtitle="اقلامی که موجودی‌شان به حداقل تعیین‌شده رسیده است">
        <div class="toolbar">
          <select class="input" v-model="reorderWarehouse" @change="loadReorderAlerts">
            <option value="">همه انبارها</option>
            <option v-for="wh in leafWarehouses" :key="wh" :value="wh">{{ wh }}</option>
          </select>
          <button type="button" class="secondary-btn" @click="loadReorderAlerts" :disabled="reorderLoading">{{ reorderLoading ? '...' : 'بروزرسانی' }}</button>
          <button type="button" class="primary-btn" @click="createPurchaseFromAlerts" :disabled="!selectedAlerts.length || reorderSaving">
            {{ reorderSaving ? '...' : `ایجاد پیش‌نویس خرید (${formatQty(selectedAlerts.length)})` }}
          </button>
        </div>
        <p class="muted" v-if="reorderLoading">در حال بررسی موجودی...</p>
        <template v-else-if="reorderAlerts.length">
          <div class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th><input type="checkbox" :checked="selectedAlerts.length === reorderAlerts.length" @change="toggleAllAlerts" /></th>
                  <th>کالا</th><th>انبار</th><th>موجودی</th><th>نقطه سفارش</th><th>پیشنهاد خرید</th><th>تأمین‌کننده</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in reorderAlerts" :key="row.item_code + row.warehouse" class="alert-row">
                  <td><input type="checkbox" :value="row" v-model="selectedAlerts" /></td>
                  <td>{{ row.item_name }}<br><small class="muted">{{ row.item_code }}</small></td>
                  <td>{{ row.warehouse }}</td>
                  <td class="warn-text">{{ formatQty(row.available) }} {{ row.stock_uom }}</td>
                  <td>{{ formatQty(row.level) }}</td>
                  <td>{{ formatQty(row.suggested_qty) }}</td>
                  <td>{{ row.default_supplier || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
        <p class="ok-text" v-else>همه مواد بالاتر از نقطه سفارش هستند. ✅</p>
      </ManagementSurfaceCard>
    </section>

    <!-- ======================= درخواست مواد ======================= -->
    <section v-if="activeTab === 'requests'" class="tab-body material-request-page">
      <p class="error" v-if="requestError">{{ requestError }}</p>
      <p class="success-msg" v-if="requestMessage">{{ requestMessage }}</p>

      <ManagementSurfaceCard title="درخواست مواد اولیه" subtitle="نیاز مواد را ثبت کنید، مقدار و واحد را ببینید و سپس به خرید منتقل کنید">
        <div class="request-toolbar">
          <select class="input" v-model="requestFilters.status" @change="loadMaterialRequests">
            <option value="">همه وضعیت‌ها</option>
            <option value="draft">پیش‌نویس</option>
            <option value="pending">در انتظار خرید</option>
            <option value="ordered">خرید کامل</option>
            <option value="cancelled">لغوشده</option>
          </select>
          <input class="input" type="date" v-model="requestFilters.date_from" @change="loadMaterialRequests" />
          <input class="input" type="date" v-model="requestFilters.date_to" @change="loadMaterialRequests" />
          <input class="input request-search" v-model.trim="requestFilters.search" placeholder="جستجوی شماره یا ماده..." @keyup.enter="loadMaterialRequests" />
          <button type="button" class="secondary-btn" @click="loadMaterialRequests" :disabled="requestLoading">{{ requestLoading ? '...' : 'جستجو' }}</button>
          <button type="button" class="primary-btn" @click="openMaterialRequestForm()">+ درخواست جدید</button>
        </div>

        <p class="muted" v-if="requestLoading">در حال دریافت درخواست‌ها...</p>
        <div v-else class="material-request-list">
          <article
            v-for="request in materialRequests"
            :key="request.name"
            class="material-request-card"
            @click="openMaterialRequestDetail(request.name)"
          >
            <header class="material-request-card-head">
              <div>
                <strong>{{ request.name }}</strong>
                <small>{{ request.transaction_date }} • نیاز تا {{ request.schedule_date || '—' }}</small>
              </div>
              <span :class="['pill', requestStatusClass(request.status)]">{{ request.status_label }}</span>
            </header>
            <div class="material-request-card-body">
              <div class="request-item-preview" v-for="item in request.items_preview" :key="item.item_code">
                <span>{{ item.item_name }}</span>
                <strong>{{ formatQty(item.qty) }} {{ item.uom }}</strong>
              </div>
              <span v-if="request.item_count > request.items_preview.length" class="request-more-items">+ {{ formatQty(request.item_count - request.items_preview.length) }} قلم دیگر</span>
            </div>
            <footer class="material-request-card-foot">
              <span>{{ formatQty(request.item_count) }} قلم • {{ formatQty(request.total_qty) }} مقدار</span>
              <span v-if="request.purchase_orders?.length" class="ok-text">خرید ایجاد شده</span>
              <span v-else class="muted">برای مشاهده جزئیات کلیک کنید</span>
            </footer>
          </article>
          <p v-if="!materialRequests.length" class="muted request-empty-state">درخواستی برای نمایش وجود ندارد.</p>
        </div>
      </ManagementSurfaceCard>

      <div v-if="materialRequestForm" class="popup-backdrop" @click.self="materialRequestForm = null">
        <div class="popup wide material-request-popup">
          <header class="request-popup-head">
            <div>
              <span class="request-kicker">فرم درخواست مواد</span>
              <h3>{{ materialRequestForm.name ? `ویرایش ${materialRequestForm.name}` : 'درخواست مواد جدید' }}</h3>
            </div>
            <button type="button" class="icon-close-btn" @click="materialRequestForm = null">×</button>
          </header>
          <p class="error" v-if="requestFormError">{{ requestFormError }}</p>
          <div class="form-grid">
            <label>تاریخ درخواست
              <input class="input" type="date" v-model="materialRequestForm.transaction_date" />
            </label>
            <label>تاریخ نیاز
              <input class="input" type="date" v-model="materialRequestForm.schedule_date" />
            </label>
            <label>انبار مقصد
              <select class="input" v-model="materialRequestForm.set_warehouse">
                <option value="">انتخاب انبار</option>
                <option v-for="wh in leafWarehouses" :key="wh" :value="wh">{{ wh }}</option>
              </select>
            </label>
            <label class="full-row">توضیحات درخواست
              <textarea class="input" rows="2" v-model.trim="materialRequestForm.note" placeholder="مثلاً خرید هفتگی آشپزخانه..."></textarea>
            </label>
          </div>
          <div class="request-lines-editor">
            <div class="request-lines-head"><strong>اقلام موردنیاز</strong><span>با انتخاب ماده، واحد اندازه‌گیری خودکار می‌آید.</span></div>
            <div v-for="(line, index) in materialRequestForm.items" :key="index" class="request-line-row">
              <SearchableDropdown
                v-model="line.item_code"
                :options="materialOptions"
                placeholder="انتخاب ماده اولیه..."
                search-placeholder="جستجوی ماده..."
                @update:model-value="syncMaterialRequestLine(line, $event)"
              />
              <input class="input request-qty-input" type="number" min="0.001" step="0.001" v-model.number="line.qty" placeholder="مقدار" />
              <div class="request-uom-field"><small>واحد</small><strong>{{ line.uom || 'خودکار' }}</strong></div>
              <button type="button" class="tertiary-btn danger" @click="removeMaterialRequestLine(index)" :disabled="materialRequestForm.items.length <= 1">حذف</button>
            </div>
            <button type="button" class="secondary-btn add-line-btn" @click="addMaterialRequestLine">+ افزودن ماده</button>
          </div>
          <footer class="request-popup-actions">
            <button type="button" class="secondary-btn" @click="materialRequestForm = null">انصراف</button>
            <button type="button" class="secondary-btn" @click="saveMaterialRequest(false)" :disabled="requestSaving">ذخیره پیش‌نویس</button>
            <button type="button" class="primary-btn" @click="saveMaterialRequest(true)" :disabled="requestSaving">{{ requestSaving ? 'در حال ثبت...' : 'ثبت نهایی درخواست' }}</button>
          </footer>
        </div>
      </div>

      <div v-if="materialRequestDetail" class="popup-backdrop" @click.self="materialRequestDetail = null">
        <div class="popup wide material-request-detail-popup">
          <header class="request-popup-head">
            <div>
              <span class="request-kicker">جزئیات درخواست</span>
              <h3>{{ materialRequestDetail.name }}</h3>
            </div>
            <button type="button" class="icon-close-btn" @click="materialRequestDetail = null">×</button>
          </header>
          <div class="request-detail-meta">
            <div><small>وضعیت</small><strong><span :class="['pill', requestStatusClass(materialRequestDetail.status)]">{{ materialRequestDetail.status_label }}</span></strong></div>
            <div><small>تاریخ درخواست</small><strong>{{ materialRequestDetail.transaction_date }}</strong></div>
            <div><small>تاریخ نیاز</small><strong>{{ materialRequestDetail.schedule_date || '—' }}</strong></div>
            <div><small>انبار مقصد</small><strong>{{ materialRequestDetail.set_warehouse || '—' }}</strong></div>
            <div><small>مجموع مقدار</small><strong>{{ formatQty(materialRequestDetail.total_qty) }}</strong></div>
          </div>
          <div class="material-request-detail-lines">
            <article v-for="line in materialRequestDetail.items" :key="line.idx + '-' + line.item_code" class="request-detail-line">
              <div class="request-detail-line-main">
                <span class="request-line-index">{{ formatQty(line.idx) }}</span>
                <div><strong>{{ line.item_name }}</strong><small>{{ line.item_code }}</small></div>
              </div>
              <div class="request-detail-line-qty"><strong>{{ formatQty(line.qty) }}</strong><span>{{ line.uom || line.stock_uom }}</span></div>
            </article>
          </div>
          <p v-if="materialRequestDetail.note" class="request-note">{{ materialRequestDetail.note }}</p>
          <div v-if="materialRequestDetail.purchase_orders?.length" class="request-purchase-links">
            <strong>سفارش‌های خرید مرتبط</strong>
            <button v-for="purchase in materialRequestDetail.purchase_orders" :key="purchase.name" type="button" class="purchase-link" @click="openLinkedPurchase(purchase.name)">
              {{ purchase.name }} • {{ purchase.status }}
            </button>
          </div>
          <footer class="request-popup-actions">
            <button v-if="materialRequestDetail.docstatus === 0" type="button" class="secondary-btn" @click="editMaterialRequestDetail">ویرایش</button>
            <button v-if="materialRequestDetail.docstatus === 0" type="button" class="secondary-btn" @click="changeMaterialRequestStatus('submit')">ثبت نهایی</button>
            <button v-if="materialRequestDetail.docstatus === 1" type="button" class="primary-btn" @click="createPurchaseFromMaterialRequest" :disabled="requestPurchaseSaving">{{ requestPurchaseSaving ? 'در حال ساخت خرید...' : 'ایجاد پیش‌نویس خرید' }}</button>
            <button v-if="materialRequestDetail.docstatus === 1" type="button" class="tertiary-btn danger" @click="changeMaterialRequestStatus('cancel')">لغو درخواست</button>
            <button type="button" class="secondary-btn" @click="printMaterialRequest">چاپ فیش</button>
            <button type="button" class="secondary-btn" @click="materialRequestDetail = null">بستن</button>
          </footer>
        </div>
      </div>
    </section>

    <!-- ======================= خرید ======================= -->
    <section v-if="activeTab === 'purchase'" class="tab-body">
      <p class="error" v-if="purchaseError">{{ purchaseError }}</p>
      <p class="success-msg" v-if="purchaseMessage">{{ purchaseMessage }}</p>
      <ManagementSurfaceCard title="سفارش‌های خرید مواد اولیه" subtitle="ثبت، ارسال و دریافت از تأمین‌کنندگان">
        <div class="toolbar">
          <select class="input" v-model="purchaseFilters.status" @change="loadPurchases">
            <option value="">همه وضعیت‌ها</option>
            <option v-for="s in purchaseStatuses" :key="s" :value="s">{{ s }}</option>
          </select>
          <input class="input" v-model.trim="purchaseFilters.search" placeholder="جستجوی شماره یا تأمین‌کننده..." @keyup.enter="loadPurchases" />
          <button type="button" class="secondary-btn" @click="loadPurchases" :disabled="purchaseLoading">{{ purchaseLoading ? '...' : 'جستجو' }}</button>
          <button type="button" class="primary-btn" @click="togglePurchaseForm">{{ showPurchaseForm ? 'بستن فرم' : '+ سفارش خرید جدید' }}</button>
          <button type="button" class="secondary-btn" @click="openSupplierForm()">+ تأمین‌کننده جدید</button>
        </div>

        <div v-if="showPurchaseForm" class="inline-form">
          <h4>{{ purchaseForm.name ? 'ویرایش پیش‌نویس ' + purchaseForm.name : 'سفارش خرید جدید' }}</h4>
          <div class="form-grid">
            <label>تأمین‌کننده
              <select class="input" v-model="purchaseForm.supplier">
                <option value="">بدون تأمین‌کننده</option>
                <option v-for="s in supplierOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
              </select>
            </label>
            <label>انبار مقصد
              <select class="input" v-model="purchaseForm.target_warehouse">
                <option value="">—</option>
                <option v-for="wh in leafWarehouses" :key="wh" :value="wh">{{ wh }}</option>
              </select>
            </label>
            <label>تاریخ سفارش <input class="input" type="date" v-model="purchaseForm.posting_date" /></label>
            <label>تاریخ تحویل مورد انتظار <input class="input" type="date" v-model="purchaseForm.expected_date" /></label>
            <label class="full-row">یادداشت <input class="input" v-model.trim="purchaseForm.note" /></label>
          </div>
          <div class="lines-editor">
            <div v-for="(line, i) in purchaseForm.items" :key="i" class="line-row">
              <SearchableDropdown v-model="line.item_code" :options="materialOptions" placeholder="کالا..." search-placeholder="جستجوی کالا..." />
              <input class="input" type="number" min="0.0001" step="0.001" v-model.number="line.qty" placeholder="مقدار" />
              <input class="input" type="number" min="0" v-model.number="line.rate" placeholder="نرخ (اختیاری)" />
              <button type="button" class="tertiary-btn danger" @click="purchaseForm.items.splice(i, 1)" :disabled="purchaseForm.items.length <= 1">حذف</button>
            </div>
          </div>
          <div class="btn-row">
            <button type="button" class="secondary-btn" @click="purchaseForm.items.push({ item_code: '', qty: 1, rate: 0 })">+ افزودن قلم</button>
            <button type="button" class="primary-btn" @click="savePurchase" :disabled="purchaseSaving">{{ purchaseSaving ? '...' : 'ذخیره پیش‌نویس' }}</button>
          </div>
        </div>

        <p class="muted" v-if="purchaseLoading">در حال دریافت...</p>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>شماره</th><th>تأمین‌کننده</th><th>تاریخ</th><th>وضعیت</th><th>تعداد</th><th>مبلغ</th><th></th></tr>
            </thead>
            <tbody>
              <tr v-for="row in purchases" :key="row.name">
                <td><strong>{{ row.name }}</strong></td>
                <td>{{ row.supplier_name || '—' }}</td>
                <td>{{ row.posting_date }}</td>
                <td><span :class="['pill', purchaseStatusClass(row.status)]">{{ row.status }}</span></td>
                <td>{{ formatQty(row.total_qty) }}</td>
                <td>{{ formatMoneyValue(row.grand_total) }}</td>
                <td><button type="button" class="tertiary-btn" @click="openPurchaseDetail(row.name)">مشاهده</button></td>
              </tr>
              <tr v-if="!purchases.length"><td colspan="7" class="muted">سفارش خریدی ثبت نشده است.</td></tr>
            </tbody>
          </table>
        </div>
      </ManagementSurfaceCard>

      <div v-if="purchaseDetail" class="popup-backdrop" @click.self="purchaseDetail = null">
        <div class="popup wide">
          <h3>سفارش خرید {{ purchaseDetail.name }}</h3>
          <div class="meta-grid">
            <div><small class="muted">تأمین‌کننده</small><strong>{{ purchaseDetail.supplier_name || '—' }}</strong></div>
            <div><small class="muted">وضعیت</small><strong><span :class="['pill', purchaseStatusClass(purchaseDetail.status)]">{{ purchaseDetail.status }}</span></strong></div>
            <div><small class="muted">تاریخ</small><strong>{{ purchaseDetail.posting_date }}</strong></div>
            <div><small class="muted">دریافت‌شده</small><strong>{{ formatQty(purchaseDetail.received_pct) }}٪</strong></div>
            <div><small class="muted">مبلغ کل</small><strong>{{ formatMoneyValue(purchaseDetail.grand_total) }}</strong></div>
          </div>
          <div class="table-wrap">
            <table class="data-table">
              <thead>
                <tr><th>کالا</th><th>سفارش</th><th>دریافت‌شده</th><th>باقی‌مانده</th><th>نرخ</th><th>مبلغ</th><th v-if="canReceivePurchase">دریافت این نوبت</th></tr>
              </thead>
              <tbody>
                <tr v-for="row in purchaseDetail.items" :key="row.idx">
                  <td>{{ row.item_name }}<br><small class="muted">{{ row.item_code }}</small></td>
                  <td>{{ formatQty(row.qty) }} {{ row.uom }}</td>
                  <td>{{ formatQty(row.received_qty) }}</td>
                  <td :class="row.remaining_qty > 0 ? 'warn-text' : 'ok-text'">{{ formatQty(row.remaining_qty) }}</td>
                  <td>{{ formatMoneyValue(row.rate) }}</td>
                  <td>{{ formatMoneyValue(row.amount) }}</td>
                  <td v-if="canReceivePurchase">
                    <input class="input compact" type="number" min="0" step="0.001" :max="row.remaining_qty" v-model.number="receiveLines[row.item_code]" placeholder="0" :disabled="row.remaining_qty <= 0" />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="canReceivePurchase" class="form-grid receive-warehouse-row">
            <label>انبار دریافت
              <select class="input" v-model="receiveWarehouse">
                <option v-for="wh in leafWarehouses" :key="wh" :value="wh">{{ wh }}</option>
              </select>
            </label>
          </div>
          <div class="btn-row">
            <button v-if="purchaseDetail.status === 'پیش‌نویس'" type="button" class="secondary-btn" @click="editPurchaseDraft">ویرایش اقلام</button>
            <button v-if="purchaseDetail.status === 'پیش‌نویس'" type="button" class="primary-btn" @click="setPurchaseStatus('ارسال‌شده')">ارسال به تأمین‌کننده</button>
            <button v-if="canReceivePurchase" type="button" class="primary-btn" @click="receivePurchase" :disabled="purchaseSaving">{{ purchaseSaving ? 'در حال دریافت...' : 'ثبت دریافت' }}</button>
            <button type="button" class="secondary-btn" @click="printPurchaseOrder" :disabled="purchasePrinting">{{ purchasePrinting ? 'در حال آماده‌سازی...' : 'چاپ سفارش' }}</button>
            <button v-if="['پیش‌نویس', 'ارسال‌شده'].includes(purchaseDetail.status)" type="button" class="tertiary-btn danger" @click="setPurchaseStatus('لغوشده')">لغو سفارش</button>
            <button type="button" class="secondary-btn" @click="purchaseDetail = null">بستن</button>
          </div>
          <div v-if="purchaseDetail.receipts && purchaseDetail.receipts.length" class="hint-line">
            اسناد دریافت: {{ purchaseDetail.receipts.join('، ') }}
          </div>
        </div>
      </div>

      <div v-if="supplierForm" class="popup-backdrop" @click.self="supplierForm = null">
        <div class="popup">
          <h3>تأمین‌کننده جدید</h3>
          <p class="error" v-if="supplierFormError">{{ supplierFormError }}</p>
          <div class="form-grid">
            <label class="full-row">نام تأمین‌کننده <span class="req">*</span>
              <input class="input" v-model.trim="supplierForm.supplier_name" />
            </label>
          </div>
          <div class="btn-row">
            <button type="button" class="primary-btn" @click="saveSupplier" :disabled="supplierSaving">{{ supplierSaving ? '...' : 'ذخیره' }}</button>
            <button type="button" class="secondary-btn" @click="supplierForm = null">انصراف</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ======================= برنامه تولید ======================= -->
    <section v-if="activeTab === 'production'" class="tab-body">
      <p class="error" v-if="productionError">{{ productionError }}</p>
      <p class="success-msg" v-if="productionMessage">{{ productionMessage }}</p>
      <ManagementSurfaceCard title="برنامه‌ریزی تولید" subtitle="نیاز مواد اولیه بر اساس سفارش‌های باز در مقایسه با موجودی">
        <div class="toolbar">
          <input class="input" type="date" v-model="planFilters.date_from" />
          <input class="input" type="date" v-model="planFilters.date_to" />
          <button type="button" class="secondary-btn" @click="loadProductionPlan" :disabled="planLoading">{{ planLoading ? '...' : 'محاسبه برنامه' }}</button>
        </div>
        <p class="muted" v-if="planLoading">در حال محاسبه...</p>
        <template v-else-if="plan">
          <div class="totals-grid">
            <div class="total-box"><small>حواله‌های تولید باز</small><strong>{{ formatQty(plan.summary.tickets) }}</strong></div>
            <div class="total-box"><small>مواد مورد نیاز</small><strong>{{ formatQty(plan.summary.materials_required) }}</strong></div>
            <div class="total-box" :class="{ 'warn-border': plan.summary.materials_shortage > 0 }">
              <small>اقلام با کمبود</small><strong :class="plan.summary.materials_shortage > 0 ? 'warn-text' : 'ok-text'">{{ formatQty(plan.summary.materials_shortage) }}</strong>
            </div>
          </div>

          <h4>مواد اولیه مورد نیاز</h4>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>ماده</th><th>نیاز</th><th>موجودی</th><th>کمبود</th></tr></thead>
              <tbody>
                <tr v-for="row in plan.materials" :key="row.item_code">
                  <td>{{ row.item_name }}<br><small class="muted">{{ row.item_code }}</small></td>
                  <td>{{ formatQty(row.required) }} {{ row.stock_uom }}</td>
                  <td>{{ formatQty(row.available) }}</td>
                  <td :class="row.shortage > 0 ? 'warn-text' : 'ok-text'">{{ row.shortage > 0 ? formatQty(row.shortage) : 'کافی' }}</td>
                </tr>
                <tr v-if="!plan.materials.length"><td colspan="4" class="muted">حواله تولید بازی در این بازه نیست.</td></tr>
              </tbody>
            </table>
          </div>

          <h4>محصولات در صف تولید</h4>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>محصول</th><th>تعداد</th><th>تعداد حواله</th></tr></thead>
              <tbody>
                <tr v-for="row in plan.products" :key="row.menu_item">
                  <td>{{ row.item_name }}<br><small class="muted">{{ row.menu_item }}</small></td>
                  <td>{{ formatQty(row.qty) }}</td>
                  <td>{{ formatQty(row.tickets) }}</td>
                </tr>
                <tr v-if="!plan.products.length"><td colspan="3" class="muted">—</td></tr>
              </tbody>
            </table>
          </div>
        </template>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="ثبت تولید دستی" subtitle="مصرف خودکار مواد بر اساس فرمول و ورود محصول به انبار">
        <div class="form-grid">
          <label>محصول
            <SearchableDropdown v-model="productionForm.menu_item" :options="productOptions" placeholder="انتخاب محصول..." search-placeholder="جستجوی محصول..." />
          </label>
          <label>تعداد تولید
            <input class="input" type="number" min="0.5" step="0.5" v-model.number="productionForm.qty" />
          </label>
          <label>انبار مواد اولیه
            <select class="input" v-model="productionForm.source_warehouse">
              <option value="">پیش‌فرض</option>
              <option v-for="wh in leafWarehouses" :key="wh" :value="wh">{{ wh }}</option>
            </select>
          </label>
          <label>انبار محصول
            <select class="input" v-model="productionForm.target_warehouse">
              <option value="">پیش‌فرض</option>
              <option v-for="wh in leafWarehouses" :key="wh" :value="wh">{{ wh }}</option>
            </select>
          </label>
        </div>
        <div class="btn-row">
          <button type="button" class="primary-btn" @click="submitProduction" :disabled="productionSaving || !productionForm.menu_item">
            {{ productionSaving ? 'در حال ثبت...' : 'ثبت تولید' }}
          </button>
        </div>
      </ManagementSurfaceCard>
    </section>

    <!-- ======================= ضایعات و اوتی‌ها ======================= -->
    <section v-if="activeTab === 'losses'" class="tab-body">
      <p class="error" v-if="lossesError">{{ lossesError }}</p>
      <p class="success-msg" v-if="lossesMessage">{{ lossesMessage }}</p>
      <ManagementSurfaceCard title="گزارش ضایعات و خسارات" subtitle="ارزش سوخت‌شده بر اساس اسناد انبار">
        <div class="toolbar">
          <input class="input" type="date" v-model="lossFilters.date_from" />
          <input class="input" type="date" v-model="lossFilters.date_to" />
          <select class="input" v-model="lossFilters.warehouse">
            <option value="">همه انبارها</option>
            <option v-for="wh in leafWarehouses" :key="wh" :value="wh">{{ wh }}</option>
          </select>
          <button type="button" class="secondary-btn" @click="loadWasteReport" :disabled="lossesLoading">{{ lossesLoading ? '...' : 'بروزرسانی' }}</button>
        </div>
        <template v-if="wasteReport">
          <div class="totals-grid">
            <div class="total-box"><small>ارزش ضایعات</small><strong class="warn-text">{{ formatMoneyValue(wasteReport.totals.waste_value) }}</strong></div>
            <div class="total-box"><small>ارزش خسارات</small><strong class="warn-text">{{ formatMoneyValue(wasteReport.totals.damage_value) }}</strong></div>
            <div class="total-box"><small>مرجوعی به انبار</small><strong class="ok-text">{{ formatMoneyValue(wasteReport.totals.return_value) }}</strong></div>
            <div class="total-box"><small>اسناد</small><strong>{{ formatQty(wasteReport.totals.movement_count) }}</strong></div>
          </div>
          <div class="totals-grid" v-if="wasteReport.order_losses.length">
            <div class="total-box" v-for="row in wasteReport.order_losses" :key="row.loss_kind">
              <small>{{ row.loss_kind }} (اوتی/خسارت ثبتی)</small>
              <strong>{{ formatQty(row.count) }} مورد • {{ formatMoneyValue(row.amount) }}</strong>
            </div>
          </div>
          <div class="table-wrap" v-if="wasteReport.by_item.length">
            <table class="data-table">
              <thead><tr><th>کالا</th><th>نوع</th><th>مقدار</th><th>ارزش</th><th>اسناد</th></tr></thead>
              <tbody>
                <tr v-for="(row, i) in wasteReport.by_item" :key="i">
                  <td>{{ row.item_name }}</td>
                  <td><span class="pill warn">{{ row.kind }}</span></td>
                  <td>{{ formatQty(row.qty) }}</td>
                  <td>{{ formatMoneyValue(row.value) }}</td>
                  <td>{{ formatQty(row.vouchers) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="ثبت اوتی / خسارت / مرجوعی" subtitle="ثبت و پیگیری سفارش‌های اوت‌شده و خسارات وارده">
        <div class="form-grid">
          <label>نوع
            <select class="input" v-model="lossForm.loss_kind">
              <option v-for="k in lossKinds" :key="k" :value="k">{{ k }}</option>
            </select>
          </label>
          <label>منشأ
            <select class="input" v-model="lossForm.source_type">
              <option>دستی</option><option>POS</option><option>وب</option><option>میز</option>
            </select>
          </label>
          <label>مرجع سفارش (اختیاری)
            <input class="input" v-model.trim="lossForm.source_reference" placeholder="شماره سفارش / میز" />
          </label>
          <label>کالا / محصول
            <SearchableDropdown v-model="lossForm.item_code" :options="allItemOptions" placeholder="انتخاب..." search-placeholder="جستجو..." />
          </label>
          <label>مقدار
            <input class="input" type="number" min="0.0001" step="0.001" v-model.number="lossForm.qty" />
          </label>
          <label>انبار (برای خسارت/مرجوعی)
            <select class="input" v-model="lossForm.warehouse">
              <option value="">—</option>
              <option v-for="wh in leafWarehouses" :key="wh" :value="wh">{{ wh }}</option>
            </select>
          </label>
          <label class="full-row">علت
            <input class="input" v-model.trim="lossForm.reason" placeholder="مثلاً سوختن سفارش، برگشت مشتری، فساد ماده اولیه" />
          </label>
        </div>
        <div class="btn-row">
          <button type="button" class="primary-btn" @click="submitOrderLoss" :disabled="lossSaving || !lossForm.item_code">
            {{ lossSaving ? 'در حال ثبت...' : 'ثبت' }}
          </button>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="سوابق اوتی‌ها و خسارات" subtitle="آخرین رخدادهای ثبت‌شده">
        <div class="toolbar">
          <select class="input" v-model="lossListFilter" @change="loadOrderLosses">
            <option value="">همه انواع</option>
            <option v-for="k in lossKinds" :key="k" :value="k">{{ k }}</option>
          </select>
          <button type="button" class="secondary-btn" @click="loadOrderLosses">بروزرسانی</button>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>تاریخ</th><th>نوع</th><th>کالا</th><th>مقدار</th><th>منشأ</th><th>علت</th><th>مبلغ</th><th>سند انبار</th></tr></thead>
            <tbody>
              <tr v-for="row in orderLosses" :key="row.name">
                <td>{{ row.entry_date }}</td>
                <td><span :class="['pill', row.loss_kind === 'مرجوعی به انبار' ? 'ok' : 'warn']">{{ row.loss_kind }}</span></td>
                <td>{{ row.item_name }}<br><small class="muted">{{ row.item_code }}</small></td>
                <td>{{ formatQty(row.qty) }} {{ row.uom }}</td>
                <td>{{ row.source_type }}<br><small class="muted">{{ row.source_reference }}</small></td>
                <td><small>{{ row.reason }}</small></td>
                <td>{{ formatMoneyValue(row.amount) }}</td>
                <td><small class="muted">{{ row.stock_entry || '—' }}</small></td>
              </tr>
              <tr v-if="!orderLosses.length"><td colspan="8" class="muted">موردی ثبت نشده است.</td></tr>
            </tbody>
          </table>
        </div>
      </ManagementSurfaceCard>
    </section>

    <!-- ======================= انبارگردانی ======================= -->
    <section v-if="activeTab === 'count'" class="tab-body">
      <p class="error" v-if="countError">{{ countError }}</p>
      <p class="success-msg" v-if="countMessage">{{ countMessage }}</p>
      <ManagementSurfaceCard title="انبارگردانی و مغایرت‌گیری" subtitle="شمارش فیزیکی و مقایسه با موجودی سیستمی">
        <div class="toolbar">
          <select class="input" v-model="countWarehouse">
            <option value="">انتخاب انبار...</option>
            <option v-for="wh in leafWarehouses" :key="wh" :value="wh">{{ wh }}</option>
          </select>
          <input class="input" v-model.trim="countSearch" placeholder="جستجوی کالا (اختیاری)..." @keyup.enter="loadCountContext" />
          <button type="button" class="primary-btn" @click="loadCountContext" :disabled="countLoading || !countWarehouse">{{ countLoading ? '...' : 'بارگذاری برگه شمارش' }}</button>
        </div>
        <p class="hint-line warn-text" v-if="countContext && !countContext.config_ready">
          حساب تعدیل موجودی یا مرکز هزینه در شرکت تنظیم نشده است؛ ثبت نهایی ممکن نیست.
        </p>
        <p class="muted" v-if="countLoading">در حال دریافت موجودی سیستمی...</p>
        <template v-else-if="countRows.length">
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>کالا</th><th>موجودی سیستمی</th><th>شمارش فیزیکی</th><th>مغایرت</th><th>نرخ</th></tr></thead>
              <tbody>
                <tr v-for="row in countRows" :key="row.item_code">
                  <td>{{ row.item_name }}<br><small class="muted">{{ row.item_code }}</small></td>
                  <td>{{ formatQty(row.system_qty) }} {{ row.stock_uom }}</td>
                  <td><input class="input compact" type="number" step="0.001" v-model.number="row.counted" /></td>
                  <td :class="countDiff(row) === 0 ? 'ok-text' : 'warn-text'">{{ countDiff(row) === 0 ? '—' : formatQty(countDiff(row)) }}</td>
                  <td>{{ formatMoneyValue(row.valuation_rate) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="btn-row">
            <button type="button" class="secondary-btn" @click="resetCountRows">انصراف از شمارش</button>
            <button type="button" class="primary-btn" @click="submitCount" :disabled="countSaving || !countedRows.length">
              {{ countSaving ? 'در حال ثبت...' : `ثبت انبارگردانی (${formatQty(countedRows.length)} قلم تغییریافته)` }}
            </button>
          </div>
        </template>

        <div v-if="countResult" class="inline-form result-block">
          <h4>نتیجه مغایرت‌گیری — سند {{ countResult.name }}</h4>
          <p>مغایرت کل ارزشی: <strong :class="countResult.difference_amount === 0 ? 'ok-text' : 'warn-text'">{{ formatMoneyValue(countResult.difference_amount) }}</strong></p>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>کالا</th><th>سیستمی</th><th>شمارش</th><th>تفاوت</th><th>ارزش تفاوت</th></tr></thead>
              <tbody>
                <tr v-for="row in countResult.rows" :key="row.item_code">
                  <td>{{ row.item_code }}</td>
                  <td>{{ formatQty(row.prev_qty) }}</td>
                  <td>{{ formatQty(row.new_qty) }}</td>
                  <td :class="row.diff_qty === 0 ? 'ok-text' : 'warn-text'">{{ row.diff_qty > 0 ? '+' : '' }}{{ formatQty(row.diff_qty) }}</td>
                  <td>{{ formatMoneyValue(row.diff_value) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="سوابق انبارگردانی" subtitle="آخرین اسناد شمارش فیزیکی">
        <div class="toolbar">
          <button type="button" class="secondary-btn" @click="loadReconciliations">بروزرسانی</button>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>سند</th><th>تاریخ</th><th>شرکت</th><th>مغایرت ارزشی</th><th></th></tr></thead>
            <tbody>
              <tr v-for="row in reconciliations" :key="row.name">
                <td><strong>{{ row.name }}</strong></td>
                <td>{{ row.posting_date }}</td>
                <td>{{ row.company }}</td>
                <td :class="row.difference_amount === 0 ? 'ok-text' : 'warn-text'">{{ formatMoneyValue(row.difference_amount) }}</td>
                <td><button type="button" class="tertiary-btn" @click="viewReconciliation(row.name)">جزئیات</button></td>
              </tr>
              <tr v-if="!reconciliations.length"><td colspan="5" class="muted">انبارگردانی‌ای ثبت نشده است.</td></tr>
            </tbody>
          </table>
        </div>
        <div v-if="reconciliationDetail" class="inline-form result-block">
          <h4>جزئیات {{ reconciliationDetail.name }}</h4>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>کالا</th><th>انبار</th><th>تغییر مقدار</th><th>تغییر ارزش</th></tr></thead>
              <tbody>
                <tr v-for="(row, i) in reconciliationDetail.rows" :key="i">
                  <td>{{ row.item_code }}</td>
                  <td>{{ row.warehouse }}</td>
                  <td :class="row.diff_qty >= 0 ? 'ok-text' : 'warn-text'">{{ row.diff_qty > 0 ? '+' : '' }}{{ formatQty(row.diff_qty) }}</td>
                  <td>{{ formatMoneyValue(row.diff_value) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </ManagementSurfaceCard>
    </section>

    <!-- ======================= بهای تمام‌شده ======================= -->
    <section v-if="activeTab === 'costs'" class="tab-body">
      <p class="error" v-if="costsError">{{ costsError }}</p>
      <ManagementSurfaceCard title="بهای تمام‌شده محصولات" subtitle="محاسبه خودکار بر اساس فرمول تولید و نرخ مواد اولیه">
        <div class="toolbar">
          <input class="input" v-model.trim="costSearch" placeholder="جستجوی محصول..." @keyup.enter="loadCosts" />
          <button type="button" class="secondary-btn" @click="loadCosts" :disabled="costsLoading">{{ costsLoading ? '...' : 'جستجو' }}</button>
        </div>
        <p class="muted" v-if="costsLoading">در حال محاسبه...</p>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>محصول</th><th>فرمول</th><th>بهای واحد</th><th>قیمت فروش</th><th>حاشیه سود</th><th>اجزا</th></tr>
            </thead>
            <tbody>
              <template v-for="row in costs" :key="row.item_code">
                <tr>
                  <td>{{ row.item_name }}<br><small class="muted">{{ row.item_code }}</small></td>
                  <td><small class="muted">{{ row.bom }}</small></td>
                  <td><strong>{{ formatMoneyValue(row.unit_cost) }}</strong></td>
                  <td>{{ formatMoneyValue(row.sale_price) }}</td>
                  <td :class="row.margin_amount >= 0 ? 'ok-text' : 'warn-text'">
                    {{ formatMoneyValue(row.margin_amount) }}
                    <br><small>{{ row.margin_pct }}٪</small>
                  </td>
                  <td>
                    <button type="button" class="tertiary-btn" @click="toggleCostDetail(row.item_code)">
                      {{ expandedCost === row.item_code ? 'بستن' : `${row.components.length} قلم` }}
                    </button>
                    <span v-if="row.missing_prices" class="badge warn">بدون نرخ: {{ row.missing_prices }}</span>
                  </td>
                </tr>
                <tr v-if="expandedCost === row.item_code" class="sub-row">
                  <td colspan="6">
                    <table class="data-table inner">
                      <thead><tr><th>ماده</th><th>مقدار</th><th>نرخ</th><th>مبلغ</th></tr></thead>
                      <tbody>
                        <tr v-for="comp in row.components" :key="comp.item_code">
                          <td>{{ comp.item_name }}</td>
                          <td>{{ formatQty(comp.qty) }} {{ comp.uom }}</td>
                          <td>{{ formatMoneyValue(comp.rate) }}</td>
                          <td>{{ formatMoneyValue(comp.amount) }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </td>
                </tr>
              </template>
              <tr v-if="!costs.length"><td colspan="6" class="muted">محصولی با فرمول فعال یافت نشد.</td></tr>
            </tbody>
          </table>
        </div>
      </ManagementSurfaceCard>
    </section>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import {
  createManagementProductionEntry,
  createManagementPurchaseFromAlerts,
  createManagementPurchaseFromMaterialRequest,
  createManagementStockMovement,
  deleteManagementWarehouse,
  exportManagementMaterialsExcel,
  getManagementInventoryBoot,
  getManagementInventoryPurchasePrint,
  getManagementMaterialRequest,
  getManagementMaterialRequestPrint,
  getManagementProductCostReport,
  getManagementProductionPlan,
  getManagementPurchaseOrder,
  getManagementReconciliationContext,
  getManagementReorderAlerts,
  getManagementStockOverview,
  getManagementStockReconciliation,
  getManagementWasteLossReport,
  importManagementMaterialsExcel,
  listManagementMaterialRequests,
  listManagementOrderLosses,
  listManagementProducts,
  listManagementPurchaseOrders,
  listManagementRawMaterials,
  listManagementStockMovements,
  listManagementStockReconciliations,
  listManagementWarehouses,
  receiveManagementPurchaseOrder,
  saveManagementMaterialRequest,
  saveManagementOrderLoss,
  saveManagementPurchaseOrder,
  saveManagementRawMaterial,
  saveManagementSupplier,
  saveManagementWarehouse,
  submitManagementStockReconciliation,
  updateManagementMaterialRequestStatus,
  updateManagementPurchaseOrderStatus,
  uploadFileToFrappe,
} from '@/utils/api'
import { formatMoney as formatMoneyUtil } from '@/utils/format'

const tabs = [
  { key: 'overview', label: 'موجودی و ارزش' },
  { key: 'materials', label: 'مواد اولیه' },
  { key: 'warehouses', label: 'انبارها' },
  { key: 'movements', label: 'ورود و خروج' },
  { key: 'reorder', label: 'نقطه سفارش' },
  { key: 'requests', label: 'درخواست مواد' },
  { key: 'purchase', label: 'خرید' },
  { key: 'production', label: 'برنامه تولید' },
  { key: 'losses', label: 'ضایعات و اوتی‌ها' },
  { key: 'count', label: 'انبارگردانی' },
  { key: 'costs', label: 'بهای تمام‌شده' },
]

const activeTab = ref('overview')
const boot = ref(null)
const bootLoading = ref(false)

const loadingAny = computed(() => bootLoading.value || requestLoading.value || purchaseLoading.value)

const leafWarehouses = computed(() => (boot.value ? boot.value.leaf_warehouses || [] : []))
const supplierOptions = computed(() =>
  (boot.value ? boot.value.suppliers || [] : []).map((s) => ({ value: s.name, label: s.supplier_name || s.name })),
)
const movementKinds = computed(() => (boot.value ? boot.value.movement_kinds || {} : {}))
const purchaseStatuses = computed(() => (boot.value ? boot.value.purchase_statuses || [] : []))
const lossKinds = computed(() => (boot.value ? boot.value.loss_kinds || [] : []))

function formatMoneyValue(value) {
  return formatMoneyUtil(Number(value || 0))
}
function formatQty(value) {
  const num = Number(value || 0)
  return new Intl.NumberFormat('fa-IR', { maximumFractionDigits: 3 }).format(num)
}
function warehouseKeys(row) {
  return Object.keys(row.warehouses || {})
}

async function loadBoot() {
  bootLoading.value = true
  try {
    boot.value = await getManagementInventoryBoot()
  } catch (err) {
    boot.value = null
    overviewError.value = err.message || 'دریافت اطلاعات انبار ناموفق بود.'
  } finally {
    bootLoading.value = false
  }
}

// ------------------------- overview -------------------------
const overview = ref(null)
const overviewLoading = ref(false)
const overviewError = ref('')
const overviewFilters = reactive({ warehouse: '', search: '', only_materials: false })

async function loadOverview() {
  overviewLoading.value = true
  overviewError.value = ''
  try {
    overview.value = await getManagementStockOverview({
      warehouse: overviewFilters.warehouse,
      search: overviewFilters.search,
      only_materials: overviewFilters.only_materials ? 1 : 0,
    })
  } catch (err) {
    overviewError.value = err.message || 'خطا در دریافت موجودی.'
  } finally {
    overviewLoading.value = false
  }
}

// ------------------------- materials -------------------------
const materials = ref([])
const materialsLoading = ref(false)
const materialsError = ref('')
const materialsMessage = ref('')
const materialsSearch = ref('')
const materialsShowInactive = ref(false)
const materialsHasMore = ref(false)
const materialsOffset = ref(0)
const materialOptionsPool = ref([])
const materialForm = ref(null)
const materialFormError = ref('')
const materialSaving = ref(false)

const materialOptions = computed(() =>
  materialOptionsPool.value.map((m) => ({ value: m.name, label: `${m.item_name} (${m.name})` })),
)

// ------------------------- material requests -------------------------
const materialRequests = ref([])
const requestLoading = ref(false)
const requestError = ref('')
const requestMessage = ref('')
const requestFilters = reactive({ status: '', search: '', date_from: '', date_to: '' })
const materialRequestForm = ref(null)
const materialRequestDetail = ref(null)
const requestFormError = ref('')
const requestSaving = ref(false)
const requestPurchaseSaving = ref(false)

function requestStatusClass(status) {
  const normalized = String(status || '').toLowerCase()
  if (['ordered', 'partially ordered'].includes(normalized)) return 'ok'
  if (['cancelled', 'stopped'].includes(normalized)) return 'warn'
  return ''
}

function todayDateValue() {
  return new Date().toISOString().slice(0, 10)
}

function materialMeta(itemCode) {
  return materialOptionsPool.value.find((item) => item.name === itemCode) || null
}

function syncMaterialRequestLine(line, itemCode = line.item_code) {
  line.item_code = itemCode
  const meta = materialMeta(itemCode)
  if (!meta) return
  line.uom = line.uom || meta.stock_uom || 'Nos'
  line.stock_uom = meta.stock_uom || line.uom
  line.conversion_factor = Number(line.conversion_factor || 1)
}

function addMaterialRequestLine() {
  materialRequestForm.value?.items.push({ item_code: '', qty: 1, uom: '', stock_uom: '', conversion_factor: 1, warehouse: '' })
}

function removeMaterialRequestLine(index) {
  if (!materialRequestForm.value || materialRequestForm.value.items.length <= 1) return
  materialRequestForm.value.items.splice(index, 1)
}

function openMaterialRequestForm(request = null) {
  requestFormError.value = ''
  if (request) {
    materialRequestForm.value = {
      name: request.name,
      transaction_date: request.transaction_date || todayDateValue(),
      schedule_date: request.schedule_date || request.transaction_date || todayDateValue(),
      set_warehouse: request.set_warehouse || boot.value?.settings?.default_warehouse || '',
      note: request.note || '',
      items: (request.items || []).map((line) => ({ ...line, conversion_factor: Number(line.conversion_factor || 1) })),
    }
  } else {
    materialRequestForm.value = {
      name: '',
      transaction_date: todayDateValue(),
      schedule_date: todayDateValue(),
      set_warehouse: boot.value?.settings?.default_warehouse || '',
      note: '',
      items: [{ item_code: '', qty: 1, uom: '', stock_uom: '', conversion_factor: 1, warehouse: '' }],
    }
  }
  materialRequestForm.value.items.forEach((line) => syncMaterialRequestLine(line))
}

async function loadMaterialRequests() {
  requestLoading.value = true
  requestError.value = ''
  try {
    if (!materialOptionsPool.value.length) await loadMaterials()
    const payload = await listManagementMaterialRequests({ ...requestFilters, limit: 100 })
    if (payload?.doctype_available === false) {
      throw new Error('داکتایپ Material Request در ERPNext در دسترس نیست.')
    }
    materialRequests.value = payload.requests || []
  } catch (err) {
    requestError.value = err.message || 'دریافت درخواست‌های مواد ناموفق بود.'
    materialRequests.value = []
  } finally {
    requestLoading.value = false
  }
}

async function openMaterialRequestDetail(name) {
  requestError.value = ''
  try {
    const payload = await getManagementMaterialRequest(name)
    materialRequestDetail.value = payload.request
    materialRequestDetail.value.purchase_orders = payload.purchase_orders || []
  } catch (err) {
    requestError.value = err.message || 'دریافت جزئیات درخواست ناموفق بود.'
  }
}

async function saveMaterialRequest(submit = false) {
  if (!materialRequestForm.value) return
  requestSaving.value = true
  requestFormError.value = ''
  try {
    const items = materialRequestForm.value.items
      .filter((line) => line.item_code && Number(line.qty) > 0)
      .map((line) => ({
        item_code: line.item_code,
        qty: Number(line.qty),
        uom: line.uom,
        stock_uom: line.stock_uom,
        conversion_factor: Number(line.conversion_factor || 1),
        warehouse: materialRequestForm.value.set_warehouse || '',
      }))
    if (!items.length) throw new Error('حداقل یک ماده با مقدار بیشتر از صفر انتخاب کنید.')
    const result = await saveManagementMaterialRequest({
      ...materialRequestForm.value,
      items,
      submit: submit ? 1 : 0,
    })
    requestMessage.value = submit ? `درخواست ${result.request.name} ثبت نهایی شد.` : `پیش‌نویس ${result.request.name} ذخیره شد.`
    materialRequestForm.value = null
    await loadMaterialRequests()
    await openMaterialRequestDetail(result.request.name)
  } catch (err) {
    requestFormError.value = err.message || 'ذخیره درخواست مواد ناموفق بود.'
  } finally {
    requestSaving.value = false
  }
}

function openLinkedPurchase(name) {
  materialRequestDetail.value = null
  openPurchaseDetail(name)
}

function editMaterialRequestDetail() {
  if (!materialRequestDetail.value || materialRequestDetail.value.docstatus !== 0) return
  openMaterialRequestForm(materialRequestDetail.value)
  materialRequestDetail.value = null
}

async function changeMaterialRequestStatus(action) {
  if (!materialRequestDetail.value) return
  requestError.value = ''
  try {
    const result = await updateManagementMaterialRequestStatus({ name: materialRequestDetail.value.name, action })
    materialRequestDetail.value = result.request
    requestMessage.value = 'وضعیت درخواست مواد به‌روزرسانی شد.'
    await loadMaterialRequests()
  } catch (err) {
    requestError.value = err.message || 'تغییر وضعیت درخواست ناموفق بود.'
  }
}

async function createPurchaseFromMaterialRequest() {
  if (!materialRequestDetail.value) return
  requestPurchaseSaving.value = true
  requestError.value = ''
  try {
    const result = await createManagementPurchaseFromMaterialRequest({
      name: materialRequestDetail.value.name,
      target_warehouse: materialRequestDetail.value.set_warehouse || boot.value?.settings?.default_warehouse || '',
      items: materialRequestDetail.value.items.map((line) => ({
        item_code: line.item_code,
        qty: line.qty,
        uom: line.uom || line.stock_uom,
        rate: line.rate || 0,
      })),
    })
    requestMessage.value = `پیش‌نویس خرید ${result.purchase.name} ساخته شد.`
    purchaseMessage.value = `از درخواست ${materialRequestDetail.value.name} پیش‌نویس خرید ${result.purchase.name} ساخته شد.`
    materialRequestDetail.value = null
    await loadPurchases()
    setActiveTab('purchase')
  } catch (err) {
    requestError.value = err.message || 'ساخت پیش‌نویس خرید ناموفق بود.'
  } finally {
    requestPurchaseSaving.value = false
  }
}

async function printMaterialRequest() {
  if (!materialRequestDetail.value) return
  try {
    const payload = await getManagementMaterialRequestPrint(materialRequestDetail.value.name)
    if (payload?.html) printReceipt(payload.html, `درخواست مواد ${payload.name}`)
  } catch (err) {
    requestError.value = err.message || 'آماده‌سازی چاپ درخواست ناموفق بود.'
  }
}

// ------------------------- materials excel -------------------------
const materialExcelBusy = ref(false)
const materialExcelMode = ref('')
const materialExcelInput = ref(null)
const materialExcelSummary = ref(null)

async function exportMaterialsExcel() {
  materialExcelBusy.value = true
  materialExcelMode.value = 'export'
  materialsError.value = ''
  materialsMessage.value = ''
  try {
    const payload = await exportManagementMaterialsExcel({ search: materialsSearch.value })
    if (payload?.file_url) {
      const link = document.createElement('a')
      link.href = payload.file_url
      link.download = payload.file_name || 'restaurant-materials.xlsx'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      materialsMessage.value = `خروجی اکسل ${formatQty(payload.rows || 0)} ماده اولیه آماده شد.`
    }
  } catch (err) {
    materialsError.value = err.message || 'دریافت خروجی اکسل ناموفق بود.'
  } finally {
    materialExcelBusy.value = false
    materialExcelMode.value = ''
  }
}

function triggerMaterialExcelImport() {
  if (materialExcelBusy.value) return
  const input = materialExcelInput.value
  if (input) {
    input.value = ''
    input.click()
  }
}

async function handleMaterialExcelFile(event) {
  const file = event?.target?.files?.[0]
  if (!file) return
  materialExcelBusy.value = true
  materialExcelMode.value = 'import'
  materialsError.value = ''
  materialsMessage.value = ''
  try {
    const uploaded = await uploadFileToFrappe(file, { isPrivate: true })
    const fileUrl = uploaded?.file_url || uploaded?.message?.file_url || ''
    if (!fileUrl) throw new Error('آپلود فایل ناموفق بود.')
    materialExcelSummary.value = await importManagementMaterialsExcel({ file_url: fileUrl, update_existing: 1 })
    await Promise.all([loadMaterials(), loadBoot()])
  } catch (err) {
    materialsError.value = err.message || 'ورود از اکسل ناموفق بود.'
  } finally {
    materialExcelBusy.value = false
    materialExcelMode.value = ''
  }
}
const allItemOptions = computed(() => [...materialOptions.value, ...productOptions.value])

async function loadMaterials(append = false) {
  materialsLoading.value = true
  materialsError.value = ''
  materialsMessage.value = ''
  try {
    const payload = await listManagementRawMaterials({
      search: materialsSearch.value,
      include_inactive: materialsShowInactive.value ? 1 : 0,
      limit: 100,
      offset: append ? materialsOffset.value : 0,
    })
    if (append) {
      materials.value = [...materials.value, ...payload.items]
    } else {
      materials.value = payload.items
    }
    materialsHasMore.value = !!payload.has_more
    materialsOffset.value = (append ? materialsOffset.value : 0) + payload.items.length
    const pool = new Map(materialOptionsPool.value.map((m) => [m.name, m]))
    payload.items.forEach((m) => pool.set(m.name, m))
    materialOptionsPool.value = Array.from(pool.values())
  } catch (err) {
    materialsError.value = err.message || 'خطا در دریافت مواد اولیه.'
  } finally {
    materialsLoading.value = false
  }
}
function loadMoreMaterials() {
  loadMaterials(true)
}

function openMaterialForm(row = null) {
  materialFormError.value = ''
  if (row) {
    materialForm.value = {
      name: row.name,
      item_code: row.name,
      item_name: row.item_name,
      item_group: row.item_group || (boot.value?.item_groups[0]?.name || ''),
      stock_uom: row.stock_uom,
      purchase_rate: row.purchase_rate,
      default_supplier: row.default_supplier || '',
      disabled: !!row.disabled,
      reorder_levels: (row.reorder_levels || []).map((rl) => ({ ...rl })),
      opening: { warehouse: '', qty: 0 },
    }
  } else {
    materialForm.value = {
      name: '',
      item_code: '',
      item_name: '',
      item_group: boot.value?.item_groups[0]?.name || '',
      stock_uom: 'Nos',
      purchase_rate: 0,
      default_supplier: '',
      disabled: false,
      reorder_levels: [],
      opening: { warehouse: boot.value?.settings?.default_warehouse || '', qty: 0, rate: 0 },
    }
  }
}

async function saveMaterial() {
  if (!materialForm.value) return
  materialSaving.value = true
  materialFormError.value = ''
  try {
    const form = materialForm.value
    const payload = {
      name: form.name,
      item_code: form.item_code,
      item_name: form.item_name,
      item_group: form.item_group,
      stock_uom: form.stock_uom,
      purchase_rate: form.purchase_rate,
      default_supplier: form.default_supplier,
      disabled: form.disabled ? 1 : 0,
      reorder_levels: form.reorder_levels.filter((rl) => rl.warehouse),
    }
    if (!form.name && form.opening.qty > 0 && form.opening.warehouse) {
      payload.opening = { warehouse: form.opening.warehouse, qty: form.opening.qty, rate: form.purchase_rate }
    }
    await saveManagementRawMaterial(payload)
    materialForm.value = null
    materialsMessage.value = 'ماده اولیه ذخیره شد.'
    await Promise.all([loadMaterials(), loadBoot()])
  } catch (err) {
    materialFormError.value = err.message || 'ذخیره ناموفق بود.'
  } finally {
    materialSaving.value = false
  }
}

// ------------------------- warehouses -------------------------
const warehouses = ref([])
const warehousesLoading = ref(false)
const warehousesError = ref('')
const warehousesMessage = ref('')
const warehouseForm = ref(null)
const warehouseFormError = ref('')
const warehouseSaving = ref(false)

async function loadWarehouses() {
  warehousesLoading.value = true
  warehousesError.value = ''
  warehousesMessage.value = ''
  try {
    const payload = await listManagementWarehouses()
    warehouses.value = payload.warehouses
  } catch (err) {
    warehousesError.value = err.message || 'خطا در دریافت انبارها.'
  } finally {
    warehousesLoading.value = false
  }
}

function openWarehouseForm(row = null) {
  warehouseFormError.value = ''
  warehouseForm.value = row
    ? {
        name: row.name,
        warehouse_name: row.warehouse_name,
        parent_warehouse: row.parent_warehouse || '',
        is_group: !!row.is_group,
        disabled: !!row.disabled,
      }
    : { name: '', warehouse_name: '', parent_warehouse: '', is_group: false, disabled: false }
}

async function saveWarehouse() {
  if (!warehouseForm.value) return
  warehouseSaving.value = true
  warehouseFormError.value = ''
  try {
    const form = warehouseForm.value
    await saveManagementWarehouse({
      name: form.name,
      warehouse_name: form.warehouse_name,
      parent_warehouse: form.parent_warehouse,
      is_group: form.is_group ? 1 : 0,
      disabled: form.disabled ? 1 : 0,
    })
    warehouseForm.value = null
    warehousesMessage.value = 'انبار ذخیره شد.'
    await Promise.all([loadWarehouses(), loadBoot()])
  } catch (err) {
    warehouseFormError.value = err.message || 'ذخیره انبار ناموفق بود.'
  } finally {
    warehouseSaving.value = false
  }
}

async function removeWarehouse(row) {
  if (!window.confirm(`انبار «${row.warehouse_name}» حذف/غیرفعال شود؟`)) return
  warehousesError.value = ''
  warehousesMessage.value = ''
  try {
    await deleteManagementWarehouse(row.name)
    warehousesMessage.value = 'انبار حذف/غیرفعال شد.'
    await Promise.all([loadWarehouses(), loadBoot()])
  } catch (err) {
    warehousesError.value = err.message || 'حذف انبار ناموفق بود.'
  }
}

// ------------------------- movements -------------------------
const movementForm = reactive({
  movement_type: 'receipt',
  from_warehouse: '',
  to_warehouse: '',
  posting_date: new Date().toISOString().slice(0, 10),
  reason: '',
  lines: [{ item_code: '', qty: 1, rate: 0 }],
})
const movementSaving = ref(false)
const movements = ref([])
const movementsLoading = ref(false)
const movementsError = ref('')
const movementsMessage = ref('')
const movementFilters = reactive({ date_from: '', date_to: '', warehouse: '', kind: '' })

async function submitMovement() {
  movementSaving.value = true
  movementsError.value = ''
  movementsMessage.value = ''
  try {
    const lines = movementForm.lines.filter((line) => line.item_code && Number(line.qty) > 0)
    if (!lines.length) throw new Error('حداقل یک قلم با کالا و مقدار معتبر لازم است.')
    const result = await createManagementStockMovement({
      movement_type: movementForm.movement_type,
      from_warehouse: movementForm.from_warehouse,
      to_warehouse: movementForm.to_warehouse,
      posting_date: movementForm.posting_date,
      reason: movementForm.reason,
      lines,
    })
    movementsMessage.value = `گردش ثبت شد: ${result.stock_entry.name}`
    movementForm.lines = [{ item_code: '', qty: 1, rate: 0 }]
    movementForm.reason = ''
    await Promise.all([loadMovements(), loadBoot()])
  } catch (err) {
    movementsError.value = err.message || 'ثبت گردش ناموفق بود.'
  } finally {
    movementSaving.value = false
  }
}

async function loadMovements() {
  movementsLoading.value = true
  movementsError.value = ''
  try {
    const payload = await listManagementStockMovements({ ...movementFilters })
    movements.value = payload.movements
  } catch (err) {
    movementsError.value = err.message || 'خطا در دریافت سوابق.'
  } finally {
    movementsLoading.value = false
  }
}

// ------------------------- reorder -------------------------
const reorderAlerts = ref([])
const reorderLoading = ref(false)
const reorderError = ref('')
const reorderMessage = ref('')
const reorderWarehouse = ref('')
const selectedAlerts = ref([])
const reorderSaving = ref(false)

async function loadReorderAlerts() {
  reorderLoading.value = true
  reorderError.value = ''
  reorderMessage.value = ''
  selectedAlerts.value = []
  try {
    const payload = await getManagementReorderAlerts({ warehouse: reorderWarehouse.value })
    reorderAlerts.value = payload.alerts
  } catch (err) {
    reorderError.value = err.message || 'خطا در دریافت هشدارها.'
  } finally {
    reorderLoading.value = false
  }
}

function toggleAllAlerts(evt) {
  selectedAlerts.value = evt.target.checked ? [...reorderAlerts.value] : []
}

async function createPurchaseFromAlerts() {
  if (!selectedAlerts.value.length) return
  reorderSaving.value = true
  reorderError.value = ''
  reorderMessage.value = ''
  try {
    const payload = await createManagementPurchaseFromAlerts({
      items: selectedAlerts.value.map((row) => ({ item_code: row.item_code, qty: row.suggested_qty })),
      target_warehouse: boot.value?.settings?.default_warehouse || '',
    })
    reorderMessage.value = `${payload.count} پیش‌نویس خرید ایجاد شد: ${payload.created.map((c) => c.order).join('، ')}`
    selectedAlerts.value = []
    setActiveTab('purchase')
  } catch (err) {
    reorderError.value = err.message || 'ایجاد پیش‌نویس ناموفق بود.'
  } finally {
    reorderSaving.value = false
  }
}

// ------------------------- purchase -------------------------
const purchases = ref([])
const purchaseLoading = ref(false)
const purchaseError = ref('')
const purchaseMessage = ref('')
const purchaseFilters = reactive({ status: '', search: '' })
const showPurchaseForm = ref(false)
const purchaseForm = reactive({
  name: '',
  supplier: '',
  target_warehouse: '',
  posting_date: new Date().toISOString().slice(0, 10),
  expected_date: '',
  note: '',
  items: [{ item_code: '', qty: 1, rate: 0 }],
})
const purchaseSaving = ref(false)
const purchaseDetail = ref(null)
const receiveLines = reactive({})
const receiveWarehouse = ref('')
const supplierForm = ref(null)
const supplierFormError = ref('')
const supplierSaving = ref(false)

const canReceivePurchase = computed(
  () => purchaseDetail.value && ['ارسال‌شده', 'دریافت جزئی'].includes(purchaseDetail.value.status),
)

async function loadPurchases() {
  purchaseLoading.value = true
  purchaseError.value = ''
  purchaseMessage.value = ''
  try {
    const payload = await listManagementPurchaseOrders({ ...purchaseFilters })
    purchases.value = payload.orders
  } catch (err) {
    purchaseError.value = err.message || 'خطا در دریافت سفارش‌ها.'
  } finally {
    purchaseLoading.value = false
  }
}

function togglePurchaseForm() {
  showPurchaseForm.value = !showPurchaseForm.value
  if (showPurchaseForm.value) resetPurchaseForm()
}
function resetPurchaseForm() {
  Object.assign(purchaseForm, {
    name: '',
    supplier: '',
    target_warehouse: boot.value?.settings?.default_warehouse || '',
    posting_date: new Date().toISOString().slice(0, 10),
    expected_date: '',
    note: '',
    items: [{ item_code: '', qty: 1, rate: 0 }],
  })
}

async function savePurchase() {
  purchaseSaving.value = true
  purchaseError.value = ''
  purchaseMessage.value = ''
  try {
    const items = purchaseForm.items.filter((line) => line.item_code && Number(line.qty) > 0)
    if (!items.length) throw new Error('حداقل یک قلم معتبر لازم است.')
    const result = await saveManagementPurchaseOrder({
      name: purchaseForm.name,
      supplier: purchaseForm.supplier,
      target_warehouse: purchaseForm.target_warehouse,
      posting_date: purchaseForm.posting_date,
      expected_date: purchaseForm.expected_date,
      note: purchaseForm.note,
      items,
    })
    purchaseMessage.value = `پیش‌نویس ذخیره شد: ${result.order.name}`
    showPurchaseForm.value = false
    await loadPurchases()
  } catch (err) {
    purchaseError.value = err.message || 'ذخیره سفارش ناموفق بود.'
  } finally {
    purchaseSaving.value = false
  }
}

async function openPurchaseDetail(name) {
  purchaseError.value = ''
  try {
    const payload = await getManagementPurchaseOrder(name)
    purchaseDetail.value = payload.order
    Object.keys(receiveLines).forEach((key) => delete receiveLines[key])
    payload.order.items.forEach((row) => {
      receiveLines[row.item_code] = 0
    })
    receiveWarehouse.value = payload.order.target_warehouse || boot.value?.settings?.default_warehouse || ''
  } catch (err) {
    purchaseError.value = err.message || 'خطا در دریافت جزئیات سفارش.'
  }
}

function editPurchaseDraft() {
  if (!purchaseDetail.value) return
  const detail = purchaseDetail.value
  Object.assign(purchaseForm, {
    name: detail.name,
    supplier: detail.supplier,
    target_warehouse: detail.target_warehouse,
    posting_date: detail.posting_date || new Date().toISOString().slice(0, 10),
    expected_date: detail.expected_date,
    note: detail.note,
    items: detail.items.map((row) => ({ item_code: row.item_code, qty: row.qty, rate: row.rate })),
  })
  showPurchaseForm.value = true
  purchaseDetail.value = null
}

async function setPurchaseStatus(status) {
  if (!purchaseDetail.value) return
  purchaseError.value = ''
  try {
    const payload = await updateManagementPurchaseOrderStatus({ name: purchaseDetail.value.name, status })
    purchaseDetail.value = payload.order
    await loadPurchases()
  } catch (err) {
    purchaseError.value = err.message || 'تغییر وضعیت ناموفق بود.'
  }
}

async function receivePurchase() {
  if (!purchaseDetail.value) return
  const lines = Object.entries(receiveLines)
    .filter(([, qty]) => Number(qty) > 0)
    .map(([item_code, qty]) => ({ item_code, qty: Number(qty) }))
  if (!lines.length) {
    purchaseError.value = 'برای حداقل یک قلم مقدار دریافتی وارد کنید.'
    return
  }
  purchaseSaving.value = true
  purchaseError.value = ''
  try {
    const payload = await receiveManagementPurchaseOrder({
      name: purchaseDetail.value.name,
      warehouse: receiveWarehouse.value,
      lines,
    })
    purchaseDetail.value = payload.order
    purchaseMessage.value = `دریافت ثبت شد: ${payload.stock_entry.name}`
    Object.keys(receiveLines).forEach((key) => {
      receiveLines[key] = 0
    })
    await Promise.all([loadPurchases(), loadBoot()])
  } catch (err) {
    purchaseError.value = err.message || 'ثبت دریافت ناموفق بود.'
  } finally {
    purchaseSaving.value = false
  }
}

function purchaseStatusClass(status) {
  if (status === 'دریافت کامل') return 'ok'
  if (status === 'لغوشده') return 'warn'
  return ''
}

function printReceipt(html, title = 'سفارش خرید') {
  if (!html) return
  const printWindow = window.open('', '_blank', 'width=800,height=640')
  if (!printWindow) return
  printWindow.document.write(`<!DOCTYPE html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>${title}</title></head><body>${html}</body></html>`)
  printWindow.document.close()
  printWindow.focus()
  printWindow.print()
}

const purchasePrinting = ref(false)
async function printPurchaseOrder() {
  if (!purchaseDetail.value || purchasePrinting.value) return
  purchasePrinting.value = true
  purchaseError.value = ''
  try {
    const payload = await getManagementInventoryPurchasePrint(purchaseDetail.value.name)
    if (payload?.html) printReceipt(payload.html, `سفارش خرید ${payload.name}`)
  } catch (err) {
    purchaseError.value = err.message || 'آماده‌سازی چاپ ناموفق بود.'
  } finally {
    purchasePrinting.value = false
  }
}

function openSupplierForm() {
  supplierFormError.value = ''
  supplierForm.value = { supplier_name: '' }
}
async function saveSupplier() {
  if (!supplierForm.value) return
  supplierSaving.value = true
  supplierFormError.value = ''
  try {
    await saveManagementSupplier({ supplier_name: supplierForm.value.supplier_name })
    supplierForm.value = null
    purchaseMessage.value = 'تأمین‌کننده ذخیره شد.'
    await loadBoot()
  } catch (err) {
    supplierFormError.value = err.message || 'ذخیره تأمین‌کننده ناموفق بود.'
  } finally {
    supplierSaving.value = false
  }
}

// ------------------------- production -------------------------
const plan = ref(null)
const planLoading = ref(false)
const productionError = ref('')
const productionMessage = ref('')
const planFilters = reactive({
  date_from: new Date(Date.now() - 6 * 864e5).toISOString().slice(0, 10),
  date_to: new Date().toISOString().slice(0, 10),
})
const productionForm = reactive({ menu_item: '', qty: 1, source_warehouse: '', target_warehouse: '' })
const productionSaving = ref(false)
const productsPool = ref([])

const productOptions = computed(() =>
  productsPool.value.map((p) => ({ value: p.name, label: `${p.title || p.item_name || p.name} (${p.name})` })),
)

async function loadProductsPool() {
  try {
    const payload = await listManagementProducts({ active_only: 0 })
    productsPool.value = (payload.products || []).filter(
      (p) => String(p.name || p.item_code || '').trim(),
    )
  } catch {
    productsPool.value = []
  }
}

async function loadProductionPlan() {
  planLoading.value = true
  productionError.value = ''
  try {
    plan.value = await getManagementProductionPlan({ ...planFilters })
  } catch (err) {
    productionError.value = err.message || 'خطا در محاسبه برنامه تولید.'
  } finally {
    planLoading.value = false
  }
}

async function submitProduction() {
  productionSaving.value = true
  productionError.value = ''
  productionMessage.value = ''
  try {
    if (!productionForm.menu_item) throw new Error('محصول را انتخاب کنید.')
    const result = await createManagementProductionEntry({ ...productionForm })
    productionMessage.value = `سند تولید ثبت شد: ${result.stock_entry.name}`
    await Promise.all([loadProductionPlan(), loadBoot()])
  } catch (err) {
    productionError.value = err.message || 'ثبت تولید ناموفق بود.'
  } finally {
    productionSaving.value = false
  }
}

// ------------------------- losses -------------------------
const wasteReport = ref(null)
const lossesLoading = ref(false)
const lossesError = ref('')
const lossesMessage = ref('')
const lossFilters = reactive({
  date_from: new Date(Date.now() - 29 * 864e5).toISOString().slice(0, 10),
  date_to: new Date().toISOString().slice(0, 10),
  warehouse: '',
})
const lossForm = reactive({
  loss_kind: 'اوت شده',
  source_type: 'دستی',
  source_reference: '',
  item_code: '',
  qty: 1,
  warehouse: '',
  reason: '',
  amount: 0,
})
const lossSaving = ref(false)
const orderLosses = ref([])
const lossListFilter = ref('')

async function loadWasteReport() {
  lossesLoading.value = true
  lossesError.value = ''
  try {
    wasteReport.value = await getManagementWasteLossReport({ ...lossFilters })
  } catch (err) {
    lossesError.value = err.message || 'خطا در دریافت گزارش.'
  } finally {
    lossesLoading.value = false
  }
}

async function loadOrderLosses() {
  lossesError.value = ''
  try {
    const payload = await listManagementOrderLosses({ loss_kind: lossListFilter.value })
    orderLosses.value = payload.losses
  } catch (err) {
    lossesError.value = err.message || 'خطا در دریافت سوابق.'
  }
}

async function submitOrderLoss() {
  lossSaving.value = true
  lossesError.value = ''
  lossesMessage.value = ''
  try {
    if (!lossForm.item_code) throw new Error('کالا را انتخاب کنید.')
    const result = await saveManagementOrderLoss({ ...lossForm })
    lossesMessage.value = `ثبت شد: ${result.name}${result.stock_entry ? ` (سند انبار: ${result.stock_entry})` : ''}`
    lossForm.reason = ''
    lossForm.source_reference = ''
    lossForm.qty = 1
    await Promise.all([loadOrderLosses(), loadWasteReport(), loadBoot()])
  } catch (err) {
    lossesError.value = err.message || 'ثبت ناموفق بود.'
  } finally {
    lossSaving.value = false
  }
}

// ------------------------- reconciliation -------------------------
const countWarehouse = ref('')
const countSearch = ref('')
const countContext = ref(null)
const countRows = ref([])
const countLoading = ref(false)
const countSaving = ref(false)
const countError = ref('')
const countMessage = ref('')
const countResult = ref(null)
const reconciliations = ref([])
const reconciliationDetail = ref(null)

const countedRows = computed(() => countRows.value.filter((row) => countDiff(row) !== 0))
function countDiff(row) {
  if (row.counted === null || row.counted === undefined || row.counted === '') return 0
  return Number((Number(row.counted) - Number(row.system_qty)).toFixed(4))
}

async function loadCountContext() {
  countLoading.value = true
  countError.value = ''
  countMessage.value = ''
  countResult.value = null
  try {
    countContext.value = await getManagementReconciliationContext({ warehouse: countWarehouse.value, search: countSearch.value })
    countRows.value = (countContext.value.items || []).map((row) => ({ ...row, counted: null }))
  } catch (err) {
    countError.value = err.message || 'خطا در بارگذاری برگه شمارش.'
  } finally {
    countLoading.value = false
  }
}

function resetCountRows() {
  countRows.value = []
  countContext.value = null
  countResult.value = null
}

async function submitCount() {
  countSaving.value = true
  countError.value = ''
  countMessage.value = ''
  try {
    if (!countedRows.value.length) throw new Error('هیچ مغایرتی برای ثبت وجود ندارد.')
    const payload = await submitManagementStockReconciliation({
      warehouse: countWarehouse.value,
      items: countedRows.value.map((row) => ({
        item_code: row.item_code,
        qty: Number(row.counted),
        valuation_rate: row.valuation_rate,
      })),
    })
    countResult.value = payload
    countMessage.value = `انبارگردانی ثبت شد: ${payload.name}`
    countRows.value = []
    await Promise.all([loadReconciliations(), loadBoot()])
  } catch (err) {
    countError.value = err.message || 'ثبت انبارگردانی ناموفق بود.'
  } finally {
    countSaving.value = false
  }
}

async function loadReconciliations() {
  try {
    const payload = await listManagementStockReconciliations()
    reconciliations.value = payload.reconciliations
  } catch {
    reconciliations.value = []
  }
}

async function viewReconciliation(name) {
  countError.value = ''
  try {
    reconciliationDetail.value = await getManagementStockReconciliation(name)
  } catch (err) {
    countError.value = err.message || 'خطا در دریافت جزئیات.'
  }
}

// ------------------------- costs -------------------------
const costs = ref([])
const costsLoading = ref(false)
const costsError = ref('')
const costSearch = ref('')
const expandedCost = ref('')

async function loadCosts() {
  costsLoading.value = true
  costsError.value = ''
  try {
    const payload = await getManagementProductCostReport({ search: costSearch.value })
    costs.value = payload.products
  } catch (err) {
    costsError.value = err.message || 'خطا در محاسبه بهای تمام‌شده.'
  } finally {
    costsLoading.value = false
  }
}
function toggleCostDetail(code) {
  expandedCost.value = expandedCost.value === code ? '' : code
}

// ------------------------- tab orchestration -------------------------
function setActiveTab(key) {
  activeTab.value = key
  loadTabData(key)
}

function loadTabData(key) {
  if (key === 'overview' && !overview.value) loadOverview()
  if (key === 'materials' && !materials.value.length) loadMaterials()
  if (key === 'warehouses' && !warehouses.value.length) loadWarehouses()
  if (key === 'movements' && !movements.value.length) loadMovements()
  if (key === 'reorder' && !reorderAlerts.value.length) loadReorderAlerts()
  if (key === 'requests' && !materialRequests.value.length) loadMaterialRequests()
  if (key === 'purchase' && !purchases.value.length) loadPurchases()
  if (key === 'production' && !plan.value) loadProductionPlan()
  if (key === 'losses') {
    if (!wasteReport.value) loadWasteReport()
    if (!orderLosses.value.length) loadOrderLosses()
  }
  if (key === 'count' && !reconciliations.value.length) loadReconciliations()
  if (key === 'costs' && !costs.value.length) loadCosts()
}

function reloadActiveTab() {
  const loaders = {
    overview: loadOverview,
    materials: loadMaterials,
    warehouses: loadWarehouses,
    movements: loadMovements,
    reorder: loadReorderAlerts,
    requests: loadMaterialRequests,
    purchase: loadPurchases,
    production: loadProductionPlan,
    losses: () => Promise.all([loadWasteReport(), loadOrderLosses()]),
    count: loadReconciliations,
    costs: loadCosts,
  }
  loadBoot()
  const loader = loaders[activeTab.value]
  if (loader) loader()
}

onMounted(async () => {
  await loadBoot()
  loadOverview()
  loadProductsPool()
})
</script>

<style scoped>
.tabs-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.tab-btn {
  border: 1px solid var(--border-color, #d8d2c4);
  background: var(--surface-soft, #f7f4ee);
  color: var(--text-primary, #2f3c36);
  border-radius: 999px;
  padding: 0.45rem 1rem;
  cursor: pointer;
  font: inherit;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}
.tab-btn.active {
  background: var(--accent-green, #2f6f5c);
  border-color: var(--accent-green, #2f6f5c);
  color: #fff;
}
.tab-body {
  display: grid;
  gap: 0.9rem;
}
.boot-kpis {
  margin-bottom: 0.2rem;
}
.totals-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0.55rem;
}
.total-box {
  border: 1px dashed var(--border-color, #d8d2c4);
  border-radius: 12px;
  padding: 0.55rem 0.7rem;
  display: grid;
  gap: 0.2rem;
}
.total-box small {
  color: var(--text-muted, #6b7a72);
}
.total-box.warn-border {
  border-color: rgba(184, 79, 79, 0.5);
}
.meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.65rem;
  margin-bottom: 0.6rem;
}
.meta-grid small {
  display: block;
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
  min-width: 170px;
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
.input.compact {
  max-width: 110px;
  padding: 0.25rem 0.4rem;
}
.btn-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.6rem;
}
.table-wrap {
  overflow-x: auto;
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
.data-table tr.group td {
  background: var(--surface-soft, #f7f4ee);
}
.data-table .sub-row td {
  background: var(--surface-soft, #f9f7f2);
  font-size: 0.82rem;
}
.data-table.inner {
  margin-top: 0.3rem;
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
}
.pill.ok {
  background: rgba(47, 111, 92, 0.14);
  color: var(--accent-green, #2f6f5c);
}
.pill.warn {
  background: rgba(184, 79, 79, 0.14);
  color: #b84f4f;
}
.badge {
  display: inline-block;
  border-radius: 999px;
  padding: 0.05rem 0.5rem;
  font-size: 0.72rem;
  background: rgba(184, 79, 79, 0.16);
  color: #b84f4f;
}
.tab-btn.active .badge {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}
.check-row {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.88rem;
}
.lines-editor {
  display: grid;
  gap: 0.45rem;
}
.line-row {
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(0, 1fr) minmax(0, 1fr) auto;
  gap: 0.5rem;
  align-items: center;
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
.request-toolbar {
  display: grid;
  grid-template-columns: minmax(130px, 0.8fr) minmax(140px, 0.9fr) minmax(140px, 0.9fr) minmax(180px, 1.4fr) auto auto;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.85rem;
}

.request-toolbar .input {
  min-width: 0;
}

.material-request-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 0.65rem;
}

.material-request-card {
  min-width: 0;
  display: grid;
  gap: 0.55rem;
  padding: 0.8rem;
  border: 1px solid var(--border-color, #d8d2c4);
  border-radius: 16px;
  background: var(--surface-bg, #fff);
  cursor: pointer;
  transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease;
}

.material-request-card:hover {
  transform: translateY(-2px);
  border-color: var(--accent-green, #2f6f5c);
  box-shadow: 0 12px 28px rgb(47 111 92 / 0.1);
}

.material-request-card-head,
.material-request-card-foot {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
}

.material-request-card-head strong {
  display: block;
  font-size: 0.9rem;
}

.material-request-card-head small,
.material-request-card-foot {
  color: var(--text-muted, #6b7a72);
  font-size: 0.72rem;
}

.material-request-card-body {
  display: grid;
  gap: 0.3rem;
  padding: 0.5rem;
  border-radius: 12px;
  background: var(--surface-soft, #f7f4ee);
}

.request-item-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  font-size: 0.77rem;
}

.request-item-preview span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.request-item-preview strong {
  flex: 0 0 auto;
  color: var(--accent-green, #2f6f5c);
  font-size: 0.72rem;
}

.request-more-items {
  color: var(--text-muted, #6b7a72);
  font-size: 0.68rem;
}

.request-empty-state {
  grid-column: 1 / -1;
  padding: 2rem 1rem;
  text-align: center;
}

.material-request-popup,
.material-request-detail-popup {
  max-height: min(92vh, 860px);
}

.request-popup-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.7rem;
}

.request-popup-head h3 {
  margin: 0.1rem 0 0;
}

.request-kicker {
  color: var(--accent-green, #2f6f5c);
  font-size: 0.7rem;
  font-weight: 800;
}

.icon-close-btn {
  width: 34px;
  height: 34px;
  border: 1px solid var(--border-color, #d8d2c4);
  border-radius: 10px;
  background: transparent;
  color: var(--text-muted, #6b7a72);
  font-size: 1.2rem;
  cursor: pointer;
}

.request-lines-editor {
  display: grid;
  gap: 0.5rem;
  padding: 0.7rem;
  border: 1px solid var(--border-color, #d8d2c4);
  border-radius: 14px;
  background: var(--surface-soft, #f7f4ee);
}

.request-lines-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.request-lines-head span {
  color: var(--text-muted, #6b7a72);
  font-size: 0.7rem;
}

.request-line-row {
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(90px, 1fr) minmax(75px, 0.75fr) auto;
  gap: 0.45rem;
  align-items: center;
  padding: 0.45rem;
  border-radius: 12px;
  background: var(--surface-bg, #fff);
}

.request-uom-field {
  min-height: 38px;
  display: grid;
  align-content: center;
  gap: 0.1rem;
  padding: 0.25rem 0.45rem;
  border: 1px solid var(--border-color, #d8d2c4);
  border-radius: 9px;
}

.request-uom-field small {
  color: var(--text-muted, #6b7a72);
  font-size: 0.62rem;
}

.request-uom-field strong {
  font-size: 0.75rem;
}

.add-line-btn {
  width: fit-content;
}

.request-popup-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.5rem;
  padding-top: 0.3rem;
  border-top: 1px solid var(--border-color, #d8d2c4);
}

.request-detail-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0.55rem;
}

.request-detail-meta > div {
  display: grid;
  gap: 0.18rem;
  padding: 0.55rem;
  border-radius: 11px;
  background: var(--surface-soft, #f7f4ee);
}

.request-detail-meta small {
  color: var(--text-muted, #6b7a72);
  font-size: 0.68rem;
}

.request-detail-meta strong {
  font-size: 0.77rem;
}

.material-request-detail-lines {
  display: grid;
  gap: 0.4rem;
}

.request-detail-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  padding: 0.62rem 0.7rem;
  border: 1px solid var(--border-color, #d8d2c4);
  border-radius: 12px;
  background: var(--surface-bg, #fff);
}

.request-detail-line-main {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.request-detail-line-main > div {
  min-width: 0;
  display: grid;
  gap: 0.12rem;
}

.request-detail-line-main strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.8rem;
}

.request-detail-line-main small {
  color: var(--text-muted, #6b7a72);
  font-size: 0.67rem;
}

.request-line-index {
  width: 24px;
  height: 24px;
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: rgba(47, 111, 92, 0.12);
  color: var(--accent-green, #2f6f5c);
  font-size: 0.7rem;
  font-weight: 800;
}

.request-detail-line-qty {
  display: grid;
  justify-items: end;
  gap: 0.08rem;
  flex: 0 0 auto;
}

.request-detail-line-qty strong {
  color: var(--accent-green, #2f6f5c);
  font-size: 0.86rem;
}

.request-detail-line-qty span {
  color: var(--text-muted, #6b7a72);
  font-size: 0.68rem;
}

.request-note {
  margin: 0;
  padding: 0.65rem;
  border-radius: 11px;
  background: var(--surface-soft, #f7f4ee);
  color: var(--text-muted, #6b7a72);
  white-space: pre-line;
  font-size: 0.78rem;
}

.request-purchase-links {
  display: grid;
  gap: 0.35rem;
  padding: 0.65rem;
  border-radius: 12px;
  background: rgba(47, 111, 92, 0.07);
}

.purchase-link {
  width: fit-content;
  border: 0;
  background: transparent;
  color: var(--accent-green, #2f6f5c);
  font: inherit;
  font-size: 0.75rem;
  cursor: pointer;
}

.inline-form {
  border: 1px dashed var(--border-color, #d8d2c4);
  border-radius: 12px;
  padding: 0.8rem 0.9rem;
  margin-bottom: 0.8rem;
  display: grid;
  gap: 0.5rem;
}
.result-block {
  margin-top: 0.8rem;
  margin-bottom: 0;
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
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}
.error-list {
  margin: 0;
  padding-inline-start: 1.1rem;
  color: #b84f4f;
  font-size: 0.82rem;
}
.hint-line {
  font-size: 0.78rem;
  color: var(--text-muted, #6b7a72);
  margin-top: 0.5rem;
}
.receive-warehouse-row {
  margin-top: 0.5rem;
}
.alert-row td {
  background: rgba(184, 79, 79, 0.04);
}
@media (max-width: 720px) {
  .line-row {
    grid-template-columns: minmax(0, 1fr);
  }
  .toolbar .input {
    flex: 1 1 100%;
    min-width: 100%;
  }
  .request-toolbar {
    grid-template-columns: 1fr 1fr;
  }
  .request-toolbar .request-search,
  .request-toolbar button:last-child {
    grid-column: 1 / -1;
  }
  .request-line-row {
    grid-template-columns: minmax(0, 1fr) minmax(90px, 1fr);
  }
  .request-line-row .request-uom-field,
  .request-line-row .tertiary-btn {
    min-height: 38px;
  }
  .request-lines-head {
    align-items: flex-start;
    flex-direction: column;
  }
  .request-popup-actions {
    justify-content: stretch;
  }
  .request-popup-actions > button {
    flex: 1 1 100%;
  }
  .material-request-card-head,
  .material-request-card-foot {
    align-items: flex-start;
    flex-direction: column;
  }
  .request-detail-meta {
    grid-template-columns: 1fr 1fr;
  }
  .material-request-popup,
  .material-request-detail-popup {
    width: 100%;
    max-height: 94vh;
    padding: 0.85rem;
  }
}

@media (max-width: 390px) {
  .request-toolbar {
    grid-template-columns: 1fr;
  }
  .request-toolbar .request-search,
  .request-toolbar button:last-child {
    grid-column: auto;
  }
  .request-detail-meta {
    grid-template-columns: 1fr;
  }
}
</style>
