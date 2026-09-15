# نقشهٔ پوشش مدیریت رستوران

این سند مرجع تصمیم‌گیری برای یکدست‌سازی رابط مدیریت است. هدف آن این است که هر صفحه بداند از کدام shell، فهرست، جزئیات، توکن و منبع داده استفاده می‌کند؛ نه این‌که برای هر صفحه یک منبع داده یا کامپوننت موازی ساخته شود.

## ساختار ماژول‌های مدیریت

صفحه‌ها و اجزای تخصصی بر اساس دامنهٔ کاری در پوشه‌های جدا قرار گرفته‌اند. مسیرهای URL و routeهای Frappe تغییر نکرده‌اند؛ این جابه‌جایی فقط مرزبندی سورس را روشن می‌کند:

| پوشه | مسئولیت | نمونه‌ها |
|---|---|---|
| `src/pages/management/catalog` و `src/components/management/catalog` | محصولات، فرمول/BOM، منو، modifier و variant | `ManagementProductsPage.vue`، `ManagementProductDetailPage.vue`، `ManagementBomsPage.vue` |
| `src/pages/management/sales` و `src/components/management/sales` | سفارش، POS، صندوق و داشبورد فروش | `ManagementOrdersPage.vue`، `ManagementPosPage.vue` |
| `src/pages/management/customers` | مشتری، باشگاه، رزرو، نظرسنجی و مرکز تماس | `ManagementClubPage.vue`، `ManagementCustomersPage.vue` |
| `src/pages/management/inventory` و `src/components/management/inventory` | موجودی، انبار، گردش، تولید، شمارش و بهای تمام‌شده | `ManagementInventoryPage.vue` و زیرصفحه‌های آن |
| `src/pages/management/purchasing` | درخواست مواد و خرید | `ManagementInventoryPurchasesPage.vue`، `ManagementMaterialRequestsPage.vue` |
| `src/pages/management/operations` و `src/components/management/tables` | آشپزخانه، میز، پیک و شعب | `ManagementKitchenPage.vue`، `ManagementTablesPage.vue` |
| `src/pages/management/finance` و `src/components/management/bi` | حسابداری، کنترل هزینه و گزارش‌ها | `ManagementAccountingPage.vue`، `ManagementReportPage.vue` |
| `src/pages/management/settings` | تنظیمات، دسترسی، چاپ و درگاه | `ManagementSiteSettingsPage.vue`، `ManagementUsersPage.vue` |
| `src/pages/management/builder` و `src/components/management/builder` | home builder و قالب‌های صفحه | `ManagementBuilderTemplatesPage.vue` |
| `src/pages/management/design-system` و `src/components/management/design-system` | مرجع توکن و تنظیمات دیزاین‌سیستم | `ManagementDesignSystemPage.vue`، `ManagementThemeStudio.vue` |

کامپوننت‌های پایه مانند `ManagementPageScaffold`، `ManagementSurfaceCard`، `ManagementListView` و کنترل‌های عمومی در ریشهٔ `components/management` باقی می‌مانند تا همهٔ ماژول‌ها از یک قرارداد مشترک استفاده کنند.

### نقشهٔ پوشه‌های کامپوننت

| پوشه | مالکیت | اجزای شاخص |
|---|---|---|
| `components/management/` | primitiveهای مشترک مدیریت | shell، surface، list، table، فیلتر، popup، state و view switcher |
| `components/management/catalog` | محصولات، BOM، منو و رسانه | `ManagementBomManager`، جدول اقلام BOM، uploader و readiness panel |
| `components/management/design-system` | تنظیمات و specimenهای DS | `ManagementThemeStudio` |
| `components/management/builder` | صفحه‌ساز و قالب‌ها | `ManagementPageBuilderWorkspace`، فرم property و step card |
| `components/management/inventory` | الگوی مشترک انبار | `InventorySectionShell`، `InventoryResponsiveList` |
| `components/management/pos` | workspace اختصاصی POS | cart، product panel، settlement و split bill |
| `components/management/sales` | نمودارهای فروش | `SalesHourlyChart` |
| `components/management/bi` | نمودار و KPI گزارش | chart renderer، KPI grid و insight cards |
| `components/management/tables` | سالن، میز، نشست و رزرو | table card، detail panel، status badge و reservations panel |
| `components/management/notion` | کنترل‌های view قابل استفادهٔ مجدد | view tabs، controls، settings و save bar |

