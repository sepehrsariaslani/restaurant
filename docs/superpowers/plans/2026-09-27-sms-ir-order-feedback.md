# SMS.ir Order Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** تکمیل مرکز پیامک SMS.ir و ارسال خودکار لینک امن نظرسنجی محصولات یک ساعت بعد از ثبت سفارش در veederakht.ir.

**Architecture:** از سیستم رویدادهای موجود `accounts.sms_ir_events` برای صف، dedupe، زمان‌بندی و گزارش استفاده می‌شود. `restaurant.survey_tokens` تنها مسئول صدور و ابطال توکن صفحهٔ موجود `/survey` است و مسیر قدیمی باشگاه مشتریان فقط وقتی قالب SMS.ir وجود ندارد به‌عنوان fallback کار می‌کند.

**Tech Stack:** Python/Frappe، DocTypeهای `SMS Template` و `SMS Delivery Log`، Vue 3، Vite، تست‌های `unittest` و Node `node:test`، Docker/Frappe scheduler.

## Global Constraints

- هیچ تستی نباید بدون درخواست صریح، پیامک billable ارسال کند؛ تست provider فقط با mock یا خواندن اعتبار و خطوط انجام می‌شود.
- کلید API و توکن خام نظرسنجی نباید در response، log، `context_json` یا UI ذخیره/نمایش داده شوند.
- نام متغیر SMS.ir حداکثر ۴۰ نویسه و مقدار پارامتر Verify حداکثر ۲۵ نویسه است.
- زمان پیش‌فرض رویداد `order_feedback_request` برابر ۶۰ دقیقه از زمان ثبت سفارش است.
- پیام‌های قابل مشاهده در رابط مرکز پیامک فارسی و راست‌به‌چپ می‌مانند و از Button/PageHeader موجود استفاده می‌کنند.
- هر تغییر backend و frontend تست focused، بررسی syntax/build و کامیت توضیح‌دار فارسی دارد.

---

### Task 1: قواعد خالص متغیرهای SMS.ir

**Files:**
- Modify: `/home/sepehr/den-v16-docker/apps/accounts/accounts/sms_ir_rules.py`
- Modify: `/home/sepehr/den-v16-docker/apps/accounts/frontend/src/services/smsIrTemplateUtils.js`
- Test: `/home/sepehr/den-v16-docker/apps/accounts/accounts/tests/test_sms_ir_rules.py`
- Test: `/home/sepehr/den-v16-docker/apps/accounts/frontend/src/smsCenterPage.test.js`

**Interfaces:**
- Produces `normalize_sms_ir_parameter_name(value) -> str`, `provider_variable_name(name) -> str` و `extract_sms_ir_parameters(text) -> list[dict[str, str]]`.
- `provider_variable_name` باید نگاشت‌های `CODE/OTP/VERIFICATIONCODE -> otp`، `TOKEN/SURVEY_TOKEN -> survey_token`، `NAME/FULLNAME/CUSTOMER_NAME -> customer_name`، `PHONE/MOBILE -> mobile`، `ORDERID/ORDER_ID/ORDER_NUMBER -> order_id`، `AMOUNT/PRICE -> amount` و `LINK -> survey_url` را برگرداند.

- [ ] **Step 1: Write the failing tests**

```python
def test_provider_names_are_normalized_and_deduplicated(self):
	self.assertEqual(rules.normalize_sms_ir_parameter_name(" order_number "), "ORDER_NUMBER")
	self.assertEqual(rules.provider_variable_name("FULLNAME"), "customer_name")
	self.assertEqual(
		rules.extract_sms_ir_parameters("#CODE# #CODE# #ORDER_NUMBER#"),
		[
			{"name": "CODE", "variable": "otp"},
			{"name": "ORDER_NUMBER", "variable": "order_id"},
		],
	)

def test_parameter_names_reject_invalid_or_long_values(self):
	with self.assertRaises(ValueError):
		rules.normalize_sms_ir_parameter_name("1BAD")
	with self.assertRaises(ValueError):
		rules.normalize_sms_ir_parameter_name("A" * 41)
```

Run: `cd /home/sepehr/den-v16-docker/apps/accounts && python3 -m unittest accounts.tests.test_sms_ir_rules`

