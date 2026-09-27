import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const frontendRoot = new URL('../src/', import.meta.url)
async function source(path) { return readFile(new URL(path, frontendRoot), 'utf8') }

test('public collaboration intake explains the terms before collecting a useful recurring-meal proposal', async () => {
  const [page, app, api, hooks] = await Promise.all([
    source('pages/CustomerCollaborationPage.vue'),
    source('App.vue'),
    source('utils/api.js'),
    readFile(new URL('../../restaurant/hooks.py', import.meta.url), 'utf8'),
  ])
  assert.ok(page.indexOf('قواعد همکاری') < page.indexOf('معرفی مجموعهٔ شما'))
  for (const type of ['سازمان و محل کار', 'باشگاه ورزشی', 'مربی و شاگردان']) assert.ok(page.includes(type))
  for (const field of ['organization_name', 'contact_name', 'mobile', 'address', 'frequency', 'weekdays', 'delivery_time']) assert.ok(page.includes(field))
  assert.match(page, /ثبت این فرم فقط درخواست بررسی است/)
  assert.match(page, /submitPublicCollaborationRequest/)
  assert.match(api, /submit_public_collaboration_request/)
  assert.match(app, /customer-collaboration/)
  assert.match(hooks, /"\/cooperation"/)
})

test('management has a protected review route for intake and reuses shared list/detail primitives', async () => {
  const [page, app, layout, backend] = await Promise.all([
    source('pages/management/customers/ManagementCollaborationRequestsPage.vue'),
    source('App.vue'),
    source('components/management/ManagementLayout.vue'),
    readFile(new URL('../../restaurant/api_collaboration.py', import.meta.url), 'utf8'),
  ])
  assert.match(page, /ManagementListView/)
  assert.match(page, /reviewManagementCollaborationRequest/)
  assert.match(app, /management-collaboration-requests/)
  assert.match(layout, /"\/management\/cooperation-requests"/)
  assert.match(backend, /@frappe\.whitelist\(allow_guest=True\)\ndef submit_public_collaboration_request/)
  assert.match(backend, /def review_management_collaboration_request/)
  assert.match(backend, /_ensure_management_access\(\)/)
})

test('recurring customer orders support per-run approval and active monthly organization contracts', async () => {
  const [page, api, backend, doctype, app, hooks] = await Promise.all([
    source('pages/CustomerRecurringOrdersPage.vue'),
    source('utils/api.js'),
    readFile(new URL('../../restaurant/api_recurring.py', import.meta.url), 'utf8'),
    readFile(new URL('../../restaurant/restaurant/doctype/restaurant_recurring_order/restaurant_recurring_order.json', import.meta.url), 'utf8'),
    source('App.vue'),
    readFile(new URL('../../restaurant/hooks.py', import.meta.url), 'utf8'),
  ])
  assert.match(page, /تأیید و پرداخت هر نوبت/)
  assert.match(page, /تسویه در فاکتور ماهانهٔ سازمان/)
  assert.match(backend, /def _contract_for\(customer\)/)
  assert.match(backend, /invoice_mode.*ماهانه/)
  assert.match(backend, /def run_due_recurring_orders\(\)/)
  assert.match(backend, /منتظر تأیید مشتری/)
  assert.match(backend, /def place_my_recurring_order\(/)
  assert.match(doctype, /"module"\s*:\s*"Restaurant"/)
  assert.match(doctype, /RRO-\{YYYY\}/)
  assert.match(api, /create_my_recurring_order/)
  assert.match(app, /customer-recurring-orders/)
  assert.match(hooks, /"\/customer\/recurring-orders"/)
})

test('coach invite binds after email verification and credits non-withdrawable cashback only after settlement', async () => {
  const [dashboard, checkout, api, backend, ordersApi, account, login, transaction, rewards] = await Promise.all([
    source('pages/CustomerDashboardPage.vue'),
    source('pages/CheckoutPage.vue'),
    source('utils/api.js'),
    readFile(new URL('../../restaurant/api_club.py', import.meta.url), 'utf8'),
    readFile(new URL('../../restaurant/api.py', import.meta.url), 'utf8'),
    readFile(new URL('../../restaurant/customer_account.py', import.meta.url), 'utf8'),
    source('pages/CustomerLoginPage.vue'),
    readFile(new URL('../../restaurant/restaurant/doctype/restaurant_wallet_transaction/restaurant_wallet_transaction.json', import.meta.url), 'utf8'),
    readFile(new URL('../../restaurant/coach_rewards.py', import.meta.url), 'utf8'),
  ])
  assert.match(dashboard, /پیوند دعوت اختصاصی/)
  assert.match(dashboard, /coach_members_count/)
  assert.match(login, /referral_code: referralCode/)
  assert.match(account, /bind_my_coach_invite\(customer_token=customer_token, referral_code=referral_code\)/)
  assert.match(api, /customer_token: payload\?\.customer_token \|\| customerEditToken\(\)/)
  assert.match(checkout, /coachDiscountAmount/)
  assert.match(ordersApi, /coach_referral_customer == customer/)
  assert.match(backend, /restaurant_status.*delivered.*served/s)
  assert.match(backend, /bucket="کش‌بک"/)
  assert.match(rewards, /def process_pending_coach_rewards\(/)
  assert.match(rewards, /restaurant_coach_recovery_due/)
  assert.match(rewards, /_restore_sales_invoice_return/)
  assert.match(backend, /relation_kind == "مربی":\s+return False/)
  assert.match(ordersApi, /restaurant_referral_relation_kind_snapshot/)
  assert.match(transaction, /کمیسیون مربی/)
})
