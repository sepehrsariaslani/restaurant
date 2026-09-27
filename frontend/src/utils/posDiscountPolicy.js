const MAX_DISCOUNT_PERCENT = 100

function safeNumber(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? Math.max(parsed, 0) : 0
}

export function resolvePosDiscount({
  groupDiscountPercent = 0,
  manualDiscountActive = false,
  discountType = 'percent',
  discountValue = 0,
} = {}) {
  const groupPercent = Math.min(safeNumber(groupDiscountPercent), MAX_DISCOUNT_PERCENT)
  const manualValue = safeNumber(discountValue)

  if (manualDiscountActive) {
    return {
      type: discountType === 'fixed' ? 'fixed' : 'percent',
      value: manualValue,
      source: 'manual',
      groupPercent,
    }
  }

  return {
    type: 'percent',
    value: groupPercent,
    source: groupPercent > 0 ? 'customer_group' : '',
    groupPercent,
  }
}

export function discountInputIsManual({
  discountType,
  discountValue,
  targetAmount = null,
} = {}) {
  const hasTarget = targetAmount !== null && targetAmount !== undefined && safeNumber(targetAmount) > 0
  return hasTarget || safeNumber(discountValue) > 0
}