Expected: FAIL because the normalization and canonical mapping functions do not exist or the old extractor maps names by lowercase only.

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `cd /home/sepehr/den-v16-docker/apps/accounts && python3 -m unittest accounts.tests.test_sms_ir_rules -v`

Expected: at least the new normalization and alias assertions fail; existing extraction assertions remain readable.

- [ ] **Step 3: Implement the minimal pure rules**

Add a compiled provider-name regex and implement the following behavior in `sms_ir_rules.py`:

```python
SMSIR_PARAMETER_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,39}$")
PROVIDER_VARIABLE_ALIASES = {
	"CODE": "otp", "OTP": "otp", "VERIFICATIONCODE": "otp",
	"TOKEN": "survey_token", "SURVEY_TOKEN": "survey_token",
	"NAME": "customer_name", "FULLNAME": "customer_name", "CUSTOMER_NAME": "customer_name",
	"PHONE": "mobile", "MOBILE": "mobile",
	"ORDERID": "order_id", "ORDER_ID": "order_id", "ORDER_NUMBER": "order_id",
	"AMOUNT": "amount", "PRICE": "amount", "LINK": "survey_url",
}

def normalize_sms_ir_parameter_name(value: Any) -> str:
	name = str(value or "").strip().upper()
	if not SMSIR_PARAMETER_NAME_RE.fullmatch(name):
		raise ValueError("نام متغیر SMS.ir باید با حرف شروع شود و حداکثر ۴۰ نویسه باشد")
	return name

def provider_variable_name(name: Any) -> str:
	normalized = normalize_sms_ir_parameter_name(name)
	return PROVIDER_VARIABLE_ALIASES.get(normalized, normalized.lower())
```

Update `extract_sms_ir_parameters` to call the normalizer, dedupe first-seen names, and use `provider_variable_name` instead of the `CODE` special case. Keep the existing marker regex so only valid markers in message text are extracted.

Update `providerVariableName` in `smsIrTemplateUtils.js` with the same alias table and return `value` only for a valid custom name fallback.

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: `cd /home/sepehr/den-v16-docker/apps/accounts && python3 -m unittest accounts.tests.test_sms_ir_rules -v`

Expected: all rules tests PASS.

Run: `cd /home/sepehr/den-v16-docker/apps/accounts/frontend && node --test src/smsCenterPage.test.js`

Expected: existing page contract tests PASS; the new variable names are not yet required until Task 5.

- [ ] **Step 5: Commit**

```bash
cd /home/sepehr/den-v16-docker/apps/accounts
git add accounts/sms_ir_rules.py accounts/tests/test_sms_ir_rules.py frontend/src/services/smsIrTemplateUtils.js frontend/src/smsCenterPage.test.js
git commit -m "تکمیل قواعد متغیرهای قالب SMS.ir"
```

### Task 2: اعتبارسنجی ذخیرهٔ قالب و تأخیر نظرسنجی

**Files:**
- Modify: `/home/sepehr/den-v16-docker/apps/accounts/accounts/sms_ir_api.py`
- Test: `/home/sepehr/den-v16-docker/apps/accounts/accounts/tests/test_sms_ir_api_contract.py`
- Test: `/home/sepehr/den-v16-docker/apps/accounts/accounts/tests/test_sms_ir_rules.py`

**Interfaces:**
- `save_sms_template(values)` باید نام‌های `parameters_json` و متغیرهای بدنه را با `normalize_sms_ir_parameter_name` validate کند.
- `order_feedback_request` در صورت نبود مقدار delay صریح، باید با `delay_minutes=60` ذخیره شود.

- [ ] **Step 1: Write the failing tests**

در `test_sms_ir_api_contract.py` قراردادهای زیر را اضافه کن:

```python
def test_template_save_enforces_parameter_name_limit_and_feedback_default_delay(self):
	source = (ROOT / "accounts" / "sms_ir_api.py").read_text()
	self.assertIn("normalize_sms_ir_parameter_name", source)
	self.assertIn('doc.event_key == "order_feedback_request"', source)
	self.assertIn("60", source)
```

