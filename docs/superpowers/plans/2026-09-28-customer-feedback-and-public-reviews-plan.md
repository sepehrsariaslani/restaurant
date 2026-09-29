# ثبت صدای مشتری و نمایش عمومی ریویوی محصول Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an authenticated customer-account feedback flow and make newly submitted product reviews public with manager replies visible on product pages.

**Architecture:** Reuse the existing `Restaurant Customer Voice` DocType and add account-bound API methods to `restaurant.api_club`; the server derives customer identity and mobile from `customer_token`. Keep product review storage and public read API unchanged except for setting newly created reviews to approved, then render the existing `manager_reply` in the product review component.

**Tech Stack:** Frappe Python API, isolated `unittest` contract tests, Vue 3 SPA, Vite build.

## Global Constraints

- Do not create new DocTypes or database tables.
- Customer voice writes must derive `customer` and `mobile` from a valid `customer_token`; browser-supplied identity fields are ignored.
- Voice subjects are limited to 140 characters and messages to 2000 characters.
- Valid voice types are exactly `شکایت`, `انتقاد`, `پیشنهاد`, `درخواست`, and `تقدیر`.
- A new product review is public immediately; a manager rejection must set `is_approved=0` and hide it from the public API.
- Preserve the existing unstaged user changes in `restaurant/api_club.py` and do not include them in feature commits.
- Commit messages must be Persian and explain what changed and why.

---

### Task 1: Add authenticated customer voice APIs

**Files:**
- Modify: `restaurant/api_club.py:36-130` to export the account voice methods.
- Modify: `restaurant/api_club.py:2095-2140` to add account-bound submit/list methods beside the existing public voice method.
- Modify: `frontend/src/utils/api.js:4115-4140` to expose client helpers.
- Test: `restaurant/tests/test_customer_voice.py`.

**Interfaces:**
- `submit_my_customer_voice(customer_token=None, payload=None) -> {status, voice}` validates an authenticated customer, accepts `type`, `subject`, `message`, and optional `order_code`, and creates `Restaurant Customer Voice` with status `جدید`.
- `list_my_customer_voices(customer_token=None) -> {voices, count}` returns only records whose `customer` equals the authenticated identity.
- `submitMyCustomerVoice(payload)` and `listMyCustomerVoices()` call the re-exported `restaurant.api` methods and include the stored customer token.

- [ ] **Step 1: Write failing isolated tests**

  Add tests that load `api_club.py` with Frappe stubs and prove:

  ```python
  def test_account_voice_uses_session_identity_and_starts_new(self):
      result = module.submit_my_customer_voice(
          customer_token="valid-token",
          payload={"type": "پیشنهاد", "subject": "منو", "message": "غذای روزانه اضافه شود"},
      )
      self.assertEqual(result["voice"]["status"], "جدید")
      self.assertEqual(saved.customer, "CUST-1")
      self.assertEqual(saved.mobile, "09123456789")
  ```

  Also cover invalid session, invalid type, missing subject/message, and an order code belonging to a different customer. The list test must prove rows for another customer are excluded.

- [ ] **Step 2: Run the focused tests and verify the expected failures**

  Run: `python -m unittest restaurant.tests.test_customer_voice -v`

  Expected: FAIL because the account methods and frontend helpers do not exist yet.

- [ ] **Step 3: Implement the minimal secure API**

  Add `submit_my_customer_voice` and `list_my_customer_voices` to `__all__`. Both methods use `_require_customer(customer_token)`. Submission validates the existing `VOICE_TYPES`, requires trimmed subject/message, truncates subject/message to 140/2000 characters, normalizes the session mobile with `_ensure_mobile`, verifies an optional order code with `_club_verify_survey_order`, and rejects a matching order linked to another customer. It saves a new `Restaurant Customer Voice` with `customer`, `customer_name`, `mobile`, `sales_order`, `order_code`, `type`, `subject`, `message`, and `status="جدید"`, then commits. Listing filters by the authenticated customer and serializes rows with `_serialize_voice`.

  Add these frontend helpers:

  ```js
  export function submitMyCustomerVoice(payload = {}) {
    return callRestaurantAPI('submit_my_customer_voice', {
      customer_token: customerEditToken(),
      payload,
    })
  }

  export function listMyCustomerVoices() {
    return callRestaurantAPI('list_my_customer_voices', { customer_token: customerEditToken() })
  }
  ```

- [ ] **Step 4: Run the focused tests and verify they pass**

  Run: `python -m unittest restaurant.tests.test_customer_voice -v`

  Expected: PASS with all account voice security cases green.

- [ ] **Step 5: Commit the task**

  Run: `git add restaurant/api_club.py frontend/src/utils/api.js restaurant/tests/test_customer_voice.py && git commit -m "افزودن ثبت امن صدای مشتری در حساب"`

### Task 2: Make new product reviews public while preserving moderation removal

**Files:**
- Modify: `restaurant/api_survey.py:540-551` to mark newly created reviews as approved.
- Test: `restaurant/tests/test_customer_review_publication.py`.