## قرارداد جدول‌های داده

تمام فهرست‌ها و جدول‌های داده‌ای مدیریت باید از این زنجیرهٔ canonical استفاده کنند:

| مالک | کاربرد | قرارداد |
|---|---|---|
| `ManagementSmartDataTable` | جدول گزارش، فهرست، جزئیات ردیفی و جدول‌های inline | جستجو، فیلتر ستونی، مرتب‌سازی، فریز/تغییر عرض ستون، empty/loading، action و row detail |
| `ManagementEditableTable` | جدول‌های قابل ویرایش با ایجاد/ویرایش/حذف ردیف | ویرایشگر popup، validation/normalize، تنظیمات ستون و انتشار `v-model`/رویدادهای ردیف |
| `ManagementListView` | facade فهرست‌های مدیریتی | API قدیمی فهرست را حفظ می‌کند و درون خود از `ManagementSmartDataTable` استفاده می‌کند |
| `ManagementDataTable` | facade سازگاری برای گزارش‌ها و صفحه‌های قدیمی | slot و eventهای قبلی را حفظ می‌کند و به `ManagementSmartDataTable` می‌رسد |

صفحات جزئیات محصول، سازندهٔ Variant، انبار و خرید نیز جدول‌های داخلی خود را از همین ownerها می‌گیرند؛ در نتیجه تغییر مشترک در جدول، فهرست‌های قدیمی و جدید را هم‌زمان یکدست می‌کند. دو جدول عمداً خارج از این قرارداد عمومی هستند: `ManagementSheetView` چون یک spreadsheet با انتخاب سلول/ردیف، ویرایش مستقیم و bulk action است؛ و جدول میانبرهای صفحهٔ POS چون دادهٔ عملیاتی نیست و فقط راهنمای صفحه‌کلید است.

## قرارداد مالکیت

| حوزه | مالک داده و چرخهٔ عمر | نقش Restaurant |
|---|---|---|
| Item، Item Attribute، User، Role | ERPNext/Frappe | نمایش RTL، فرم و مسیر مدیریتی یکدست |
| Sales Order، Sales Invoice، Purchase Invoice، Warehouse و ledgerها | ERPNext/Frappe | facade و workflow عملیاتی؛ بدون کپی‌کردن سند یا ledger |
| پیک، وسیلهٔ پیک، زون، آشپزخانه، میز و context سفارش | Restaurant | منبع داده و workflow اختصاصی رستوران |
| گارسون/نفرات | هویت در ERPNext User؛ تخصیص و گزارش در context سفارش Restaurant | نمایش عملیاتی بر اساس contract واقعی backend |

## سطوح مرجع و وضعیت فعلی

