# نقشهٔ پوشش مدیریت رستوران

این سند مرجع تصمیم‌گیری برای یکدست‌سازی رابط مدیریت است. هدف آن این است که هر صفحه بداند از کدام shell، فهرست، جزئیات، توکن و منبع داده استفاده می‌کند؛ نه این‌که برای هر صفحه یک منبع داده یا کامپوننت موازی ساخته شود.

## ساختار ماژول‌های مدیریت

صفحه‌ها و اجزای تخصصی بر اساس دامنهٔ کاری در پوشه‌های جدا قرار گرفته‌اند. مسیرهای URL و routeهای Frappe تغییر نکرده‌اند؛ این جابه‌جایی فقط مرزبندی سورس را روشن می‌کند:

| پوشه | مسئولیت | نمونه‌ها |
|---|---|---|
| `src/pages/management/catalog` و `src/components/management/catalog` | محصولات، فرمول/BOM، منو، modifier و variant | `ManagementProductsPage.vue`، `ManagementProductDetailPage.vue`، `ManagementBomsPage.vue` |
| `src/pages/management/sales` و `src/components/management/sales` | سفارش، POS، صندوق، تماس و داشبورد فروش | `ManagementOrdersPage.vue`، `ManagementPosPage.vue` |
| `src/pages/management/customers` | مشتری، باشگاه، رزرو و نظرسنجی | `ManagementClubPage.vue`، `ManagementCustomersPage.vue` |
| `src/pages/management/inventory` و `src/components/management/inventory` | موجودی، انبار، گردش، تولید، شمارش و بهای تمام‌شده | `ManagementInventoryPage.vue` و زیرصفحه‌های آن |
| `src/pages/management/purchasing` | درخواست مواد و خرید | `ManagementInventoryPurchasesPage.vue`، `ManagementMaterialRequestsPage.vue` |
| `src/pages/management/operations` و `src/components/management/tables` | آشپزخانه، میز، پیک و شعب | `ManagementKitchenPage.vue`، `ManagementTablesPage.vue` |
| `src/pages/management/finance` و `src/components/management/bi` | حسابداری، کنترل هزینه و گزارش‌ها | `ManagementAccountingPage.vue`، `ManagementReportPage.vue` |
| `src/pages/management/settings` | تنظیمات، دسترسی، چاپ و درگاه | `ManagementSiteSettingsPage.vue`، `ManagementUsersPage.vue` |
| `src/pages/management/builder` و `src/components/management/builder` | home builder و قالب‌های صفحه | `ManagementBuilderTemplatesPage.vue` |
| `src/pages/management/design-system` و `src/components/management/design-system` | مرجع توکن و تنظیمات دیزاین‌سیستم | `ManagementDesignSystemPage.vue`، `ManagementThemeStudio.vue` |

کامپوننت‌های پایه مانند `ManagementPageScaffold`، `ManagementSurfaceCard`، `ManagementListView` و کنترل‌های عمومی در ریشهٔ `components/management` باقی می‌مانند تا همهٔ ماژول‌ها از یک قرارداد مشترک استفاده کنند.

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
| دیزاین سیستم | `/management/design-system` | token/catalog محلی، fixture بی‌خطر | تب‌های تم، آیکون، کامپوننت، پترن و تمپلیت | Navbar، App resolver، Frappe page/context و route rule تراز شده؛ نیازمند build/restart برای bundle فعال |
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
| مرکز تماس | `/management/call-center` | Restaurant call log و Customer context | تماس‌های اخیر با فهرست مشترک، وضعیت فارسی و عملیات پاسخ/پایان | تراز شده در این مرحله؛ تست source موفق |
| گزارش‌های مدیریتی | `/management/reports` و `/management/reports/:key` | API گزارش Restaurant/ERPNext | فهرست گزارش، فیلتر بازه، KPI، نمودار و جدول با عنوان فارسی | گارسون و عنوان‌های تکمیلی اصلاح شد؛ browser smoke باقی است |

