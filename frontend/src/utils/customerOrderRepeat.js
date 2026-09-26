import { estimateLine } from './itemConfig.js'

export function buildCustomerReorderLine(orderLine = {}, detail = {}, builderPrice = null) {
	const item = detail?.item || {}
	if (!item.slug) throw new Error('نشانی محصول در منو پیدا نشد.')
	if (Number(item.out_of_stock || 0) === 1 || Number(item.stock_out || 0) === 1 || Number(item.coming_soon || 0) === 1) {
		throw new Error('این محصول فعلاً برای سفارش در دسترس نیست.')
	}
	if (
		item.base_price === null
		|| item.base_price === undefined
		|| item.base_price === ''
		|| !Number.isFinite(Number(item.base_price))
		|| Number(item.base_price) < 0
	) {
		throw new Error('قیمت فعلی این محصول دریافت نشد.')
	}

	const requestedQty = Number(orderLine.qty || 1)
	const qty = Number.isFinite(requestedQty) && requestedQty > 0 ? requestedQty : 1
	const customization = orderLine.customization && typeof orderLine.customization === 'object'
		? { ...orderLine.customization }
		: {}
	const isBuilder = Number(item.restaurant_builder_active || 0) === 1
	let preview

	if (isBuilder) {
		const previousSelection = customization.builder_selection || {}
		const selections = Array.isArray(previousSelection.selections)
			? previousSelection.selections
			: Array.isArray(customization.builder_portion_rows)
				? customization.builder_portion_rows
				: []
		if (
			!selections.length
			|| builderPrice === null
			|| builderPrice === undefined
			|| builderPrice === ''
			|| !Number.isFinite(Number(builderPrice))
			|| Number(builderPrice) < 0
		) {
			throw new Error('قیمت سفارشی‌سازی فعلی دریافت نشد.')
		}
		const currentPrice = Number(builderPrice)
		customization.builder_selection = { ...previousSelection, selections, final_price: currentPrice }
		customization.builder_pricing_breakdown = {
			...(customization.builder_pricing_breakdown || {}),
			final_price: currentPrice,
		}
		preview = { unitPrice: currentPrice, lineTotal: currentPrice * qty }
	} else {
		preview = estimateLine({
			basePrice: Number(item.base_price || 0),
			qty,
			ingredients: detail.ingredients || [],
			modifierGroups: detail.modifier_groups || [],
			customization,
		})
	}

	return {
		item_slug: item.slug,
		item_title: item.title || orderLine.title || orderLine.item_name || 'محصول',
		item_image: item.image || orderLine.image || '',
		base_price: Number(item.base_price || 0),
		qty,
		unit_price_preview: Number(preview.unitPrice || 0),
		line_total_preview: Number(preview.lineTotal || 0),
		customization: isBuilder ? customization : preview.customization,
		ingredient_catalog: isBuilder ? [] : (detail.ingredients || []),
		modifier_groups_catalog: isBuilder ? [] : (detail.modifier_groups || []),
	}
}