| سطح | مسیر | منبع داده | قرارداد بصری | وضعیت بررسی |
|---|---|---|---|---|
| فهرست محصولات | `/management/products` | ERPNext Item + API امن محصولات | مرجع collection، جستجو، نماها و bulk actions | مرجع تثبیت‌شده |
| جزئیات محصول | `/management/product` | ERPNext Item و داده‌های Restaurant | مرجع detail، رسانه، قیمت، BOM، modifier، variant و activity | مرجع تثبیت‌شده |
| کارت محصول مشتری | `/menu` | API منوی رستوران | تصویرمحور، قیمت، وضعیت و اقدام | مرجع تثبیت‌شده |
| جزئیات محصول مشتری | `/item` | API منوی رستوران | gallery، nutrition، customization و cart | مرجع تثبیت‌شده |
| دیزاین سیستم | `/management/design-system` | token/catalog محلی، fixture بی‌خطر | تب‌های تم، آیکون، کامپوننت، پترن و تمپلیت | Navbar، App resolver، Frappe page/context و route rule تراز شده؛ با bundle فعال روی `veederakht` تأیید شد |
| سفارش‌ها | `/management/orders` | ERPNext Sales Order/Invoice + فیلدهای Restaurant | `ManagementListView` → جزئیات انتخاب‌شده → پرداخت/تکمیل/پیک | تراز شده در این مرحله؛ تست source موفق |
| پیک‌ها | `/management/couriers` | Restaurant courier/vehicle | فهرست پیک → فرم جزئیات چسبان → fleet/rules | تراز شده در این مرحله؛ تست source موفق |
| صفت‌های کالا | `/management/product?variant_studio=1` | ERPNext Item Attribute | فهرست قابل جستجو → ویرایشگر صفت | تراز شده در این مرحله؛ تست source موفق |
| کاربران و دسترسی | `/management/users` | ERPNext User/Role | native access surface با shell مشترک | مالکیت حفظ شده؛ بررسی دیداری بعدی |
| باشگاه مشتریان | `/management/club` | Restaurant CRM روی Customer و اسناد فروش ERPNext | تب‌های مشتری، سازمان، کیف پول، صدای مشتری و کمپین با فهرست مشترک برای مشتریان | مشتری، سازمان، کیف پول، پیامک، صدا، معرف و کمپین تراز شده؛ browser smoke باقی است |
| رزرواسیون | `/management/reservations` | Reservation و Table context رستوران | فیلتر تاریخ/جایگاه/وضعیت، فهرست واکنش‌گرا و فرم ایجاد/ویرایش با چرخه وضعیت | تراز شده در این مرحله؛ تست source و SFC موفق |
| نظرسنجی | `/management/surveys` | Survey Question/Response رستوران | مدیریت سؤال و پاسخ با فیلتر بازه/امتیاز و هشدار نارضایتی در فهرست مشترک | تراز شده در این مرحله؛ تست source و SFC موفق |
| شعب | `/management/branches` | Company/Customer و KPIهای شعب ERPNext | شاخص‌های شعب، فهرست واکنش‌گرا، ویرایش/فعال‌سازی و انتقال مشتری | تراز شده در این مرحله؛ تست source و SFC موفق |
| کنترل هزینه | `/management/cost-control` | گزارش فروش/بهای تمام‌شده و بودجه Restaurant/ERPNext | سود و زیان و بودجه در فهرست مشترک، جمع سال و ROI در کارت‌های semantic | تراز شده در این مرحله؛ تست source و SFC موفق |
| حسابداری | `/management/accounting` | سندها و گزارش‌های مالی ERPNext، اتصال مودیان Restaurant | تراز دریافت/پرداخت، روش پرداخت، ارسال مودیان و اسناد اخیر در فهرست‌های مشترک | تراز شده در این مرحله؛ تست source و SFC موفق |
| مرکز تماس | `/management/call-center` | Restaurant call log و Customer context | تماس‌های اخیر با فهرست مشترک، وضعیت فارسی و عملیات پاسخ/پایان | در ماژول مشتریان و ارتباط؛ تست source موفق |
| گزارش‌های مدیریتی | `/management/reports` و `/management/reports/:key` | API گزارش Restaurant/ERPNext | فهرست گزارش، فیلتر بازه، KPI، نمودار و جدول با عنوان فارسی | همهٔ کلیدهای فهرست به wrapper/API متصل و گزارش‌های نماینده با browser smoke تأیید شدند |

## صفحات Restaurant-specific

این صفحات منبع دادهٔ اختصاصی Restaurant دارند و باید از `ManagementPageScaffold`، `ManagementSurfaceCard`، توکن‌های semantic و در صورت وجود schema پایدار از `ManagementListView` استفاده کنند:

- پیک‌ها و ناوگان: `pages/management/operations/ManagementCouriersPage.vue`
- آشپزخانه: `pages/management/operations/ManagementKitchenPage.vue`
- میزها: `pages/management/operations/ManagementTablesPage.vue`
- منو و گروه‌های منو: `pages/management/catalog/ManagementMenuDesignerPage.vue`، `pages/management/catalog/ManagementMenuGroupsPage.vue`، `pages/management/catalog/ManagementMenuGroupDetailPage.vue`
- modifierها: `pages/management/catalog/ManagementModifierGroupsPage.vue`
- POS و پیش‌فرض‌های POS: `pages/management/sales/ManagementPosPage.vue`، `pages/management/sales/ManagementPosProfilePage.vue`، `pages/management/sales/ManagementPosDefaultsPage.vue`
- ثبت سفارش/صندوق: `pages/management/sales/ManagementRegisterPage.vue`
- شعبه‌ها، رزرو و مرکز تماس: `pages/management/operations/ManagementBranchesPage.vue`، `pages/management/customers/ManagementReservationsPage.vue`، `pages/management/customers/ManagementCallCenterPage.vue`

## ماتریس کامل صفحات مدیریت

این ماتریس تمام فایل‌های route-level و wrapperهای فعلی `frontend/src/pages/management` را پوشش می‌دهد. `Scaffold/Card` یعنی استفاده از `ManagementPageScaffold` و `ManagementSurfaceCard`؛ `List` یعنی `ManagementListView`؛ `Table` یعنی `ManagementDataTable`؛ و `Inventory shell/list` یعنی `InventorySectionShell` و `InventoryResponsiveList`. در ستون وضعیت، «بررسی منبع» به معنی کنترل سورس و قرارداد است، نه فعال‌شدن bundle روی سایت.

### catalog — محصولات و فرمول

| صفحه | مسیر | منبع | ترکیب UI | فهرست/جزئیات | وضعیت |
|---|---|---|---|---|---|
| `ManagementProductsPage` | `/management/products` | ERPNext Item + API محصولات | مرجع collection | `List`، gallery، kanban، sheet، تقویم، درخت | protected reference؛ دست‌نخورده |
| `ManagementProductDetailPage` | `/management/product?item_name=...` | ERPNext Item + دادهٔ رستوران | مرجع detail | detail، BOM، modifier، variant و activity | protected reference؛ دست‌نخورده |
| `ManagementVariantBuilderPage` | `/management/product?variant_studio=1` | ERPNext Item Attribute/Variant | Scaffold/Card | `List` → ویرایشگر صفت | بررسی منبع؛ payload و API حفظ شده |
| `ManagementBomsPage` | `/management/boms` | ERPNext BOM | Scaffold/Card | فهرست تخصصی و انتخاب BOM | بررسی منبع؛ مسیر حفظ شده |
| `ManagementBomDetailPage` | `/management/bom?bom=...` | ERPNext BOM و Item | Scaffold/Card | detail/form اقلام BOM | بررسی منبع؛ چرخهٔ native حفظ شده |
| `ManagementMenuDesignerPage` | `/management/menu-design` | Restaurant menu config + ERPNext Item/Group | Scaffold + ویرایشگر تخصصی | نمای دسته/محصول و انتشار | بررسی منبع؛ editor عمداً custom است |
| `ManagementMenuGroupsPage` | `/management/menu-groups` | ERPNext Item Group + فیلدهای Restaurant | Scaffold | فهرست تخصصی گروه‌ها | بررسی منبع؛ فرم detail جداست |
| `ManagementMenuGroupDetailPage` | `/management/menu-group?name=...` | ERPNext Item Group | Scaffold/Card | فرم ایجاد/ویرایش گروه | بررسی منبع؛ payload حفظ شده |
| `ManagementModifierGroupsPage` | `/management/modifier-groups` | Restaurant modifier groups | Scaffold | فهرست/تنظیمات تخصصی | بررسی منبع؛ editor فعلی حفظ شده |

### sales — فروش و سفارش

