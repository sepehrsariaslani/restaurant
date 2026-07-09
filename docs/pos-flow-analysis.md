# 📊 تحلیل کامل جریان‌های POS

## 📍 سشن جاری (کارت POS)
### سه دکمه اصلی:

| دکمه | Event | API | SO | SI+Payment | Production | DN | Status نهایی |
|------|-------|-----|:--:|:-----------:|:----------:|:--:|:-----------:|
| **ثبت سفارش** 🔵 | `submit-order` | `createPOSOrder` | ✅ | ❌ | ❌ | ❌ | `confirmed` |
| **تسویه فاکتور** 💳 | `submit-and-pay` | `createAndPayPOSOrder` | ✅ | ✅ | ❌ | ❌ | `paid` |
| **تسویه و تحویل** 🚀 | `submit-and-settle` | `createAndSettlePOSOrder` | ✅ | ✅ | ✅ | ✅ | `delivered` |

---

## 📋 تب سفارش‌های اخیر (ساید پنل)
### دکمه‌های روی هر کارت:

| دکمه | API | Production | SI+Payment | DN | Status |
|------|-----|:----------:|:-----------:|:--:|:------:|
| **ثبت و تسویه** 🚀 (on card) | `quickSettleOrder` → پاپ‌آپ پرداخت | ✅ | ✅ | ✅ | `delivered` |
| **🏭 تحویل** (on card) | `deliverPOSOrder` | ✅ | ❌ | ✅ | `delivered` |

---

## 📑 تب فاکتورهای باز (ساید پنل - آکاردئون)
### دکمه‌های توی هر آکاردئون:

| دکمه | API | SI+Payment | Production | DN | Status | فاکتور باز میمونه؟ |
|------|-----|:----------:|:----------:|:--:|:------:|:-----------------:|
| **انتخاب و بارگذاری** 📋 | `selectAndLoadInvoice` | ❌ | ❌ | ❌ | - | ✅ |
| **پرداخت** 💳 | `settleSelectedInvoice` → پاپ‌آپ → `settlePOSOrder` | ✅ | ❌ | ❌ | `paid` | ❌ |
| **تسویه و تحویل** 🟢 | `settleAndDeliverFromInvoice` | ✅ | ✅ | ✅ | `delivered` | ❌ |
| **تحویل** 🔵 | `deliverInvoiceOnly` | ❌ | ❌ | ✅ | unchanged | ✅ (فقط مخفی شدن دکمه) |

---

## 🍳 صفحه آشپزخانه (KDS) - `/management/kitchen`

| وضعیت | معنی | دکمه | Status بعدی |
|-------|------|------|:-----------:|
| **جدید** 🆕 (`new`, `confirmed`) | آماده شروع تولید | ✓ شروع تولید | `preparing` |
| **تولید** 🔧 (`preparing`) | در حال آماده‌سازی | ✓ آماده شد | `ready` |
| **آماده** ✅ (`ready`) | آماده تحویل | ✓ تحویل داده شد | `delivered` |

---

## 🔍 تحلیل وضعیت‌های از قلم افتاده

### ۱. مشکل: تب "فاکتورهای باز" بعد از تحویل
- وضعیت فعلی: وقتی دکمه **تحویل 🔵** رو میزنیم، `delivery_exists=true` میشه و دکمه‌ها مخفی میشن
- ولی اگر API رفرش بشه... الان با `deliveredInvoices Set` درست شد ✅

### ۲. مشکل: وضعیت "تحویل شده بدون پرداخت" توی سفارش‌های اخیر
- فاکتور تحویل شده ولی پرداخت نشده توی تب سفارش‌های اخیر هست
- دکمه **ثبت و تسویه** باید براش بیاد؟ **بله**
- دکمه **🏭 تحویل** نباید بیاد چون DN خورده
- با `canDeliverOrder` و `canSettleOrder` درست شد ✅

