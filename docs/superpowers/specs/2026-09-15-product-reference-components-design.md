# Product Reference Components Design

## Goal

قالب واقعی صفحات فهرست محصولات و جزئیات محصول به دو shell قابل استفاده‌ی مجدد تبدیل شود و همان نمونه‌ها به‌صورت زنده در Design System نمایش داده شوند.

## Scope

- افزودن `ManagementProductCollectionShell.vue` برای قاب فهرست و نماهای چندگانه.
- افزودن `ManagementProductDetailShell.vue` برای قاب جزئیات، وضعیت‌های async و بخش‌های محصول.
- اتصال `ManagementProductsPage.vue` و `ManagementProductDetailPage.vue` به shellهای مشترک بدون تغییر API، URL، payload یا منطق ERPNext.
- افزودن specimenهای واقعی و deterministic به تب‌های components، patterns و templates در Design System.
- ثبت قرارداد props/slots/emits و تست source-level آن‌ها.

## Architecture

صفحات route منطق داده، فرم و عملیات را نگه می‌دارند و shellها فقط composition بصری، عنوان، toolbar، وضعیت بارگذاری/خطا و ناحیه‌ی محتوای slot شده را مالک می‌شوند. shellها با slot طراحی می‌شوند تا نمای لیست، گالری، کانبان، شیت و بخش‌های جزئیات محصول بدون شرط‌های business-specific داخل کامپوننت قابل تعویض باشند.

`ManagementProductCollectionShell` یک سطح اصلی با `title` و `subtitle` دارد و slotهای `toolbar`، `status`، `default` و `overlays` را منتشر می‌کند. `ManagementProductDetailShell` slotهای `breadcrumb`، `hero`، `navigation`، `status`، `default` و `overlays` را منتشر می‌کند و loading/error را با متن فارسی و حالت retry قابل اتصال نگه می‌دارد.

## Invariants

- رنگ‌ها، فاصله‌ها، radius و focus فقط از `--ds-*` و aliasهای فعلی مصرف می‌شوند.
- هیچ API، DocType، payload، query parameter یا رفتار save/delete جابه‌جا یا duplicated نمی‌شود.
- fixtureهای Design System ثابت‌اند و هیچ mutation واقعی انجام نمی‌دهند.
- نماهای تخصصی محصولات مثل کانبان، گالری و شیت همچنان در خودشان باقی می‌مانند و فقط داخل shell نمایش داده می‌شوند.
- صفحات مصرف‌کننده باید بتوانند shell را بدون دسترسی به internals آن استفاده کنند.

## Verification

- تست قرارداد باید وجود shellها، props/slots اصلی، ثبت catalog و استفاده‌ی دو route محصول را بررسی کند.
- `npm test` از مسیر `frontend/` اجرا می‌شود.
- همه‌ی فایل‌های SFC در `pages/management` و `components/management` با parser/compiler Vue بررسی می‌شوند.
- build، restart، migrate و Graphify در این تغییر اجرا نمی‌شوند.
