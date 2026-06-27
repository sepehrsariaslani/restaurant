import { computed } from 'vue'
import { cartState, defaultOrderContext, saveOrderContext } from '@/stores/cartStore'
import { formatMoney } from '@/utils/format'

export const ORDER_FLOW_CURRENCY_FALLBACK = 'IRR'

export function orderContextChangeUrl(context = cartState.orderContext || {}) {
  if (context.order_type === 'delivery') return '/order/delivery'
  if (context.order_type === 'pickup') return '/order/pickup'
  if (context.order_type === 'dine_in') return '/order/dine-in'
  return '/order/type'
}

export function resetOrderContextForType(type) {
  const nextType = ['dine_in', 'pickup', 'delivery'].includes(type) ? type : ''
  const next = {
    ...defaultOrderContext(),
    order_type: nextType,
    delivery_fee: 0,
  }
  if (nextType !== 'delivery') {
    next.address = null
    next.courier_note = ''
  }
  saveOrderContext(next, { replace: true })
  return next
}

export function calculateOrderTotals({ lines = [], context = {}, discount = 0 } = {}) {
  const subtotal = (Array.isArray(lines) ? lines : []).reduce((sum, line) => {
    return sum + Number(line.line_total_preview ?? (Number(line.base_price || 0) * Number(line.qty || 0)) ?? 0)
  }, 0)
  const deliveryFee = context?.order_type === 'delivery' ? Number(context.delivery_fee || 0) : 0
  const discountAmount = Math.min(Math.max(Number(discount || 0), 0), subtotal + deliveryFee)

  // Tax/service is intentionally not added here until it is backed by server-side rules.
  // This keeps cart and checkout totals identical and avoids over-promising fees.
  const taxAmount = 0
  const serviceAmount = 0
  const grandTotal = Math.max(subtotal + deliveryFee + taxAmount + serviceAmount - discountAmount, 0)

  return {
    subtotal,
    delivery_fee: deliveryFee,
    discount: discountAmount,
    tax: taxAmount,
    service: serviceAmount,
    grand_total: grandTotal,
  }
}

export function useOrderTotals(discountRef = null) {
  return computed(() => calculateOrderTotals({
    lines: cartState.lines,
    context: cartState.orderContext,
    discount: discountRef?.value || 0,
  }))
}

export function orderTypeLabel(context = {}) {
  if (context.order_type === 'dine_in') return 'حضوری داخل سالن'
  if (context.order_type === 'delivery') return 'ارسال با پیک'
  if (context.order_type === 'pickup') return 'بیرون‌بر'
  return 'نوع سفارش انتخاب نشده'
}

export function orderDestinationText(context = {}) {
  if (context.order_type === 'dine_in') {
    return `${context.branch_title || context.branch || 'شعبه'} · میز ${context.table || '-'}`
  }
  if (context.order_type === 'pickup') {
    return `تحویل از ${context.branch_title || context.branch || 'شعبه انتخاب نشده'}`
  }
  if (context.order_type === 'delivery') {
    const address = context.address || {}
    return address.title || address.address_line ? `ارسال به ${address.title || address.address_line}` : 'آدرس انتخاب نشده'
  }
  return 'ابتدا نوع سفارش را انتخاب کنید'
}

export function orderTimeText(context = {}) {
  if (context.order_type === 'pickup') {
    if (context.pickup_time_type === 'scheduled' && context.pickup_time) return `تحویل در ${context.pickup_time}`
    return context.prep_time_mins ? `آماده‌سازی حدود ${context.prep_time_mins} دقیقه` : 'آماده‌سازی پس از تایید شعبه'
  }
  if (context.order_type === 'delivery') {
    if (context.delivery_time_type === 'scheduled' && context.delivery_time) return `ارسال در ${context.delivery_time}`
    if (context.eta_min && context.eta_max) return `${context.eta_min} تا ${context.eta_max} دقیقه`
    return 'زمان نهایی پس از تایید شعبه مشخص می‌شود'
  }
  if (context.order_type === 'dine_in') {
    return context.prep_time_mins ? `آماده سرو حدود ${context.prep_time_mins} دقیقه` : 'پس از تایید آشپزخانه'
  }
  return 'نامشخص'
}

export function deliveryFeeText(context = {}, currency = ORDER_FLOW_CURRENCY_FALLBACK) {
  if (context.order_type !== 'delivery') return 'بدون هزینه ارسال'
  const fee = Number(context.delivery_fee || 0)
  return fee ? formatMoney(fee, currency) : 'هزینه نهایی پس از تایید شعبه'
}

export function orderContextStripText(context = {}, currency = ORDER_FLOW_CURRENCY_FALLBACK) {
  if (!context?.order_type) return 'نوع سفارش هنوز انتخاب نشده است'
  return `${orderDestinationText(context)} · ${orderTimeText(context)} · ${deliveryFeeText(context, currency)}`
}

export function fallbackTimeline(orderType, currentStatus = 'new') {
  const flows = {
    dine_in: ['new', 'confirmed', 'preparing', 'ready', 'served'],
    pickup: ['new', 'confirmed', 'preparing', 'ready', 'delivered'],
    delivery: ['new', 'confirmed', 'preparing', 'courier_handoff', 'on_the_way', 'delivered'],
  }
  const statuses = flows[orderType] || flows.pickup
  const index = statuses.includes(currentStatus) ? statuses.indexOf(currentStatus) : 0
  return statuses.map((status, rowIndex) => ({ status, done: rowIndex <= index }))
}