در `test_sms_ir_rules.py` یک نام ۴۱ نویسه‌ای را از مسیر normalizer رد کن؛ این تست با Task 1 آماده است و اجرای کل suite باید نشان دهد validation هنوز به save path وصل نشده است.

- [ ] **Step 2: Run the focused tests to verify the contract is missing**

Run: `cd /home/sepehr/den-v16-docker/apps/accounts && python3 -m unittest accounts.tests.test_sms_ir_api_contract -v`

Expected: FAIL on the missing normalizer usage/default-delay contract.

- [ ] **Step 3: Implement validation and default delay**

در `sms_ir_api.py`:

1. `normalize_sms_ir_parameter_name` را import کن.
2. هنگام خواندن `parameters_json`، برای هر نام از normalizer استفاده کن؛ `ValueError` را به `frappe.ValidationError` با پیام فارسی تبدیل کن.
3. استخراج پارامترهای بدنه نیز باید با همان normalizer انجام شود.
4. اگر `event_key == "order_feedback_request"` و `delay_minutes` در values خالی است، مقدار ۶۰ قرار بده؛ اگر کاربر مقدار عددی صریح داده، همان مقدار معتبر ۰ تا ۴۳۲۰۰ را نگه دار.
5. duplicate نام پارامتر supplied همچنان خطای validation بدهد و duplicateای که از body کشف شده، فقط یک‌بار append شود.

نمونهٔ شاخهٔ تأخیر:

```python
raw_delay = values.get("delay_minutes")
if raw_delay in (None, "") and doc.event_key == "order_feedback_request":
	delay_minutes = 60
else:
	delay_minutes = cint(raw_delay or 0)
```

- [ ] **Step 4: Run the focused backend tests**

Run: `cd /home/sepehr/den-v16-docker/apps/accounts && python3 -m unittest accounts.tests.test_sms_ir_rules accounts.tests.test_sms_ir_api_contract -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/sepehr/den-v16-docker/apps/accounts
git add accounts/sms_ir_api.py accounts/tests/test_sms_ir_api_contract.py accounts/tests/test_sms_ir_rules.py
git commit -m "اعتبارسنجی متغیر و تأخیر پیش‌فرض نظرسنجی"
```

### Task 3: context سفارش و زمان پایهٔ ثبت سفارش در رویداد SMS.ir

**Files:**
- Modify: `/home/sepehr/den-v16-docker/apps/accounts/accounts/sms_ir_events.py`
- Modify: `/home/sepehr/den-v16-docker/apps/accounts/accounts/sms_ir_event_rules.py`
- Test: `/home/sepehr/den-v16-docker/apps/accounts/accounts/tests/test_sms_ir_system_events.py`
- Test: `/home/sepehr/den-v16-docker/apps/accounts/accounts/tests/test_sms_ir_api_contract.py`

**Interfaces:**
- `schedule_system_event(..., event_time=None)` باید زمان schedule را از `event_time + delay` بسازد و برای سررسید گذشته، `now` را استفاده کند.
- `_context_for_sales_order` باید `order_id`, `order_number`, `customer_name`, `mobile`, `amount`, `price`, `status`, `items_count`, `date`, `time` را تولید کند.
- `_template_parameters` باید مقدار بیش از ۲۵ نویسه را با `ValueError` رد کند و هرگز silent truncate نکند.

- [ ] **Step 1: Write failing tests**

در `test_sms_ir_system_events.py` تست‌های خالص زیر را اضافه کن:

```python
def test_scheduled_time_never_stays_before_now(self):
	rules = _load_rules()
	base = datetime(2026, 9, 22, 10, 0, tzinfo=timezone.utc)
	now = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)
	self.assertEqual(rules.scheduled_time(base, 60, now=now), now)

def test_feedback_context_contains_order_fields(self):
	source = (ROOT / "accounts" / "sms_ir_events.py").read_text()
	for field in ("order_number", "items_count", "price", "date", "time"):
		self.assertIn(f'"{field}"', source)

def test_verify_parameter_value_is_not_silently_truncated(self):
	source = (ROOT / "accounts" / "sms_ir_events.py").read_text()
	self.assertIn("نباید بیشتر از ۲۵ نویسه", source)
	self.assertNotIn("[:25]", source)
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `cd /home/sepehr/den-v16-docker/apps/accounts && python3 -m unittest accounts.tests.test_sms_ir_system_events -v`

Expected: FAIL because `scheduled_time` does not accept `now`, fields are absent, and parameters are currently truncated.

- [ ] **Step 3: Implement event context and safe scheduling**

1. Extend `scheduled_time(event_time, delay_minutes, now=None)` to return `max(event_time + delay, now)` while preserving timezone-naive compatibility.
2. Add `event_time` to `enqueue_system_event`, `schedule_system_event` and `_enqueue_sales_order`; pass `doc.creation` from `sales_order_on_submit` and status update hooks.
3. In `_context_for_sales_order`, count non-auto-added items and provide aliases for the provider variables. Use `frappe.utils.get_datetime` for creation and format stable strings for date/time.
4. In `_template_parameters`, resolve `variable` through the context alias map and raise `ValueError("مقدار پارامتر ... نباید بیشتر از ۲۵ نویسه باشد")` for a long Verify value.
5. Preserve `_safe_context` filtering for token/url and keep the actual token issuance only at dispatch time.

Example parameter guard:

```python
value = str(context.get(variable) or "")
if len(value) > 25:
	raise ValueError(f"مقدار پارامتر {name} نباید بیشتر از ۲۵ نویسه باشد")
parameters.append({"name": name, "value": value})
```

- [ ] **Step 4: Run focused system-event tests**

Run: `cd /home/sepehr/den-v16-docker/apps/accounts && python3 -m unittest accounts.tests.test_sms_ir_system_events accounts.tests.test_sms_ir_api_contract -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/sepehr/den-v16-docker/apps/accounts
git add accounts/sms_ir_events.py accounts/sms_ir_event_rules.py accounts/tests/test_sms_ir_system_events.py accounts/tests/test_sms_ir_api_contract.py
git commit -m "تکمیل زمان‌بندی و اطلاعات سفارش پیامک"
```

### Task 4: توکن امن و اتصال دعوت نظرسنجی در restaurant

**Files:**
- Create: `/home/sepehr/den-v16-docker/apps/restaurant/restaurant/survey_tokens.py`
- Modify: `/home/sepehr/den-v16-docker/apps/restaurant/restaurant/api_survey.py`
- Test: `/home/sepehr/den-v16-docker/apps/restaurant/restaurant/tests/test_customer_survey_security.py`
- Test: `/home/sepehr/den-v16-docker/apps/restaurant/restaurant/tests/test_survey_sms_bridge.py`

**Interfaces:**
- `issue_token(order_name, customer, mobile, expires_at) -> str` creates/updates the invitation and stores only SHA-256 digest.
- `revoke_token(token) -> None` clears the invitation digest after provider failure.
- `resolve_token(token) -> invitation | None` validates expiry and digest without exposing stored token.

- [ ] **Step 1: Write the failing tests**

Create `test_survey_sms_bridge.py` with isolated Frappe stubs and assertions for the pure token contract:

```python
def test_issued_token_is_short_and_only_digest_is_persisted(self):
	token = module.generate_token()
	self.assertLessEqual(len(token), 25)
	self.assertNotEqual(module.token_digest(token), token)

def test_feedback_dispatch_source_uses_secure_token_module(self):
	source = Path(ACCOUNTS_ROOT / "accounts" / "sms_ir_events.py").read_text()
	self.assertIn("from restaurant.survey_tokens import issue_token", source)
