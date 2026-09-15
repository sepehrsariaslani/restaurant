# معماری کامل جزئیات محصول — برنامه پیاده‌سازی

> **برای عامل‌های اجرایی:** برای اجرای این برنامه از `superpowers:executing-plans` یا `superpowers:subagent-driven-development` استفاده شود. مراحل با checkbox (`- [ ]`) قابل پیگیری هستند.

**هدف:** صفحه جزئیات محصول Restaurant را به مرجع یکپارچه مدیریت Item تبدیل کنیم؛ با تب‌های کم‌تراکم، فیلدها و جدول‌های native کالا، اتصالات اسناد و عملیات واقعی انبار/دفتر موجودی.

**معماری:** Restaurant فقط facade فارسی و RTL است و داده، lifecycle، permission و ledger را از ERPNext می‌خواند و روی همان DocTypeهای `Item`, `Bin`, `Stock Ledger Entry`, `Item Price`, `BOM` و اسناد خرید/فروش/انبار عمل می‌کند. جزئیات native، اتصالات و موجودی به‌صورت payloadهای مشخص از API برمی‌گردند؛ UI آن‌ها را در کامپوننت‌های مستقل و lazy-loaded نمایش می‌دهد. `EditableTable` برای child tableهای قابل ویرایش و `SmartDataTable` برای گزارش، ledger و اتصالات read-only استفاده می‌شود.

**فناوری:** Vue 3، Frappe Python API، `ManagementEditableTable`, `ManagementSmartDataTable`, `ManagementPopup`, SearchableDropdown، semantic Restaurant tokens و تست‌های Node/Python موجود پروژه.

**Spec:** `docs/superpowers/specs/2026-09-15-product-detail-information-architecture-design.md`

## محدودیت‌های سراسری

- منبع داده و مالکیت lifecycle همچنان ERPNext/Frappe است و مدل موازی برای Item یا ledger ساخته نمی‌شود.
- تب‌های اصلی باید این شش مسیر را پوشش دهند: خلاصه، فروش و نمایش، فرمول و تولید، مدل‌ها و سفارشی‌سازی، انبار و موجودی، گزارش و تاریخچه.
- تب «اتصالات» به‌عنوان قابلیت cross-domain اضافه می‌شود و در کنار این شش مسیر قرار می‌گیرد.
- جدول BOM و child tableهای قابل تغییر با `ManagementEditableTable` هستند؛ ledger، تاریخچه، KPI و اتصالات با `ManagementSmartDataTable` یا `ManagementDataTable` خواندنی هستند.
- URL، payloadهای فعلی و رفتارهای موجود product detail حفظ می‌شوند؛ مقدارهای قدیمی `builder` و `changes` به تب جدید مربوط نگاشت می‌شوند.
- build، restart، `bench migrate` و Graphify/remote update اجرا نمی‌شوند.

---

### کار ۱: قرارداد API برای native item، اتصالات و موجودی

**فایل‌ها:**
- تغییر: `restaurant/api.py` در `get_management_product_detail` و endpoint جدید native/connections.
- تغییر: `restaurant/api_inventory.py` برای endpoint موجودی مخصوص یک Item.
- تغییر: `frontend/src/utils/api.js` برای wrapperهای endpoint.
- ایجاد: `frontend/tests/management-product-detail-operations.test.mjs`.
- تغییر: `frontend/tests/management-product-detail-payload.test.mjs` برای قرارداد payload ذخیره native.

**رابط‌ها:**
- `get_management_product_detail(item_name, date_from, date_to)` بخش `native` را با فیلدهای Item و child tableهای زیر برمی‌گرداند: `attributes`, `barcodes`, `reorder_levels`, `uoms`, `supplier_items`, `customer_items`, `taxes`, `item_defaults`.
- `get_management_product_connections(item_name, limit=200)` مقدار `{groups, count}` برمی‌گرداند؛ هر ردیف شامل `doctype`, `name`, `title`, `date`, `status`, `amount`, `route` است.
- `get_management_product_inventory(item_name, date_from='', date_to='', warehouse='', limit=200)` مقدار `{summary, bins, ledger, reorder_levels}` برمی‌گرداند.
- `update_management_product_native(payload)` فقط فیلدهای allowlist‌شده Item و child tableهای فوق را روی همان DocType ذخیره می‌کند و سپس detail کامل را برمی‌گرداند.
- در فرانت wrapperهای `getManagementProductConnections`, `getManagementProductInventory` و `updateManagementProductNative` دقیقاً همین نام‌ها را expose می‌کنند.

