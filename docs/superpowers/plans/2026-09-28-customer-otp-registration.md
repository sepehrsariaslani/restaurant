# Customer OTP Registration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task with verification checkpoints.

**Goal:** Replace email-link customer registration with mobile OTP verification, support optional email, complete new-customer profile setup, unify OTP event logging, reduce OTP request hangs, and add password change.

**Architecture:** Keep the public restaurant OTP endpoints as the single customer entry point. Existing customers receive a normal customer session; unknown mobiles receive a short-lived one-time mobile-verification ticket and only become Customer/User records after the profile form is submitted. SMS.ir Verify remains synchronous with a bounded client timeout, while unknown network outcomes preserve the OTP and are reported as pending instead of deleting it.

**Tech Stack:** Frappe/Python, Redis cache, SMS.ir Verify API, Vue 3/Vite, Node `node:test`, unittest.

## Global Constraints

- Email is optional during customer registration and must never trigger a required email-link step in the new UI.
- OTP values, API keys, and raw secrets must never be persisted in logs or returned to the browser.
- Existing customer OTP/password and legacy email endpoints remain backward-compatible unless this plan explicitly changes their caller.
- Every production behavior change is preceded by a failing test and followed by focused plus regression verification.
- Commits use Persian messages describing what changed and why.

### Task 1: Lock the backend OTP contract with failing tests

**Files:**
- Create: `restaurant/tests/test_customer_otp_contract.py`
- Modify: `restaurant/tests/test_customer_account.py`
- Create: `accounts/tests/test_sms_ir_customer_otp_contract.py` additions in the accounts repository

**Interfaces:**
- `verify_otp` returns `customer_exists=True` and `customer_token` for an existing mobile.
- `verify_otp` returns `customer_exists=False`, `mobile_verified=True`, and `mobile_verification_token` for a new mobile.
- `customer_register_password` accepts `mobile_verification_token`.
- `send_customer_otp` accepts optional `challenge_id` and logs `sms_sent`/`sms_failed` through Frappe’s shared OTP event logger.

- [ ] **Step 1: Write failing tests** for new-mobile verification tickets, one-time ticket consumption, optional-email registration contract, password-change endpoint presence, customer OTP event logging, and `delivery_pending` handling.
- [ ] **Step 2: Run the focused tests**:

```bash
python3 -m unittest restaurant.tests.test_customer_otp_contract restaurant.tests.test_customer_account
python3 -m unittest accounts.tests.test_sms_ir_customer_otp_contract
```

Expected: FAIL because the verification-ticket fields, password-change endpoint, shared logging call, and pending-delivery branch do not yet exist.

### Task 2: Implement secure OTP ticketing and unified event logging

**Files:**
- Modify: `restaurant/restaurant/api.py:10446-10547`
- Modify: `accounts/accounts/sms_ir_customer.py:1-100`
- Modify: `accounts/accounts/tests/test_sms_ir_customer_otp_contract.py`

**Interfaces:**
- Add `_otp_verified_ticket_key`, `_issue_mobile_verification_ticket`, and `_consume_mobile_verification_ticket` in `restaurant.api`.
- Store OTP cache as `{otp, challenge_id}` while accepting the old string shape for compatibility.
- Pass `challenge_id` into `send_customer_otp`.
- Preserve OTP cache on an `SmsIrProviderError` with no provider/HTTP status and return `delivery_pending=True`; delete it for definitive provider rejection.
- Log customer `sms_sent`, `sms_failed`, `otp_verified`, and `otp_failed` through `frappe.mobile_login._log_mobile_otp_event` without storing OTP values.

- [ ] **Step 1: Run the tests from Task 1 and confirm RED.**
- [ ] **Step 2: Implement only the ticket/cache/logging changes.** The success response must include `challenge_id`, `expires_in`, and either `customer_token` or `mobile_verification_token`.
- [ ] **Step 3: Run focused Python tests and confirm GREEN.**
- [ ] **Step 4: Run the existing customer OTP retry contract test:**

```bash
node --test frontend/tests/customer-otp-retry-contract.test.mjs
```

- [ ] **Step 5: Commit the backend OTP change in Persian.**

```bash
git add restaurant/api.py restaurant/tests/test_customer_otp_contract.py
git commit -m "یکپارچه‌سازی OTP مشتری و حفظ کد در خطای نامشخص"
```

### Task 3: Complete new-customer registration and password change

**Files:**
- Modify: `restaurant/restaurant/customer_account.py:441-518`
- Modify: `restaurant/frontend/src/utils/api.js:3549-3590,4402-4410`
- Add tests to: `restaurant/tests/test_customer_account.py`

**Interfaces:**
- `customer_register_password(customer_token=None, mobile_verification_token=None, name=None, email=None, password=None, referral_code=None)` creates the native Customer/User only after consuming a valid mobile ticket.
- `customer_change_password(customer_token=None, current_password=None, new_password=None, confirm_password=None)` validates the current password and updates the linked Website User.
- `customerRegisterPassword` sends `mobile_verification_token`.
- `changeCustomerPassword` sends the three password fields.

