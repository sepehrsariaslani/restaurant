# تشخیص سفارش دستی بر اساس مشتری اسنپ — برنامهٔ اجرا

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** سفارش Partner فقط وقتی سفارش دستیِ همان روز با مبلغ و اقلام/تعداد یکسان و هویت مشتری قابل‌تطبیق دارد، به‌عنوان تکراری علامت بخورد.

**Architecture:** تطبیق pure در `food_partner_duplicates.py` شناسهٔ اسنپ را در اولویت می‌گذارد، سپس موبایل نرمال‌شده و در نبود آن نام غیرعمومی را مقایسه می‌کند؛ نبود هویت قابل‌اعتماد باعث عدم تطبیق می‌شود. `snapp_sync.py` فقط در دادهٔ داخلی candidateها، شناسه/موبایل را از Sales Order یا Customer تکمیل می‌کند تا شناسهٔ مشتری به API عمومی سفارش‌ها اضافه نشود.

**Tech Stack:** Python، Frappe API، unittest.

## Global Constraints

- هیچ سفارش یا فاکتوری زنده تأیید، رد، ایجاد یا ویرایش نمی‌شود.
- تطبیق یک‌به‌یک، همان‌روز، اقلام/تعداد و تلورانس مبلغ موجود حفظ می‌شود؛ سفارش دستیِ پیش‌نویس یا نهایی‌شده قابل تطبیق است.
- اگر هویت مشتری قابل‌تطبیق نباشد، سفارش به‌اشتباه پنهان/حذف نشود.

---

### کار ۱: نوشتن تست رگرسیون هویت مشتری

**Files:**
- Modify: `restaurant/tests/test_food_partner_duplicates.py`
- Test: `restaurant/tests/test_food_partner_duplicates.py`

**Interfaces:** ورودی‌های fixture شامل `external_customer_id`، `mobile` و `customer_name` خواهند بود؛ matcher فعلی باید برای تست‌های جدید ابتدا اشتباه پاسخ دهد.

- [x] تست‌های موفق برای شناسهٔ یکسان، موبایل یکسان با ارقام فارسی/عربی، نام معتبر در نبود موبایل، و سفارش دستیِ پیش‌نویس؛ تست‌های رد برای مشتری متفاوت، نام عمومی و هویت خالی نوشته و پیش از پیاده‌سازی اجرا شدند.
- [x] اجرا: `python3 -m unittest restaurant.tests.test_food_partner_duplicates`؛ تست‌های مشتری و draft ابتدا شکست درست نشان دادند.

### کار ۲: تطبیق مطمئن مشتری و انتقال شناسه

**Files:**
- Modify: `restaurant/food_partner_duplicates.py`
- Modify: `restaurant/snapp_sync.py` در `_manual_pos_orders_for_window`
- Test: `restaurant/tests/test_food_partner_duplicates.py`

**Interfaces:** `find_manual_duplicate(partner_order, manual_orders, ...)` همچنان ورودی/خروجی فعلی را دارد؛ رکورد دستی در صورت دسترسی فیلد `external_customer_id`، `mobile` و `customer_name` می‌گیرد.

- [x] شناسهٔ بیرونیِ متناقض رد شود؛ شناسهٔ یکسان پذیرفته شود؛ در نبود شناسه، موبایل نرمال‌شده مقایسه شود؛ سپس فقط نام غیرعمومیِ نرمال‌شده fallback باشد.
- [x] `snapp_sync.py` شناسه/موبایل مشتری را فقط در candidate داخلی از Sales Order یا Customer تکمیل می‌کند؛ پاسخ عمومی API تغییر نمی‌کند.
- [x] `python3 -m unittest restaurant.tests.test_food_partner_duplicates` (۲۴ تست)، `node --test frontend/tests/foodPartnerDuplicatePrevention.test.js` (۴ تست)، `python3 -m py_compile ...` و `git diff --check` پاس شدند. اجرای `restaurant.tests.test_snapp_sync` به‌علت نبود بستهٔ `frappe` در Python محیط میزبان ممکن نبود.

### کار ۳: بازبینی و ثبت تغییر

- [x] diff و وضعیت مخزن بازبینی شد و هیچ فایل نامرتبطی در این worktree تغییر نکرد.
- [x] تغییرات با پیام commit فارسی ثبت شوند؛ انتشار و تغییر سفارش‌های زنده خارج از این تغییر است.