- [ ] **گام ۱: تست failing قرارداد فرانت را بنویس**

```js
test('product detail exposes native, connections and inventory API contracts', () => {
  assert.match(apiSource, /getManagementProductConnections/)
  assert.match(apiSource, /getManagementProductInventory/)
  assert.match(apiSource, /updateManagementProductNative/)
  assert.match(detailSource, /native/)
  assert.match(apiSource, /get_management_product_connections/)
  assert.match(apiSource, /get_management_product_inventory/)
})
```

- [ ] **گام ۲: اجرای تست failing**

Run: `cd frontend && node --test tests/management-product-detail-operations.test.mjs`

Expected: FAIL چون wrapperها و قراردادهای payload هنوز وجود ندارند.

- [ ] **گام ۳: پیاده‌سازی حداقلی API**

در `restaurant/api.py`، فیلدهای native موجود و child tableها با `frappe.get_meta('Item')` به‌صورت امن خوانده شوند؛ فیلدهایی که روی نسخه نصب‌شده وجود ندارند حذف شوند. در `restaurant/api_inventory.py`، برای `Bin` و `Stock Ledger Entry` فقط ردیف‌های همان Item خوانده شوند و query دارای date/warehouse/limit باشد. اتصالات از child tableهای `Sales Invoice Item`, `Sales Order Item`, `Delivery Note Item`, `Purchase Order Item`, `Purchase Receipt Item`, `Purchase Invoice Item`, `Stock Entry Detail`, `Material Request Item` و `BOM` جمع شوند؛ جدول/DocType ناموجود باید به‌صورت خالی رد شود.

در update native، فقط این گروه‌ها مجاز باشند: مشخصات پایه و variant، فروش، خرید، انبار، کیفیت/تولید، وب‌سایت و accounting؛ child tableها با `doc.set(fieldname, rows)` روی همان Item ذخیره شوند و هر row بدون `name/parent/parenttype/parentfield` خطرناک از payload حذف شود. بعد از save، detail دوباره خوانده شود.

- [ ] **گام ۴: اجرای تست و بررسی سبز شدن**

Run: `cd frontend && node --test tests/management-product-detail-operations.test.mjs tests/management-product-detail-payload.test.mjs`

Expected: PASS و در Python، import/syntax check فقط روی فایل‌های تغییرکرده اجرا شود؛ بدون migrate یا restart.

- [ ] **گام ۵: commit**

```bash
git add restaurant/api.py restaurant/api_inventory.py frontend/src/utils/api.js frontend/tests/management-product-detail-operations.test.mjs frontend/tests/management-product-detail-payload.test.mjs
git commit -m "افزودن قرارداد native و عملیات محصول"
```

### کار ۲: پنل native کالا و child tableهای قابل ویرایش

**فایل‌ها:**
- ایجاد: `frontend/src/utils/managementProductNative.js` برای schema، normalization و payload امن native.
- ایجاد: `frontend/src/components/management/catalog/ManagementProductNativePanel.vue`.
- تغییر: `frontend/src/pages/management/catalog/ManagementProductDetailPage.vue` برای اتصال فرم native به detail و save bar.
- تغییر: `frontend/src/composables/useProductDetail.js` برای نگهداری state native، snapshot و save action مشترک.
- تغییر: `frontend/tests/management-product-detail-operations.test.mjs`.

**رابط‌ها:**
- کامپوننت `ManagementProductNativePanel` props: `modelValue`, `loading`, `saving`, `fieldOptions`, `tables`; emits: `update:modelValue`, `save`.
- schema native هفت بخش را پوشش می‌دهد: طبقه‌بندی، مدل‌ها و بارکد، فروش، خرید، انبار، عملیات/کیفیت/تولید، مالیات و پیش‌فرض‌های شرکت.
- child tableهای `attributes`, `barcodes`, `reorder_levels`, `uoms`, `supplier_items`, `customer_items`, `taxes`, `item_defaults` با `ManagementEditableTable` نمایش داده می‌شوند و هر table عنوان/empty state/row key مشخص دارد.