- [ ] **Step 1: Add failing tests** for one-time ticket registration with empty email, rejection of reused/expired tickets, password length/mismatch validation, and successful password change.
- [ ] **Step 2: Run `python3 -m unittest restaurant.tests.test_customer_account` and verify RED.**
- [ ] **Step 3: Add the verified-mobile customer creation branch.** It must reject a race where the mobile becomes an existing Customer before ticket consumption, create a unique Customer name, create a Website User with a safe internal fallback email when no email was supplied, and bind the portal user.
- [ ] **Step 4: Add `customer_change_password`.** Use `frappe.utils.password.check_password` for the old password and the existing `User.new_password` save path for the new password.
- [ ] **Step 5: Run focused Python tests and confirm GREEN.**
- [ ] **Step 6: Commit the account API change in Persian.**

```bash
git add restaurant/customer_account.py restaurant/tests/test_customer_account.py frontend/src/utils/api.js
git commit -m "ثبت‌نام مشتری با شماره تأییدشده و تغییر رمز عبور"
```

### Task 4: Replace email-link registration UI with OTP/profile flow

**Files:**
- Modify: `restaurant/frontend/src/pages/CustomerLoginPage.vue`
- Create or modify: `restaurant/frontend/tests/customer-registration-otp-contract.test.mjs`

**Interfaces:**
- Password login remains available for email/mobile plus password.
- Password registration sends an OTP to the entered mobile; email validation is optional.
- OTP login for a new mobile switches to a profile form containing name, optional email, referral code, password, and confirmation.
- Existing mobile OTP login persists `customer_token` and redirects immediately.

- [ ] **Step 1: Write failing Node contract tests** asserting no new UI call to `customerRegisterWithEmail`/`customerVerifyEmailRegistration`, optional email validation, `mobile_verification_token` handling, and profile-step rendering.
- [ ] **Step 2: Run the new test and confirm RED.**
- [ ] **Step 3: Remove the email-link branch from the active UI.** Keep backend wrappers for compatibility but remove their imports and query-driven activation from this page.
- [ ] **Step 4: Add `register_profile` state and registration ticket state.** The OTP verification branch must route unknown mobiles to this state instead of persisting an incomplete session.
- [ ] **Step 5: Change password registration to call `sendOtpAPI`, then verify OTP, then call `customerRegisterPassword` with the ticket.**
- [ ] **Step 6: Run the focused Node tests and `npm test` from `frontend/`.**
- [ ] **Step 7: Build the restaurant frontend with `npm run build` and inspect the generated asset diff.
- [ ] **Step 8: Commit the UI change in Persian.**

```bash
git add frontend/src/pages/CustomerLoginPage.vue frontend/tests/customer-registration-otp-contract.test.mjs frontend/src/utils/api.js public/frontend/assets
git commit -m "تغییر ثبت‌نام مشتری از لینک ایمیل به کد پیامکی"
```

### Task 5: Add password change to the customer profile

**Files:**
- Modify: `restaurant/frontend/src/pages/CustomerProfilePage.vue`
- Modify: `restaurant/frontend/src/utils/api.js`
- Add assertions to: `restaurant/frontend/tests/customer-account-guardrails.test.mjs`

- [ ] **Step 1: Add a failing UI contract** for current/new/confirmation password fields and the `changeCustomerPassword` API call.
- [ ] **Step 2: Run the focused Node test and confirm RED.**
- [ ] **Step 3: Add the password form, validation messages, busy state, and success state to the profile page.
- [ ] **Step 4: Run the focused test and full frontend tests.**
- [ ] **Step 5: Commit the profile change in Persian.**

```bash
git add frontend/src/pages/CustomerProfilePage.vue frontend/src/utils/api.js frontend/tests/customer-account-guardrails.test.mjs
git commit -m "افزودن تغییر رمز به پروفایل مشتری"
```

### Task 6: Validate both apps and deployment readiness

**Files:**
- Modify only if needed after verification: focused source/test files above.

- [ ] **Step 1: Run restaurant Python focused tests.**

```bash
python3 -m unittest restaurant.tests.test_customer_otp_contract restaurant.tests.test_customer_account
```

- [ ] **Step 2: Run accounts SMS tests.**

```bash
python3 -m unittest accounts.tests.test_sms_ir_customer_otp_contract accounts.tests.test_sms_ir_full_client accounts.tests.test_sms_ir_api_contract
```

- [ ] **Step 3: Run the restaurant frontend test suite and build.**

```bash
cd frontend
npm test
npm run build
```

- [ ] **Step 4: Inspect `git diff --check`, repository status, and generated assets.**
- [ ] **Step 5: Run a read-only site migration check and verify no OTP/API secret is printed.** Do not send a live SMS automatically.
- [ ] **Step 6: Commit any final test-only/doc-only adjustment in Persian and report exact verification results.**