**Interfaces:**
- Existing `submit_public_survey` continues to create one `Restaurant Customer Review` per submitted order item.
- Existing `get_item_reviews` continues to filter `is_approved=1` and returns `manager_reply`.

- [ ] **Step 1: Write failing publication tests**

  Add a focused test that captures the newly inserted review document and asserts:

  ```python
  self.assertEqual(saved_review.moderation_status, 'تأییدشده')
  self.assertEqual(saved_review.is_approved, 1)
  ```

  Add a read-path test or contract assertion that a rejected review (`is_approved=0`) is excluded while an approved review with `manager_reply='پاسخ مجموعه'` includes that reply in the public payload.

- [ ] **Step 2: Run the focused tests and verify the expected failure**

  Run: `python -m unittest restaurant.tests.test_customer_review_publication -v`.

  Expected: FAIL because new reviews currently start as `در انتظار بررسی` and `is_approved=0`.

- [ ] **Step 3: Implement the minimal publication change**

  In `submit_public_survey`, assign `doc.moderation_status = "تأییدشده"` and `doc.is_approved = 1` for new and edited customer reviews. Do not change the public filter: a manager rejection must continue to make the review disappear.

- [ ] **Step 4: Run the focused tests and verify they pass**

  Run: `python -m unittest restaurant.tests.test_customer_review_publication -v` and the existing survey security suite.

  Expected: PASS, including manager-reply preservation and rejection hiding.

- [ ] **Step 5: Commit the task**

  Run: `git add restaurant/api_survey.py restaurant/tests/test_customer_review_publication.py restaurant/tests/test_customer_survey_security.py && git commit -m "عمومی‌کردن ریویوی جدید محصول با حفظ رد مدیریت"`

### Task 3: Add the feedback form and history to the customer dashboard

**Files:**
- Modify: `frontend/src/pages/CustomerDashboardPage.vue:66-110` to add the account feedback section.
- Modify: `frontend/src/pages/CustomerDashboardPage.vue:291-405` to load, submit, and refresh customer voices.
- Modify: `frontend/src/pages/CustomerDashboardPage.vue` style block to match existing customer cards and responsive forms.

**Interfaces:**
- Consumes `submitMyCustomerVoice(payload)` and `listMyCustomerVoices()` from Task 1.
- Displays `type`, `subject`, `message`, `status`, `response`, `creation`, and optional `order_code` returned by the API.

- Test: `frontend/tests/customer-feedback.test.mjs`.

- [ ] **Step 1: Add the frontend source contract test**

  Add a Node source contract test that reads `CustomerDashboardPage.vue`, `ItemDetailPage.vue`, and `utils/api.js` and asserts the dashboard imports and calls both voice helpers, renders `type`, `subject`, `message`, and `order_code`, renders status/response history, and the product page renders `manager_reply`.

- [ ] **Step 2: Run the frontend contract test and verify the expected failure**

  Run: `node --test tests/customer-feedback.test.mjs` from `/home/sepehr/den-v16-docker/apps/restaurant/frontend`.

  Expected: FAIL because the dashboard has no customer voice state, form, or API calls.

- [ ] **Step 3: Implement the dashboard flow**

  Add an account card after the survey/reply area. The card contains a type select, subject input, message textarea, optional order code input, submit button, success/error feedback, and a compact history list. On mount, load the customer’s voices alongside invitations/reviews. On success, clear the form, prepend or reload the saved entry, and show the returned status. Keep the form hidden behind the existing authenticated dashboard redirect.

- [ ] **Step 4: Run the frontend build and verify it passes**

  Run: `npm run build` from `/home/sepehr/den-v16-docker/apps/restaurant/frontend`.

  Expected: exit code 0 with the dashboard compiling and no Vue template/import errors.

- [ ] **Step 5: Commit the task**

  Run: `git add frontend/src/pages/CustomerDashboardPage.vue frontend/tests/customer-feedback.test.mjs && git commit -m "افزودن پیشنهاد و انتقاد به حساب مشتری"`

### Task 4: Verify product-page review and manager-reply rendering

**Files:**
- Test: `frontend/tests/customer-feedback.test.mjs`.

**Interfaces:**
- Product details call `getItemReviews({ item_slug, page_size: 50 })`.
- Review rows normalize `customer_name`, `rating`, `comment`, `strengths`, `weaknesses`, and `manager_reply`.

- [ ] **Step 1: Verify the existing rendering contract**

  Confirm the product page renders `rv.manager_reply` under the corresponding review and that the API returns it for approved reviews.

- [ ] **Step 2: Keep the existing product rendering contract intact**

  The current product page must keep showing the manager reply only when non-empty, under the matching review. No product-page source change is required when the contract test passes.

- [ ] **Step 3: Run the final verification set**

  Run:

  ```bash
  python -m unittest restaurant.tests.test_customer_voice restaurant.tests.test_customer_review_publication restaurant.tests.test_customer_survey_security -v
  npm run build
  git diff --check
  git status --short
  ```

  Expected: all focused Python tests pass, frontend build exits 0, diff check is clean, and only intended feature files plus the pre-existing user change remain visible.
