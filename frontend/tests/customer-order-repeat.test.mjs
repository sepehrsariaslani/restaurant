import test from 'node:test'
import assert from 'node:assert/strict'
import { buildCustomerReorderLine } from '../src/utils/customerOrderRepeat.js'

test('reorder rebuilds a regular item with current menu pricing and customization', () => {
	const line = buildCustomerReorderLine(
		{ qty: 2, title: 'ساندویچ', customization: { selected_modifiers: [{ group: 'اندازه', option: 'بزرگ', qty: 1 }] } },
		{
			item: { slug: 'sandwich', title: 'ساندویچ', base_price: 120 },
			modifier_groups: [{ group_name: 'اندازه', title: 'اندازه', options: [{ name: 'بزرگ', label: 'بزرگ', base_price: 40 }] }],
		},
	)

	assert.equal(line.item_slug, 'sandwich')
	assert.equal(line.qty, 2)
	assert.equal(line.unit_price_preview, 160)
	assert.equal(line.line_total_preview, 320)
	assert.equal(line.customization.selected_modifiers[0].option, 'بزرگ')
})

test('reorder recalculates builder price using the current builder quote', () => {
	const line = buildCustomerReorderLine(
		{ qty: 1, customization: { builder_selection: { selections: [{ option: 'large' }] } } },
		{ item: { slug: 'custom-bowl', restaurant_builder_active: 1, base_price: 50 } },
		275,
	)

	assert.equal(line.unit_price_preview, 275)
	assert.equal(line.line_total_preview, 275)
	assert.equal(line.customization.builder_selection.final_price, 275)
})

test('reorder rejects unavailable items and builders without a fresh quote', () => {
	assert.throws(
		() => buildCustomerReorderLine({}, { item: { slug: 'sold-out', out_of_stock: 1 } }),
		/در دسترس نیست/,
	)
	assert.throws(
		() => buildCustomerReorderLine(
			{ customization: { builder_selection: { selections: [{ option: 'large' }] } } },
			{ item: { slug: 'custom-bowl', restaurant_builder_active: 1, base_price: 0 } },
		),
		/قیمت سفارشی‌سازی فعلی/,
	)
	assert.throws(
		() => buildCustomerReorderLine({}, { item: { slug: 'missing-price' } }),
		/قیمت فعلی این محصول/,
	)
})