- [ ] **گام ۱: تست failing پنل native**

```js
test('native product panel keeps Accounts item sections and editable child tables', () => {
  assert.match(nativeConfigSource, /classification/)
  assert.match(nativeConfigSource, /sales/)
  assert.match(nativeConfigSource, /purchase/)
  assert.match(nativeConfigSource, /inventory/)
  assert.match(nativeConfigSource, /operations/)
  assert.match(nativeConfigSource, /accounting/)
  for (const key of ['attributes', 'barcodes', 'reorder_levels', 'uoms', 'supplier_items', 'customer_items', 'taxes', 'item_defaults']) {
    assert.match(nativeConfigSource, new RegExp(key))
    assert.match(nativePanelSource, /ManagementEditableTable/)
  }
})
```

- [ ] **گام ۲: اجرای تست failing**

Run: `cd frontend && node --test tests/management-product-detail-operations.test.mjs`

Expected: FAIL چون config و panel ایجاد نشده‌اند.

- [ ] **گام ۳: پیاده‌سازی schema و panel**

schema باید label فارسی، field type، link doctype، `showWhen` و width table را در یک فایل نگه دارد. فیلدهای Link از `SearchableDropdown` استفاده کنند؛ checkboxها semantic label داشته باشند؛ child tableها فقط rows همان payload را edit کنند. هنگام loading/empty/error پیام همان surface نشان داده شود و هیچ table دوم برای همان داده در page باقی نماند.

- [ ] **گام ۴: اتصال به save bar**

صفحه باید native state را هنگام `syncForms` hydrate کند، dirty state آن را در snapshot حساب کند و save را با `updateManagementProductNative` انجام دهد. پس از save، detail، inventory و connections cache همان Item refresh شوند.

- [ ] **گام ۵: اجرای تست سبز**

Run: `cd frontend && node --test tests/management-product-detail-operations.test.mjs tests/management-product-detail-payload.test.mjs`

Expected: PASS.

- [ ] **گام ۶: commit**

```bash
git add frontend/src/utils/managementProductNative.js frontend/src/components/management/catalog/ManagementProductNativePanel.vue frontend/src/pages/management/catalog/ManagementProductDetailPage.vue frontend/src/composables/useProductDetail.js frontend/tests/management-product-detail-operations.test.mjs
git commit -m "افزودن پنل native و جدول های قابل ویرایش محصول"
```

### کار ۳: تب اتصالات بر اساس اسناد واقعی ERPNext

**فایل‌ها:**
- ایجاد: `frontend/src/components/management/catalog/ManagementProductConnectionsPanel.vue`.
- تغییر: `frontend/src/pages/management/catalog/ManagementProductDetailPage.vue` برای lazy load و تب `connections`.
- تغییر: `frontend/tests/management-product-detail-operations.test.mjs`.

**رابط‌ها:**
- پنل props: `groups`, `loading`, `error`, `itemName`; emits: `retry`, `open`.
- گروه‌ها: فروش، خرید، انبار و تولید، قیمت و فرمول. هر گروه count، empty state و SmartDataTable دارد.
- ردیف اتصال با click/دکمه «باز کردن» به route بازگشت‌داده‌شده از backend می‌رود؛ برای سندی که route مدیریتی ندارد، لینک native ERPNext با `target="_blank"` باز می‌شود.

- [ ] **گام ۱: تست failing**

```js
test('connections tab uses native document links and a read-only smart table', () => {
  assert.match(detailSource, /connections/)
  assert.match(connectionsSource, /ManagementSmartDataTable/)
  for (const type of ['Sales Invoice', 'Purchase Receipt', 'Stock Entry', 'BOM']) {
    assert.match(connectionsSource, new RegExp(type))
  }
})
```

- [ ] **گام ۲: اجرای failing test**

Run: `cd frontend && node --test tests/management-product-detail-operations.test.mjs`

Expected: FAIL چون پنل اتصالات و tab هنوز وجود ندارد.

- [ ] **گام ۳: پیاده‌سازی پنل و lazy loading**

با انتخاب تب فقط یک بار endpoint فراخوانی شود؛ در تغییر Item یا retry cache پاک شود. جدول فقط read-only باشد و مبلغ/تاریخ/وضعیت با formatter فارسی نمایش داده شود.

- [ ] **گام ۴: اجرای تست سبز و commit**

