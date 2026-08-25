import test from 'node:test'
import assert from 'node:assert/strict'

import {
  buildProductSettingsPayload,
  createInitialProductSettingsForm,
  hydrateProductSettingsForm,
} from '../src/utils/managementProductDetail.js'

test('product detail save can disable customization even when a builder template is already linked', () => {
  const form = createInitialProductSettingsForm()
  hydrateProductSettingsForm(form, {
    item: {
      item_code: 'BEEF-NOODLE',
      item_name: 'کاسه نودل بیف تریاکی',
      restaurant_is_customizable: 1,
      restaurant_builder_active: 1,
      restaurant_builder_template: 'PBT-01310',
    },
  })

  form.restaurant_is_customizable = false

  const payload = buildProductSettingsPayload({
    itemName: 'کاسه نودل بیف تریاکی',
    form,
    builderConfig: { title: 'Builder', steps: [] },
  })

  assert.equal(payload.restaurant_is_customizable, 0)
  assert.equal(payload.restaurant_builder_active, 0)
  assert.equal(payload.restaurant_builder_template, 'PBT-01310')
})

test('product detail save serializes legacy tag text from selected tag rows', () => {
  const form = createInitialProductSettingsForm()
  hydrateProductSettingsForm(form, {
    item: {
      item_code: 'ITEM-1',
      item_name: 'کالا',
      restaurant_item_tags: 'پرفروش, رژیمی',
    },
  })

  form.restaurant_item_tag_table.push({ tag: 'جدید', _tag_title: 'جدید' })

  const payload = buildProductSettingsPayload({
    itemName: 'ITEM-1',
    form,
  })

  assert.deepEqual(
    payload.restaurant_item_tag_table.map((row) => row._tag_title),
    ['پرفروش', 'رژیمی', 'جدید'],
  )
  assert.equal(payload.restaurant_item_tags, 'پرفروش, رژیمی, جدید')
})
