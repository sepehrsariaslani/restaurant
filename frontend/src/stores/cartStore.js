import { reactive } from 'vue'

const CART_KEY = 'restaurant-cart-v1'
const CHECKOUT_KEY = 'restaurant-checkout-v1'
const LAST_ORDER_KEY = 'restaurant-last-order-v1'

function safeRead(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch (error) {
    return fallback
  }
}

function safeWrite(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (error) {
    // ignore storage write errors
  }
}

function uid() {
  return `line_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

function defaultCheckoutDraft() {
  return {
    customer_name: '',
    mobile: '',
    delivery_mode: 'pickup',
    order_type: 'takeaway',
    delivery_address_id: '',
    use_new_address: true,
    address_title: '',
    address_phone: '',
    address_line: '',
    address_plaque: '',
    address_unit: '',
    address_floor: '',
    address_lat: '',
    address_lng: '',
    note: '',
    include_service_items: true,
  }
}

function normalizeCheckoutDraft(rawValue) {
  const raw = rawValue && typeof rawValue === 'object' ? rawValue : {}
  const deliveryMode = raw.delivery_mode || (raw.order_type === 'delivery' ? 'delivery' : 'pickup')

  return {
    ...defaultCheckoutDraft(),
    ...raw,
    delivery_mode: deliveryMode,
    order_type: deliveryMode === 'delivery' ? 'delivery' : 'takeaway',
    address_line: raw.address_line || raw.address || '',
    include_service_items: raw.include_service_items !== false,
    use_new_address: raw.use_new_address !== false,
  }
}

export const cartState = reactive({
  lines: safeRead(CART_KEY, []),
  checkoutDraft: normalizeCheckoutDraft(safeRead(CHECKOUT_KEY, defaultCheckoutDraft())),
  lastOrder: safeRead(LAST_ORDER_KEY, {
    order_code: '',
    mobile: '',
  }),
})

function persistLines() {
  safeWrite(CART_KEY, cartState.lines)
}

export function saveCheckoutDraft(payload) {
  cartState.checkoutDraft = normalizeCheckoutDraft({
    ...cartState.checkoutDraft,
    ...payload,
  })
  safeWrite(CHECKOUT_KEY, cartState.checkoutDraft)
}

export function saveLastOrder(payload) {
  cartState.lastOrder = {
    ...cartState.lastOrder,
    ...payload,
  }
  safeWrite(LAST_ORDER_KEY, cartState.lastOrder)
}

export function getLineById(lineId) {
  return cartState.lines.find((line) => line.id === lineId)
}

export function upsertLine(payload) {
  const lineId = payload.id || payload.lineId
  const index = lineId ? cartState.lines.findIndex((line) => line.id === lineId) : -1

  const normalized = {
    id: lineId || uid(),
    item_slug: payload.item_slug,
    item_title: payload.item_title,
    item_image: payload.item_image || '',
    base_price: Number(payload.base_price || 0),
    qty: Math.max(Number(payload.qty || 1), 1),
    unit_price_preview: Number(payload.unit_price_preview || payload.base_price || 0),
    line_total_preview: Number(payload.line_total_preview || payload.base_price || 0),
    customization: payload.customization || {
      ingredient_adjustments: [],
      selected_modifiers: [],
    },
    ingredient_catalog: Array.isArray(payload.ingredient_catalog) ? payload.ingredient_catalog : [],
    modifier_groups_catalog: Array.isArray(payload.modifier_groups_catalog) ? payload.modifier_groups_catalog : [],
  }

  if (index >= 0) {
    cartState.lines[index] = normalized
  } else {
    cartState.lines.push(normalized)
  }

  persistLines()
  return normalized
}

export function removeLine(lineId) {
  cartState.lines = cartState.lines.filter((line) => line.id !== lineId)
  persistLines()
}

export function setLineQty(lineId, qty) {
  const line = getLineById(lineId)
  if (!line) {
    return
  }

  const nextQty = Math.max(Number(qty || 1), 1)
  line.qty = nextQty
  line.line_total_preview = Number(line.unit_price_preview || line.base_price || 0) * nextQty
  persistLines()
}

export function clearCart() {
  cartState.lines = []
  persistLines()
}

export function cartSubtotal() {
  return cartState.lines.reduce((sum, line) => sum + Number(line.line_total_preview || 0), 0)
}
