# برنامه پیاده‌سازی اولویت تخفیف POS

> این برنامه بر اساس طراحی تأییدشده کاربر اجرا می‌شود و به‌صورت inline در همین نشست پیش می‌رود.

## گام ۱: ثبت رفتار مورد انتظار و تست قرمز

فایل‌های هدف:

- `restaurant/pricing_policy.py`
- `restaurant/tests/test_customer_pricing_policy.py`
- `restaurant/tests/test_customer_discount_hook.py`
- `frontend/src/utils/posDiscountPolicy.js`
- `frontend/tests/pos-discount-policy.test.mjs`

کار:

1. یک helper قابل تست برای تعیین تخفیف مؤثر بساز که حالت‌های `customer_group`، `manual` و پاک‌شدن تخفیف دستی را پوشش دهد.
2. تستی اضافه کن که تخفیف دستی حتی اگر از تخفیف گروهی کمتر باشد، برنده شود.
3. تست hook را اصلاح کن تا مشتری `POS Customer` نیز در صورت داشتن گروه، درصد گروه را دریافت کند.
4. تست‌ها را اجرا کن و شکست مورد انتظار را ثبت کن.

## گام ۲: اصلاح policy بک‌اند

فایل‌های هدف:

- `restaurant/pricing_policy.py`
- `restaurant/api_club.py`
- `restaurant/api.py`

کار دقیق:

1. محاسبه مبلغ تخفیف دستی را با پشتیبانی درصدی و مبلغ ثابت به policy اضافه کن.
2. در ساخت سفارش، `financial_modifiers.manual_discount` و نوع/مقدار تخفیف را بخوان.
3. اگر منبع تخفیف دستی بود، همان مبلغ را در payload سفارش ثبت کن و منبع داخلی را `manual` قرار بده.
4. hook تخفیف مشتری را طوری تغییر بده که source=`manual` را دست‌نخورده نگه دارد.
5. در صورت نبود تخفیف دستی، رفتار قبلی گروه/کوپن/معرفی حفظ شود.

## گام ۳: ارسال تخفیف گروهی از API مشتریان

فایل هدف:

- `restaurant/api.py`

کار دقیق:

1. در `list_management_customers` گروه مشتری و درصد `restaurant_default_discount_percent` گروه را به هر ردیف اضافه کن.
2. مقدار درصد را به بازه معتبر محدود کن تا مقدار نامعتبر وارد UI نشود.

## گام ۴: اصلاح وضعیت و رابط POS

فایل‌های هدف:

- `frontend/src/utils/posDiscountPolicy.js`
- `frontend/src/pages/management/sales/ManagementPosPage.vue`
- `frontend/src/components/management/pos/PosCartPanel.vue`

کار دقیق:

1. `groupDiscountPercent` و `manualDiscountActive` را به state مالی POS اضافه کن.
2. هنگام انتخاب مشتری، تخفیف گروهی را در صورت نبود حالت دستی در state مؤثر بنویس.
3. هنگام تغییر کنترل تخفیف یا مبلغ نهایی، حالت دستی را فعال کن؛ هنگام پاک‌کردن مقدار، گروه را برگردان.
4. `manual_discount` و منبع تخفیف را در payload ثبت سفارش ارسال کن.
5. در پنل سبد، تخفیف گروهی فعال و جایگزین‌شدن آن با تخفیف دستی را شفاف نمایش بده.
6. snapshot و resetهای POS را با state جدید سازگار کن.

## گام ۵: بررسی و تحویل

1. تست‌های خالص پایتون و smokeهای Frappe را اجرا کن.
2. تست‌های Node و build فرانت‌اند را اجرا کن.
3. diff و وضعیت git را بررسی کن.
4. تغییرات را با پیام و توضیح فارسی commit کن.
5. commit را روی `origin/develop` push کن.

## مرور خودکار برنامه

- هر گام یک خروجی قابل بررسی دارد.
- منبع تخفیف صریح است و به تشخیص مبهم از مقدار تخفیف متکی نیست.
- پاک‌شدن تخفیف دستی مسیر بازگشت به تخفیف گروهی دارد.
- تغییرات محدود به مسیر POS و policy تخفیف است و settlement را دست‌کاری نمی‌کند.
