import test from 'node:test'
import assert from 'node:assert/strict'
import { transformPosProductPanel } from '../scripts/pos-reliability-transform.mjs'

test('compact product cards respect out-of-stock state while keeping quick edit available', () => {
  const fixture = `
<article
  v-for="item in group.items"
  :key="item.slug || item.name"
  class="compact-card"
  :class="{ 'has-qty': quantityValue(item.slug) > 0 }"
>
  <button type="button" class="compact-main-btn" @click="$emit('increment-product', item)">
    <span class="compact-name">{{ item.title || item.name }}</span>
  </button>
  <button type="button" class="compact-action-btn compact-action-btn--primary" @click="$emit('increment-product', item)">+</button>
  <button type="button" class="compact-action-btn compact-action-btn--edit" @click.stop="$emit('quick-edit', item)">edit</button>
</article>
<style scoped>.compact-card { display:block; }</style>`
  const out = transformPosProductPanel(fixture)
  assert.match(out, /'out-of-stock': Number\(item\.out_of_stock\) === 1/)
  assert.match(out, /class="compact-main-btn"\s*:disabled="Number\(item\.out_of_stock\) === 1"/s)
  assert.match(out, /compact-action-btn--primary"\s*:disabled="Number\(item\.out_of_stock\) === 1"/s)
  assert.match(out, /ناموجود/)
  assert.match(out, /compact-action-btn--edit/)
})