Run: `cd frontend && node --test tests/management-product-detail-operations.test.mjs`

```bash
git add frontend/src/components/management/catalog/ManagementProductConnectionsPanel.vue frontend/src/pages/management/catalog/ManagementProductDetailPage.vue frontend/tests/management-product-detail-operations.test.mjs
git commit -m "افزودن تب اتصالات اسناد محصول"
```

### کار ۴: تب انبار و عملیات، دفتر موجودی و تراز انبار

**فایل‌ها:**
- ایجاد: `frontend/src/components/management/catalog/ManagementProductInventoryPanel.vue`.
- تغییر: `frontend/src/pages/management/catalog/ManagementProductDetailPage.vue`.
- تغییر: `frontend/src/utils/api.js` در صورت تکمیل wrapperهای lazy loading.
- تغییر: `frontend/tests/management-product-detail-operations.test.mjs`.

**رابط‌ها:**
- پنل props: `summary`, `bins`, `ledger`, `reorderLevels`, `loading`, `error`, `dateRange`, `warehouse`; emits: `update:dateRange`, `update:warehouse`, `refresh`, `open-ledger`.
- summary شامل `actual_qty`, `projected_qty`, `reserved_qty`, `ordered_qty`, `indented_qty`, `value`, `valuation_rate` است.
- جدول «مانده به تفکیک انبار» از Bin و جدول «دفتر موجودی» از Stock Ledger Entry پر می‌شود؛ هر دو با `ManagementSmartDataTable` و ستون‌های محدود و قابل اسکرول هستند.
- کارت عملیات لینک‌های موجود به `/management/inventory`, `/management/inventory/count` و گزارش stock movements را نشان می‌دهد و عملیات posting را داخل صفحه detail دوباره‌سازی نمی‌کند.

- [ ] **گام ۱: تست failing**

```js
test('inventory tab exposes warehouse balance, stock ledger and native operations', () => {
  assert.match(detailSource, /activeTab === 'inventory'/)
  assert.match(inventoryPanelSource, /Stock Ledger|دفتر موجودی/)
  assert.match(inventoryPanelSource, /ManagementSmartDataTable/)
  assert.match(inventoryPanelSource, /management\/inventory\/count/)
  assert.match(apiSource, /get_management_product_inventory/)
})
```

- [ ] **گام ۲: اجرای failing test**

Run: `cd frontend && node --test tests/management-product-detail-operations.test.mjs`

Expected: FAIL چون تب و panel جدید وجود ندارد.

- [ ] **گام ۳: پیاده‌سازی panel و load lifecycle**

بازه تاریخ پیش‌فرض همان بازه گزارش فعلی detail باشد. changing date/warehouse فقط inventory endpoint را refresh کند و load اصلی محصول را دوباره اجرا نکند. در نبود Bin یا ledger، empty state توضیح دهد که سندی برای این Item ثبت نشده است.

- [ ] **گام ۴: تست سبز و commit**

Run: `cd frontend && node --test tests/management-product-detail-operations.test.mjs`

```bash
git add frontend/src/components/management/catalog/ManagementProductInventoryPanel.vue frontend/src/pages/management/catalog/ManagementProductDetailPage.vue frontend/src/utils/api.js frontend/tests/management-product-detail-operations.test.mjs
git commit -m "افزودن موجودی و دفتر موجودی به جزئیات محصول"
```

### کار ۵: یکپارچه‌سازی تب‌ها، کاهش شلوغی و Design System

**فایل‌ها:**
- تغییر: `frontend/src/utils/managementProductDetail.js` برای `PRODUCT_DETAIL_TABS` و نگاشت legacy tabها.
- تغییر: `frontend/src/pages/management/catalog/ManagementProductDetailPage.vue` برای subtab گزارش/تاریخچه و مدل‌ها/سفارشی‌سازی.
- تغییر: `frontend/src/design-system/catalog.js` برای specimenهای native product, connections و inventory ledger.
- تغییر: `frontend/src/pages/management/design-system/ManagementDesignSystemPage.vue` برای نمایش specimenهای جدید در بخش کامپوننت/پترن.
- تغییر: `frontend/tests/design-system-contract.test.mjs` و `frontend/tests/management-product-detail-operations.test.mjs`.
- تغییر: `docs/restaurant-management-coverage.md` برای ثبت پوشش جزئیات Item.

