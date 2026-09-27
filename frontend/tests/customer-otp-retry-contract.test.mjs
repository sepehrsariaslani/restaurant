import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const page = fs.readFileSync(path.join(here, '../src/pages/CustomerLoginPage.vue'), 'utf8')
const api = fs.readFileSync(path.join(here, '../../restaurant/api.py'), 'utf8')

test('customer OTP cooldown is returned as a normal response and shown to the customer', () => {
  assert.match(api, /"cooldown": True/)
  assert.match(page, /result\?\.cooldown/)
  assert.match(page, /e\?\.message/)
})
