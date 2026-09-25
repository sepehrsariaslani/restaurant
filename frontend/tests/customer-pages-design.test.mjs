import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const source = (path) => readFileSync(new URL(path, import.meta.url), 'utf8')

test('customer account and service pages use the shared page header', () => {
  const pages = [
    '../src/pages/CustomerAddressesPage.vue',
    '../src/pages/CustomerBranchesPage.vue',
    '../src/pages/CustomerDashboardPage.vue',
    '../src/pages/CustomerDeliveryPage.vue',
    '../src/pages/CustomerOrderDetailPage.vue',
    '../src/pages/CustomerOrdersPage.vue',
    '../src/pages/CustomerProfilePage.vue',
    '../src/pages/CustomerTableReservationPage.vue',
  ]

  for (const page of pages) {
    assert.match(source(page), /CustomerPageHeader/, `${page} should use the shared RTL customer header`)
  }
})

test('customer branches exclude non-company locations and handle missing media and map URLs', () => {
  const page = source('../src/pages/CustomerBranchesPage.vue')

  assert.match(page, /branches\.value\.filter\(isCustomerCompany\)/)
  assert.match(page, /branch\.image && !imageFailed\(branch\)/)
  assert.match(page, /rawUrl === 'https:\/\/maps\.google\.com'/)
  assert.match(page, /return `\/menu\?branch=\$\{encodeURIComponent\(branchKey\(branch\)\)\}`/)
  assert.match(page, /role="status" aria-live="polite"/)
})

test('table reservation selects live available tables and the legacy route returns to that flow', () => {
  const reservation = source('../src/pages/CustomerTableReservationPage.vue')
  const legacyRoute = source('../src/pages/CustomerTableSelectPage.vue')

  assert.match(reservation, /getAvailableTables\(/)
  assert.match(reservation, /:disabled="!t\.is_available"/)
  assert.match(reservation, /aria-pressed="selectedTable\?\.id === t\.id"/)
  assert.doesNotMatch(legacyRoute, /const tables = \[/)
  assert.match(legacyRoute, /window\.location\.replace\('\/table-reservation\?step=table'\)/)
})

test('Veederakht default colors use readable, runtime-derived foregrounds', () => {
  const tokens = source('../src/design-system/tokens.js')
  const themeSettings = source('../src/utils/themeSettings.js')

  assert.match(tokens, /primary: '#B94712'/)
  assert.match(tokens, /accent: '#DFAF2E'/)
  assert.match(themeSettings, /readableForeground\(normalized\.primary\)/)
  assert.match(themeSettings, /readableForeground\(normalized\.accent\)/)
})