## صفحات Restaurant-specific

این صفحات منبع دادهٔ اختصاصی Restaurant دارند و باید از `ManagementPageScaffold`، `ManagementSurfaceCard`، توکن‌های semantic و در صورت وجود schema پایدار از `ManagementListView` استفاده کنند:

- پیک‌ها و ناوگان: `pages/management/operations/ManagementCouriersPage.vue`
- آشپزخانه: `pages/management/operations/ManagementKitchenPage.vue`
- میزها: `pages/management/operations/ManagementTablesPage.vue`
- منو و گروه‌های منو: `pages/management/catalog/ManagementMenuDesignerPage.vue`، `pages/management/catalog/ManagementMenuGroupsPage.vue`، `pages/management/catalog/ManagementMenuGroupDetailPage.vue`
- modifierها: `pages/management/catalog/ManagementModifierGroupsPage.vue`
- POS و پیش‌فرض‌های POS: `pages/management/sales/ManagementPosPage.vue`، `pages/management/sales/ManagementPosProfilePage.vue`، `pages/management/sales/ManagementPosDefaultsPage.vue`
- ثبت سفارش/صندوق: `pages/management/sales/ManagementRegisterPage.vue`
- شعبه‌ها، رزرو و مرکز تماس: `pages/management/operations/ManagementBranchesPage.vue`، `pages/management/customers/ManagementReservationsPage.vue`، `pages/management/sales/ManagementCallCenterPage.vue`

## صفحات ERPNext-backed

این صفحات نباید DocType یا ledger موازی بسازند. ظاهر و workflow آن‌ها می‌تواند Restaurant-specific باشد، اما API و lifecycle باید در نهایت به native ERPNext برسد:

- `Item`، `Item Attribute`، `Item Variant`، `Customer` و `Supplier`
- `User`/`Role` و مدیریت دسترسی
- `Warehouse`، `Stock Ledger Entry`، گردش موجودی و هزینهٔ محصول
- `Sales Order`، `Sales Invoice`، `Purchase Order`، `Purchase Invoice` و `Payment Entry`
- `BOM` و جزئیات BOM، گزارش‌های حسابداری و گزارش‌های عملیاتی

برای هر کدام، صفحهٔ Restaurant فقط facade و presentation layer است؛ مجوز، lifecycle، submit/cancel و ثبت ledger باید از قرارداد Frappe/ERPNext عبور کند.

برای صفحات انبار، `InventorySectionShell` مالک الگوی دامنه‌ای است. برای صفحات گزارش و ledger، `SmartDataTable` یا primitive معادل موجود باید بر جدول محلی ترجیح داده شود.

## صفحات و کارهای باقی‌مانده برای audit مرحله‌ای

این فهرست به معنی حذف قابلیت نیست؛ فقط اولویت یکدست‌سازی را ثبت می‌کند:

1. inventory: dashboard، materials، material detail، requests، request detail، purchases، purchase detail، warehouses، movements، reorder، production، losses، count و costs.
2. finance/operations: accounting، reports، report detail، sales dashboard، cost control و print formats.
3. settings/content: site settings، home builder، builder templates، settings، Zarinpal settings و help.
4. CRM/engagement: customers، club، surveys و call center.
5. product-adjacent: BOM list/detail، modifier groups، menu designer و menu groups.

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

- تست frontend این مرحله: موفق؛ تست‌های contract دیزاین‌سیستم، مسیرها و ماژول‌بندی.
- parse/compile همهٔ ۱۲۱ SFC مدیریتی و کامپوننت‌های مدیریتی: موفق.
- بررسی importهای نسبی و alias همهٔ SFCهای مدیریتی: موفق.
- syntax بررسی `restaurant/hooks.py`: موفق.
- build، restart، migrate، Graphify و browser smoke احراز‌شده: عمداً اجرا نشده و باید توسط کاربر در زمان انتشار انجام شود.