```

Extend `test_customer_survey_security.py` to assert that Sales Order status `confirmed` is accepted by `_read_order_identity`/`_load_order` and that the public token path still rejects a forged order item.

- [ ] **Step 2: Run the new tests to verify failure**

Run: `cd /home/sepehr/den-v16-docker/apps/restaurant && python3 -m unittest restaurant.tests.test_survey_sms_bridge restaurant.tests.test_customer_survey_security -v`

Expected: FAIL because `survey_tokens.py` is absent and Sales Order survey loading only accepts delivered/served.

- [ ] **Step 3: Implement secure token bridge**

Create `survey_tokens.py` with a 15-byte URL-safe token, SHA-256 digest, constant-time digest comparison, expiry check, and invitation upsert. The invitation key is `Sales Order:<order_name>`; a pre-existing invitation is reused. The token module stores `token_hash`, `expires_at`, customer/mobile and a sent/active state, never the raw token.

Update `api_survey.py`:

1. Accept submitted Sales Orders in `new`, `confirmed`, `preparing`, `ready`, `delivered`, and `served` for survey reads.
2. Let `_queue_invitation` use the order creation timestamp as the base for `due_at`, with `max(now, creation + delay)`.
3. Before legacy dispatch, check `SMS Delivery Log` for a scheduled/sent/processing `order_feedback_request` for the same Sales Order. If present, mark the old invitation as skipped and do not call the legacy gateway.
4. Keep URL redaction and existing ownership/item validation unchanged.

- [ ] **Step 4: Run restaurant security tests**

Run: `cd /home/sepehr/den-v16-docker/apps/restaurant && python3 -m unittest restaurant.tests.test_survey_sms_bridge restaurant.tests.test_customer_survey_security -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/sepehr/den-v16-docker/apps/restaurant
git add restaurant/survey_tokens.py restaurant/api_survey.py restaurant/tests/test_survey_sms_bridge.py restaurant/tests/test_customer_survey_security.py
git commit -m "اتصال امن توکن نظرسنجی به پیامک سفارش"
```

### Task 5: تکمیل رابط مرکز پیامک و قالب آمادهٔ نظرسنجی

**Files:**
- Modify: `/home/sepehr/den-v16-docker/apps/accounts/frontend/src/pages/SmsCenter.vue`
- Modify: `/home/sepehr/den-v16-docker/apps/accounts/frontend/src/services/smsIrTemplateUtils.js`
- Test: `/home/sepehr/den-v16-docker/apps/accounts/frontend/src/smsCenterPage.test.js`

**Interfaces:**
- `templateVariableOptions` contains every screenshot variable plus `SURVEY_TOKEN`, `CUSTOMER_NAME`, `MOBILE`.
- `insertTemplateVariable(name)` remains caret/selection-aware.
- `newFeedbackTemplate()` pre-fills `event_key=order_feedback_request`, `system_template=true`, `delay_mode=delayed`, `delay_minutes=60`, and a Persian starter body.
- `addCustomTemplateVariable()` validates the ۴۰-character provider rule and inserts the token.

- [ ] **Step 1: Write the failing UI contract tests**

Extend `smsCenterPage.test.js`:

```js
test('sms template editor exposes all SMS.ir variables and feedback shortcut', () => {
  for (const variable of ['TOKEN', 'OTP', 'CODE', 'NAME', 'TIME', 'VERIFICATIONCODE', 'DATE', 'USERNAME', 'FULLNAME', 'ORDERID', 'PASSWORD', 'TITLE', 'AMOUNT', 'PRICE', 'ORDER_NUMBER', 'LINK', 'STATUS', 'ITEMS_COUNT', 'PHONE']) {
    assert.match(page, new RegExp(variable))
  }
  assert.match(page, /newFeedbackTemplate/)
  assert.match(page, /متغیر دلخواه/)
  assert.match(page, /حداکثر ۴۰/)
})
```

- [ ] **Step 2: Run the UI contract test to confirm failure**

Run: `cd /home/sepehr/den-v16-docker/apps/accounts/frontend && node --test src/smsCenterPage.test.js`

Expected: FAIL because the page currently has only six variable buttons and no custom-variable/feedback shortcut contract.

- [ ] **Step 3: Implement the Persian RTL controls**

1. Replace the six-item array with the exact provider list and app-specific aliases; use Persian labels and canonical `variable` values from `providerVariableName`.
2. Add a text input and button titled `افزودن متغیر دلخواه`; normalize uppercase, validate `/^[A-Z][A-Z0-9_]{0,39}$/`, show Persian validation, and call `insertTemplateVariable`.
3. Add `newFeedbackTemplate()` beside the existing system-template action. Prefill:

```js
body: 'سلام #NAME# عزیز،\nنظر شما درباره سفارش #ORDER_NUMBER# برای ما مهم است:\nhttps://veederakht.ir/survey?token=#TOKEN#',
parameters_json: '[{"name":"NAME","variable":"customer_name"},{"name":"ORDER_NUMBER","variable":"order_id"},{"name":"TOKEN","variable":"survey_token"}]',
event_key: 'order_feedback_request',
recipient_type: 'مشتری',
system_template: true,
delay_mode: 'delayed',
delay_minutes: 60,
```

4. Keep the existing provider-template table, rejection reason, line tab and persistent credit card unchanged; update the feedback helper text to recommend `#TOKEN#` because Verify values are limited to ۲۵ نویسه.