| صفحه | مسیر | منبع | ترکیب UI | فهرست/جزئیات | وضعیت |
|---|---|---|---|---|---|
| `ManagementOrdersPage` | `/management/orders` | ERPNext Sales Order/Invoice + order context | Scaffold/Card | `List` → سفارش انتخاب‌شده و جزئیات | aligned؛ تست contract موفق |
| `ManagementPosPage` | `/management/pos` | ERPNext + Restaurant POS | POS workspace اختصاصی | cart، محصول، پرداخت و میز | protected reference؛ دست‌نخورده |
| `ManagementPosProfilePage` | `/management/pos-profile` | ERPNext POS Profile | Scaffold/Card | فرم تنظیمات | بررسی منبع؛ native settings حفظ شده |
| `ManagementPosDefaultsPage` | `/management/pos-defaults` | Restaurant POS config + ERPNext Customer/Courier | Scaffold/Card | فرم و lookupها | بررسی منبع؛ API حفظ شده |
| `ManagementRegisterPage` | `/management/register` | Restaurant register + ERPNext print/payment context | Scaffold/Card | تب‌های صندوق، شیفت و کمبو | بررسی منبع؛ workflow تخصصی حفظ شده |
| `ManagementSalesDashboardPage` | `/management/sales` | گزارش‌های Restaurant/ERPNext | Scaffold/Card | KPI و نمودارهای اختصاصی | خارج از اولویت بازطراحی فعلی |

### customers — مشتریان و ارتباط

| صفحه | مسیر | منبع | ترکیب UI | فهرست/جزئیات | وضعیت |
|---|---|---|---|---|---|
| `ManagementCustomersPage` | `/management/customers` | ERPNext Customer + order context | Scaffold/Card | جدول/فهرست → detail مشتری | بررسی منبع؛ جزئیات و تب‌ها حفظ شده |
| `ManagementClubPage` | `/management/club` | Restaurant CRM روی Customer و اسناد فروش | Scaffold/Card | `List` برای مشتری، سازمان، کیف پول، کمپین و صدا | aligned؛ API و actionها حفظ شده |
| `ManagementReservationsPage` | `/management/reservations` | Reservation/Table context رستوران | Scaffold/Card | `List` → فرم ایجاد/ویرایش | aligned؛ وضعیت‌های فارسی و actionها حفظ شده |
| `ManagementSurveysPage` | `/management/surveys` | Survey Question/Response رستوران | Scaffold/Card | `List` برای سؤال و پاسخ | aligned؛ پاسخ/حذف و فیلترها حفظ شده |
| `ManagementCallCenterPage` | `/management/call-center` | Call log رستوران + ERPNext Customer | Scaffold/Card | `List` تماس‌های اخیر | aligned؛ در پوشهٔ customers قرار دارد |

### inventory — انبار و تولید

| صفحه | مسیر | منبع | ترکیب UI | فهرست/جزئیات | وضعیت |
|---|---|---|---|---|---|
| `ManagementInventoryDashboardPage` | `/management/inventory` | ERPNext stock/Warehouse | Inventory shell/list | `InventoryResponsiveList` موجودی + KPI | بررسی منبع؛ read-only |
| `ManagementInventoryMaterialsPage` | `/management/inventory/materials` | ERPNext Item + تأمین‌کننده | Inventory shell/list | `InventoryResponsiveList` → detail | بررسی منبع؛ جستجو و empty/error حفظ شده |
| `ManagementInventoryMaterialDetailPage` | `/management/inventory/materials/detail` | ERPNext Item/Material | Inventory shell + Card | detail/form | بررسی منبع؛ save native facade |
| `ManagementInventoryWarehousesPage` | `/management/inventory/warehouses` | ERPNext Warehouse | legacy wrapper → aggregate inventory | tab تخصصی انبارها | compatibility wrapper؛ logic بازنویسی نشده |
| `ManagementInventoryMovementsPage` | `/management/inventory/movements` | Stock Ledger/Stock Entry ERPNext | legacy wrapper → aggregate inventory | tab گردش موجودی | compatibility wrapper؛ ledger موازی ندارد |
| `ManagementInventoryReorderPage` | `/management/inventory/reorder` | Item reorder levels + stock ERPNext | legacy wrapper → aggregate inventory | tab هشدار نقطه سفارش | compatibility wrapper؛ API حفظ شده |
| `ManagementInventoryProductionPage` | `/management/inventory/production` | BOM/Stock Entry ERPNext | legacy wrapper → aggregate inventory | tab برنامه تولید | compatibility wrapper؛ lifecycle native است |
| `ManagementInventoryLossesPage` | `/management/inventory/losses` | Restaurant waste + ERPNext stock context | legacy wrapper → aggregate inventory | tab ضایعات/خسارت | compatibility wrapper؛ API حفظ شده |
| `ManagementInventoryCountPage` | `/management/inventory/count` | Stock reconciliation ERPNext | legacy wrapper → aggregate inventory | tab شمارش/مغایرت | compatibility wrapper؛ mutationها حفظ شده |
| `ManagementInventoryCostsPage` | `/management/inventory/costs` | Product cost/report APIs | legacy wrapper → aggregate inventory | tab بهای تمام‌شده | compatibility wrapper؛ گزارش native/facade است |
| `ManagementInventoryPage` | internal compatibility | همهٔ زیرسطح‌های inventory | Scaffold + Card/List | aggregate tab workspace | legacy aggregate؛ route جدیدی اضافه نمی‌کند |
| `ManagementInventoryLegacySectionPage` | internal compatibility | همان منبع aggregate inventory | wrapper سبک | انتخاب tab برای صفحات قدیمی | فقط adapter؛ منطق اصلی move نشده |

