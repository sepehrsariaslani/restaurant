import test from 'node:test'
import assert from 'node:assert/strict'

import {
  ingredientQtyStep,
  sanitizeCustomization,
  upsertIngredientMultiplier,
  estimateIngredientSelection,
} from '../src/utils/itemConfig.js'

const steak = {
  key: 'فیله استیک مرینیت شده',
  name: 'فیله استیک مرینیت شده',
  base_qty: 120,
  qty_uom: 'گرم',
  is_included_by_default: 1,
  can_remove: 1,
  is_required: 0,
  is_editable_qty: 1,
  min_multiplier: 0,
  max_multiplier: 3,
  step_multiplier: 0.5,
  multiplier_qty: 60,
  unit_rate: 1000,
  conversion_factor: 1,
}

test('BOM ingredient multiplier quantity is scaled by the step multiplier', () => {
  assert.equal(ingredientQtyStep(steak), 30)

  const customization = upsertIngredientMultiplier({}, steak, 1.25)
  const selection = estimateIngredientSelection(steak, customization)

  assert.equal(selection.selectedComponentQty, 150)
  assert.equal(selection.delta, 30000)
})

test('removable included ingredients can be removed even when quantity is locked', () => {
  const lockedRemovable = {
    ...steak,
    key: 'قارچ',
    name: 'قارچ',
    base_qty: 50,
    is_editable_qty: 0,
    multiplier_qty: 0,
  }

  const clean = sanitizeCustomization(
    { ingredient_adjustments: [{ ingredient_key: 'قارچ', multiplier: 0 }] },
    [lockedRemovable],
  )

  assert.deepEqual(clean.ingredient_adjustments, [{ ingredient_key: 'قارچ', multiplier: 0 }])
  assert.equal(estimateIngredientSelection(lockedRemovable, clean).selectedComponentQty, 0)
})