- [ ] **Step 4: Run UI tests and build**

Run: `cd /home/sepehr/den-v16-docker/apps/accounts/frontend && node --test src/smsCenterPage.test.js && npm run build:check`

Expected: all SMS center tests PASS and Vite build-check succeeds with only existing chunk-size warnings.

- [ ] **Step 5: Commit**

```bash
cd /home/sepehr/den-v16-docker/apps/accounts
git add frontend/src/pages/SmsCenter.vue frontend/src/services/smsIrTemplateUtils.js frontend/src/smsCenterPage.test.js
git commit -m "تکمیل رابط قالب‌ها و متغیرهای SMS.ir"
```

### Task 6: یکپارچه‌سازی fallback و تست گردش سفارش

**Files:**
- Modify: `/home/sepehr/den-v16-docker/apps/restaurant/restaurant/api_survey.py`
- Modify: `/home/sepehr/den-v16-docker/apps/restaurant/restaurant/tests/test_customer_survey_security.py`
- Create: `/home/sepehr/den-v16-docker/apps/restaurant/restaurant/tests/test_survey_invitation_flow.py`
- Test: `/home/sepehr/den-v16-docker/apps/accounts/accounts/tests/test_sms_ir_system_events.py`

**Interfaces:**
- `run_due_survey_invitations` must skip legacy send when an SMS.ir feedback log exists.
- `accounts.sms_ir_events.sales_order_on_submit` must create `order_feedback_request` and `order_confirmed` through the existing hook only once per order/template.
- cancellation must leave no sendable scheduled feedback log.

- [ ] **Step 1: Write failing flow tests**

Create `test_survey_invitation_flow.py` with stubbed `frappe.db` and `api_club`:

```python
def test_legacy_survey_does_not_send_after_sms_ir_feedback_is_queued(self):
    invitation = FakeInvitation(status="در انتظار ارسال")
    self.module.frappe.db.exists = lambda doctype, name=None: doctype in {"Restaurant Survey Invitation", "SMS Delivery Log"}
    self.module.frappe.get_all = lambda *args, **kwargs: [{"name": "SDL-1"}] if args and args[0] == "SMS Delivery Log" else []
    self.module.frappe.get_doc = lambda *args, **kwargs: invitation
    result = self.module.run_due_survey_invitations()
    self.assertEqual(result["sent"], 0)
    self.assertEqual(invitation.status, "بدون درگاه")
```

Add a contract assertion that the cancellation function targets `event_key='order_feedback_request'` and only `status='زمان‌بندی‌شده'`.

- [ ] **Step 2: Run flow tests to verify failure**

Run: `cd /home/sepehr/den-v16-docker/apps/restaurant && python3 -m unittest restaurant.tests.test_survey_invitation_flow -v`

Expected: FAIL because the old scheduler currently calls the legacy gateway without checking `SMS Delivery Log`.

- [ ] **Step 3: Implement the deduplicated fallback**

Add a small `_sms_ir_feedback_exists(reference_name)` helper that queries `SMS Delivery Log` for the same Sales Order and event key, accepting `زمان‌بندی‌شده`, `در حال ارسال`, `ارسال شد`, `تحویل‌شده`, `تحویل‌نشده`, or `ناموفق` as an existing provider attempt. In `run_due_survey_invitations`, mark the invitation `بدون درگاه` with a safe note and commit before continuing. Do not store any raw URL in the note.

Keep `accounts.sms_ir_scheduler.cancel_scheduled_order_feedback` as the single cancellation implementation and do not add a second queue.

- [ ] **Step 4: Run the combined backend tests**

Run:

```bash
cd /home/sepehr/den-v16-docker/apps/accounts
python3 -m unittest accounts.tests.test_sms_ir_full_client accounts.tests.test_sms_ir_customer_otp_contract accounts.tests.test_sms_ir_api_contract accounts.tests.test_sms_ir_full_api accounts.tests.test_sms_ir_rules accounts.tests.test_sms_ir_system_events accounts.tests.test_sms_ir_templates
cd /home/sepehr/den-v16-docker/apps/restaurant
python3 -m unittest restaurant.tests.test_survey_invitation_flow restaurant.tests.test_customer_survey_security restaurant.tests.test_survey_scale_patch
```

Expected: all focused accounts tests and the three focused restaurant survey tests PASS; no real provider send is attempted.

- [ ] **Step 5: Commit**

```bash
cd /home/sepehr/den-v16-docker/apps/restaurant
git add restaurant/api_survey.py restaurant/tests/test_survey_invitation_flow.py restaurant/tests/test_customer_survey_security.py
git commit -m "جلوگیری از ارسال تکراری نظرسنجی سفارش"
```

### Task 7: بیلد، استقرار و بررسی نهایی

**Files:**
- Modify: `/home/sepehr/den-v16-docker/apps/accounts/accounts/public/frontend/` only through the approved frontend build output.
- Modify: `/home/sepehr/den-v16-docker/apps/restaurant/restaurant/public/frontend/` only through the approved frontend build output.
- Verify: Docker services for `veederakht.ir`.

**Interfaces:**
- No API key or real SMS content is written into build output.
- The public website must serve the new bundles and backend methods without HTTP 500/417 caused by code regressions.

- [ ] **Step 1: Run source syntax and focused UI tests before build**

Run:

```bash
python3 -m py_compile /home/sepehr/den-v16-docker/apps/accounts/accounts/sms_ir_rules.py /home/sepehr/den-v16-docker/apps/accounts/accounts/sms_ir_api.py /home/sepehr/den-v16-docker/apps/accounts/accounts/sms_ir_events.py /home/sepehr/den-v16-docker/apps/restaurant/restaurant/survey_tokens.py /home/sepehr/den-v16-docker/apps/restaurant/restaurant/api_survey.py
cd /home/sepehr/den-v16-docker/apps/accounts/frontend && node --test src/smsCenterPage.test.js
cd /home/sepehr/den-v16-docker/apps/restaurant/frontend && node --test tests/*.test.mjs
```

Expected: Python syntax and focused accounts UI tests PASS. Any unrelated pre-existing restaurant frontend failures must be listed separately rather than hidden.

- [ ] **Step 2: Build both frontends**

Run `npm run build` in `/home/sepehr/den-v16-docker/apps/accounts/frontend` and `/home/sepehr/den-v16-docker/apps/restaurant/frontend`.

Expected: Vite completes; generated assets are copied/tracked in the app public frontend directories according to the existing repository convention.

- [ ] **Step 3: Restart/reload Frappe services and verify public routes**

From `/home/sepehr/den-v16-docker`, reload the relevant backend/frontend services using the existing deployment workflow, then verify:

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' https://veederakht.ir/customer/login
curl -fsS -o /dev/null -w '%{http_code}\n' https://veederakht.ir/survey
```

Expected: both routes return HTTP 200. Verify the SMS center route loads the new variable palette and feedback shortcut.

- [ ] **Step 4: Verify provider status without sending SMS**

Call the existing provider status endpoint and confirm the UI shows credit and available lines. Do not call `send_sms_ir_verify`, `send_sms_ir_legacy`, or OTP login while the known credit is zero.

Expected: connection/credit/line read succeeds or reports the provider’s current insufficient-credit message; no new message ID is created.

- [ ] **Step 5: Commit generated assets and final verification**

```bash
cd /home/sepehr/den-v16-docker/apps/accounts
git status --short
git add accounts/public/frontend
git commit -m "انتشار رابط نهایی مرکز پیامک"

cd /home/sepehr/den-v16-docker/apps/restaurant
git status --short
git add restaurant/public/frontend
git commit -m "انتشار رابط نهایی نظرسنجی سفارش"
```

Expected: both repositories are clean except for unrelated pre-existing user changes, and final report includes commit hashes, tests, build result, deployed routes, and the fact that live SMS was not consumed because credit is zero.
