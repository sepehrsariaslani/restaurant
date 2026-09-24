import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const root = new URL('../src/pages/', import.meta.url)

async function page(name) {
  return readFile(new URL(name, root), 'utf8')
}

test('guest profile explains the login requirement and does not expose editable fields', async () => {
  const source = await page('CustomerProfilePage.vue')

  assert.match(source, /const isLoggedIn = computed\(\(\) => Boolean\(String\(form\.value\.phone \|\| ''\)\.trim\(\)\)\)/)
  assert.match(source, /v-if="!isLoggedIn"[^]*?ورود به حساب/)
  assert.match(source, /v-else class="customer-section customer-glass-card customer-list-card"/)
  assert.match(source, /if \(!readAuth\(\)\.mobile\)[^]*?customer\/login\?redirect=\/customer\/profile/)
})

test('address form opens manual coordinates when the map key is missing', async () => {
  const source = await page('CustomerAddressesPage.vue')

  assert.match(source, /<details class="location-coordinates" :open="!hasMapKey">/)
  assert.match(source, /ثبت دستی مختصات/)
  assert.match(source, /const hasMapKey = computed\(\(\) => Boolean\(String\(mapConfig\.value\.api_key \|\| ''\)\.trim\(\)\)\)/)
  assert.match(source, /مختصات را دستی وارد کنید تا بتوانید آدرس را ذخیره کنید/)
})
