import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const source = readFileSync(resolve(here, '../public/sw.js'), 'utf8')

test('service worker keeps POS shell addressable across query-string navigation changes', () => {
  assert.match(source, /CACHE_VERSION\s*=\s*["']veederakht-pwa-v4["']/)
  assert.match(source, /function isManagementPOSNavigation\(url\)/)
  assert.match(source, /url\.pathname\s*===\s*["']\/management\/pos["']/)
  assert.match(source, /navigationAlias/)
  assert.match(source, /cache\.put\(navigationCacheRequest\(request\)/)
  assert.match(source, /cache\.match\(navigationCacheRequest\(request\)\)/)
})

test('service worker does not pretend POST management APIs are offline-cacheable', () => {
  assert.match(source, /if \(request\.method !== ["']GET["']\) return/)
  assert.doesNotMatch(source, /request\.method\s*===\s*["']POST["'][\s\S]*cache\.put/)
})
