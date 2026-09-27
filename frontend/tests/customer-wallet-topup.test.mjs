import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const source = (path) => readFileSync(new URL(path, import.meta.url), 'utf8')

test('customer can discover balances and manual top-up from the dashboard and wallet page', () => {
  const dashboard = source('../src/pages/CustomerDashboardPage.vue')
  const wallet = source('../src/pages/CustomerWalletPage.vue')
  const api = source('../src/utils/api.js')

  assert.match(dashboard, /getMyWallet\(\)/)
  assert.match(dashboard, /موجودی قابل برداشت/)
  assert.match(dashboard, /اعتبار خرید \(کش‌بک\)/)
  assert.match(dashboard, /href="\/customer\/wallet"/)
  assert.match(wallet, /requestMyWalletCharge/)
  assert.match(wallet, /submitMyWalletChargeReference/)
  assert.match(wallet, /شارژ کیف پول/)
  assert.match(wallet, /درخواست‌های شارژ/)
  assert.match(api, /customer_token: customerEditToken\(\), amount, payment_reference, note/)
})

test('cashback remains purchase-only and its rule is visible to customers', () => {
  const wallet = source('../src/pages/CustomerWalletPage.vue')
  const api = readFileSync(new URL('../../restaurant/api_club.py', import.meta.url), 'utf8')

  assert.match(wallet, /قانون بازگشت وجه خرید/)
  assert.match(wallet, /قابل برداشت نیست/)
  assert.match(api, /"cashback_percent": settings\["cashback_percent"\]/)
  assert.match(api, /"cashback_min_order": settings\["cashback_min_order"\]/)
})

test('manual top-up is credited only after staff approval and is manageable from loyalty settings', () => {
  const backend = readFileSync(new URL('../../restaurant/api_club.py', import.meta.url), 'utf8')
  const management = source('../src/pages/management/customers/ManagementClubPage.vue')
  const chargeApi = backend.slice(backend.indexOf('def request_my_wallet_charge('), backend.indexOf('def request_my_wallet_withdrawal('))
  const approval = backend.slice(backend.indexOf('def review_management_wallet_charge_request('), backend.indexOf('def charge_management_wallet('))

  assert.match(chargeApi, /request\.insert\(ignore_permissions=True\)/)
  assert.doesNotMatch(chargeApi.slice(0, chargeApi.indexOf('def submit_my_wallet_charge_reference')), /_club_wallet_txn\(/)
  assert.match(approval, /if action == "approve"/)
  assert.match(approval, /kind="شارژ"/)
  assert.match(management, /restaurant_wallet_charge_enabled/)
  assert.match(management, /listManagementWalletChargeRequests/)
  assert.match(management, /reviewManagementWalletChargeRequest/)
  assert.match(management, /پس از تطبیق مبلغ واریزی/)
})
