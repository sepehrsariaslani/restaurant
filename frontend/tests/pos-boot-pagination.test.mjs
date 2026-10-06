import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

test('native POS boot exposes pagination instead of truncating products at 300 rows', () => {
  const api = fs.readFileSync(new URL('../../restaurant/api.py', import.meta.url), 'utf8')
  assert.match(api, /def get_management_pos_boot\(branch=None, limit_start=0, limit_page_length=300\)/)
  assert.match(api, /limit_start=offset/)
  assert.match(api, /limit_page_length=page_size \+ 1/)
  assert.match(api, /"items_has_more": has_more/)
})