### purchasing — خرید و تأمین

| صفحه | مسیر | منبع | ترکیب UI | فهرست/جزئیات | وضعیت |
|---|---|---|---|---|---|
| `ManagementMaterialRequestsPage` | `/management/inventory/requests` | Restaurant request + ERPNext Item/Warehouse | Inventory shell/list | `InventoryResponsiveList` → detail | بررسی منبع؛ مسیر legacy URL حفظ شده |
| `ManagementMaterialRequestDetailPage` | `/management/inventory/requests/detail` | material request + ERPNext | Inventory shell/Card | detail/form و انتقال به خرید | بررسی منبع؛ API حفظ شده |
| `ManagementInventoryPurchasesPage` | `/management/inventory/purchases` | ERPNext Purchase Order/Invoice | Inventory shell/list | `InventoryResponsiveList` → detail | بررسی منبع؛ status workflow حفظ شده |
| `ManagementInventoryPurchaseDetailPage` | `/management/inventory/purchases/detail` | ERPNext Purchase Order | Inventory shell/Card | detail/form و دریافت مرحله‌ای | بررسی منبع؛ submit/lifecycle native است |

### operations — عملیات رستوران

| صفحه | مسیر | منبع | ترکیب UI | فهرست/جزئیات | وضعیت |
|---|---|---|---|---|---|
| `ManagementBranchesPage` | `/management/branches` | Company/Customer + branch context | Scaffold/Card | `List` → فرم شعبه | aligned؛ native actionها حفظ شده |
| `ManagementCouriersPage` | `/management/couriers` | Courier/Vehicle/Zone رستوران | Scaffold/Card | `List` → workbench جزئیات پیک | aligned؛ تست contract موفق |
| `ManagementKitchenPage` | `/management/kitchen` | order/kitchen context رستوران | KDS workspace اختصاصی | board و صف وضعیت | specialized؛ realtime UI عمداً custom است |
| `ManagementTablesPage` | `/management/tables` | Table/Session/Reservation رستوران | Scaffold + سالن workspace | کارت میز، نشست و رزرو | specialized؛ الگوی میز حفظ شده |

### finance — مالی و گزارش

| صفحه | مسیر | منبع | ترکیب UI | فهرست/جزئیات | وضعیت |
|---|---|---|---|---|---|
| `ManagementAccountingPage` | `/management/accounting` | ERPNext accounting reports + tax context | Scaffold/Card | `List` تراز، ارسال مالیات و journal | aligned؛ تست contract موفق |
| `ManagementCostControlPage` | `/management/cost-control` | فروش/بهای تمام‌شده + بودجه Restaurant | Scaffold/Card | `List` سودوزیان و بودجه | aligned؛ تست contract موفق |
| `ManagementReportsIndexPage` | `/management/reports` | report catalog Restaurant/ERPNext | Scaffold/Card | فهرست گزارش‌ها | بررسی منبع؛ عنوان‌ها فارسی |
| `ManagementReportPage` | `/management/reports/<report_key>` | BI/report APIs Restaurant/ERPNext | Scaffold/Card | KPI، chart و `ManagementDataTable` | aligned؛ کلید فنی در UI نمایش داده نمی‌شود |

