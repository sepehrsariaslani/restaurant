# Restaurant Management Design-System Alignment

## هدف

یکدست‌سازی رابط مدیریت رستوران بر پایه‌ی دیزاین‌سیستم Restaurant، با حفظ سه مرجع تثبیت‌شده‌ی محصولات، جزئیات محصول و POS، و استفاده از ERPNext به‌عنوان منبع اصلی داده و چرخه‌ی اسناد.

## محدوده

صفحات زیر در این پروژه مرجع تغییر نیستند و نباید برای بازطراحی بصری یا تغییر فرایند بازنویسی شوند:

- `frontend/src/pages/management/catalog/ManagementProductsPage.vue`
- `frontend/src/pages/management/catalog/ManagementProductDetailPage.vue`
- `frontend/src/pages/management/sales/ManagementPosPage.vue`
- `frontend/src/pages/management/sales/ManagementSalesDashboardPage.vue` فقط در اولویت فعلی بازطراحی نیست

صفحات هدف اول:

- سفارش‌ها: لیست سفارش، انتخاب سفارش، جزئیات، پرداخت، تکمیل و تخصیص پیک
- پیک و ناوگان: لیست، جزئیات پیک، وسیله، زون، مسیر و provider
- Item Attribute و Variant: لیست صفت‌های ERPNext، انتخاب، ویرایش و اتصال به محصول
- صفحه‌ی Design System و مسیر قابل‌دسترسی آن

سپس ممیزی و یکدست‌سازی سایر صفحات مدیریت در دامنه‌های فروش، منو، مواد و تولید، مشتریان، گزارش‌ها، تنظیمات و عملیات انجام می‌شود.

## اصول محصول و داده

1. ERPNext برای DocTypeها، مجوزها، اسناد مالی، انبار، مشتری، کاربر، کالا، Item Attribute و چرخه‌ی ثبت/ارسال/لغو منبع اصلی است.
2. Restaurant فقط facade رابط/API و دامنه‌های رستورانی را اضافه می‌کند؛ داده‌ی موازی برای سندهای native ساخته نمی‌شود.
3. صفحات Sales Invoice، Purchase Invoice، User و سایر masterهای موجود در ERPNext از همان منبع استفاده می‌کنند و فقط presentation فارسی، RTL و کامپوننت‌های Restaurant روی آن‌ها اعمال می‌شود.
4. دامنه‌های اختصاصی مثل میزها، وضعیت سالن، آشپزخانه، پیک و ناوگان، زون ارسال، منوی رستوران و فرایندهای عملیاتی خاص Restaurant در همین اپ مدیریت می‌شوند.
5. URL، payload، emit و رفتارهای عملیاتی موجود حفظ می‌شوند مگر اینکه ممیزی یک نقص واقعی در فرایند را نشان دهد.

## قرارداد بصری

- `frontend/src/design-system/tokens.js` منبع نام‌گذاری tokenهاست.
- `frontend/src/theme.css` tokenهای `--ds-*` و aliasهای سازگاری را منتشر می‌کند.
- `frontend/src/components/management/ManagementPageScaffold.vue`، `ManagementSurfaceCard.vue`، `ManagementListView.vue`، `ManagementDataTable.vue` و اجزای موجود مرجع composition هستند.
- Peyda، RTL، فاصله‌های ۴/۸، هدف تعاملی حداقل ۴۴px، focus قابل مشاهده، وضعیت متنی همراه رنگ و `prefers-reduced-motion` الزامی است.
- متن قابل مشاهده‌ی رابط فارسی است؛ نام DocType یا endpoint فقط در توضیح فنی، لینک ERP یا مقدار کد نمایش داده می‌شود.

## رفتارهای کلیدی

### سفارش‌ها

- لیست مشترک سفارش‌ها با جستجو، منبع، تب وضعیت و حالت‌های loading/empty/error.
- انتخاب ردیف باید جزئیات سفارش را با query معتبر باز کند و در صورت refresh همان جزئیات را بازیابی کند.
- جزئیات شامل مشتری، کانال، مبلغ، پرداخت، آیتم‌ها، تخصیص پیک و عملیات مجاز باشد.
- status و payment status باید با متن فارسی و رنگ معنایی نمایش داده شوند.

### پیک و نفرهای عملیاتی

- فرض پروژه برای «نفرها» گارسون‌ها و کارکنان عملیاتی است؛ Users/Role همچنان native ERPNext باقی می‌ماند.
- صفحه‌ی پیک باید الگوی `list → detail` مشابه محصول داشته باشد؛ انتخاب پیک فرم جزئیات را پر کند.
- ناوگان، زون، بهینه‌سازی مسیر و provider در تب‌های عملیاتی جدا بمانند.
- گزارش گارسون از API موجود استفاده می‌کند و در صورت نیاز صفحه‌ی عملیاتی آن جدا از Users ساخته می‌شود.

### Item Attribute و Variant

- catalog صفت‌های ERPNext از `ManagementListView` یا الگوی لیست محصولات استفاده کند.
- انتخاب ردیف، ویرایشگر را باز کند؛ تغییرات از API ERPNext/Restaurant ذخیره شود.
- عبارت‌های فنی قابل مشاهده مانند From Range، To Range، Increment و Item Attribute به برچسب فارسی تبدیل شوند.

## پوشش صفحات

ممیزی اولیه نشان داد بسیاری از صفحات از `ManagementPageScaffold` و `ManagementSurfaceCard` استفاده می‌کنند، اما صفحات inventory قدیمی، آشپزخانه، Home Builder، بعضی صفحات menu و تنظیمات هنوز shellهای پراکنده یا tokenهای legacy بیشتری دارند. این صفحات در ماتریس پوشش plan مرحله‌بندی می‌شوند؛ بازطراحی هر دامنه پس از تست contract همان دامنه انجام می‌شود.

## محدودیت انتشار

در اجرای اولیهٔ این پروژه build، restart، migrate و Graphify جزو دامنه نبودند؛ با درخواست صریح بعدی کاربر، build، migrate و restart روی سایت `veederakht` اجرا و با browser smoke تأیید شدند. Graphify همچنان اجرا نشده است.
