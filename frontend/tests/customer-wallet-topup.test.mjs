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
  assert.match(api, /customer_token: customerEditToken\(\), \.\.\.payload, request_key: key\.requestKey/)
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
  const adapters = backend.slice(backend.lastIndexOf('# Accounts wallet ownership adapters'))
  const chargeApi = adapters.slice(adapters.indexOf('def request_my_wallet_charge('), adapters.indexOf('def submit_my_wallet_charge_reference('))
  const approval = adapters.slice(adapters.indexOf('def review_management_wallet_charge_request('), adapters.indexOf('def _submit_manual_wallet_operation('))

  assert.match(chargeApi, /request_for_customer\(/)
  assert.doesNotMatch(chargeApi, /record_event\(|_club_wallet_txn\(/)
  assert.match(approval, /review_request\(/)
  assert.match(approval, /"approve" if action in \{"approve", "approved"\}/)
  assert.match(management, /restaurant_wallet_charge_enabled/)
  assert.match(management, /listManagementWalletChargeRequests/)
  assert.match(management, /reviewManagementWalletChargeRequest/)
  assert.match(management, /پس از تطبیق مبلغ واریزی/)
})

test('Accounts-owned customer wallet requests accept stable retry keys', () => {
  const backend = readFileSync(new URL('../../restaurant/api_club.py', import.meta.url), 'utf8')
  const api = source('../src/utils/api.js')
  const adapters = backend.slice(backend.lastIndexOf('# Accounts wallet ownership adapters'))
  const charge = adapters.slice(adapters.indexOf('def request_my_wallet_charge('), adapters.indexOf('def submit_my_wallet_charge_reference('))

  assert.match(charge, /request_key=""/)
  assert.match(charge, /source_name=request_key or frappe\.generate_hash/)
  assert.match(api, /request_key: key\.requestKey/)
  assert.match(api, /sessionStorage\?\.setItem\(storageKey, requestKey\)/)
})

test('POS wallet tender validates against the Accounts wallet and ledger', () => {
  const backend = readFileSync(new URL('../../restaurant/api.py', import.meta.url), 'utf8')
  const start = backend.indexOf('def _validate_pos_wallet_tender(')
  const end = backend.indexOf('@frappe.whitelist()\ndef settle_pos_order(', start)
  const validator = backend.slice(start, end)

  assert.match(validator, /_club_wallet_mode_of_payment\(\)/)
  assert.match(validator, /from accounts\.wallet_service import validate_pos_tender/)
  assert.match(validator, /validate_pos_tender\(/)
  assert.doesNotMatch(validator, /`tabCustomer Wallet`|get_doc\("Customer Wallet"|Customer Wallet Settings|withdrawable_balance|cashback_balance/)
  assert.doesNotMatch(validator, /Restaurant Customer Wallet/)
})

test('POS settlement aborts when shared wallet events cannot be recorded', () => {
  const api = readFileSync(new URL('../../restaurant/api.py', import.meta.url), 'utf8')
  const apiClub = readFileSync(new URL('../../restaurant/api_club.py', import.meta.url), 'utf8')
  const settleStart = api.indexOf('def settle_pos_order(')
  const settleEnd = api.indexOf('@frappe.whitelist()\ndef deliver_invoice_only(', settleStart)
  const settlement = api.slice(settleStart, settleEnd)
  const effectsStart = apiClub.indexOf('def club_apply_settle_effects(')
  const effectsEnd = apiClub.indexOf('# ---------------------------------------------------------------------------\n# Referral', effectsStart)
  const effects = apiClub.slice(effectsStart, effectsEnd)

  assert.match(settlement, /except Exception:\s+frappe\.log_error\(frappe\.get_traceback\(\), "Settle POS Club Effects"\)\s+raise/)
  assert.match(effects, /except Exception:\s+frappe\.log_error\(frappe\.get_traceback\(\), "Restaurant club settle effects failed"\)\s+raise/)
})

test('POS wallet debits remain active when loyalty rewards are disabled', () => {
  const apiClub = readFileSync(new URL('../../restaurant/api_club.py', import.meta.url), 'utf8')
  const start = apiClub.indexOf('def club_apply_settle_effects(')
  const end = apiClub.indexOf('# ---------------------------------------------------------------------------\n# Referral', start)
  const effects = apiClub.slice(start, end)

  assert.doesNotMatch(effects, /if not settings\["club_enabled"\]:\s+return/)
  assert.match(effects, /wallet_enabled = _accounts_wallet_enabled\(\)/)
  assert.ok(effects.indexOf('_club_wallet_mode_of_payment()') < effects.indexOf('if wallet_enabled and settings["club_enabled"] and settings["cashback_percent"]'))
  assert.match(effects, /if settings\["club_enabled"\]:\s+_club_process_points_earning\(so_name\)/)
  assert.match(effects, /if wallet_enabled:\s+_club_process_coach_commission\(so_name\)/)
})

test('withdrawal requests are retried with the same idempotency key', () => {
  const api = source('../src/utils/api.js')
  const backend = readFileSync(new URL('../../restaurant/api_club.py', import.meta.url), 'utf8')
  const adapters = backend.slice(backend.lastIndexOf('# Accounts wallet ownership adapters'))
  const withdrawal = adapters.slice(adapters.indexOf('def request_my_wallet_withdrawal('), adapters.indexOf('def list_management_wallets('))

  assert.match(api, /requestMyWalletWithdrawal[\s\S]*?request_key: key\.requestKey/)
  assert.match(withdrawal, /request_key=""/)
  assert.match(withdrawal, /source_name=request_key or frappe\.generate_hash/)
})

test('points conversion locks the customer and uses a stable idempotency key', () => {
  const backend = readFileSync(new URL('../../restaurant/api_club.py', import.meta.url), 'utf8')
  const api = source('../src/utils/api.js')
  const start = backend.indexOf('def _redeem_points_core(')
  const end = backend.indexOf('\n\ndef adjust_management_points', start)
  const conversion = backend.slice(start, end)

  assert.match(conversion, /tabCustomer.*for update/)
  assert.ok(conversion.indexOf('existing_name = frappe.db.get_value') < conversion.indexOf('balance = _club_points_balance'))
  assert.match(conversion, /idempotency_key=request_key/)
  assert.match(api, /points-redemption-customer/)
  assert.match(api, /points-redemption-management/)
})

test('manual cashback requires an idempotency key and company resolution does not guess a default', () => {
  const backend = readFileSync(new URL('../../restaurant/api_club.py', import.meta.url), 'utf8')
  const accountsWallet = backend.slice(backend.lastIndexOf('# Accounts wallet ownership adapters'))
  const cashback = accountsWallet.slice(accountsWallet.indexOf('def grant_management_cashback('))

  assert.match(cashback, /request_key = str\(data\.get\("request_key"\)/)
  assert.match(cashback, /idempotency_key=request_key/)
  assert.doesNotMatch(accountsWallet, /get_user_default\("Company"\)/)
  assert.match(accountsWallet, /if club_company and web_company and club_company != web_company:/)
})

test('referral awards check the Accounts ledger and key events without the reward amount', () => {
  const backend = readFileSync(new URL('../../restaurant/api_club.py', import.meta.url), 'utf8')
  const referralStart = backend.indexOf('def _club_process_referral_reward(')
  const referralEnd = backend.indexOf('\n\n# ---------------------------------------------------------------------------\n# Campaigns', referralStart)
  const referral = backend.slice(referralStart, referralEnd)
  const adapterStart = backend.lastIndexOf('def _club_wallet_txn(')
  const adapterEnd = backend.indexOf('\n\ndef _club_post_cashback_journal', adapterStart)
  const adapter = backend.slice(adapterStart, adapterEnd)

  assert.match(referral, /TRANSACTION as ACCOUNTS_WALLET_TRANSACTION/)
  assert.match(referral, /reference_name": so_name/)
  assert.match(referral, /savepoint\("restaurant_referral_wallet_award"\)/)
  assert.match(adapter, /identity = f"\{company\}:\{reference_doctype\}:\{reference_name\}:\{customer\}:\{kind\}:\{bucket\}:\{direction\}"/)
})