### settings — دسترسی، محتوا و تنظیمات

| صفحه | مسیر | منبع | ترکیب UI | فهرست/جزئیات | وضعیت |
|---|---|---|---|---|---|
| `ManagementUsersPage` | `/management/users` | ERPNext User/Role | Scaffold/Card | list-detail اختصاصی دسترسی | native ownership حفظ شده |
| `ManagementSiteSettingsPage` | `/management/site-settings` | Restaurant site settings + page builder | Scaffold/Card/List + builder workspace | تب‌های سایت، theme و builder | بررسی منبع؛ API حفظ شده |
| `ManagementPrintFormatsPage` | `/management/print-formats` | ERPNext Print Format | Scaffold/Card | gallery/preview اختصاصی | بررسی منبع؛ preview و print حفظ شده |
| `ManagementHelpPage` | `/management/help` | navigation/help content | Scaffold/Card | راهنما و quick links | بررسی منبع؛ read-only |
| `ManagementSettingsPage` | internal compatibility | تنظیمات قدیمی مدیریت | Scaffold | wrapper سابق theme/settings | compatibility؛ مسیر active از SiteSettings عبور می‌کند |
| `ManagementZarinpalSettingsPage` | `/management/zarinpal-settings` | قرارداد backend اختصاصی هنوز موجود نیست | صفحهٔ وضعیت ساده | بدون فرم جعلی | placeholder آگاهانه؛ تا قرارداد API واقعی تغییر نمی‌کند |

### builder، dashboard و design-system

| صفحه | مسیر | منبع | ترکیب UI | فهرست/جزئیات | وضعیت |
|---|---|---|---|---|---|
| `ManagementDashboardPage` | `/management` | dashboard/report APIs Restaurant/ERPNext | Scaffold/Card + DataTable | KPI، هشدار، مشتری، سفارش و چیدمان | بررسی منبع؛ dashboard عمومی مدیریت |
| `ManagementBuilderTemplatesPage` | `/management/builder-templates` | Restaurant customization templates | Scaffold/Card + DataTable | فهرست قالب‌ها → ویرایش | بررسی منبع؛ API حفظ شده |
| `ManagementBuilderTemplatePage` | `/management/builder-template/edit/:id` یا `new` | Restaurant customization templates | Scaffold/Card | فرم detail و steps | بررسی منبع؛ save/delete حفظ شده |
| `ManagementHomeBuilderPage` | internal compatibility | Restaurant page layout | builder workspace اختصاصی | drag/drop block editor | legacy compatibility؛ مسیر فعال از SiteSettings عبور می‌کند |
| `ManagementDesignSystemPage` | `/management/design-system` | local tokens/catalog + safe fixtures | Scaffold/Card | تب‌های تم، آیکون، کامپوننت، پترن و تمپلیت | مرجع اصلی؛ Navbar و direct route تراز شده |

تمام ردیف‌های بالا از `theme.css` و aliasهای semantic `--ds-*`/`--mg-*` استفاده می‌کنند؛ چند literal قدیمی در CSS صفحات تخصصی فقط fallback سازگاری هستند و در این جابه‌جایی بازنویسی نشده‌اند. قاعدهٔ تغییر بعدی این است که هر اصلاح جدید از `tokens.js`، انتشار CSS و mapping runtime عبور کند.

## صفحات ERPNext-backed

این صفحات نباید DocType یا ledger موازی بسازند. ظاهر و workflow آن‌ها می‌تواند Restaurant-specific باشد، اما API و lifecycle باید در نهایت به native ERPNext برسد:

- `Item`، `Item Attribute`، `Item Variant`، `Customer` و `Supplier`
- `User`/`Role` و مدیریت دسترسی
- `Warehouse`، `Stock Ledger Entry`، گردش موجودی و هزینهٔ محصول
- `Sales Order`، `Sales Invoice`، `Purchase Order`، `Purchase Invoice` و `Payment Entry`
- `BOM` و جزئیات BOM، گزارش‌های حسابداری و گزارش‌های عملیاتی

برای هر کدام، صفحهٔ Restaurant فقط facade و presentation layer است؛ مجوز، lifecycle، submit/cancel و ثبت ledger باید از قرارداد Frappe/ERPNext عبور کند.

برای صفحات انبار، `InventorySectionShell` مالک الگوی دامنه‌ای است. برای صفحات گزارش و ledger، `SmartDataTable` یا primitive معادل موجود باید بر جدول محلی ترجیح داده شود.

## مرزهای باقی‌مانده برای انتشار

ممیزی سورس و ماژول‌بندی تمام شد؛ موارد زیر عمداً خارج از ادعای «فعال‌شدن روی سایت» باقی می‌مانند:

1. smoke احراز هویت‌شده روی سایت `veederakht` انجام شده است؛ برای هر سایت دیگری باید host/site درست انتخاب شود.
2. صفحهٔ زرین‌پال تا زمان وجود endpoint و قرارداد backend واقعی placeholder می‌ماند.
3. wrapperهای legacy انبار، `ManagementSettingsPage` و `ManagementHomeBuilderPage` برای سازگاری نگه داشته شده‌اند؛ قابلیت‌های فعال از صفحات جدید/aggregate عبور می‌کنند.
4. فایل‌های bundle داخل `public/frontend/assets` با build تولید شده‌اند؛ فایل‌های generated عمداً برای commit feature stage نشده‌اند.

## تعریف Done برای هر صفحه

یک صفحه زمانی aligned محسوب می‌شود که این موارد را داشته باشد:

- مسیر `App.vue`، ورودی Navbar، active state و در صورت direct load، route rule در `restaurant/hooks.py` با هم وجود داشته باشند.
- shell و spacing از design token استفاده کنند و raw hex جدید در page-local CSS اضافه نشود.
- حالت loading، empty، error و success قابل فهم باشد و status فقط با رنگ منتقل نشود.
- list/detail، create/edit و lifecycle واقعی همان API موجود را حفظ کند.
- رفتار موبایل، focus keyboard، RTL و reduced-motion بررسی شود.
- تست contract یا behavior مربوط به invariant جدید اضافه شود.
- تست source به‌تنهایی به‌عنوان deployment موفق گزارش نشود؛ build/restart و browser smoke جداگانه ثبت شوند.

## وضعیت اعتبارسنجی این نقشه

- تست frontend این مرحله: موفق؛ ۲۵ تست contract دیزاین‌سیستم، مسیرها، API گزارش و ماژول‌بندی.
- parse/compile همهٔ ۱۲۱ SFC مدیریتی و کامپوننت‌های مدیریتی: موفق.
- بررسی importهای نسبی و alias همهٔ SFCهای مدیریتی: موفق.
- syntax بررسی `restaurant/hooks.py`: موفق.
- build production: موفق؛ ۲۱۷۱ ماژول Vite تبدیل شد و bundle فعال تولید شد.
- migrate سایت `veederakht`: موفق؛ route ruleهای مستقیم و hookهای سایت refresh شدند.
- restart سرویس‌های web/socketio/worker: موفق.
- browser smoke احراز‌شده: مسیرهای اصلی تمام ماژول‌ها، aliasهای مستقیم، صفحات create/detail و گزارش‌های `sales-summary`، `menu-engineering`، `tax-reconciliation`، `branch-performance`، `vendor-sales` و `receipt-payment-balance` بدون 404 یا خطای runtime تأیید شدند.
- Graphify/remote update: اجرا نشد؛ خارج از دامنهٔ این ممیزی باقی مانده است.