### ۳. 🔴 سناریوی از قلم افتاده: تسویه از سفارش‌های اخیر
وقتی کاربر دکمه **ثبت و تسویه** رو روی کارت سفارش‌ها میزنه (`quickSettleOrder`):
→ مودال جزئیات باز میشه
→ باید بتونه SI + Payment بزنه
→ و اگر میخواد Production + DN هم بزنه

این الان از طریق `confirmSettleOrder` در مودال جزئیات انجام میشه که فقط `markManagementOrderPaid` صدا میزنه و تولید/تحویل انجام نمیده ❌

### ۴. 🔴 سناریوی از قلم افتاده: حالت "اعتباری + تحویل شده"
- مشتری اعتباری خرید کرده
- بعداً میاد تحویل میگیره
- دکمه تحویل باید براش بیاد چون payment_method = 'credit' هست

با `canDeliverOrder` که چک میکنه `payment_method !== 'credit'` درست شد ✅

### ۵. 🔴 سناریوی از قلم افتاده: ترکیب پرداخت (Split Payment)
- مشتری با دو روش پرداخت میکنه (مثلاً نقد + کارت)
- پاپ‌آپ پرداخت قبلاً از `paymentSplits` پشتیبانی میکنه ✅

### ۶. 🤔 سناریوی مرزی: دوبار زدن دکمه
- اگه کاربر ۲ بار دکمه **تسویه و تحویل** رو بزنه چی؟ 
- API دوبار صدا زده میشه
- مشکل: SI تکراری ساخته میشه ❌

### ۷. 🤔 سناریوی مرزی: Production Ticket قبلاً وجود داره
- کد فعلی: `if not ticket_names: cp = _create_production_for_sales_order(so_doc)` ✅

### ۸. 🔴 نیاز: چک کردن اینکه آیا DN قبلاً وجود داره
- `_create_delivery_note_for_sales_order` اول `_existing_delivery_note_for_sales_order` چک میکنه ✅
- ولی فرانت‌اند نمیدونه DN خورده یا نه

---

## 🔗 خلاصه APIهای موجود

### سمت فرانت‌اند (api.js):
```javascript
createPOSOrder(payload)           // فقط SO
producePOSOrder(order_name)       // فقط تولید
settlePOSOrder(order_name, payment) // فقط SI + Payment
deliverPOSOrder(order_name)        // تولید + تحویل (status = delivered)
deliverInvoiceOnly(order_name)     // فقط رسید تحویل (status unchanged)
createAndPayPOSOrder(payload)     // SO + SI + Payment
createAndSettlePOSOrder(payload)  // SO + Production + SI + DN + Payment
createAndProducePOSOrder(payload) // SO + Production (قدیمی - شاید حذف بشه)
```

### سمت بک‌اند (api.py):
```python
create_pos_order(payload)
produce_pos_order(order_name)
settle_pos_order(order_name, payment, reference_no, rrn)
deliver_pos_order(order_name)         # تولید کامل + تحویل
deliver_invoice_only(order_name)      # فقط رسید تحویل
create_and_pay_pos_order(payload)     # SO + SI + Payment
create_and_settle_pos_order(payload)  # همه چیز
produce_and_deliver_pos_order(order_name) # تولید هوشمند + تحویل
```

---

## 🔧 مواردی که نیاز به بهبود داره:

| اولویت | مورد | توضیح |
|:------:|------|-------|
| 🔴 | **دکمه ثبت و تسویه روی کارت سفارش‌ها** | `confirmSettleOrder` فقط `markManagementOrderPaid` صدا میزنه. باید `createAndSettlePOSOrder` صدا بزنه |
| 🟡 | **جلوگیری از دوبار کلیک** | Disable کردن دکمه بعد از کلیک (الان تا حدی با `submitting` هست) |
| 🟢 | **نمایش اینکه DN خورده در فاکتورهای باز** | API باید `dn_exists` رو برگردونه تا فرانت بدون رفرش متوجه بشه |
| 🟢 | **نمایش خلاصه POS** | مجموع فروش روز، تعداد سفارش، میانگین زمان در صفحه POS |