**رابط‌ها و رفتار نهایی:**
- تب‌های قابل مشاهده: `overview`, `settings`, `formula`, `variants`, `inventory`, `connections`, `reports`.
- `builder` به `variants` و `changes` به `reports` نگاشت می‌شوند تا bookmarkهای قبلی نشکنند.
- تب گزارش یک انتخابگر داخلی «تحلیل فروش / تاریخچه تغییرات» دارد و تمام محتوا هم‌زمان روی صفحه انباشته نمی‌شود.
- تب مدل‌ها یک انتخابگر داخلی «مدل‌ها / سفارشی‌سازی» دارد؛ بدنه BOM و جدول native در تب‌های خودشان باقی می‌مانند.
- header، breadcrumb، یک save bar sticky و وضعیت dirty مشترک می‌مانند؛ برای هر تب loading/error/empty/retry قابل مشاهده است.
- design-system catalog باید `product-native-fields`, `product-connections` و `product-inventory-ledger` را به‌عنوان component/pattern مرجع ثبت کند.

- [ ] **گام ۱: تست failing تب‌ها و catalog**

```js
test('product detail has the complete operational tab contract', () => {
  assert.deepEqual(PRODUCT_DETAIL_TABS.map(tab => tab.value), [
    'overview', 'settings', 'formula', 'variants', 'inventory', 'connections', 'reports',
  ])
  assert.match(detailSource, /builder.*variants|legacy|changes.*reports/)
})
```

- [ ] **گام ۲: اجرای failing test**

Run: `cd frontend && node --test tests/management-product-detail-operations.test.mjs tests/design-system-contract.test.mjs`

Expected: FAIL تا زمانی که tab contract و catalog به‌روز نشده‌اند.

- [ ] **گام ۳: پیاده‌سازی ترکیب نهایی**

شرط‌های template را به tabهای جدید منتقل کن، بدون حذف componentهای قبلی. state tab را normalize کن، مقدار ذخیره‌شده localStorage را برای `builder` و `changes` مهاجرت بده و هیچ route یا payload قدیمی را تغییر نده.

- [ ] **گام ۴: تست‌های متمرکز و بررسی قالب**

Run: `cd frontend && node --test tests/management-product-detail-operations.test.mjs tests/management-product-detail-payload.test.mjs tests/design-system-contract.test.mjs`

Run: `git diff --check`

Expected: همه تست‌های متمرکز PASS و خروجی `git diff --check` بدون خطا باشد.

- [ ] **گام ۵: commit نهایی پیاده‌سازی**

```bash
git add frontend/src/utils/managementProductDetail.js frontend/src/pages/management/catalog/ManagementProductDetailPage.vue frontend/src/design-system/catalog.js frontend/src/pages/management/design-system/ManagementDesignSystemPage.vue frontend/tests/management-product-detail-operations.test.mjs frontend/tests/design-system-contract.test.mjs docs/restaurant-management-coverage.md
git commit -m "تکمیل معماری جزئیات محصول و عملیات native"
```

## معیار پذیرش نهایی

- جزئیات محصول در نگاه اول خلاصه و کم‌تراکم است و فقط یک save bar اصلی دارد.
- تمام فیلدهای مهم native Item که در Accounts/یاربینکس بررسی شدند در پنل native قابل مشاهده و موارد مجاز قابل ویرایش‌اند.
- BOM و child tableها فقط یک‌بار رندر می‌شوند و مسیر ویرایش آن‌ها `EditableTable` است.
- تب اتصالات اسناد واقعی ERPNext را با گروه‌بندی، count، empty/loading/error و لینک سند نشان می‌دهد.
- تب انبار مانده هر warehouse، summary موجودی و Stock Ledger واقعی را نشان می‌دهد و به عملیات موجودی فعلی لینک می‌دهد.
- گزارش و تاریخچه به‌صورت progressive disclosure نمایش داده می‌شوند و صفحه شلوغ نمی‌شود.
- design system specimenهای جدید را ثبت می‌کند و از همان componentها در صفحه واقعی استفاده می‌شود.
- تست‌های متمرکز سبز هستند؛ build/restart/migrate اجرا نشده و در گزارش نهایی نیاز آن‌ها جداگانه اعلام می‌شود.
